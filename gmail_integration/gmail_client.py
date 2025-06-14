import base64
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
    sender: str
    recipient: str
    subject: str
    date: str
    body: str
    timestamp: datetime  # For sorting


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
            "message_id": message["id"],
            "sender": "",
            "recipient": "",
            "subject": "",
            "date": "",
            "body": "",
            "timestamp": datetime.now(),  # Default value
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


# Example usage
if __name__ == "__main__":
    # Create Gmail client
    gmail = GmailClient()

    # Get the last email
    print("Getting last email...")
    last_email = gmail.get_last_email()
    if last_email:
        print(f"Last email from: {last_email.sender}")
        print(f"Subject: {last_email.subject}")
        print(f"Date: {last_email.date}")
        print(f"Body preview: {last_email.body[:100]}...")
    else:
        print("No emails found.")

    # Get emails from a specific sender
    sender = "vtitko27@gmail.com"  # Replace with a sender email to test
    print(f"\nGetting emails from {sender}...")
    emails = gmail.get_emails_by_sender(sender, max_results=5)
    print(f"Found {len(emails)} emails from {sender}")
    for i, email in enumerate(emails):
        print(f"{i+1}. Subject: {email.subject} (Date: {email.date})")

    # Send an email
    recipient = "vtitko27@gmail.com"  # Replace with your test recipient
    print(f"\nSending test email to {recipient}...")
    success = gmail.send_email(
        to_email=recipient,
        subject="Test Email from GmailClient Class",
        body="Hello! This is a test email sent using the GmailClient class.",
    )
    if success:
        print("Email sent successfully!")
    else:
        print("Failed to send email.")
