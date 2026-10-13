from django.db import models
from django.utils import timezone

from apps.authentication.models import FreelancerProfile
from apps.invoicing.models import Invoice
from core.models import TimeStampedModel
from core.utils import generate_random_token


class ReminderTone(models.TextChoices):
    FRIENDLY = 'FRIENDLY', 'Friendly (Pre-due reminder)'
    POLITE_NUDGE = 'POLITE_NUDGE', 'Polite Nudge (Due date)'
    FIRM = 'FIRM', 'Firm (Overdue 3-7 days)'
    FINAL_NOTICE = 'FINAL_NOTICE', 'Final Notice (Overdue 14+ days)'

class ReminderChannelChoice(models.TextChoices):
    EMAIL = 'EMAIL', 'Email'
    IN_APP = 'IN_APP', 'Portal In-App'
    WHATSAPP = 'WHATSAPP', 'WhatsApp'
    TELEGRAM = 'TELEGRAM', 'Telegram'


class ReminderRule(TimeStampedModel):
    freelancer = models.ForeignKey(
        FreelancerProfile,
        on_delete=models.CASCADE,
        related_name='reminder_rules'
    )
    name = models.CharField(max_length=150)
    trigger_offset_days = models.IntegerField(
        help_text='Negative for days before due date (e.g. -3), 0 on due date, positive for overdue (e.g. +7)'
    )
    tone = models.CharField(
        max_length=30,
        choices=ReminderTone.choices,
        default=ReminderTone.FRIENDLY
    )
    channel = models.CharField(
        max_length=20,
        choices=ReminderChannelChoice.choices,
        default=ReminderChannelChoice.EMAIL
    )
    subject_template = models.CharField(max_length=255)
    body_template = models.TextField(
        help_text='Variables: {{client_name}}, {{invoice_number}}, {{amount}}, {{due_date}}, {{pay_link}}, {{freelancer_name}}'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['trigger_offset_days']

    def __str__(self):
        offset = f"+{self.trigger_offset_days}" if self.trigger_offset_days > 0 else str(self.trigger_offset_days)
        return f"{self.name} ({offset}d, {self.get_tone_display()})"


class ReminderLog(TimeStampedModel):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='reminder_logs'
    )
    rule = models.ForeignKey(
        ReminderRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs'
    )
    scheduled_date = models.DateField(default=timezone.now)
    channel = models.CharField(max_length=20, default='EMAIL')
    tone = models.CharField(max_length=30, default='FRIENDLY')
    recipient = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    message_body = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)

    tracking_token = models.CharField(max_length=64, unique=True, db_index=True, blank=True)
    opened = models.BooleanField(default=False)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked = models.BooleanField(default=False)
    clicked_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['invoice', 'scheduled_date']),
            models.Index(fields=['tracking_token']),
        ]

    def __str__(self):
        return f"Reminder for {self.invoice.invoice_number} to {self.recipient} ({self.sent_at.strftime('%Y-%m-%d %H:%M')})"

    def save(self, *args, **kwargs):
        if not self.tracking_token:
            self.tracking_token = generate_random_token(40)
        super().save(*args, **kwargs)

    def record_open(self):
        if not self.opened:
            self.opened = True
            self.opened_at = timezone.now()
            self.save(update_fields=['opened', 'opened_at'])

    def record_click(self):
        if not self.clicked:
            self.clicked = True
            self.clicked_at = timezone.now()
            self.save(update_fields=['clicked', 'clicked_at'])
