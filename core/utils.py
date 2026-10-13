import secrets
import string

from django.utils import timezone


def generate_random_token(length: int = 32) -> str:
    """Generate a cryptographically secure URL-safe token."""
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

def format_currency(amount, currency_symbol: str = "$") -> str:
    """Helper to format currency strings with commas."""
    if amount is None:
        amount = 0
    return f"{currency_symbol}{amount:,.2f}"

def get_current_utc():
    return timezone.now()
