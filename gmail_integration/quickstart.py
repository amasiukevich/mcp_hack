import base64
import os.path
from email.message import EmailMessage
from typing import Any, Dict, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
# Using 'https://mail.google.com/' for full read/write access.
# If you only need to send, 'https://www.googleapis.com/auth/gmail.send' is sufficient.
SCOPES = ["https://mail.google.com/"]
# Alternatively, if you want more granular control:
# SCOPES = [
#     "https://www.googleapis.com/auth/gmail.readonly", # For reading emails
#     "https://www.googleapis.com/auth/gmail.send"      # For sending emails
# ]


def main() -> None:
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels, gets the last email, and sends a new email.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # Build the Gmail API service
        service = build("gmail", "v1", credentials=creds)

        # --- List Gmail Labels ---
        print("--- Gmail Labels ---")
        results = service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])

        if not labels:
            print("No labels found.")
        else:
            print("Labels:")
            for label in labels:
                print(f"- {label['name']}")

        # --- Get the last received email ---
        print("\n--- Last Received Email ---")
        last_email = get_last_email(service)
        if last_email:
            print(f"From: {last_email.get('from', 'Unknown')}")
            print(f"Subject: {last_email.get('subject', 'No Subject')}")
            print(f"Date: {last_email.get('date', 'Unknown')}")
            # Print only a snippet of the body for brevity
            print(f"Body: {last_email.get('body', 'No Body')[:100]}...")
        else:
            print("No emails found in inbox.")

        # --- Send an Email ---
        print("\n--- Sending a Test Email ---")
        # !!! IMPORTANT: Replace these with actual email addresses for testing !!!
        # The 'to_email' should be a valid email address you can check.
        # The sender will be the Gmail account you authenticated with.

        # NOTE: Make sure the authenticated user's email is set as 'my_email'
        # in create_raw_message if you choose to modify that function.
        # For simplicity, send_email currently uses the authenticated user as sender ('me').

        # recipient_email = "pahanchik.pk@gmail.com" # Replace with your test recipient email
        recipient_email = "vtitko27@gmail.com"  # Replace with your test recipient email

        try:
            send_email(
                service=service,
                to_email=recipient_email,
                subject="Test Email from Gmail API (Updated)",
                body="Hello! This is an updated test email sent using the Gmail API, confirming write access.",
            )
            print("Email sent successfully!")
        except HttpError as error:
            print(f"An error occurred while trying to send email: {error}")

    except HttpError as error:
        print(f"An error occurred with Gmail API: {error}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def get_last_email(service: Any) -> Optional[Dict[str, str]]:
    """Get the last received email.

    Args:
        service: Authorized Gmail API service instance.

    Returns:
        A dictionary containing email details or None if no emails found.
    """
    try:
        # Get the list of messages, only the most recent one from INBOX
        results = (
            service.users()
            .messages()
            .list(userId="me", maxResults=1, labelIds=["INBOX"])
            .execute()
        )

        messages = results.get("messages", [])

        if not messages:
            return None

        # Get the full message details
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=messages[0]["id"], format="full")
            .execute()
        )

        # Extract headers
        headers = msg["payload"]["headers"]
        email_data = {}

        for header in headers:
            name = header["name"].lower()
            if name in ["from", "to", "subject", "date"]:
                email_data[name] = header["value"]

        # Extract body content (handles multipart and plain text)
        if "parts" in msg["payload"]:
            for part in msg["payload"]["parts"]:
                if part["mimeType"] == "text/plain" and "data" in part["body"]:
                    body = base64.urlsafe_b64decode(
                        part["body"]["data"].encode("ASCII")
                    ).decode("utf-8")
                    email_data["body"] = body
                    break  # Assuming we only want the first plain text part
        elif "body" in msg["payload"] and "data" in msg["payload"]["body"]:
            # Handle cases where the email is a simple plain text message
            body = base64.urlsafe_b64decode(
                msg["payload"]["body"]["data"].encode("ASCII")
            ).decode("utf-8")
            email_data["body"] = body
        else:
            email_data["body"] = "No decipherable body content found."

        return email_data

    except HttpError as error:
        print(f"An error occurred while retrieving email: {error}")
        return None


def send_email(service: Any, to_email: str, subject: str, body: str) -> None:
    """Send an email using Gmail API.

    Args:
        service: Authorized Gmail API service instance.
        to_email: Email address of the recipient.
        subject: Subject of the email.
        body: Body text of the email.
    """
    try:
        # Create an EmailMessage object
        message = EmailMessage()
        message["To"] = to_email
        # The 'From' header is automatically set by Gmail when using 'userId="me"'
        # message["From"] = "your_email@gmail.com" # You can explicitly set this if needed
        message["Subject"] = subject
        message.set_content(body)

        # Encode the EmailMessage object into a base64url string
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Create the message payload for the API
        create_message = {"raw": encoded_message}

        # Send the message
        service.users().messages().send(userId="me", body=create_message).execute()

    except HttpError as error:
        # Re-raise the error after printing, so the main function can catch it.
        print(f"An error occurred while sending email: {error}")
        raise


if __name__ == "__main__":
    main()
