import json
import time

from gmail_integration.gmail_client import Email, GmailClient
from llm_function_calling.llm_engine import LLMEngine

if __name__ == "__main__":
    # Example usage
    engine = LLMEngine()
    gmail_client = GmailClient(
        credentials_file="gmail_integration/credentials.json",
        token_file="gmail_integration/token.json",
    )

    while True:

        print("Getting unread messages...")
        emails: list[Email] = gmail_client.get_unread_messages(
            max_results=10, mark_as_read=True
        )

        for email in emails:
            email_body = email.body
            result = engine.create_response(query=email_body)
            print("Request:")
            print(email_body)
            print("Response:")
            print(json.dumps(result, indent=4))

            gmail_client.reply_to_email(email, result)

        time.sleep(10)
