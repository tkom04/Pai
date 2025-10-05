"""Google OAuth2 authentication flow for Calendar API."""
import os
import json
import pickle
from typing import Optional, Dict, Any
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# OAuth2 scopes for Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Token storage path
TOKEN_FILE = Path("google_token.json")


class GoogleOAuthManager:
    """Manages Google OAuth2 authentication and token lifecycle."""

    def __init__(self):
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8080/auth/google/callback")

        if not self.client_id or not self.client_secret:
            raise ValueError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set")

        self._credentials: Optional[Credentials] = None
        self._load_credentials()

    def _load_credentials(self) -> None:
        """Load credentials from token file if it exists."""
        if TOKEN_FILE.exists():
            try:
                with open(TOKEN_FILE, 'r') as token:
                    creds_data = json.load(token)
                    self._credentials = Credentials.from_authorized_user_info(creds_data, SCOPES)
            except Exception as e:
                print(f"Failed to load credentials: {e}")
                self._credentials = None

    def _save_credentials(self) -> None:
        """Save credentials to token file."""
        if self._credentials:
            try:
                with open(TOKEN_FILE, 'w') as token:
                    token.write(self._credentials.to_json())
            except Exception as e:
                print(f"Failed to save credentials: {e}")

    def get_authorization_url(self) -> str:
        """Generate OAuth2 authorization URL."""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=SCOPES,
            redirect_uri=self.redirect_uri
        )

        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

        return authorization_url

    def exchange_code_for_token(self, code: str) -> bool:
        """Exchange authorization code for access token."""
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=SCOPES,
                redirect_uri=self.redirect_uri
            )

            flow.fetch_token(code=code)
            self._credentials = flow.credentials
            self._save_credentials()
            return True
        except Exception as e:
            print(f"Failed to exchange code for token: {e}")
            return False

    def get_valid_credentials(self) -> Optional[Credentials]:
        """Get valid credentials, refreshing if necessary."""
        if not self._credentials:
            return None

        # Refresh token if expired
        if self._credentials.expired and self._credentials.refresh_token:
            try:
                self._credentials.refresh(Request())
                self._save_credentials()
            except Exception as e:
                print(f"Failed to refresh token: {e}")
                return None

        return self._credentials

    def is_authenticated(self) -> bool:
        """Check if user is authenticated with valid credentials."""
        creds = self.get_valid_credentials()
        return creds is not None and creds.valid

    def revoke_token(self) -> bool:
        """Revoke the current token and clear credentials."""
        if self._credentials:
            try:
                self._credentials.revoke(Request())
            except:
                pass

            self._credentials = None
            if TOKEN_FILE.exists():
                TOKEN_FILE.unlink()
            return True
        return False

    def get_calendar_service(self):
        """Get authenticated Google Calendar service."""
        creds = self.get_valid_credentials()
        if not creds:
            raise ValueError("Not authenticated with Google")

        try:
            service = build('calendar', 'v3', credentials=creds)
            return service
        except HttpError as e:
            raise ValueError(f"Failed to create calendar service: {e}")


# Global OAuth manager instance
oauth_manager = GoogleOAuthManager()
