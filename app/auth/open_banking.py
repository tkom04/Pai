"""Open Banking OAuth2 authentication flow for TrueLayer API - Multi-tenant version."""
import os
import json
import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from supabase import create_client, Client

from ..util.time import utc_now
from ..util.logging import logger


class OpenBankingOAuthManager:
    """Manages Open Banking OAuth2 authentication and token lifecycle for multi-tenant use."""

    def __init__(self):
        self.provider = os.getenv("OPEN_BANKING_PROVIDER", "truelayer")
        self.client_id = os.getenv("TRUELAYER_CLIENT_ID")
        self.client_secret = os.getenv("TRUELAYER_CLIENT_SECRET")
        self.redirect_uri = os.getenv("TRUELAYER_REDIRECT_URI", "http://localhost:8000/auth/open-banking/callback")
        self.environment = os.getenv("TRUELAYER_ENVIRONMENT", "sandbox")

        if not self.client_id or not self.client_secret:
            logger.warning("TRUELAYER_CLIENT_ID and TRUELAYER_CLIENT_SECRET not set - Open Banking will not work")

        # TrueLayer API endpoints
        if self.environment == "sandbox":
            self.auth_url = "https://auth.truelayer-sandbox.com"
            self.api_url = "https://api.truelayer-sandbox.com"
        else:
            self.auth_url = "https://auth.truelayer.com"
            self.api_url = "https://api.truelayer.com"

        # Initialize Supabase client for token storage
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

        self.supabase: Client = create_client(supabase_url, supabase_key)

    def get_authorization_url(self, user_id: str, state: Optional[str] = None) -> str:
        """Generate OAuth2 authorization URL for a specific user."""
        # Use user_id as state if not provided
        state_value = state or user_id

        # TrueLayer OAuth2 authorization URL
        # Scopes: accounts, transactions, balance, info
        scopes = ["accounts", "transactions", "balance", "info", "offline_access"]

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(scopes),
            "state": state_value,
            "providers": "uk-ob-all uk-oauth-all",  # All UK banks
        }

        # Build authorization URL with proper URL encoding
        from urllib.parse import urlencode
        query_string = urlencode(params)
        authorization_url = f"{self.auth_url}?{query_string}"

        logger.info(f"Generated Open Banking authorization URL for user: {user_id}")
        return authorization_url

    async def exchange_code_for_token(self, code: str, user_id: str) -> bool:
        """Exchange authorization code for access token and store in Supabase."""
        try:
            logger.info(f"Starting token exchange for user: {user_id}")

            # TrueLayer token endpoint
            token_url = f"{self.auth_url}/connect/token"

            data = {
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
                "code": code,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data)
                response.raise_for_status()
                token_data = response.json()

            logger.info(f"Token exchange successful for user: {user_id}")

            # Calculate token expiry (5 minute buffer for safety)
            expires_in = token_data.get("expires_in", 3600)
            expiry = utc_now() + timedelta(seconds=expires_in - 300)

            # Store token in Supabase
            await self.save_user_token(user_id, token_data, expiry)
            logger.info(f"Token saved successfully for user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to exchange code for token: {e}", exc_info=True)
            return False

    async def save_user_token(self, user_id: str, token_data: Dict[str, Any], expiry: datetime) -> None:
        """Save user's OAuth credentials to Supabase."""
        try:
            logger.info(f"Saving token data for user: {user_id}")

            token_record = {
                "user_id": user_id,
                "provider": self.provider,
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token"),
                "scope": ["accounts", "transactions", "balance", "info", "offline_access"],
                "expires_at": expiry.isoformat(),
                "updated_at": utc_now().isoformat()
            }

            # Upsert token (insert or update)
            result = self.supabase.table("open_banking_tokens").upsert(
                token_record,
                on_conflict="user_id"
            ).execute()

            logger.info(f"Saved Open Banking OAuth token for user: {user_id}")
        except Exception as e:
            logger.error(f"Failed to save user token: {e}", exc_info=True)
            raise ValueError(f"Failed to save OAuth token: {str(e)}")

    async def get_user_token(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user's OAuth token from Supabase."""
        try:
            result = self.supabase.table("open_banking_tokens").select("*").eq(
                "user_id", user_id
            ).execute()

            if result.data and len(result.data) > 0:
                token_data = result.data[0].copy()
                # Normalize expires_at format (Supabase format handling)
                if token_data.get("expires_at"):
                    expiry_str = token_data["expires_at"]
                    if isinstance(expiry_str, str):
                        try:
                            # Convert "2025-10-10 22:26:34+00" to "2025-10-10T22:26:34+00:00"
                            if '+00' in expiry_str and 'T' not in expiry_str:
                                iso_str = expiry_str.replace(' ', 'T').replace('+00', '+00:00')
                                token_data["expires_at"] = iso_str
                        except Exception as e:
                            logger.error(f"Error normalizing token_expiry format: {e}")
                return token_data
            return None
        except Exception as e:
            logger.error(f"Failed to get user token: {e}", exc_info=True)
            return None

    async def get_valid_access_token(self, user_id: str) -> Optional[str]:
        """Get valid access token for user, refreshing if necessary."""
        token_data = await self.get_user_token(user_id)

        if not token_data:
            return None

        # Parse expiry and check if token is expired
        expiry_str = token_data.get("expires_at")
        if expiry_str:
            try:
                expiry_dt = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
                if expiry_dt.tzinfo is None:
                    expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)
            except Exception as e:
                logger.error(f"Error parsing expiry: {e}")
                expiry_dt = None
        else:
            expiry_dt = None

        # Check if token is expired (with 5-minute buffer)
        now = utc_now()
        is_expired = expiry_dt and expiry_dt < now

        # Refresh token if expired
        if is_expired and token_data.get("refresh_token"):
            try:
                logger.info(f"Refreshing expired token for user {user_id}")
                new_token_data = await self._refresh_token(token_data["refresh_token"])

                # Calculate new expiry
                expires_in = new_token_data.get("expires_in", 3600)
                new_expiry = utc_now() + timedelta(seconds=expires_in - 300)

                # Save refreshed token
                await self.save_user_token(user_id, new_token_data, new_expiry)
                return new_token_data["access_token"]
            except Exception as e:
                logger.error(f"Failed to refresh token for user {user_id}: {e}", exc_info=True)
                return None

        return token_data["access_token"]

    async def _refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token."""
        token_url = f"{self.auth_url}/connect/token"

        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
            return response.json()

    async def is_authenticated(self, user_id: str) -> bool:
        """Check if user is authenticated with valid credentials."""
        try:
            access_token = await self.get_valid_access_token(user_id)
            return access_token is not None
        except Exception as e:
            logger.error(f"Error checking authentication status: {e}", exc_info=True)
            return False

    async def revoke_token(self, user_id: str) -> bool:
        """Revoke user's OAuth token and remove from database."""
        try:
            # Note: TrueLayer doesn't have a token revocation endpoint
            # We just delete from database
            self.supabase.table("open_banking_tokens").delete().eq(
                "user_id", user_id
            ).execute()

            logger.info(f"Revoked Open Banking OAuth token for user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}", exc_info=True)
            return False


# Global OAuth manager instance
open_banking_oauth_manager = OpenBankingOAuthManager()

