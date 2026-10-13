from abc import ABC, abstractmethod
from typing import Any, Dict


class NotificationChannel(ABC):
    """Abstract interface for dispatching payment reminders across different mediums."""

    @abstractmethod
    def send(self, recipient: str, subject: str, body: str, context: Dict[str, Any]) -> bool:
        """Dispatch notification to recipient and return True if successful."""
        pass
