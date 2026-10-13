from datetime import timedelta

from django.db import models
from django.utils import timezone

from apps.authentication.models import FreelancerProfile
from core.models import TimeStampedModel
from core.utils import generate_random_token


class ReminderChannel(models.TextChoices):
    EMAIL = 'EMAIL', 'Email'
    WHATSAPP = 'WHATSAPP', 'WhatsApp'
    TELEGRAM = 'TELEGRAM', 'Telegram'
    IN_APP = 'IN_APP', 'Portal In-App'

class Client(TimeStampedModel):
    freelancer = models.ForeignKey(
        FreelancerProfile,
        on_delete=models.CASCADE,
        related_name='clients'
    )
    name = models.CharField(max_length=150, help_text='Primary contact name')
    company = models.CharField(max_length=200, blank=True, default='', help_text='Company or Agency name')
    email = models.EmailField(help_text='Billing & communication email')
    phone = models.CharField(max_length=50, blank=True, default='')
    address = models.TextField(blank=True, default='')
    currency = models.CharField(max_length=10, default='USD')
    timezone = models.CharField(max_length=50, default='UTC')
    preferred_channel = models.CharField(
        max_length=20,
        choices=ReminderChannel.choices,
        default=ReminderChannel.EMAIL
    )
    notes = models.TextField(blank=True, default='', help_text='Private freelancer notes')
    tags = models.CharField(max_length=255, blank=True, default='', help_text='Comma-separated tags (e.g. VIP, Retainer)')

    # Secure tokenized access for Client Portal
    portal_token = models.CharField(max_length=64, unique=True, blank=True, null=True, db_index=True)
    portal_token_expires_at = models.DateTimeField(blank=True, null=True)

    # Reliability score (0-100), calculated from on-time payment ratio
    reliability_score = models.IntegerField(default=100)
    reminders_paused = models.BooleanField(default=False)

    class Meta:
        ordering = ['company', 'name']
        indexes = [
            models.Index(fields=['freelancer', 'email']),
            models.Index(fields=['portal_token']),
        ]

    def __str__(self):
        if self.company:
            return f"{self.company} ({self.name})"
        return self.name

    @property
    def display_title(self):
        return self.company or self.name

    @property
    def tag_list(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    @property
    def reliability_badge(self):
        score = self.reliability_score
        if score >= 90:
            return {'label': 'Gold', 'color': 'emerald', 'desc': 'Prompt payer (90-100%)'}
        elif score >= 75:
            return {'label': 'Silver', 'color': 'indigo', 'desc': 'Reliable (75-89%)'}
        elif score >= 50:
            return {'label': 'Bronze', 'color': 'amber', 'desc': 'Occasional delay (50-74%)'}
        return {'label': 'At-Risk', 'color': 'rose', 'desc': 'Frequent late payments (<50%)'}

    def get_or_create_portal_token(self, days_valid: int = 30) -> str:
        """Return valid portal token or generate a fresh one."""
        now = timezone.now()
        if not self.portal_token or not self.portal_token_expires_at or self.portal_token_expires_at < now:
            self.portal_token = generate_random_token(48)
            self.portal_token_expires_at = now + timedelta(days=days_valid)
            self.save(update_fields=['portal_token', 'portal_token_expires_at'])
        return self.portal_token
