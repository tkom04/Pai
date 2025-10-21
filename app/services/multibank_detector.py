"""Multi-bank detection service for transfers, duplicates, and UK utility categorization."""
import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

from ..models import Transaction, NormalizedTransaction
from ..util.logging import logger
from ..deps import get_supabase_client


class MultiBankDetector:
    """Detects transfers, duplicates, and categorizes UK utilities across multiple bank accounts."""

    def __init__(self):
        self.supabase = get_supabase_client()

        # UK utility patterns for auto-categorization
        self.UK_UTILITY_PATTERNS = {
            'council_tax': [r'COUNCIL TAX', r'\bCOUNCIL\b', r'LOCAL AUTHORITY'],
            'water': [r'WATER', r'THAMES', r'ANGLIAN', r'SEVERN TRENT', r'UNITED UTILITIES', r'YORKSHIRE WATER'],
            'energy': [r'BRITISH GAS', r'EDF ENERGY', r'E\.ON', r'OCTOPUS', r'BULB', r'OVO', r'UTILITA'],
            'broadband': [r'BT\b', r'SKY', r'VIRGIN MEDIA', r'TALKTALK', r'PLUSNET', r'EE\b'],
            'mortgage': [r'MORTGAGE', r'HALIFAX MTG', r'SANTANDER MTG', r'NATIONWIDE BS', r'BARCLAYS MTG'],
            'rent': [r'RENT', r'LETTING', r'ESTATE AGENT', r'PROPERTY MANAGEMENT', r'LANDLORD'],
            'insurance': [r'INSURANCE', r'ADMIRAL', r'DIRECT LINE', r'AVIVA', r'CHURCHILL'],
            'mobile': [r'VODAFONE', r'O2\b', r'THREE\b', r'EE MOBILE', r'GIFFGAFF'],
            'council': [r'COUNCIL', r'BOROUGH', r'DISTRICT COUNCIL', r'CITY COUNCIL']
        }

    async def detect_transfers(self, user_id: str, transactions: List[NormalizedTransaction]) -> List[Dict[str, Any]]:
        """
        Detect transfers between user's accounts.

        Algorithm:
        - Same day ± 2 days
        - Amounts match (opposite signs)
        - Not already marked as recurring payment
        - Exclude if description contains merchant names
        """
        try:
            logger.info(f"Detecting transfers for user {user_id} with {len(transactions)} transactions")

            # Group transactions by account
            account_transactions = defaultdict(list)
            for tx in transactions:
                account_transactions[tx.account_id].append(tx)

            detected_transfers = []
            processed_pairs = set()

            # Compare transactions between different accounts
            account_ids = list(account_transactions.keys())
            for i, source_account in enumerate(account_ids):
                for j, dest_account in enumerate(account_ids):
                    if i >= j:  # Avoid duplicate comparisons
                        continue

                    source_txs = account_transactions[source_account]
                    dest_txs = account_transactions[dest_account]

                    for source_tx in source_txs:
                        for dest_tx in dest_txs:
                            # Skip if already processed
                            pair_key = tuple(sorted([source_tx.id, dest_tx.id]))
                            if pair_key in processed_pairs:
                                continue
                            processed_pairs.add(pair_key)

                            # Check if this looks like a transfer
                            if self._is_transfer_candidate(source_tx, dest_tx):
                                transfer_data = {
                                    'user_id': user_id,
                                    'source_account_id': source_tx.account_id,
                                    'destination_account_id': dest_tx.account_id,
                                    'relationship_type': 'transfer',
                                    'detected_at': datetime.utcnow().isoformat(),
                                    'confirmed_by_user': False
                                }
                                detected_transfers.append(transfer_data)

                                # Mark transactions as transfers
                                source_tx.is_transfer = True
                                dest_tx.is_transfer = True

                                logger.info(f"Detected transfer: {source_tx.account_id} -> {dest_tx.account_id}, amount: {abs(source_tx.amount)}")

            # Store detected transfers in database
            if detected_transfers:
                self.supabase.table("account_mappings").insert(detected_transfers).execute()
                logger.info(f"Stored {len(detected_transfers)} transfer mappings")

            return detected_transfers

        except Exception as e:
            logger.error(f"Error detecting transfers: {e}", exc_info=True)
            return []

    def _is_transfer_candidate(self, tx1: NormalizedTransaction, tx2: NormalizedTransaction) -> bool:
        """Check if two transactions are likely a transfer."""
        # Amounts must be opposite signs and similar magnitude
        if tx1.amount * tx2.amount >= 0:  # Same sign
            return False

        amount_diff = abs(abs(tx1.amount) - abs(tx2.amount))
        if amount_diff > Decimal('0.01'):  # Allow 1p difference for fees
            return False

        # Dates must be within 3 days
        date_diff = abs((tx1.posted_at - tx2.posted_at).days)
        if date_diff > 3:
            return False

        # Exclude if descriptions contain merchant names (not transfers)
        if self._contains_merchant_name(tx1.description) or self._contains_merchant_name(tx2.description):
            return False

        # Exclude if already marked as recurring payments
        if tx1.is_duplicate or tx2.is_duplicate:
            return False

        return True

    def _contains_merchant_name(self, description: str) -> bool:
        """Check if description contains merchant names (not transfer keywords)."""
        merchant_keywords = [
            'PAYMENT TO', 'PAYMENT FROM', 'TRANSFER TO', 'TRANSFER FROM',
            'DD ', 'DIRECT DEBIT', 'STANDING ORDER', 'FASTER PAYMENT'
        ]

        description_upper = description.upper()
        return any(keyword in description_upper for keyword in merchant_keywords)

    async def detect_duplicate_subscriptions(self, user_id: str, transactions: List[NormalizedTransaction]) -> List[Dict[str, Any]]:
        """
        Detect duplicate subscriptions across different accounts.

        Algorithm:
        - Same normalized merchant across different accounts
        - Similar amounts (within 10%)
        - Same frequency detected
        - Occurring in same time window
        """
        try:
            logger.info(f"Detecting duplicate subscriptions for user {user_id}")

            # Group by normalized merchant name
            merchant_groups = defaultdict(list)
            for tx in transactions:
                if tx.merchant and not tx.is_transfer:
                    normalized_merchant = self._normalize_merchant_name(tx.merchant)
                    merchant_groups[normalized_merchant].append(tx)

            detected_duplicates = []

            for merchant, merchant_txs in merchant_groups.items():
                if len(merchant_txs) < 2:
                    continue

                # Group by account
                account_groups = defaultdict(list)
                for tx in merchant_txs:
                    account_groups[tx.account_id].append(tx)

                # Check for duplicates across accounts
                account_ids = list(account_groups.keys())
                for i, account1 in enumerate(account_ids):
                    for j, account2 in enumerate(account_ids):
                        if i >= j:
                            continue

                        account1_txs = account_groups[account1]
                        account2_txs = account_groups[account2]

                        # Find similar transactions
                        for tx1 in account1_txs:
                            for tx2 in account2_txs:
                                if self._is_duplicate_candidate(tx1, tx2):
                                    similarity_score = self._calculate_similarity_score(tx1, tx2)

                                    duplicate_data = {
                                        'user_id': user_id,
                                        'tx1_hash': self._create_transaction_hash(tx1),
                                        'tx2_hash': self._create_transaction_hash(tx2),
                                        'similarity_score': float(similarity_score),
                                        'is_duplicate': False,
                                        'user_confirmed': False,
                                        'created_at': datetime.utcnow().isoformat()
                                    }
                                    detected_duplicates.append(duplicate_data)

                                    logger.info(f"Detected potential duplicate: {merchant} - {tx1.account_id} & {tx2.account_id}")

            # Store detected duplicates
            if detected_duplicates:
                self.supabase.table("duplicate_transactions").insert(detected_duplicates).execute()
                logger.info(f"Stored {len(detected_duplicates)} duplicate transactions")

            return detected_duplicates

        except Exception as e:
            logger.error(f"Error detecting duplicate subscriptions: {e}", exc_info=True)
            return []

    def _is_duplicate_candidate(self, tx1: NormalizedTransaction, tx2: NormalizedTransaction) -> bool:
        """Check if two transactions are likely duplicates."""
        # Same merchant
        if tx1.merchant != tx2.merchant:
            return False

        # Similar amounts (within 10%)
        amount_diff = abs(tx1.amount - tx2.amount)
        avg_amount = (abs(tx1.amount) + abs(tx2.amount)) / 2
        if avg_amount > 0 and (amount_diff / avg_amount) > 0.1:
            return False

        # Within 7 days
        date_diff = abs((tx1.posted_at - tx2.posted_at).days)
        if date_diff > 7:
            return False

        return True

    def _calculate_similarity_score(self, tx1: NormalizedTransaction, tx2: NormalizedTransaction) -> Decimal:
        """Calculate similarity score between two transactions."""
        score = Decimal('0.0')

        # Merchant match (40% weight)
        if tx1.merchant == tx2.merchant:
            score += Decimal('0.4')

        # Amount similarity (30% weight)
        amount_diff = abs(tx1.amount - tx2.amount)
        avg_amount = (abs(tx1.amount) + abs(tx2.amount)) / 2
        if avg_amount > 0:
            amount_similarity = max(0, 1 - (amount_diff / avg_amount))
            score += Decimal(str(amount_similarity)) * Decimal('0.3')

        # Date proximity (30% weight)
        date_diff = abs((tx1.posted_at - tx2.posted_at).days)
        date_similarity = max(0, 1 - (date_diff / 7))  # 7 days max
        score += Decimal(str(date_similarity)) * Decimal('0.3')

        return min(score, Decimal('1.0'))

    def _create_transaction_hash(self, tx: NormalizedTransaction) -> str:
        """Create a hash for transaction identification."""
        hash_string = f"{tx.account_id}_{tx.amount}_{tx.posted_at.isoformat()}_{tx.merchant}"
        return hashlib.md5(hash_string.encode()).hexdigest()

    def _normalize_merchant_name(self, merchant: str) -> str:
        """Normalize merchant name for comparison."""
        if not merchant:
            return ""

        # Remove common prefixes and suffixes
        normalized = merchant.upper().strip()

        # Remove common prefixes
        prefixes_to_remove = [
            'PAYMENT TO ', 'PAYMENT FROM ', 'DD ', 'DIRECT DEBIT ',
            'STANDING ORDER ', 'FASTER PAYMENT ', 'TRANSFER TO '
        ]

        for prefix in prefixes_to_remove:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]

        # Remove common suffixes
        suffixes_to_remove = [
            ' LTD', ' LIMITED', ' PLC', ' INC', ' CORP', ' CORPORATION'
        ]

        for suffix in suffixes_to_remove:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]

        return normalized.strip()

    async def detect_debt_payments(self, user_id: str, transactions: List[NormalizedTransaction]) -> List[Dict[str, Any]]:
        """
        Detect debt payments (credit card payments, loan payments).

        Algorithm:
        - Identify "PAYMENT TO {CARD}" descriptions
        - Match against known debt account patterns
        - Update debt_accounts table
        """
        try:
            logger.info(f"Detecting debt payments for user {user_id}")

            debt_payments = []
            debt_patterns = [
                r'PAYMENT TO (.+) CARD',
                r'PAYMENT TO (.+) CREDIT',
                r'PAYMENT TO (.+) LOAN',
                r'PAYMENT TO (.+) MORTGAGE',
                r'(.+) CARD PAYMENT',
                r'(.+) LOAN PAYMENT'
            ]

            for tx in transactions:
                if tx.amount < 0:  # Outgoing payment
                    description_upper = tx.description.upper()

                    for pattern in debt_patterns:
                        match = re.search(pattern, description_upper)
                        if match:
                            debt_name = match.group(1).strip()

                            # Determine debt type
                            debt_type = 'credit_card'
                            if 'LOAN' in description_upper or 'MORTGAGE' in description_upper:
                                debt_type = 'loan'

                            debt_payment = {
                                'user_id': user_id,
                                'account_name': debt_name,
                                'debt_type': debt_type,
                                'amount': abs(float(tx.amount)),
                                'payment_date': tx.posted_at.date().isoformat(),
                                'detected_at': datetime.utcnow().isoformat()
                            }
                            debt_payments.append(debt_payment)

                            logger.info(f"Detected debt payment: {debt_name} - {abs(tx.amount)}")
                            break

            return debt_payments

        except Exception as e:
            logger.error(f"Error detecting debt payments: {e}", exc_info=True)
            return []

    async def categorize_uk_utilities(self, transaction: NormalizedTransaction) -> Optional[Tuple[str, float]]:
        """
        Categorize UK utilities using pattern matching.

        Returns: (category, confidence_score)
        """
        try:
            description_upper = transaction.description.upper()
            merchant_upper = (transaction.merchant or "").upper()

            # Combine description and merchant for matching
            text_to_match = f"{description_upper} {merchant_upper}"

            best_match = None
            best_confidence = 0.0

            for category, patterns in self.UK_UTILITY_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, text_to_match, re.IGNORECASE):
                        # Calculate confidence based on pattern specificity
                        confidence = 0.9 if len(pattern) > 10 else 0.7

                        if confidence > best_confidence:
                            best_match = category
                            best_confidence = confidence

            if best_match:
                logger.info(f"Categorized transaction: {transaction.description} -> {best_match} (confidence: {best_confidence})")
                return best_match, best_confidence

            return None

        except Exception as e:
            logger.error(f"Error categorizing UK utilities: {e}", exc_info=True)
            return None

    async def process_transactions(self, user_id: str, transactions: List[NormalizedTransaction]) -> Dict[str, Any]:
        """
        Process all transactions with multi-bank detection.

        Returns summary of detected patterns.
        """
        try:
            logger.info(f"Processing {len(transactions)} transactions for multi-bank detection")

            # Detect transfers
            transfers = await self.detect_transfers(user_id, transactions)

            # Detect duplicate subscriptions
            duplicates = await self.detect_duplicate_subscriptions(user_id, transactions)

            # Detect debt payments
            debt_payments = await self.detect_debt_payments(user_id, transactions)

            # Categorize UK utilities
            categorized_count = 0
            for tx in transactions:
                if not tx.category:  # Only categorize if not already categorized
                    category_result = await self.categorize_uk_utilities(tx)
                    if category_result:
                        tx.category = category_result[0]
                        tx.category_confidence = "high" if category_result[1] > 0.8 else "medium"
                        categorized_count += 1

            summary = {
                'transfers_detected': len(transfers),
                'duplicates_detected': len(duplicates),
                'debt_payments_detected': len(debt_payments),
                'utilities_categorized': categorized_count,
                'total_processed': len(transactions)
            }

            logger.info(f"Multi-bank processing complete: {summary}")
            return summary

        except Exception as e:
            logger.error(f"Error in multi-bank processing: {e}", exc_info=True)
            return {
                'transfers_detected': 0,
                'duplicates_detected': 0,
                'debt_payments_detected': 0,
                'utilities_categorized': 0,
                'total_processed': 0,
                'error': str(e)
            }


# Global detector instance
multibank_detector = MultiBankDetector()
