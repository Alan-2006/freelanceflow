from abc import ABC, abstractmethod
from typing import Any, Dict


class PaymentGateway(ABC):
    """Abstract interface isolating payment processing providers."""

    @abstractmethod
    def create_order(self, amount: float, currency: str, receipt: str, notes: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create an order with the payment provider."""
        pass

    @abstractmethod
    def verify_payment_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        """Verify cryptographic signature from provider webhook or checkout return."""
        pass
