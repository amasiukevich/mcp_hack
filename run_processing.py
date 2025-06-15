import logging
import time

import requests

from gmail_integration.gmail_client import Email, GmailClient

mcp_api_url = "http://0.0.0.0:8000"

def call_mcp_server(email: str, query: str) -> str:
    url = mcp_api_url + "/query"
    params = {"email": email, "query": query}
    headers = {"accept": "application/json"}

    try:
        response = requests.post(url, headers=headers, params=params, data="")
        response.raise_for_status()

        return response.json()["response"]
    except requests.RequestException as e:
        logging.error(f"Error calling MCP server: {e}")
        return f"Error: {str(e)}"


def create_query(email: Email) -> str:
    query = f"Send from email: {email.sender}\n"
    query += f"Email subject: {email.subject}\n"
    query += f"Email text: \n{email.body}"

    return query


if __name__ == "__main__":
    gmail_client = GmailClient(
        credentials_file="credentials.json",
        token_file="token.json",
    )

    unique_message_ids = set()

    while True:

        print("Getting unread messages...")
        emails: list[Email] = gmail_client.get_unread_messages(
            max_results=10, mark_as_read=True
        )
        emails = [email for email in emails if email.message_id not in unique_message_ids]
        print(f"Found {len(emails)} unread messages")

        unique_message_ids.update([email.message_id for email in emails])

        for email in emails:
            result = call_mcp_server(email=email.sender, query=email.body)
            logging.info(f"Request: {email.sender} {email.body}")
            logging.info(f"Response: {result}")

            gmail_client.reply_to_email(email, result)

        time.sleep(10)
