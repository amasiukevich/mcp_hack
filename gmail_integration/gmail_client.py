import base64
import json
import os.path
from dataclasses import dataclass
from datetime import datetime
from email.message import EmailMessage
from typing import Any, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


@dataclass
class Email:
    message_id: str
    thread_id: str
    sender: str
    recipient: str
    subject: str
    date: str
    body: str
    timestamp: datetime
    email_message_id: str

    def to_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "thread_id": self.thread_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "subject": self.subject,
            "date": self.date,
            "body": self.body,
            "timestamp": self.timestamp.isoformat(),
            "email_message_id": self.email_message_id,
        }


class GmailClient:
    SCOPES = ["https://mail.google.com/"]

    def __init__(
        self, credentials_file: str = "credentials.json", token_file: str = "token.json"
    ):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = self._authenticate()

    def _authenticate(self) -> Any:
        creds = None

        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(self.token_file, "w") as token:
                token.write(creds.to_json())

        return build("gmail", "v1", credentials=creds)

    def _parse_email_message(self, message: dict) -> Email:
        headers = message["payload"]["headers"]
        email_data = {
            "message_id": message["id"],
            "thread_id": message["threadId"],
            "sender": "",
            "recipient": "",
            "subject": "",
            "date": "",
            "body": "",
            "timestamp": datetime.now(),
            "email_message_id": "",
        }

        for header in headers:
            name = header["name"].lower()
            if name == "from":
                email_data["sender"] = header["value"]
            elif name == "to":
                email_data["recipient"] = header["value"]
            elif name == "subject":
                email_data["subject"] = header["value"]
            elif name == "date":
                email_data["date"] = header["value"]
                try:
                    email_data["timestamp"] = datetime.strptime(
                        header["value"], "%a, %d %b %Y %H:%M:%S %z"
                    )
                except ValueError:
                    pass
            elif name.lower() == "message-id":
                email_data["email_message_id"] = header["value"]

        if "parts" in message["payload"]:
            for part in message["payload"]["parts"]:
                if part["mimeType"] == "text/plain" and "data" in part["body"]:
                    body = base64.urlsafe_b64decode(
                        part["body"]["data"].encode("ASCII")
                    ).decode("utf-8")
                    email_data["body"] = body
                    break
        elif "body" in message["payload"] and "data" in message["payload"]["body"]:
            body = base64.urlsafe_b64decode(
                message["payload"]["body"]["data"].encode("ASCII")
            ).decode("utf-8")
            email_data["body"] = body

        return Email(**email_data)

    def get_last_email(self) -> Optional[Email]:
        try:
            results = (
                self.service.users()
                .messages()
                .list(userId="me", maxResults=1, labelIds=["INBOX"])
                .execute()
            )

            messages = results.get("messages", [])

            if not messages:
                return None

            msg = (
                self.service.users()
                .messages()
                .get(userId="me", id=messages[0]["id"], format="full")
                .execute()
            )

            return self._parse_email_message(msg)

        except HttpError as error:
            return None

    def get_emails_by_sender(
        self, sender_email: str, max_results: int = 10
    ) -> List[Email]:
        try:
            query = f"from:{sender_email}"
            results = (
                self.service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results)
                .execute()
            )

            messages = results.get("messages", [])
            emails = []

            for message in messages:
                msg = (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=message["id"], format="full")
                    .execute()
                )

                emails.append(self._parse_email_message(msg))

            return sorted(emails, key=lambda x: x.timestamp, reverse=True)

        except HttpError as error:
            return []

    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        try:
            message = EmailMessage()
            message["To"] = to_email
            message["Subject"] = subject
            message.set_content(body)

            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            create_message = {"raw": encoded_message}

            self.service.users().messages().send(
                userId="me", body=create_message
            ).execute()

            return True

        except HttpError as error:
            return False

    def reply_to_email(self, email: Email, body: str) -> bool:
        try:
            to_email = email.sender

            subject = email.subject
            if not subject.lower().startswith("re:"):
                subject = f"Re: {subject}"

            quoted_text_html = self._format_quoted_text_html(email)

            message = EmailMessage()
            message["To"] = to_email
            message["Subject"] = subject

            if email.email_message_id:
                message["References"] = email.email_message_id
                message["In-Reply-To"] = email.email_message_id

            body = body.replace("\n>", "<br>")
            body = body.replace("\n", "<br>")
            html_content = f"""
            <div style="font-family: Arial, sans-serif;">
                <div>{body}</div>
                {quoted_text_html}
            </div>
            """
            html_content = html_content.replace("\n", "")

            message.set_content(html_content, subtype="html")
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            create_message = {"raw": encoded_message, "threadId": email.thread_id}

            self.service.users().messages().send(
                userId="me", body=create_message
            ).execute()

            return True

        except HttpError as error:
            return False

    def _format_quoted_text_html(self, email: Email) -> str:
        try:
            date_obj = email.timestamp
            formatted_date = date_obj.strftime("%a, %b %d, %Y at %I:%M %p")
        except (ValueError, AttributeError):
            formatted_date = email.date

        quoted_header = f"On {formatted_date}, {email.sender} wrote:"

        quoted_body = email.body.replace("\n", "<br>")

        return f"""
        <div style="margin-top: 0px; color: #666;">
            <div>{quoted_header}</div>
            <blockquote style="margin: 0 0 0 0.8ex; padding-left: 1ex; border-left: 1px solid #ccc;">{quoted_body}</blockquote>
        </div>
        """


if __name__ == "__main__":
    gmail = GmailClient()

    last_email = gmail.get_last_email()

    if last_email:
        reply_body = (
            "This is an automated reply to your email."
            "\nThank you for your message."
            f"\nCurrent time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        gmail.reply_to_email(last_email, reply_body)
