from typing import Any, Dict

from .base import NotificationChannel


class InAppNotificationChannel(NotificationChannel):
    def send(self, recipient: str, subject: str, body: str, context: Dict[str, Any]) -> bool:
        # In-app notification creation
        return True

class WebhookBotNotificationChannel(NotificationChannel):
    def send(self, recipient: str, subject: str, body: str, context: Dict[str, Any]) -> bool:
        # Placeholder / mock for WhatsApp or Telegram webhook delivery
        return True
