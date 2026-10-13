from datetime import timedelta

from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.utils import timezone

from apps.clients.models import Client

signer = TimestampSigner()

class PortalAuthService:
    @staticmethod
    def generate_magic_link_token(client: Client) -> str:
        """Sign a secure token containing client UUID with expiration timestamp."""
        return signer.sign(str(client.id))

    @staticmethod
    def verify_magic_link_token(token: str, max_age_days: int = 30) -> Client | None:
        """Validate token signature and expiration, returning Client or None."""
        try:
            # First attempt signature verification
            client_id = signer.unsign(token, max_age=timedelta(days=max_age_days))
            return Client.objects.filter(id=client_id).first()
        except (BadSignature, SignatureExpired):
            # Fallback to direct portal_token match
            now = timezone.now()
            return Client.objects.filter(
                portal_token=token,
                portal_token_expires_at__gte=now
            ).first()
