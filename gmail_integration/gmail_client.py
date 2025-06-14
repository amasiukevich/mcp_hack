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
    message_id: str  # Google's internal ID
    thread_id: str
    sender: str
    recipient: str
    subject: str
    date: str
    body: str
    timestamp: datetime  # For sorting
    email_message_id: str  # Standard email Message-ID header

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
    # Using full access scope
    SCOPES = ["https://mail.google.com/"]

    def __init__(
        self, credentials_file: str = "credentials.json", token_file: str = "token.json"
    ):
        """Initialize the Gmail client.

        Args:
            credentials_file: Path to the credentials JSON file.
            token_file: Path to store the token.
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = self._authenticate()

    def _authenticate(self) -> Any:
        """Authenticate with Gmail API.

        Returns:
            Authenticated Gmail API service.
        """
        creds = None

        # Load existing token if available
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)

        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save token for future use
            with open(self.token_file, "w") as token:
                token.write(creds.to_json())

        return build("gmail", "v1", credentials=creds)

    def _parse_email_message(self, message: dict) -> Email:
        """Parse Gmail API message into Email dataclass.

        Args:
            message: Gmail API message object.

        Returns:
            Email dataclass with parsed data.
        """
        # Extract headers
        headers = message["payload"]["headers"]
        email_data = {
            "message_id": message["id"],  # Google's internal ID
            "thread_id": message["threadId"],
            "sender": "",
            "recipient": "",
            "subject": "",
            "date": "",
            "body": "",
            "timestamp": datetime.now(),  # Default value
            "email_message_id": "",  # Standard email Message-ID header
        }

        # Extract header values
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
                # Try to parse the date for sorting
                try:
                    # RFC 2822 format often used in email headers
                    email_data["timestamp"] = datetime.strptime(
                        header["value"], "%a, %d %b %Y %H:%M:%S %z"
                    )
                except ValueError:
                    # If parsing fails, keep the default timestamp
                    pass
            elif name.lower() == "message-id":
                email_data["email_message_id"] = header["value"]

        # Extract body
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
        """Get the last received email.

        Returns:
            Email dataclass or None if no emails found.
        """
        try:
            # Get the list of messages, only the most recent one from INBOX
            results = (
                self.service.users()
                .messages()
                .list(userId="me", maxResults=1, labelIds=["INBOX"])
                .execute()
            )

            messages = results.get("messages", [])

            if not messages:
                return None

            # Get the full message details
            msg = (
                self.service.users()
                .messages()
                .get(userId="me", id=messages[0]["id"], format="full")
                .execute()
            )

            return self._parse_email_message(msg)

        except HttpError as error:
            print(f"An error occurred while retrieving email: {error}")
            return None

    def get_emails_by_sender(
        self, sender_email: str, max_results: int = 10
    ) -> List[Email]:
        """Get emails from a specific sender.

        Args:
            sender_email: Email address of the sender to filter by.
            max_results: Maximum number of emails to retrieve.

        Returns:
            List of Email dataclasses sorted by timestamp (newest first).
        """
        try:
            # Search for emails from the specified sender
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
                # Get the full message details
                msg = (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=message["id"], format="full")
                    .execute()
                )

                emails.append(self._parse_email_message(msg))

            # Sort emails by timestamp (newest first)
            return sorted(emails, key=lambda x: x.timestamp, reverse=True)

        except HttpError as error:
            print(f"An error occurred while retrieving emails: {error}")
            return []

    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send an email.

        Args:
            to_email: Email address of the recipient.
            subject: Subject of the email.
            body: Body text of the email.

        Returns:
            True if email was sent successfully, False otherwise.
        """
        try:
            # Create an EmailMessage object
            message = EmailMessage()
            message["To"] = to_email
            message["Subject"] = subject
            message.set_content(body)

            # Encode the EmailMessage object into a base64url string
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # Create the message payload for the API
            create_message = {"raw": encoded_message}

            # Send the message
            self.service.users().messages().send(
                userId="me", body=create_message
            ).execute()

            return True

        except HttpError as error:
            print(f"An error occurred while sending email: {error}")
            return False

    def reply_to_email(self, email: Email, body: str) -> bool:
        """Reply to an email with proper quoting of previous messages.

        Args:
            email: The Email object to reply to
            body: Body text of the reply

        Returns:
            True if reply was sent successfully, False otherwise.
        """
        try:
            # Extract the original sender to use as recipient
            to_email = email.sender

            # Create reply subject (Re: original subject)
            subject = email.subject
            if not subject.lower().startswith("re:"):
                subject = f"Re: {subject}"

            # Format the quoted text like Gmail does
            quoted_text_html = self._format_quoted_text_html(email)

            # Create the reply message
            message = EmailMessage()
            message["To"] = to_email
            message["Subject"] = subject

            # Use the proper email Message-ID for threading
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

            print(f"Reply sent to {to_email} with thread ID: {email.thread_id}")
            return True

        except HttpError as error:
            print(f"An error occurred while sending reply: {error}")
            return False

    def _format_quoted_text_html(self, email: Email) -> str:
        """Format the original email as quoted text in HTML with vertical line.

        Args:
            email: The Email object to quote

        Returns:
            Formatted quoted text in HTML
        """
        # Format the date in a readable format
        try:
            date_obj = email.timestamp
            formatted_date = date_obj.strftime("%a, %b %d, %Y at %I:%M %p")
        except (ValueError, AttributeError):
            formatted_date = email.date

        # Format the quoted header like Gmail does
        quoted_header = f"On {formatted_date}, {email.sender} wrote:"

        # Format the body with a vertical line
        quoted_body = email.body.replace("\n", "<br>")

        # The CSS creates a vertical line similar to Gmail's interface
        return f"""
        <div style="margin-top: 0px; color: #666;">
            <div>{quoted_header}</div>
            <blockquote style="margin: 0 0 0 0.8ex; padding-left: 1ex; border-left: 1px solid #ccc;">{quoted_body}</blockquote>
        </div>
        """


# Example usage
if __name__ == "__main__":
    # Create Gmail client
    gmail = GmailClient()

    # success = gmail.send_email(
    #     to_email="vtitko27@gmail.com",
    #     subject="Test Email from GmailClient Class",
    #     body="Hello! This is a test email sent using the GmailClient class.",
    # )
    # if success:
    #     print("Email sent successfully!")
    # else:
    #     print("Failed to send email.")

    # Get the last email
    print("Getting last email...")
    last_email = gmail.get_last_email()

    if last_email:
        with open("email_last.json", "w") as f:
            json.dump([last_email.to_dict()], f, indent=4)

    if last_email:
        print(f"Last email from: {last_email.sender}")
        print(f"Subject: {last_email.subject}")
        print(f"Date: {last_email.date}")
        print(f"Thread ID: {last_email.thread_id}")
        print(f"Body preview: {last_email.body[:100]}...")

        # Reply to the last email with proper quoting
        print("\nReplying to the last email...")
        reply_body = (
            "This is an automated reply to your email."
            "\nThank you for your message."
            f"\nCurrent time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        if gmail.reply_to_email(last_email, reply_body):
            print("Reply sent successfully!")
        else:
            print("Failed to send reply.")

    else:
        print("No emails found.")
