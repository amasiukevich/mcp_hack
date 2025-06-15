import os
from typing import Any, Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from starlette.middleware.sessions import SessionMiddleware

# Load environment variables from .env file
load_dotenv()

# Set this environment variable to allow OAuth2 on HTTP (only for development)
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

app = FastAPI(title="Gmail API Authentication")
# For development, use a strong random secret key in production
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("API_SECRET_KEY", "super-secret-development-key"),
)

# Add CORS middleware to allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Update with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define where your credentials.json and token.json will be stored on the server
CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")

# The scopes required for your application
SCOPES = ["https://mail.google.com/"]  # For full read/write access


def get_gmail_service() -> Optional[Any]:
    """Gets an authenticated Gmail service instance."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If there are no (valid) credentials available, return None,
    # and the frontend needs to initiate the OAuth flow.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(GoogleRequest())
                with open(TOKEN_FILE, "w") as token:
                    token.write(creds.to_json())
            except Exception as e:
                print(f"Token refresh failed: {e}")
                return None
        else:
            return None  # No valid credentials, need full OAuth flow

    try:
        service = build("gmail", "v1", credentials=creds)
        return service
    except HttpError as error:
        print(f"Error building Gmail service: {error}")
        return None


@app.get("/authorize")
async def authorize(request: Request):
    """Initiates the Google OAuth 2.0 flow."""
    base_url = str(request.base_url)
    callback_url = f"{base_url}oauth2callback"

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=callback_url
    )
    authorization_url, state = flow.authorization_url(
        access_type="offline",  # Important to get a refresh token
        include_granted_scopes="true",
    )
    request.session["oauth_state"] = state
    return RedirectResponse(authorization_url)


@app.get("/oauth2callback")
async def oauth2callback(request: Request):
    """Callback endpoint for Google OAuth 2.0."""
    state = request.session.get("oauth_state")
    query_state = request.query_params.get("state")

    print(f"State from session: {state}")
    print(f"State from query: {query_state}")

    if not state or state != query_state:
        print(f"State validation failed: session={state}, query={query_state}")
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    base_url = str(request.base_url)
    callback_url = f"{base_url}oauth2callback"
    print(f"Callback URL: {callback_url}")

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=callback_url
    )

    try:
        # Get the full URL including query parameters
        authorization_response = str(request.url)
        print(f"Authorization response URL: {authorization_response}")
        flow.fetch_token(authorization_response=authorization_response)
        creds = flow.credentials
        print(f"Credentials obtained: {creds.valid}")

        # Save the credentials for future use on the server
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
        print(f"Credentials saved to {TOKEN_FILE}")

        # Redirect back to frontend after successful authentication
        frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:8080")
        print(f"Redirecting to frontend: {frontend_url}")
        return RedirectResponse(url=frontend_url)
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        print(f"Error type: {type(e)}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@app.get("/check_auth_status")
async def check_auth_status():
    """Checks if the user is currently authenticated."""
    service = get_gmail_service()
    return {"authenticated": service is not None}


if __name__ == "__main__":
    uvicorn.run("run_api_auth:app", host="0.0.0.0", port=8000, reload=True)
