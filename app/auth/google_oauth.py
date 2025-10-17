"""Google OAuth2 authentication flow for Calendar API and Smart Home Actions - Multi-tenant version."""
import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone, date, time as dt_time
from supabase import create_client, Client

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..deps import get_supabase_client
from ..util.time import utc_now, make_aware

# OAuth2 scopes for Calendar API and Smart Home
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
]


class GoogleOAuthManager:
    """Manages Google OAuth2 authentication and token lifecycle for multi-tenant use."""

    def __init__(self):
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8080/auth/google/callback")

        if not self.client_id or not self.client_secret:
            raise ValueError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set")

        # Initialize Supabase client for token storage
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

        self.supabase: Client = create_client(supabase_url, supabase_key)

    def _get_client_config(self) -> Dict[str, Any]:
        """Generate OAuth client configuration."""
        return {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.redirect_uri]
            }
        }

    def get_authorization_url(self, user_id: str, state: Optional[str] = None) -> str:
        """Generate OAuth2 authorization URL for a specific user."""
        flow = Flow.from_client_config(
            self._get_client_config(),
            scopes=SCOPES,
            redirect_uri=self.redirect_uri
        )

        # Use user_id as state if not provided
        state_value = state or user_id

        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=state_value
        )

        return authorization_url

    async def exchange_code_for_token(self, code: str, user_id: str) -> bool:
        """Exchange authorization code for access token and store in Supabase."""
        try:
            print(f"Starting token exchange for user: {user_id}")

            flow = Flow.from_client_config(
                self._get_client_config(),
                scopes=SCOPES,
                redirect_uri=self.redirect_uri
            )

            print(f"Fetching token with code: {code[:20]}...")
            flow.fetch_token(code=code)
            credentials = flow.credentials

            print(f"Token exchange successful. Token: {credentials.token[:20]}...")

            # Store token in Supabase
            await self.save_user_token(user_id, credentials)
            print(f"Token saved successfully for user: {user_id}")
            return True
        except Exception as e:
            print(f"Failed to exchange code for token: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def save_user_token(self, user_id: str, credentials: Credentials) -> None:
        """Save user's OAuth credentials to Supabase."""
        try:
            print(f"Saving token data for user: {user_id}")

            token_data = {
                "user_id": user_id,
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_expiry": credentials.expiry.isoformat() if credentials.expiry else None,
                "scopes": list(SCOPES),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }

            print(f"Token data prepared: {token_data}")

            # Upsert token (insert or update)
            result = self.supabase.table("google_oauth_tokens").upsert(
                token_data,
                on_conflict="user_id"
            ).execute()

            print(f"Supabase upsert result: {result}")
            print(f"Saved OAuth token for user: {user_id}")
        except Exception as e:
            print(f"Failed to save user token: {e}")
            import traceback
            traceback.print_exc()
            raise ValueError(f"Failed to save OAuth token: {str(e)}")

    async def get_user_token(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user's OAuth token from Supabase."""
        try:
            result = self.supabase.table("google_oauth_tokens").select("*").eq(
                "user_id", user_id
            ).execute()

            if result.data and len(result.data) > 0:
                token_data = result.data[0].copy()
                # CRITICAL SUPABASE FIX: Ensure token_expiry is properly formatted
                if token_data.get("token_expiry"):
                    expiry_str = token_data["token_expiry"]
                    # Parse Supabase timestamp format: "2025-10-10 22:26:34+00"
                    if isinstance(expiry_str, str):
                        try:
                            # Convert Supabase format to ISO format for consistent parsing
                            if '+00' in expiry_str and 'T' not in expiry_str:
                                # Convert "2025-10-10 22:26:34+00" to "2025-10-10T22:26:34+00:00"
                                iso_str = expiry_str.replace(' ', 'T').replace('+00', '+00:00')
                                token_data["token_expiry"] = iso_str
                        except Exception as e:
                            print(f"Error normalizing token_expiry format: {e}")
                return token_data
            return None
        except Exception as e:
            print(f"Failed to get user token: {e}")
            return None

    async def get_valid_credentials(self, user_id: str) -> Optional[Credentials]:
        """Get valid credentials for user, refreshing if necessary."""
        token_data = await self.get_user_token(user_id)

        if not token_data:
            return None

        # Reconstruct credentials from stored data
        credentials = Credentials(
            token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=token_data["scopes"]
        )

        # Set expiry if available - ALWAYS ensure timezone-aware
        if token_data.get("token_expiry"):
            expiry_str = token_data["token_expiry"]
            try:
                # Parse the datetime
                expiry_dt = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
                # Force timezone-aware
                if expiry_dt.tzinfo is None:
                    expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)
                credentials.expiry = expiry_dt
            except Exception as e:
                print(f"Error parsing expiry: {e}")
                credentials.expiry = None

        # Check if token is expired using timezone-aware comparison
        now = utc_now()

        # CRITICAL FIX: Check if expiry exists before comparing
        if credentials.expiry is None:
            is_expired = False
        else:
            # Ensure credentials.expiry is timezone-aware before comparison
            if credentials.expiry.tzinfo is None:
                credentials.expiry = credentials.expiry.replace(tzinfo=timezone.utc)
            is_expired = credentials.expiry < now

        # Refresh token if expired
        if is_expired and credentials.refresh_token:
            try:
                print(f"Refreshing expired token for user {user_id}")
                credentials.refresh(Request())

                # CRITICAL FIX: After refresh, ensure expiry is timezone-aware
                if credentials.expiry and credentials.expiry.tzinfo is None:
                    credentials.expiry = credentials.expiry.replace(tzinfo=timezone.utc)

                # Save refreshed token
                await self.save_user_token(user_id, credentials)
            except Exception as e:
                print(f"Failed to refresh token for user {user_id}: {e}")
                return None

        # FINAL CHECK: Ensure expiry is always timezone-aware before returning
        if credentials.expiry and credentials.expiry.tzinfo is None:
            credentials.expiry = credentials.expiry.replace(tzinfo=timezone.utc)

        return credentials

    async def is_authenticated(self, user_id: str) -> bool:
        """Check if user is authenticated with valid credentials."""
        try:
            creds = await self.get_valid_credentials(user_id)
            if not creds:
                return False

            # Additional safety check - ensure expiry is timezone-aware
            if creds.expiry and creds.expiry.tzinfo is None:
                creds.expiry = creds.expiry.replace(tzinfo=timezone.utc)

            # Check if credentials are valid using timezone-aware comparison
            now = utc_now()

            # Check expiry only if it exists
            if creds.expiry:
                # Ensure expiry is timezone-aware before comparison
                if creds.expiry.tzinfo is None:
                    creds.expiry = creds.expiry.replace(tzinfo=timezone.utc)
                is_expired = creds.expiry < now
            else:
                is_expired = False

            return not is_expired and creds.token is not None
        except Exception as e:
            print(f"Error checking authentication status: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def revoke_token(self, user_id: str) -> bool:
        """Revoke user's OAuth token and remove from database."""
        try:
            # Get credentials to revoke
            credentials = await self.get_valid_credentials(user_id)

            if credentials:
                try:
                    credentials.revoke(Request())
                except:
                    pass  # Continue even if revocation fails

            # Delete from database
            self.supabase.table("google_oauth_tokens").delete().eq(
                "user_id", user_id
            ).execute()

            print(f"Revoked OAuth token for user: {user_id}")
            return True
        except Exception as e:
            print(f"Failed to revoke token: {e}")
            return False

    async def get_calendar_service(self, user_id: str):
        """Get authenticated Google Calendar service for user."""
        creds = await self.get_valid_credentials(user_id)
        if not creds:
            raise ValueError(f"Not authenticated with Google for user: {user_id}")

        # CRITICAL FIX: Workaround for google-auth comparison bug
        # If expiry is offset-aware but google-auth's utcnow() is naive (or vice-versa),
        # normalize expiry to naive UTC to prevent "can't compare offset-naive and offset-aware" error
        if getattr(creds, "expiry", None) is not None:
            if creds.expiry.tzinfo is not None:
                # Make expiry naive UTC so google-auth's internal comparison succeeds
                creds.expiry = creds.expiry.astimezone(timezone.utc).replace(tzinfo=None)

        try:
            service = build('calendar', 'v3', credentials=creds)
            return service
        except HttpError as e:
            raise ValueError(f"Failed to create calendar service: {e}")

    async def get_homegraph_service(self, user_id: str):
        """Get authenticated Google Home Graph API service for user."""
        creds = await self.get_valid_credentials(user_id)
        if not creds:
            raise ValueError(f"Not authenticated with Google for user: {user_id}")

        try:
            service = build('homegraph', 'v1', credentials=creds)
            return service
        except HttpError as e:
            raise ValueError(f"Failed to create homegraph service: {e}")


# Global OAuth manager instance
oauth_manager = GoogleOAuthManager()
