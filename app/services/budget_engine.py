"""Budget engine for calculating summaries and managing budget data."""
from decimal import Decimal
from typing import List, Dict
import logging

from app.models import NormalizedTransaction, BudgetSummaryResponse
from app.util.time import utc_now

logger = logging.getLogger(__name__)


class BudgetEngine:
    """Calculates budget summaries and manages budget logic."""

    async def calculate_summary(
        self,
        transactions: List[NormalizedTransaction],
        user_id: str,
        period: str = None,
        currency: str = "GBP"
    ) -> BudgetSummaryResponse:
        """Calculate budget summary"""
        categories = await self._load_categories(user_id)

        # Filter valid transactions
        valid_txs = [tx for tx in transactions if not tx.is_transfer and not tx.is_duplicate]

        # Filter by period
        if period:
            year, month = map(int, period.split("-"))
            valid_txs = [
                tx for tx in valid_txs
                if tx.posted_at.year == year and tx.posted_at.month == month
            ]

        # Group by category
        spending_by_category = {}
        for tx in valid_txs:
            if tx.category and tx.amount < 0:
                spending_by_category[tx.category] = (
                    spending_by_category.get(tx.category, Decimal(0)) + abs(tx.amount)
                )

        # Build summaries
        category_summaries = []
        for cat in categories:
            spent = spending_by_category.get(cat['key'], Decimal(0))
            target = Decimal(str(cat['target']))
            remaining = target - spent

            category_summaries.append({
                "key": cat['key'],
                "label": cat['label'],
                "target": float(target),
                "spent": float(spent),
                "remaining": float(remaining),
                "rollover": cat['rollover']
            })

        # Calculate totals
        total_spent = sum(spending_by_category.values())
        total_income = sum(abs(tx.amount) for tx in valid_txs if tx.amount > 0)

        # Coverage
        categorized = sum(1 for tx in valid_txs if tx.category)
        coverage = categorized / len(valid_txs) if valid_txs else 0

        return BudgetSummaryResponse(
            period=period or utc_now().strftime("%Y-%m"),
            last_updated=utc_now(),
            totals={
                "spent": float(total_spent),
                "income": float(total_income),
                "savings": 0
            },
            categories=category_summaries,
            coverage_pct=coverage
        )

    async def _load_categories(self, user_id: str) -> List[Dict]:
        """Load categories via Supabase client"""
        from app.deps import get_supabase_client

        supabase = get_supabase_client()
        result = supabase.table("budget_categories").select("*").eq("user_id", user_id).order("order").execute()
        return result.data or []


# Global instance
budget_engine = BudgetEngine()

