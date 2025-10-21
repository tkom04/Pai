"""Transaction processing service with O(n) algorithms and security fixes."""
from collections import defaultdict
from decimal import Decimal
from typing import List, Dict, Optional, Set, Tuple
from datetime import timedelta, date
import hashlib
import logging

from app.models import Transaction, NormalizedTransaction
from app.util.time import utc_now

logger = logging.getLogger(__name__)


class TransactionProcessor:
    """Processes and normalizes bank transactions with deduplication and categorization."""

    def __init__(self):
        self.ecb_rates_cache: Dict[str, Tuple[float, datetime]] = {}
        self.cache_ttl = 3600
        self.recent_hashes: Dict[str, datetime] = {}  # For 72h dedup window

    async def normalize_batch(self, transactions: List[Transaction]) -> List[NormalizedTransaction]:
        """Normalize, deduplicate, detect transfers"""
        normalized = [await self.normalize_transaction(tx) for tx in transactions]
        normalized = self.deduplicate_transactions(normalized)
        normalized = self.detect_transfers(normalized)
        return normalized

    async def normalize_transaction(self, tx: Transaction) -> NormalizedTransaction:
        """FIXED: Use real account_id, not transaction_id"""
        merchant = tx.merchant_name or self._extract_merchant(tx.description)

        amount, currency = tx.amount, tx.currency
        if currency != "GBP":
            rate = await self._get_exchange_rate(currency, "GBP")
            amount = amount * Decimal(str(rate))
            currency = "GBP"

        # Use real account_id from TrueLayer response
        account_id = tx.account_id

        return NormalizedTransaction(
            id=tx.transaction_id,
            posted_at=tx.timestamp,
            amount=Decimal(str(amount)),
            currency=currency,
            description=tx.description,
            merchant=merchant,
            mcc=None,
            account_id=account_id,  # FIXED
            is_transfer=False,
            is_duplicate=False,
            category=None
        )

    def deduplicate_transactions(self, transactions: List[NormalizedTransaction]) -> List[NormalizedTransaction]:
        """FIXED: 72-hour window + timestamp (not just date)"""
        seen: Set[str] = set()

        for tx in transactions:
            tx_hash = self._transaction_hash(tx)

            # Check if seen within 72-hour window
            if tx_hash in self.recent_hashes:
                time_diff = abs((tx.posted_at - self.recent_hashes[tx_hash]).total_seconds())
                if time_diff < 72 * 3600:  # 72 hours
                    tx.is_duplicate = True
                    continue

            seen.add(tx_hash)
            self.recent_hashes[tx_hash] = tx.posted_at

        # Cleanup old hashes (>7 days)
        cutoff = utc_now() - timedelta(days=7)
        self.recent_hashes = {
            h: t for h, t in self.recent_hashes.items() if t > cutoff
        }

        return transactions

    def detect_transfers(self, transactions: List[NormalizedTransaction]) -> List[NormalizedTransaction]:
        """FIXED: O(n) using date+amount buckets instead of O(n²)"""
        buckets: Dict[Tuple[date, Decimal], List[NormalizedTransaction]] = defaultdict(list)

        def _round_amount(a: Decimal) -> Decimal:
            return a.quantize(Decimal("0.01"))

        # Bucket by date + rounded amount
        for tx in transactions:
            key = (tx.posted_at.date(), _round_amount(abs(tx.amount)))
            buckets[key].append(tx)

        # Find opposite-sign pairs from different accounts
        for group in buckets.values():
            positive = [t for t in group if t.amount > 0]
            negative = [t for t in group if t.amount < 0]

            for pos_tx, neg_tx in zip(positive, negative):
                if pos_tx.account_id != neg_tx.account_id:
                    pos_tx.is_transfer = True
                    neg_tx.is_transfer = True

        return transactions

    def _transaction_hash(self, tx: NormalizedTransaction) -> str:
        """FIXED: Include timestamp + first 50 chars of description"""
        data = (
            f"{tx.account_id}:"
            f"{tx.posted_at.isoformat()}:"
            f"{tx.amount}:"
            f"{tx.description[:50]}"
        )
        return hashlib.sha256(data.encode()).hexdigest()

    def _extract_merchant(self, description: str) -> str:
        """Extract merchant name from description"""
        parts = description.strip().split()
        return parts[0] if parts else description

    async def _get_exchange_rate(self, from_curr: str, to_curr: str) -> float:
        """Get ECB rate with 1-hour cache"""
        cache_key = f"{from_curr}_{to_curr}"

        if cache_key in self.ecb_rates_cache:
            rate, cached_at = self.ecb_rates_cache[cache_key]
            if (utc_now() - cached_at).total_seconds() < self.cache_ttl:
                return rate

        # TODO: Implement ECB API call
        rate = 1.0
        self.ecb_rates_cache[cache_key] = (rate, utc_now())
        return rate

    async def apply_rules(self, transactions: List[NormalizedTransaction], user_id: str) -> List[NormalizedTransaction]:
        """Apply user rules + heuristics"""
        rules = await self._load_rules(user_id)

        for tx in transactions:
            if tx.is_transfer or tx.is_duplicate:
                continue

            category = self._apply_user_rules(tx, rules)
            if not category:
                category = self._categorize_heuristic(tx)

            tx.category = category
            tx.category_confidence = "high" if category else "low"

        return transactions

    async def _load_rules(self, user_id: str) -> List[Dict]:
        """Load rules via Supabase client"""
        from app.deps import get_supabase_client

        supabase = get_supabase_client()
        result = supabase.table("budget_rules").select("*").eq("user_id", user_id).order("priority").execute()
        return result.data or []

    def _apply_user_rules(self, tx: NormalizedTransaction, rules: List[Dict]) -> Optional[str]:
        """Apply user-defined rules"""
        for rule in rules:
            matchers = rule['matchers']
            if self._rule_matches(tx, matchers):
                return rule['category_key']
        return None

    def _rule_matches(self, tx: NormalizedTransaction, matchers: Dict) -> bool:
        """Check if transaction matches rule"""
        if 'merchant' in matchers:
            if not tx.merchant or matchers['merchant'].lower() not in tx.merchant.lower():
                return False

        if 'description_contains' in matchers:
            if matchers['description_contains'].lower() not in tx.description.lower():
                return False

        if 'amount_min' in matchers and tx.amount < Decimal(str(matchers['amount_min'])):
            return False

        if 'amount_max' in matchers and tx.amount > Decimal(str(matchers['amount_max'])):
            return False

        return True

    def _categorize_heuristic(self, tx: NormalizedTransaction) -> Optional[str]:
        """UK-specific keyword categorization"""
        text = f"{tx.merchant or ''} {tx.description}".lower()

        if any(kw in text for kw in ["tesco", "sainsbury", "asda", "waitrose", "morrisons", "aldi", "lidl", "restaurant", "cafe", "pizza"]):
            return "groceries"
        elif any(kw in text for kw in ["shell", "bp", "esso", "tfl", "uber", "train", "fuel", "petrol"]):
            return "transport"
        elif any(kw in text for kw in ["british gas", "edf", "bt", "virgin", "sky", "vodafone"]):
            return "utilities"
        elif any(kw in text for kw in ["cinema", "netflix", "spotify", "steam", "gym"]):
            return "entertainment"
        elif any(kw in text for kw in ["amazon", "ebay", "argos", "john lewis"]):
            return "shopping"

        return None


# Global instance
transaction_processor = TransactionProcessor()

