"""Open Banking service for real-time transaction fetching via TrueLayer."""
import os
import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone

from ..auth.open_banking import open_banking_oauth_manager
from ..models import BankAccount, Transaction
from ..util.time import utc_now, to_aware_utc
from ..util.logging import logger


class OpenBankingService:
    """Service for Open Banking operations - real-time data fetching (NO storage)."""

    def __init__(self):
        self.environment = os.getenv("TRUELAYER_ENVIRONMENT", "sandbox")

        if self.environment == "sandbox":
            self.api_url = "https://api.truelayer-sandbox.com"
        else:
            self.api_url = "https://api.truelayer.com"

    async def get_bank_accounts(self, user_id: str) -> List[BankAccount]:
        """
        Fetch bank accounts for user (minimal metadata only).

        COMPLIANCE: We do NOT fetch or store balances - only account metadata.
        """
        try:
            access_token = await open_banking_oauth_manager.get_valid_access_token(user_id)
            if not access_token:
                raise ValueError(f"User {user_id} is not authenticated with Open Banking")

            # Fetch accounts from TrueLayer
            url = f"{self.api_url}/data/v1/accounts"
            headers = {"Authorization": f"Bearer {access_token}"}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

            accounts = []
            for account_data in data.get("results", []):
                # Map TrueLayer account to our BankAccount model
                account = BankAccount(
                    id=account_data["account_id"],
                    user_id=user_id,
                    provider_account_id=account_data["account_id"],
                    provider="truelayer",
                    account_type=account_data.get("account_type"),
                    display_name=account_data.get("display_name"),
                    bank_name=account_data.get("provider", {}).get("display_name"),
                    currency=account_data.get("currency", "GBP"),
                    created_at=utc_now()
                )
                accounts.append(account)

            logger.info(f"Fetched {len(accounts)} bank accounts for user {user_id}")
            return accounts
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching bank accounts: {e.response.status_code} - {e.response.text}", exc_info=True)
            raise ValueError(f"Failed to fetch bank accounts: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching bank accounts: {e}", exc_info=True)
            raise

    async def get_transactions(
        self,
        user_id: str,
        account_id: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[Transaction]:
        """
        Fetch transactions in real-time from TrueLayer API.

        CRITICAL: Transactions are NEVER stored - always fetched live.
        This avoids PCI-DSS compliance and financial data regulations.
        """
        try:
            access_token = await open_banking_oauth_manager.get_valid_access_token(user_id)
            if not access_token:
                raise ValueError(f"User {user_id} is not authenticated with Open Banking")

            # Default date range: last 90 days
            # IMPORTANT: 'to_date' must not be in the future
            if not from_date:
                from_date = (utc_now() - timedelta(days=90)).strftime("%Y-%m-%d")
            if not to_date:
                to_date = utc_now().strftime("%Y-%m-%d")

            # Ensure to_date is not in the future (TrueLayer rejects future dates)
            today = utc_now().strftime("%Y-%m-%d")
            if to_date > today:
                to_date = today

            # Fetch transactions from TrueLayer
            url = f"{self.api_url}/data/v1/accounts/{account_id}/transactions"
            headers = {"Authorization": f"Bearer {access_token}"}
            params = {
                "from": from_date,
                "to": to_date
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()

            transactions = []
            for tx_data in data.get("results", []):
                # Parse timestamp and ensure timezone-aware
                timestamp_str = tx_data.get("timestamp")
                timestamp = to_aware_utc(timestamp_str) if timestamp_str else utc_now()

                # Map TrueLayer transaction to our Transaction model
                transaction = Transaction(
                    transaction_id=tx_data["transaction_id"],
                    timestamp=timestamp,
                    description=tx_data.get("description", ""),
                    amount=tx_data["amount"],
                    currency=tx_data.get("currency", "GBP"),
                    transaction_type=tx_data["transaction_type"],
                    transaction_category=tx_data.get("transaction_category"),
                    transaction_classification=tx_data.get("transaction_classification"),
                    merchant_name=tx_data.get("merchant_name"),
                    running_balance=tx_data.get("running_balance")
                )
                transactions.append(transaction)

            logger.info(f"Fetched {len(transactions)} transactions for user {user_id}, account {account_id}")
            return transactions
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching transactions: {e.response.status_code} - {e.response.text}", exc_info=True)
            raise ValueError(f"Failed to fetch transactions: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching transactions: {e}", exc_info=True)
            raise

    async def sync_bank_accounts(self, user_id: str) -> int:
        """
        Sync bank accounts to database (minimal metadata only).

        Returns number of accounts synced.
        """
        try:
            accounts = await self.get_bank_accounts(user_id)

            # Store minimal metadata in database
            supabase = open_banking_oauth_manager.supabase
            synced_count = 0

            for account in accounts:
                account_data = {
                    "user_id": user_id,
                    "provider_account_id": account.provider_account_id,
                    "provider": account.provider,
                    "account_type": account.account_type,
                    "display_name": account.display_name,
                    "bank_name": account.bank_name,
                    "currency": account.currency,
                }

                # Upsert account (insert or update)
                result = supabase.table("bank_accounts").upsert(
                    account_data,
                    on_conflict="user_id,provider_account_id"
                ).execute()

                synced_count += 1

            logger.info(f"Synced {synced_count} bank accounts for user {user_id}")
            return synced_count
        except Exception as e:
            logger.error(f"Error syncing bank accounts: {e}", exc_info=True)
            raise

    async def get_stored_bank_accounts(self, user_id: str) -> List[BankAccount]:
        """Get bank accounts from database (metadata only)."""
        try:
            supabase = open_banking_oauth_manager.supabase
            result = supabase.table("bank_accounts").select("*").eq(
                "user_id", user_id
            ).execute()

            accounts = []
            for account_data in result.data:
                # Parse created_at to timezone-aware datetime
                created_at_str = account_data.get("created_at")
                created_at = to_aware_utc(created_at_str) if created_at_str else utc_now()

                account = BankAccount(
                    id=account_data["id"],
                    user_id=account_data["user_id"],
                    provider_account_id=account_data["provider_account_id"],
                    provider=account_data["provider"],
                    account_type=account_data.get("account_type"),
                    display_name=account_data.get("display_name"),
                    bank_name=account_data.get("bank_name"),
                    currency=account_data.get("currency", "GBP"),
                    created_at=created_at
                )
                accounts.append(account)

            return accounts
        except Exception as e:
            logger.error(f"Error getting stored bank accounts: {e}", exc_info=True)
            raise


# Global service instance
open_banking_service = OpenBankingService()

