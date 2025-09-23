"""Budget service for CSV parsing and Notion integration."""
import csv
import os
from typing import List, Dict, Any
from datetime import datetime

from ..models import BudgetScanRequest, BudgetScanResponse, CategorySummary
from ..deps import notion_client
from ..util.logging import logger


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

    async def scan_budget(self, request: BudgetScanRequest) -> BudgetScanResponse:
        """Scan budget for given period."""
        logger.info(f"Budget scan requested for period {request.period.from_date} to {request.period.to_date}")

        if request.source == "csv":
            transactions = await self._parse_csv(request.path or "data/sample_transactions.csv")
        else:
            # TODO: Implement Notion integration in Phase 3
            transactions = []

        categories = await self._calculate_category_totals(transactions, request.period)
        buffer_remaining = sum(cat.delta for cat in categories)

        return BudgetScanResponse(
            period=request.period,
            categories=categories,
            buffer_remaining=buffer_remaining
        )

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
