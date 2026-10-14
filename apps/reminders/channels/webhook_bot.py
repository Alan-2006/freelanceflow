import logging
from typing import Any, Dict
from django.conf import settings

from .base import NotificationChannel

logger = logging.getLogger(__name__)


class InAppNotificationChannel(NotificationChannel):
    def send(self, recipient: str, subject: str, body: str, context: Dict[str, Any]) -> bool:
        """Create an in-app notification in the database for the user."""
        try:
            from apps.authentication.models import Notification, NotificationType, User
            user = context.get('user')
            if not user and recipient:
                user = User.objects.filter(email__iexact=recipient).first()
            if not user and 'freelancer' in context:
                user = context['freelancer'].user

            if user:
                Notification.objects.create(
                    user=user,
                    title=subject,
                    message=body,
                    url=context.get('url', ''),
                    notification_type=NotificationType.INVOICE
                )
                return True
            return True
        except Exception as e:
            logger.error("InAppNotificationChannel error: %s", e)
            return False


class WebhookBotNotificationChannel(NotificationChannel):
    def send(self, recipient: str, subject: str, body: str, context: Dict[str, Any]) -> bool:
        """Dispatch notification to WhatsApp, Telegram, or custom webhook bridge."""
        import requests
        webhook_url = context.get('webhook_url') or getattr(settings, 'REMINDER_WEBHOOK_URL', '')
        if webhook_url:
            try:
                payload = {
                    'recipient': recipient,
                    'subject': subject,
                    'message': body,
                    'channel': context.get('channel', 'WEBHOOK'),
                    'site_url': context.get('site_url', ''),
                }
                resp = requests.post(webhook_url, json=payload, timeout=5)
                return resp.status_code in [200, 201, 202, 204]
            except Exception as e:
                logger.error("WebhookBot delivery error: %s", e)
                return False
        # If no external webhook URL configured, gracefully succeed
        return True
