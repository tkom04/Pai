"""Tests for TransactionProcessor with security and performance focus."""
import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

from app.services.transaction_processor import TransactionProcessor
from app.models import Transaction, NormalizedTransaction


class TestTransactionProcessor:

    @pytest.fixture
    def processor(self):
        return TransactionProcessor()

    @pytest.fixture
    def sample_transaction(self):
        return Transaction(
            transaction_id="tx_123",
            timestamp=datetime.now(timezone.utc),
            description="Tesco Express",
            amount=-5.50,
            currency="GBP",
            transaction_type="DEBIT",
            merchant_name="Tesco"
        )

    @pytest.fixture
    def sample_transactions(self):
        return [
            Transaction(
                transaction_id="tx_1",
                timestamp=datetime.now(timezone.utc),
                description="Tesco Express",
                amount=-5.50,
                currency="GBP",
                transaction_type="DEBIT",
                merchant_name="Tesco"
            ),
            Transaction(
                transaction_id="tx_2",
                timestamp=datetime.now(timezone.utc) + timedelta(minutes=5),
                description="Tesco Express",
                amount=-5.50,
                currency="GBP",
                transaction_type="DEBIT",
                merchant_name="Tesco"
            ),
            Transaction(
                transaction_id="tx_3",
                timestamp=datetime.now(timezone.utc),
                description="Shell Petrol",
                amount=-45.00,
                currency="GBP",
                transaction_type="DEBIT",
                merchant_name="Shell"
            )
        ]

    @pytest.mark.asyncio
    async def test_normalize_transaction(self, processor, sample_transaction):
        """Test transaction normalization with proper account_id."""
        normalized = await processor.normalize_transaction(sample_transaction)

        assert isinstance(normalized, NormalizedTransaction)
        assert normalized.id == "tx_123"
        assert normalized.amount == Decimal("-5.50")
        assert normalized.currency == "GBP"
        assert normalized.merchant == "Tesco"
        assert normalized.description == "Tesco Express"
        assert normalized.account_id == "tx_123"  # Fallback until Transaction model updated
        assert not normalized.is_transfer
        assert not normalized.is_duplicate

    def test_deduplication_allows_multiple_same_merchant(self, processor, sample_transactions):
        """Two coffees same day should NOT be duplicates."""
        # Convert to normalized transactions
        normalized = []
        for tx in sample_transactions:
            norm = NormalizedTransaction(
                id=tx.transaction_id,
                posted_at=tx.timestamp,
                amount=Decimal(str(tx.amount)),
                currency=tx.currency,
                description=tx.description,
                merchant=tx.merchant_name,
                account_id=tx.transaction_id,
                is_transfer=False,
                is_duplicate=False
            )
            normalized.append(norm)

        # Process deduplication
        result = processor.deduplicate_transactions(normalized)

        # Should have 3 transactions, none marked as duplicates
        assert len(result) == 3
        duplicates = [tx for tx in result if tx.is_duplicate]
        assert len(duplicates) == 0

    def test_deduplication_marks_exact_duplicates(self, processor):
        """Exact same transactions should be marked as duplicates."""
        now = datetime.now(timezone.utc)

        # Create two identical transactions
        tx1 = NormalizedTransaction(
            id="tx_1",
            posted_at=now,
            amount=Decimal("-5.50"),
            currency="GBP",
            description="Tesco Express",
            merchant="Tesco",
            account_id="acc_123",
            is_transfer=False,
            is_duplicate=False
        )

        tx2 = NormalizedTransaction(
            id="tx_2",
            posted_at=now,
            amount=Decimal("-5.50"),
            currency="GBP",
            description="Tesco Express",
            merchant="Tesco",
            account_id="acc_123",
            is_transfer=False,
            is_duplicate=False
        )

        result = processor.deduplicate_transactions([tx1, tx2])

        # Second transaction should be marked as duplicate
        duplicates = [tx for tx in result if tx.is_duplicate]
        assert len(duplicates) == 1
        assert duplicates[0].id == "tx_2"

    def test_transfer_detection_performance(self, processor):
        """Test transfer detection with large dataset - should be O(n)."""
        import time

        # Create 1000 transactions with some transfers
        transactions = []
        now = datetime.now(timezone.utc)

        for i in range(500):
            # Positive transaction (incoming)
            tx_pos = NormalizedTransaction(
                id=f"pos_{i}",
                posted_at=now,
                amount=Decimal("100.00"),
                currency="GBP",
                description=f"Transfer In {i}",
                merchant="Bank Transfer",
                account_id="acc_1",
                is_transfer=False,
                is_duplicate=False
            )
            transactions.append(tx_pos)

            # Negative transaction (outgoing) - different account
            tx_neg = NormalizedTransaction(
                id=f"neg_{i}",
                posted_at=now,
                amount=Decimal("-100.00"),
                currency="GBP",
                description=f"Transfer Out {i}",
                merchant="Bank Transfer",
                account_id="acc_2",
                is_transfer=False,
                is_duplicate=False
            )
            transactions.append(tx_neg)

        # Measure processing time
        start_time = time.time()
        result = processor.detect_transfers(transactions)
        end_time = time.time()

        processing_time = end_time - start_time

        # Should process 1000 transactions in <1 second
        assert processing_time < 1.0, f"Processing took {processing_time:.2f}s, expected <1s"

        # Check that transfers were detected
        transfers = [tx for tx in result if tx.is_transfer]
        assert len(transfers) == 1000  # All should be marked as transfers

    def test_heuristic_categorization(self, processor):
        """Test UK-specific keyword categorization."""
        test_cases = [
            ("Tesco Superstore", "groceries"),
            ("Shell Petrol Station", "transport"),
            ("British Gas", "utilities"),
            ("Netflix Subscription", "entertainment"),
            ("Amazon Purchase", "shopping"),
            ("Unknown Merchant", None)
        ]

        for description, expected_category in test_cases:
            tx = NormalizedTransaction(
                id="test",
                posted_at=datetime.now(timezone.utc),
                amount=Decimal("-10.00"),
                currency="GBP",
                description=description,
                merchant=None,
                account_id="test",
                is_transfer=False,
                is_duplicate=False
            )

            category = processor._categorize_heuristic(tx)
            assert category == expected_category, f"Failed for '{description}': expected {expected_category}, got {category}"

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, processor):
        """Test that malicious input is safely handled."""
        malicious_inputs = [
            "'; DROP TABLE budget_categories;--",
            "1' OR '1'='1",
            "<script>alert('xss')</script>",
            "../../etc/passwd",
            "null\0byte"
        ]

        for malicious in malicious_inputs:
            tx = NormalizedTransaction(
                id=malicious,
                posted_at=datetime.now(timezone.utc),
                amount=Decimal("-10.00"),
                currency="GBP",
                description=malicious,
                merchant=malicious,
                account_id=malicious,
                is_transfer=False,
                is_duplicate=False
            )

            # Should not crash or execute malicious code
            category = processor._categorize_heuristic(tx)
            assert category is None or isinstance(category, str)

            # Hash should be generated safely
            tx_hash = processor._transaction_hash(tx)
            assert isinstance(tx_hash, str)
            assert len(tx_hash) == 64  # SHA256 hex length

    @pytest.mark.asyncio
    async def test_rule_matching(self, processor):
        """Test rule matching logic."""
        tx = NormalizedTransaction(
            id="test",
            posted_at=datetime.now(timezone.utc),
            amount=Decimal("-25.50"),
            currency="GBP",
            description="Tesco Express Purchase",
            merchant="Tesco",
            account_id="acc_123",
            is_transfer=False,
            is_duplicate=False
        )

        # Test merchant matching
        rule1 = {"merchant": "Tesco"}
        assert processor._rule_matches(tx, rule1)

        # Test description matching
        rule2 = {"description_contains": "Express"}
        assert processor._rule_matches(tx, rule2)

        # Test amount matching
        rule3 = {"amount_min": 20, "amount_max": 30}
        assert processor._rule_matches(tx, rule3)

        # Test negative matching
        rule4 = {"merchant": "Sainsbury"}
        assert not processor._rule_matches(tx, rule4)

        # Test amount outside range
        rule5 = {"amount_min": 50}
        assert not processor._rule_matches(tx, rule5)

    def test_72_hour_deduplication_window(self, processor):
        """Test 72-hour deduplication window."""
        base_time = datetime.now(timezone.utc)

        # Create transactions within 72-hour window
        tx1 = NormalizedTransaction(
            id="tx_1",
            posted_at=base_time,
            amount=Decimal("-5.50"),
            currency="GBP",
            description="Tesco Express",
            merchant="Tesco",
            account_id="acc_123",
            is_transfer=False,
            is_duplicate=False
        )

        tx2 = NormalizedTransaction(
            id="tx_2",
            posted_at=base_time + timedelta(hours=36),  # Within 72h window
            amount=Decimal("-5.50"),
            currency="GBP",
            description="Tesco Express",
            merchant="Tesco",
            account_id="acc_123",
            is_transfer=False,
            is_duplicate=False
        )

        # First pass - should not be duplicates
        result1 = processor.deduplicate_transactions([tx1, tx2])
        duplicates1 = [tx for tx in result1 if tx.is_duplicate]
        assert len(duplicates1) == 0

        # Second pass - should mark as duplicate due to hash cache
        result2 = processor.deduplicate_transactions([tx1, tx2])
        duplicates2 = [tx for tx in result2 if tx.is_duplicate]
        assert len(duplicates2) == 1

    def test_hash_cleanup(self, processor):
        """Test that old hashes are cleaned up."""
        # Add some old hashes
        old_time = datetime.now(timezone.utc) - timedelta(days=8)
        processor.recent_hashes["old_hash"] = old_time

        # Add a new hash
        new_time = datetime.now(timezone.utc)
        processor.recent_hashes["new_hash"] = new_time

        # Process a transaction to trigger cleanup
        tx = NormalizedTransaction(
            id="test",
            posted_at=new_time,
            amount=Decimal("-10.00"),
            currency="GBP",
            description="Test",
            merchant="Test",
            account_id="acc_123",
            is_transfer=False,
            is_duplicate=False
        )

        processor.deduplicate_transactions([tx])

        # Old hash should be removed
        assert "old_hash" not in processor.recent_hashes
        assert "new_hash" in processor.recent_hashes

