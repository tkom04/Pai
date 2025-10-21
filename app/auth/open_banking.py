"""Open Banking OAuth2 authentication flow for TrueLayer API - Multi-tenant version."""
import os
import json
import httpx
from typing import Optional, Dict, Any, List
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

            # Get institution metadata from TrueLayer
            institution_metadata = await self.get_institution_metadata_from_token(token_data["access_token"])

            # Store token in Supabase with institution metadata
            await self.save_user_token(user_id, token_data, expiry, institution_metadata)
            logger.info(f"Token saved successfully for user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to exchange code for token: {e}", exc_info=True)
            return False

    async def save_user_token(self, user_id: str, token_data: Dict[str, Any], expiry: datetime, institution_metadata: Optional[Dict[str, Any]] = None) -> str:
        """Save user's OAuth credentials to Supabase and return token_id."""
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

            # Add institution metadata if provided
            if institution_metadata:
                token_record.update({
                    "institution_id": institution_metadata.get("institution_id"),
                    "institution_name": institution_metadata.get("institution_name"),
                    "consent_expires_at": institution_metadata.get("consent_expires_at"),
                    "last_sync_at": utc_now().isoformat()
                })

            # Insert token (no longer using upsert since we support multiple banks)
            result = self.supabase.table("open_banking_tokens").insert(token_record).execute()

            if not result.data:
                raise ValueError("Failed to insert token")

            token_id = result.data[0]["id"]

            # Create bank connection record
            if institution_metadata:
                connection_record = {
                    "user_id": user_id,
                    "token_id": token_id,
                    "institution_id": institution_metadata.get("institution_id"),
                    "institution_name": institution_metadata.get("institution_name"),
                    "status": "active",
                    "created_at": utc_now().isoformat(),
                    "last_sync_at": utc_now().isoformat()
                }

                self.supabase.table("bank_connections").insert(connection_record).execute()

            logger.info(f"Saved Open Banking OAuth token for user: {user_id}")
            return token_id
        except Exception as e:
            logger.error(f"Failed to save user token: {e}", exc_info=True)
            raise ValueError(f"Failed to save OAuth token: {str(e)}")

    async def get_user_tokens(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieve all OAuth tokens for a user from Supabase."""
        try:
            result = self.supabase.table("open_banking_tokens").select("*").eq(
                "user_id", user_id
            ).execute()

            tokens = []
            for token_data in result.data:
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
                tokens.append(token_data)
            return tokens
        except Exception as e:
            logger.error(f"Failed to get user tokens: {e}", exc_info=True)
            return []

    async def get_user_token(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user's first OAuth token from Supabase (legacy method)."""
        tokens = await self.get_user_tokens(user_id)
        return tokens[0] if tokens else None

    async def get_valid_access_token(self, user_id: str, token_id: Optional[str] = None) -> Optional[str]:
        """Get valid access token for user, refreshing if necessary."""
        if token_id:
            # Get specific token
            result = self.supabase.table("open_banking_tokens").select("*").eq("id", token_id).eq("user_id", user_id).execute()
            token_data = result.data[0] if result.data else None
        else:
            # Get first available token (legacy behavior)
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

    async def extend_connection(self, user_id: str, connection_id: str, user_name: str = None, user_email: str = None) -> Dict[str, Any]:
        """Extend a TrueLayer connection using the /connections/extend endpoint."""
        try:
            # Validate required environment variables
            missing_env_vars = []
            if not self.client_id:
                missing_env_vars.append("TRUELAYER_CLIENT_ID")
            if not self.client_secret:
                missing_env_vars.append("TRUELAYER_CLIENT_SECRET")
            if not self.redirect_uri:
                missing_env_vars.append("TRUELAYER_REDIRECT_URI")

            if missing_env_vars:
                raise ValueError(f"Missing required environment variables: {', '.join(missing_env_vars)}")

            # Get the connection details
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            if not supabase_url or not supabase_key:
                raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
            supabase = create_client(supabase_url, supabase_key)

            connection_result = supabase.table("bank_connections").select("*").eq("id", connection_id).eq("user_id", user_id).limit(1).execute()

            if not connection_result.data:
                raise ValueError(f"Connection {connection_id} not found for user {user_id}")

            connection = connection_result.data[0]
            token_result = supabase.table("open_banking_tokens").select("*").eq("id", connection["token_id"]).limit(1).execute()

            if not token_result.data:
                raise ValueError(f"Token not found for connection {connection_id}")

            token = token_result.data[0]

            # Get user details for TrueLayer
            user_result = supabase.table("user_profiles").select("full_name, email").eq("id", user_id).limit(1).execute()
            user_data = user_result.data[0] if user_result.data else {}

            # Call TrueLayer's extend endpoint with proper payload
            extend_url = f"{self.api_url}/connections/extend"

            # Build the complete payload as required by TrueLayer
            payload = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
                "refresh_token": token["refresh_token"],
                "user_has_reconfirmed_consent": True,
                "user": {
                    "name": user_name or user_data.get("full_name", "User"),
                    "email": user_email or user_data.get("email", "user@example.com")
                }
            }

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(extend_url, json=payload)

                # Handle TrueLayer's response properly
                if response.status_code == 200:
                    extend_data = response.json()

                    # Update the token with new expiry information
                    if "expires_in" in extend_data:
                        new_expiry = utc_now() + timedelta(seconds=extend_data["expires_in"] - 300)
                        await self.save_user_token(
                            user_id=user_id,
                            access_token=extend_data.get("access_token", token["access_token"]),
                            refresh_token=extend_data.get("refresh_token", token["refresh_token"]),
                            expires_at=new_expiry.isoformat(),
                            institution_id=token.get("institution_id"),
                            institution_name=token.get("institution_name"),
                            consent_expires_at=extend_data.get("consent_expires_at"),
                            last_sync_at=utc_now().isoformat()
                        )

                    logger.info(f"Successfully extended connection {connection_id} for user {user_id}")
                    return {
                        "success": True,
                        "message": "Connection extended successfully",
                        "expires_in": extend_data.get("expires_in"),
                        "consent_expires_at": extend_data.get("consent_expires_at")
                    }

                elif response.status_code == 400:
                    # TrueLayer validation error - bubble up the details
                    error_data = response.json()
                    logger.error(f"TrueLayer validation error: {error_data}")
                    return {
                        "success": False,
                        "error": "validation_error",
                        "message": f"Validation error: {error_data.get('error_description', 'Invalid request')}",
                        "details": error_data
                    }

                elif response.status_code == 401:
                    return {
                        "success": False,
                        "error": "reauth_required",
                        "message": "Connection expired. Please reconnect your bank account."
                    }

                elif response.status_code == 403:
                    return {
                        "success": False,
                        "error": "consent_required",
                        "message": "User consent required. Please confirm access to your bank account."
                    }

                else:
                    # Other HTTP errors
                    error_text = response.text
                    logger.error(f"TrueLayer extend error: {response.status_code} - {error_text}")
                    return {
                        "success": False,
                        "error": "extension_failed",
                        "message": f"Failed to extend connection: {response.status_code} - {error_text}"
                    }

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error extending connection: {e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "error": "http_error",
                "message": f"HTTP error: {e.response.status_code}"
            }
        except Exception as e:
            logger.error(f"Error extending connection: {e}", exc_info=True)
            return {
                "success": False,
                "error": "extension_error",
                "message": f"Failed to extend connection: {str(e)}"
            }

    async def test_token_validity(self, user_id: str, token_id: Optional[str] = None) -> Dict[str, Any]:
        """Test if the access token is valid and not affected by SCA expiry."""
        try:
            access_token = await self.get_valid_access_token(user_id, token_id)
            if not access_token:
                return {"valid": False, "reason": "no_token", "sca_expired": False}

            # Test the token by making a simple API call
            test_url = f"{self.api_url}/data/v1/accounts"
            headers = {"Authorization": f"Bearer {access_token}"}

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(test_url, headers=headers)

                if response.status_code == 200:
                    return {"valid": True, "reason": "success", "sca_expired": False}
                elif response.status_code == 403:
                    try:
                        payload = response.json()
                        if payload.get("error") == "sca_exceeded":
                            return {"valid": False, "reason": "sca_expired", "sca_expired": True}
                    except:
                        pass
                    return {"valid": False, "reason": "forbidden", "sca_expired": False}
                else:
                    return {"valid": False, "reason": f"http_{response.status_code}", "sca_expired": False}

        except Exception as e:
            logger.error(f"Error testing token validity: {e}", exc_info=True)
            return {"valid": False, "reason": "error", "sca_expired": False, "error": str(e)}

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

    async def get_institution_metadata_from_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get institution metadata from TrueLayer using access token."""
        try:
            # First get accounts to find institution info
            accounts_url = f"{self.api_url}/data/v1/accounts"
            headers = {"Authorization": f"Bearer {access_token}"}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(accounts_url, headers=headers)
                response.raise_for_status()
                accounts_data = response.json()

            if accounts_data.get("results"):
                # Get institution info from first account
                first_account = accounts_data["results"][0]
                provider = first_account.get("provider", {})

                institution_id = provider.get("provider_id")
                institution_name = provider.get("display_name")

                # Calculate consent expiry (typically 90 days from now)
                consent_expires_at = utc_now() + timedelta(days=90)

                return {
                    "institution_id": institution_id,
                    "institution_name": institution_name,
                    "consent_expires_at": consent_expires_at.isoformat()
                }

            return None
        except Exception as e:
            logger.error(f"Failed to get institution metadata: {e}", exc_info=True)
            return None

    async def get_institution_metadata(self, institution_id: str) -> Optional[Dict[str, Any]]:
        """Get institution metadata from TrueLayer API in real-time."""
        try:
            # TrueLayer doesn't have a direct institution metadata endpoint
            # We'll return basic info based on common UK banks
            uk_banks = {
                "uk-ob-barclays": {"name": "Barclays", "logo": "barclays"},
                "uk-ob-hsbc": {"name": "HSBC", "logo": "hsbc"},
                "uk-ob-lloyds": {"name": "Lloyds Bank", "logo": "lloyds"},
                "uk-ob-natwest": {"name": "NatWest", "logo": "natwest"},
                "uk-ob-santander": {"name": "Santander", "logo": "santander"},
                "uk-ob-halifax": {"name": "Halifax", "logo": "halifax"},
                "uk-ob-nationwide": {"name": "Nationwide", "logo": "nationwide"},
                "uk-ob-metro": {"name": "Metro Bank", "logo": "metro"},
                "uk-ob-firstdirect": {"name": "First Direct", "logo": "firstdirect"},
                "uk-ob-tesco": {"name": "Tesco Bank", "logo": "tesco"}
            }

            return uk_banks.get(institution_id, {"name": institution_id, "logo": "bank"})
        except Exception as e:
            logger.error(f"Failed to get institution metadata: {e}", exc_info=True)
            return None

    async def revoke_token(self, user_id: str, connection_id: Optional[str] = None) -> bool:
        """Revoke user's OAuth token and remove from database (privacy-first)."""
        try:
            # Call TrueLayer revoke API if we have a specific connection
            if connection_id:
                try:
                    # Get token for this connection
                    connection_result = self.supabase.table("bank_connections").select("token_id").eq("id", connection_id).eq("user_id", user_id).execute()
                    if connection_result.data:
                        token_result = self.supabase.table("open_banking_tokens").select("access_token").eq("id", connection_result.data[0]["token_id"]).execute()
                        if token_result.data:
                            access_token = token_result.data[0]["access_token"]

                            # Call TrueLayer revoke endpoint
                            revoke_url = f"{self.api_url}/auth/revoke"
                            headers = {"Authorization": f"Bearer {access_token}"}

                            async with httpx.AsyncClient(timeout=10.0) as client:
                                await client.post(revoke_url, headers=headers)
                except Exception as e:
                    logger.warning(f"Failed to call TrueLayer revoke API: {e}")
                    # Continue with local cleanup anyway

            # Delete from database (privacy-first compliance)
            if connection_id:
                # Delete specific connection and its token
                connection_result = self.supabase.table("bank_connections").select("token_id").eq("id", connection_id).eq("user_id", user_id).execute()
                if connection_result.data:
                    token_id = connection_result.data[0]["token_id"]

                    # Delete token
                    self.supabase.table("open_banking_tokens").delete().eq("id", token_id).execute()

                    # Delete connection
                    self.supabase.table("bank_connections").delete().eq("id", connection_id).execute()

                    # Delete cached transaction data (privacy-first)
                    self.supabase.table("transaction_cache").delete().eq("user_id", user_id).execute()

                    # Delete account mappings
                    self.supabase.table("account_mappings").delete().eq("user_id", user_id).execute()

                    # Delete recurring payments
                    self.supabase.table("recurring_payments").delete().eq("user_id", user_id).execute()

                    # Delete duplicate transactions
                    self.supabase.table("duplicate_transactions").delete().eq("user_id", user_id).execute()

                    logger.info(f"Revoked bank connection {connection_id} for user: {user_id}")
            else:
                # Delete all tokens for user (legacy behavior)
                self.supabase.table("open_banking_tokens").delete().eq("user_id", user_id).execute()
                logger.info(f"Revoked all Open Banking OAuth tokens for user: {user_id}")

            return True
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}", exc_info=True)
            return False


# Global OAuth manager instance
open_banking_oauth_manager = OpenBankingOAuthManager()

