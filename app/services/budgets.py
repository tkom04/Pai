"""Budget service for CSV parsing, Open Banking integration, and Notion integration."""
import csv
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models import BudgetScanRequest, BudgetScanResponse, CategorySummary
from ..deps import notion_service
from ..util.logging import logger
from ..services.open_banking import open_banking_service
from ..auth.open_banking import open_banking_oauth_manager


class BudgetService:
    """Service for budget operations."""

    def __init__(self):
        self.categories = {
            "Food": 140.0,
            "Fun": 50.0,
            "Transport": 80.0,
            "Utilities": 120.0,
            "Shopping": 100.0
        }

    async def scan_budget(self, request: BudgetScanRequest, user_id: Optional[str] = None) -> BudgetScanResponse:
        """Scan budget for given period."""
        logger.info(f"Budget scan requested for period {request.period.from_date} to {request.period.to_date}")

        # Priority: Open Banking > CSV > Sample Data
        transactions = []

        if request.source == "open_banking" and user_id:
            try:
                transactions = await self._fetch_open_banking_transactions(
                    user_id=user_id,
                    from_date=request.period.from_date,
                    to_date=request.period.to_date
                )
                logger.info(f"Fetched {len(transactions)} transactions from Open Banking")
            except Exception as e:
                logger.error(f"Failed to fetch Open Banking transactions: {e}", exc_info=True)
                # Fall back to CSV
                transactions = await self._parse_csv(request.path or "data/sample_transactions.csv")
        elif request.source == "csv":
            transactions = await self._parse_csv(request.path or "data/sample_transactions.csv")
        else:
            # Fallback to sample data
            transactions = self._get_sample_transactions()

        categories = await self._calculate_category_totals(transactions, request.period)
        buffer_remaining = sum(cat.delta for cat in categories)

        return BudgetScanResponse(
            period=request.period,
            categories=categories,
            buffer_remaining=buffer_remaining
        )

    async def _fetch_open_banking_transactions(self, user_id: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """
        Fetch transactions from Open Banking in real-time.

        Returns transactions in a normalized format compatible with CSV parser.
        """
        try:
            # Check if user is authenticated
            is_authenticated = await open_banking_oauth_manager.is_authenticated(user_id)
            if not is_authenticated:
                raise ValueError("User not authenticated with Open Banking")

            # Get user's bank accounts (real-time from TrueLayer API)
            accounts = await open_banking_service.get_bank_accounts(user_id)
            if not accounts:
                logger.warning(f"No bank accounts found for user {user_id}")
                return []

            # Fetch transactions from all accounts
            all_transactions = []
            for account in accounts:
                try:
                    transactions = await open_banking_service.get_transactions(
                        user_id=user_id,
                        account_id=account.provider_account_id,
                        from_date=from_date,
                        to_date=to_date
                    )

                    # Normalize to CSV-compatible format
                    for tx in transactions:
                        # Only include DEBIT transactions (spending)
                        if tx.transaction_type == "DEBIT":
                            normalized_tx = {
                                "Date": tx.timestamp.strftime("%Y-%m-%d"),
                                "Merchant": tx.merchant_name or tx.description,
                                "Amount": abs(tx.amount),  # Convert to positive for spending
                                "Category": self._categorize_transaction(tx)
                            }
                            all_transactions.append(normalized_tx)
                except Exception as e:
                    logger.error(f"Failed to fetch transactions for account {account.provider_account_id}: {e}")
                    continue

            logger.info(f"Fetched {len(all_transactions)} DEBIT transactions from {len(accounts)} accounts")
            return all_transactions
        except Exception as e:
            logger.error(f"Error fetching Open Banking transactions: {e}", exc_info=True)
            raise

    def _categorize_transaction(self, transaction) -> str:
        """
        Categorize transaction based on merchant name, description, and TrueLayer classification.

        Categories: Food, Fun, Transport, Utilities, Shopping, Other
        """
        # Use TrueLayer's classification if available
        if transaction.transaction_classification:
            classifications = transaction.transaction_classification
            for classification in classifications:
                classification_lower = classification.lower()
                if any(keyword in classification_lower for keyword in ["groceries", "supermarkets", "restaurants", "food"]):
                    return "Food"
                elif any(keyword in classification_lower for keyword in ["entertainment", "leisure", "recreation"]):
                    return "Fun"
                elif any(keyword in classification_lower for keyword in ["transport", "travel", "fuel", "petrol"]):
                    return "Transport"
                elif any(keyword in classification_lower for keyword in ["utilities", "bills", "electric", "gas", "water"]):
                    return "Utilities"
                elif any(keyword in classification_lower for keyword in ["shopping", "retail", "general"]):
                    return "Shopping"

        # Fallback: keyword-based categorization
        text = f"{transaction.merchant_name or ''} {transaction.description}".lower()

        # Food keywords
        if any(keyword in text for keyword in ["tesco", "sainsbury", "asda", "waitrose", "morrisons", "aldi", "lidl",
                                                 "co-op", "marks", "restaurant", "cafe", "pizza", "mcdonald",
                                                 "kfc", "subway", "starbucks", "costa", "pret"]):
            return "Food"

        # Fun keywords
        elif any(keyword in text for keyword in ["cinema", "netflix", "spotify", "steam", "game", "vue", "odeon",
                                                   "amazon prime", "disney", "gym", "fitness"]):
            return "Fun"

        # Transport keywords
        elif any(keyword in text for keyword in ["shell", "bp", "esso", "texaco", "tfl", "uber", "train", "bus",
                                                   "petrol", "fuel", "parking", "national rail"]):
            return "Transport"

        # Utilities keywords
        elif any(keyword in text for keyword in ["british gas", "edf", "eon", "octopus energy", "thames water",
                                                   "bt", "virgin", "sky", "vodafone", "ee", "o2", "three"]):
            return "Utilities"

        # Rent keywords
        elif any(keyword in text for keyword in ["rent", "rnd estates", "landlord", "letting", "estate"]):
            return "Utilities"  # Rent counts as utilities for budgeting

        # Debt/loan/savings keywords (exclude from regular spending)
        elif any(keyword in text for keyword in ["debt", "loan repayment", "savings", "transfer to savings"]):
            return "Other"  # These shouldn't count against spending budgets

        # Shopping keywords
        elif any(keyword in text for keyword in ["amazon", "ebay", "argos", "john lewis", "next", "h&m", "zara",
                                                   "primark", "boots", "superdrug"]):
            return "Shopping"

        # Default to Other
        return "Other"

    async def _parse_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse CSV file for transactions."""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"CSV file {file_path} not found, using sample data")
                return self._get_sample_transactions()

            transactions = []
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    transactions.append(row)

            logger.info(f"Parsed {len(transactions)} transactions from {file_path}")
            return transactions
        except Exception as e:
            logger.error(f"Error parsing CSV: {e}")
            return self._get_sample_transactions()

    async def _calculate_category_totals(self, transactions: List[Dict[str, Any]], period) -> List[CategorySummary]:
        """Calculate spending totals by category."""
        category_totals = {}

        for transaction in transactions:
            category = transaction.get("Category", "Other")
            amount = float(transaction.get("Amount", 0))
            category_totals[category] = category_totals.get(category, 0) + amount

        categories = []
        for name, cap in self.categories.items():
            spent = category_totals.get(name, 0)
            delta = cap - spent
            status = "WARN" if spent / cap > 0.8 else "OK"

            categories.append(CategorySummary(
                name=name,
                cap=cap,
                spent=spent,
                delta=delta,
                status=status
            ))

        return categories

    def _get_sample_transactions(self) -> List[Dict[str, Any]]:
        """Return sample transaction data."""
        return [
            {"Date": "2025-01-15", "Merchant": "Tesco", "Amount": 45.50, "Category": "Food"},
            {"Date": "2025-01-16", "Merchant": "Cinema", "Amount": 12.00, "Category": "Fun"},
            {"Date": "2025-01-17", "Merchant": "Shell", "Amount": 35.00, "Category": "Transport"},
            {"Date": "2025-01-18", "Merchant": "Amazon", "Amount": 25.99, "Category": "Shopping"},
        ]


# Global service instance
budget_service = BudgetService()
