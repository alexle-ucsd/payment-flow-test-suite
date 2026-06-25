"""
Payment Flow Test Suite
40 pytest test cases covering payment processing, refunds, 
voids, chargebacks, and transaction retrieval.
Author: Alex Le
"""

import pytest
from payment_processor import PaymentProcessor, ChargebackHandler


@pytest.fixture
def processor():
    return PaymentProcessor()

@pytest.fixture
def handler(processor):
    return ChargebackHandler(processor)

@pytest.fixture
def approved_txn(processor):
    result = processor.process_payment(
        amount=75.00, card_type="visa",
        card_number="4111111111111111", merchant_id="MERCHANT-001"
    )
    return result["transaction_id"]


class TestPaymentProcessing:
    def test_valid_visa_payment_approved(self, processor):
        result = processor.process_payment(100.00, "visa", "4111111111111111", "M-001")
        assert result["status"] == "approved"
        assert result["amount"] == 100.00

    def test_valid_mastercard_approved(self, processor):
        result = processor.process_payment(250.50, "mastercard", "5500005555555559", "M-002")
        assert result["status"] == "approved"

    def test_valid_amex_approved(self, processor):
        result = processor.process_payment(500.00, "amex", "378282246310005", "M-001")
        assert result["status"] == "approved"

    def test_unsupported_card_rejected(self, processor):
        result = processor.process_payment(50.00, "unionpay", "6221234567890123", "M-001")
        assert result["status"] == "error"
        assert result["code"] == "UNSUPPORTED_CARD"

    def test_invalid_card_number_rejected(self, processor):
        result = processor.process_payment(50.00, "visa", "1234ABC", "M-001")
        assert result["status"] == "error"
        assert result["code"] == "INVALID_CARD"

    def test_zero_amount_rejected(self, processor):
        result = processor.process_payment(0.00, "visa", "4111111111111111", "M-001")
        assert result["status"] == "error"
        assert result["code"] == "AMOUNT_TOO_LOW"

    def test_negative_amount_rejected(self, processor):
        result = processor.process_payment(-10.00, "visa", "4111111111111111", "M-001")
        assert result["status"] == "error"
        assert result["code"] == "AMOUNT_TOO_LOW"

    def test_amount_exceeds_limit(self, processor):
        result = processor.process_payment(55000.00, "visa", "4111111111111111", "M-001")
        assert result["status"] == "error"
        assert result["code"] == "AMOUNT_EXCEEDS_LIMIT"

    def test_maximum_amount_approved(self, processor):
        result = processor.process_payment(50000.00, "visa", "4111111111111111", "M-001")
        assert result["status"] == "approved"

    def test_minimum_amount_approved(self, processor):
        result = processor.process_payment(0.01, "visa", "4111111111111111", "M-001")
        assert result["status"] == "approved"

    def test_missing_merchant_id(self, processor):
        result = processor.process_payment(50.00, "visa", "4111111111111111", "")
        assert result["status"] == "error"
        assert result["code"] == "INVALID_MERCHANT"

    def test_amount_rounded_to_two_decimals(self, processor):
        result = processor.process_payment(19.999, "visa", "4111111111111111", "M-001")
        assert result["amount"] == 20.00

    def test_card_number_with_spaces(self, processor):
        result = processor.process_payment(75.00, "visa", "4111 1111 1111 1111", "M-001")
        assert result["status"] == "approved"

    def test_unique_transaction_ids(self, processor):
        r1 = processor.process_payment(50.00, "visa", "4111111111111111", "M-001")
        r2 = processor.process_payment(75.00, "visa", "4111111111111111", "M-001")
        assert r1["transaction_id"] != r2["transaction_id"]

    def test_card_type_case_insensitive(self, processor):
        result = processor.process_payment(100.00, "VISA", "4111111111111111", "M-001")
        assert result["status"] == "approved"


class TestRefunds:
    def test_full_refund_succeeds(self, processor, approved_txn):
        result = processor.refund_payment(approved_txn)
        assert result["status"] == "refunded"
        assert result["refund_amount"] == 75.00

    def test_partial_refund_succeeds(self, processor, approved_txn):
        result = processor.refund_payment(approved_txn, refund_amount=25.00)
        assert result["status"] == "refunded"
        assert result["refund_amount"] == 25.00

    def test_refund_exceeds_original(self, processor, approved_txn):
        result = processor.refund_payment(approved_txn, refund_amount=200.00)
        assert result["status"] == "error"
        assert result["code"] == "REFUND_EXCEEDS_ORIGINAL"

    def test_double_refund_rejected(self, processor, approved_txn):
        processor.refund_payment(approved_txn)
        result = processor.refund_payment(approved_txn)
        assert result["status"] == "error"
        assert result["code"] == "ALREADY_REFUNDED"

    def test_refund_nonexistent_transaction(self, processor):
        result = processor.refund_payment("TXN-FAKE-9999")
        assert result["status"] == "error"
        assert result["code"] == "TXN_NOT_FOUND"

    def test_refund_zero_amount_rejected(self, processor, approved_txn):
        result = processor.refund_payment(approved_txn, refund_amount=0.00)
        assert result["status"] == "error"
        assert result["code"] == "INVALID_REFUND_AMOUNT"

    def test_cannot_refund_voided_transaction(self, processor, approved_txn):
        processor.void_transaction(approved_txn)
        result = processor.refund_payment(approved_txn)
        assert result["status"] == "error"
        assert result["code"] == "TXN_VOIDED"


