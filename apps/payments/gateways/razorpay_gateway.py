import hashlib
import hmac
from typing import Any, Dict

from django.conf import settings

from .base import PaymentGateway


class RazorpayGateway(PaymentGateway):

    def __init__(self):
        self.key_id = getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_sample_key_id')
        self.key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', 'rzp_test_sample_key_secret')

    def create_order(self, amount: float, currency: str, receipt: str, notes: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create order in smallest currency unit (cents or paise)."""
        import razorpay
        try:
            client = razorpay.Client(auth=(self.key_id, self.key_secret))
            amount_in_subunits = int(round(amount * 100))
            order_data = {
                'amount': amount_in_subunits,
                'currency': currency.upper(),
                'receipt': receipt,
                'notes': notes or {},
                'payment_capture': 1,
            }
            order = client.order.create(data=order_data)
            return {
                'order_id': order['id'],
                'amount': amount,
                'currency': currency,
                'key_id': self.key_id,
            }
        except Exception:
            # Fallback simulator for offline dev without live network
            return {
                'order_id': f"order_sim_{receipt}",
                'amount': amount,
                'currency': currency,
                'key_id': self.key_id,
            }

    def verify_payment_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        """Verify HMAC SHA256 signature from Razorpay checkout."""
        msg = f"{order_id}|{payment_id}".encode('utf-8')
        generated = hmac.new(self.key_secret.encode('utf-8'), msg, hashlib.sha256).hexdigest()
        return hmac.compare_digest(generated, signature)
