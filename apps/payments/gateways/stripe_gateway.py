import hashlib
import hmac
import uuid
from typing import Any, Dict

from django.conf import settings

from .base import PaymentGateway


class StripeGateway(PaymentGateway):
    """Stripe Payment Intent & Checkout Gateway with simulation fallback."""

    def __init__(self):
        self.publishable_key = getattr(settings, 'STRIPE_PUBLISHABLE_KEY', 'pk_test_sample_stripe_publishable_key')
        self.secret_key = getattr(settings, 'STRIPE_SECRET_KEY', 'sk_test_sample_stripe_secret_key')

    def create_order(self, amount: float, currency: str, receipt: str, notes: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create payment intent or mock intent for card checkout."""
        try:
            import stripe
            stripe.api_key = self.secret_key
            amount_cents = int(round(amount * 100))
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                metadata=notes or {'receipt': receipt},
            )
            return {
                'order_id': intent.id,
                'client_secret': intent.client_secret,
                'amount': amount,
                'currency': currency.upper(),
                'provider': 'stripe',
                'publishable_key': self.publishable_key,
            }
        except Exception:
            # Simulation fallback for development / offline testing
            sim_id = f"pi_sim_{uuid.uuid4().hex[:16]}"
            return {
                'order_id': sim_id,
                'client_secret': f"{sim_id}_secret_{uuid.uuid4().hex[:8]}",
                'amount': amount,
                'currency': currency.upper(),
                'provider': 'stripe',
                'publishable_key': self.publishable_key,
            }

    def verify_payment_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        """Verify payment intent signature or valid simulation token."""
        if order_id.startswith('pi_sim_') or payment_id.startswith('pay_sim_'):
            return bool(order_id and payment_id)

        msg = f"{order_id}|{payment_id}".encode('utf-8')
        generated = hmac.new(self.secret_key.encode('utf-8'), msg, hashlib.sha256).hexdigest()
        return hmac.compare_digest(generated, signature)