class TestVoids:
    def test_void_succeeds(self, processor, approved_txn):
        result = processor.void_transaction(approved_txn)
        assert result["status"] == "voided"

    def test_double_void_rejected(self, processor, approved_txn):
        processor.void_transaction(approved_txn)
        result = processor.void_transaction(approved_txn)
        assert result["status"] == "error"
        assert result["code"] == "ALREADY_VOIDED"

    def test_void_nonexistent_transaction(self, processor):
        result = processor.void_transaction("TXN-FAKE-0000")
        assert result["status"] == "error"
        assert result["code"] == "TXN_NOT_FOUND"

    def test_cannot_void_refunded_transaction(self, processor, approved_txn):
        processor.refund_payment(approved_txn)
        result = processor.void_transaction(approved_txn)
        assert result["status"] == "error"
        assert result["code"] == "TXN_REFUNDED"

    def test_voided_status_persists(self, processor, approved_txn):
        processor.void_transaction(approved_txn)
        txn = processor.get_transaction(approved_txn)
        assert txn["voided"] is True


class TestChargebacks:
    def test_file_chargeback_unauthorized(self, processor, handler, approved_txn):
        result = handler.file_chargeback(approved_txn, reason="unauthorized")
        assert result["status"] == "filed"

    def test_invalid_chargeback_reason(self, processor, handler, approved_txn):
        result = handler.file_chargeback(approved_txn, reason="invalid_reason")
        assert result["status"] == "error"
        assert result["code"] == "INVALID_REASON"

    def test_duplicate_chargeback_rejected(self, processor, handler, approved_txn):
        handler.file_chargeback(approved_txn, reason="unauthorized")
        result = handler.file_chargeback(approved_txn, reason="duplicate")
        assert result["status"] == "error"
        assert result["code"] == "CHARGEBACK_EXISTS"

    def test_chargeback_nonexistent_transaction(self, processor, handler):
        result = handler.file_chargeback("TXN-FAKE-111", reason="unauthorized")
        assert result["status"] == "error"
        assert result["code"] == "TXN_NOT_FOUND"

    def test_resolve_chargeback_won(self, processor, handler, approved_txn):
        handler.file_chargeback(approved_txn, reason="unauthorized")
        result = handler.resolve_chargeback(approved_txn, outcome="won")
        assert result["outcome"] == "won"

    def test_resolve_chargeback_lost(self, processor, handler, approved_txn):
        handler.file_chargeback(approved_txn, reason="product_not_received")
        result = handler.resolve_chargeback(approved_txn, outcome="lost")
        assert result["outcome"] == "lost"

    def test_invalid_resolution_outcome(self, processor, handler, approved_txn):
        handler.file_chargeback(approved_txn, reason="unauthorized")
        result = handler.resolve_chargeback(approved_txn, outcome="maybe")
        assert result["status"] == "error"
        assert result["code"] == "INVALID_OUTCOME"

    def test_resolve_nonexistent_chargeback(self, processor, handler, approved_txn):
        result = handler.resolve_chargeback(approved_txn, outcome="won")
        assert result["status"] == "error"
        assert result["code"] == "NO_CHARGEBACK"

    def test_chargeback_amount_matches_transaction(self, processor, handler, approved_txn):
        result = handler.file_chargeback(approved_txn, reason="duplicate")
        assert result["chargeback"]["amount"] == 75.00

    def test_all_valid_reasons_accepted(self, processor, handler):
        reasons = ["unauthorized", "duplicate", "product_not_received",
                   "credit_not_processed", "general"]
        for i, reason in enumerate(reasons):
            txn = processor.process_payment(
                10.00 * (i+1), "visa", "4111111111111111", f"M-{i}"
            )
            result = handler.file_chargeback(txn["transaction_id"], reason=reason)
            assert result["status"] == "filed"


class TestTransactionRetrieval:
    def test_get_existing_transaction(self, processor, approved_txn):
        txn = processor.get_transaction(approved_txn)
        assert txn["status"] == "approved"
        assert txn["amount"] == 75.00
        assert txn["card_last4"] == "1111"

    def test_get_nonexistent_transaction(self, processor):
        result = processor.get_transaction("TXN-DOES-NOT-EXIST")
        assert result["status"] == "error"
        assert result["code"] == "TXN_NOT_FOUND"

    def test_card_last4_stored_correctly(self, processor):
        result = processor.process_payment(
            50.00, "visa", "4111111111119876", "M-001"
        )
        txn = processor.get_transaction(result["transaction_id"])
        assert txn["card_last4"] == "9876"
