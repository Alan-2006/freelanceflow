from typing import Any, Dict

from .base import PaymentGateway


class MockPaymentGateway(PaymentGateway):

    def create_order(self, amount: float, currency: str, receipt: str, notes: Dict[str, Any] = None) -> Dict[str, Any]:
        return {
            'order_id': f"order_mock_{receipt}",
            'amount': amount,
            'currency': currency,
            'key_id': 'rzp_test_mock_key',
        }

    def verify_payment_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        # Mock signature check succeeds if signature is 'valid_mock_signature' or starts with 'mock_sig'
        return signature.startswith('mock_sig') or signature == 'valid_mock_signature'
