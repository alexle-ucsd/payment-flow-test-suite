"""
Payment Processor Module
Simulates core payment processing logic for a POS system.
Covers: card transactions, refunds, voids, chargebacks, 
and validation.
Author: Alex Le
"""


class PaymentProcessor:
    SUPPORTED_CARD_TYPES = ["visa", "mastercard", "amex", "discover"]
    MAX_TRANSACTION_AMOUNT = 50000.00
    MIN_TRANSACTION_AMOUNT = 0.01

    def __init__(self):
        self.transactions = {}
        self.transaction_counter = 1000

    def _generate_transaction_id(self):
        self.transaction_counter += 1
        return f"TXN-{self.transaction_counter}"

    def process_payment(self, amount, card_type, card_number, merchant_id):
        if not merchant_id or not merchant_id.strip():
            return {"status": "error", "code": "INVALID_MERCHANT", 
                    "message": "Merchant ID is required"}
        if card_type.lower() not in self.SUPPORTED_CARD_TYPES:
            return {"status": "error", "code": "UNSUPPORTED_CARD", 
                    "message": f"Card type '{card_type}' not supported"}
        if not self._validate_card_number(card_number):
            return {"status": "error", "code": "INVALID_CARD", 
                    "message": "Invalid card number"}
        if amount < self.MIN_TRANSACTION_AMOUNT:
            return {"status": "error", "code": "AMOUNT_TOO_LOW", 
                    "message": "Amount too low"}
        if amount > self.MAX_TRANSACTION_AMOUNT:
            return {"status": "error", "code": "AMOUNT_EXCEEDS_LIMIT", 
                    "message": "Amount exceeds limit"}

        txn_id = self._generate_transaction_id()
        transaction = {
            "transaction_id": txn_id,
            "status": "approved",
            "amount": round(amount, 2),
            "card_type": card_type.lower(),
            "card_last4": card_number.replace(" ", "").replace("-", "")[-4:],
            "merchant_id": merchant_id,
            "type": "sale",
            "refunded": False,
            "voided": False,
        }
        self.transactions[txn_id] = transaction
        return {"status": "approved", "transaction_id": txn_id, 
                "amount": round(amount, 2)}

    def refund_payment(self, transaction_id, refund_amount=None):
        if transaction_id not in self.transactions:
            return {"status": "error", "code": "TXN_NOT_FOUND", 
                    "message": "Transaction not found"}
        txn = self.transactions[transaction_id]
        if txn["voided"]:
            return {"status": "error", "code": "TXN_VOIDED", 
                    "message": "Cannot refund voided transaction"}
        if txn["refunded"]:
            return {"status": "error", "code": "ALREADY_REFUNDED", 
                    "message": "Already refunded"}
        original_amount = txn["amount"]
        refund_amount = refund_amount if refund_amount is not None else original_amount
        if refund_amount <= 0:
            return {"status": "error", "code": "INVALID_REFUND_AMOUNT", 
                    "message": "Refund amount must be greater than zero"}
        if refund_amount > original_amount:
            return {"status": "error", "code": "REFUND_EXCEEDS_ORIGINAL", 
                    "message": "Refund exceeds original amount"}
        txn["refunded"] = True
        txn["refund_amount"] = round(refund_amount, 2)
        return {"status": "refunded", "transaction_id": transaction_id, 
                "refund_amount": round(refund_amount, 2)}

    def void_transaction(self, transaction_id):
        if transaction_id not in self.transactions:
            return {"status": "error", "code": "TXN_NOT_FOUND", 
                    "message": "Transaction not found"}
        txn = self.transactions[transaction_id]
        if txn["refunded"]:
            return {"status": "error", "code": "TXN_REFUNDED", 
                    "message": "Cannot void refunded transaction"}
        if txn["voided"]:
            return {"status": "error", "code": "ALREADY_VOIDED", 
                    "message": "Already voided"}
        txn["voided"] = True
        return {"status": "voided", "transaction_id": transaction_id}

    def get_transaction(self, transaction_id):
        if transaction_id not in self.transactions:
            return {"status": "error", "code": "TXN_NOT_FOUND", 
                    "message": "Transaction not found"}
        return self.transactions[transaction_id]

    def _validate_card_number(self, card_number):
        digits = card_number.replace(" ", "").replace("-", "")
        return digits.isdigit() and 13 <= len(digits) <= 19


class ChargebackHandler:
    VALID_REASONS = ["unauthorized", "duplicate", "product_not_received", 
                     "credit_not_processed", "general"]

    def __init__(self, processor):
        self.processor = processor
        self.chargebacks = {}

    def file_chargeback(self, transaction_id, reason, description=""):
        if transaction_id not in self.processor.transactions:
            return {"status": "error", "code": "TXN_NOT_FOUND", 
                    "message": "Transaction not found"}
        if reason not in self.VALID_REASONS:
            return {"status": "error", "code": "INVALID_REASON", 
                    "message": f"Reason must be one of: {self.VALID_REASONS}"}
        if transaction_id in self.chargebacks:
            return {"status": "error", "code": "CHARGEBACK_EXISTS", 
                    "message": "Chargeback already filed"}
        chargeback = {
            "transaction_id": transaction_id,
            "reason": reason,
            "description": description,
            "status": "open",
            "amount": self.processor.transactions[transaction_id]["amount"]
        }
        self.chargebacks[transaction_id] = chargeback
        return {"status": "filed", "transaction_id": transaction_id, 
                "chargeback": chargeback}

    def resolve_chargeback(self, transaction_id, outcome):
        if transaction_id not in self.chargebacks:
            return {"status": "error", "code": "NO_CHARGEBACK", 
                    "message": "No chargeback found"}
        if outcome not in ["won", "lost"]:
            return {"status": "error", "code": "INVALID_OUTCOME", 
                    "message": "Outcome must be 'won' or 'lost'"}
        self.chargebacks[transaction_id]["status"] = outcome
        return {"status": "resolved", "transaction_id": transaction_id, 
                "outcome": outcome}
