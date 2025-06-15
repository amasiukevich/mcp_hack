import logging
import time

import requests

from gmail_integration.gmail_client import Email, GmailClient

mcp_api_url = "http://0.0.0.0:8000"

def call_mcp_server(query: str) -> str:
    url = mcp_api_url + "/query"
    params = {"query": query}
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

    while True:

        logging.info("Getting unread messages...")
        emails: list[Email] = gmail_client.get_unread_messages(
            max_results=10, mark_as_read=True
        )

        for email in emails:
            query = create_query(email)

            result = call_mcp_server(query=query)
            logging.info(f"Request: {query}")
            logging.info(f"Response: {result}")

            gmail_client.reply_to_email(email, result)

        time.sleep(10)
