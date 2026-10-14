import zoneinfo
from typing import Any, Dict

from django.utils import timezone

from apps.invoicing.models import Invoice, InvoiceStatus

from .channels.email import EmailNotificationChannel
from .channels.webhook_bot import InAppNotificationChannel, WebhookBotNotificationChannel
from .defaults import DEFAULT_RULES
from .models import ReminderChannelChoice, ReminderLog, ReminderRule


class PaymentReminderEngine:

    @staticmethod
    def ensure_default_rules_exist(freelancer_profile):
        """Seed default escalating reminder rules for freelancer if none exist."""
        if not freelancer_profile.reminder_rules.exists():
            for r_data in DEFAULT_RULES:
                ReminderRule.objects.create(
                    freelancer=freelancer_profile,
                    **r_data
                )

    @staticmethod
    def is_in_quiet_hours(client_timezone_str: str) -> bool:
        """Check if current time in client's timezone is outside 09:00 - 19:00."""
        try:
            tz = zoneinfo.ZoneInfo(client_timezone_str)
            client_now = timezone.now().astimezone(tz)
            hour = client_now.hour
            # Quiet hours: before 9 AM or after 7 PM (19:00)
            return hour < 9 or hour >= 19
        except Exception:
            # If invalid timezone, default to UTC
            now_utc = timezone.now()
            return now_utc.hour < 9 or now_utc.hour >= 19

    @staticmethod
    def interpolate_template(template_str: str, context: Dict[str, str]) -> str:
        res = template_str
        for k, v in context.items():
            res = res.replace(f"{{{{{k}}}}}", str(v))
        return res

    @classmethod
    def evaluate_invoices(
        cls,
        dry_run: bool = False,
        site_url: str = 'http://127.0.0.1:8000',
        ignore_quiet_hours: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluate all unpaid invoices across all active freelancers,
        verifying idempotency, quiet hours, and pause toggles.
        """
        today = timezone.now().date()
        unpaid_invoices = Invoice.objects.filter(
            status__in=[
                InvoiceStatus.SENT,
                InvoiceStatus.VIEWED,
                InvoiceStatus.PARTIALLY_PAID,
                InvoiceStatus.OVERDUE
            ]
        ).select_related('freelancer', 'client')

        stats = {
            'evaluated': 0,
            'dispatched': 0,
            'skipped_paused': 0,
            'skipped_quiet_hours': 0,
            'skipped_idempotent': 0,
            'details': []
        }

        email_channel = EmailNotificationChannel()

        for invoice in unpaid_invoices:
            stats['evaluated'] += 1

            # 1. Check if reminders are paused
            if invoice.reminders_paused or invoice.client.reminders_paused:
                stats['skipped_paused'] += 1
                continue

            # 2. Check if invoice is already settled
            if invoice.balance_due <= 0 or invoice.status == InvoiceStatus.PAID:
                continue

            # 3. Check quiet hours (unless running dry-run or testing)
            if not dry_run and not ignore_quiet_hours and cls.is_in_quiet_hours(invoice.client.timezone):
                stats['skipped_quiet_hours'] += 1
                continue

            # 4. Calculate day offset
            offset = (today - invoice.due_date).days

            # Ensure default rules exist for this freelancer
            cls.ensure_default_rules_exist(invoice.freelancer)

            # Find matching active rule
            rule = invoice.freelancer.reminder_rules.filter(
                trigger_offset_days=offset,
                is_active=True
            ).first()

            if not rule:
                continue

            # 5. Idempotency check: has reminder already been dispatched today for this rule and invoice?
            already_sent = ReminderLog.objects.filter(
                invoice=invoice,
                rule=rule,
                scheduled_date=today
            ).exists()

            if already_sent:
                stats['skipped_idempotent'] += 1
                continue

            # 6. Build Context & Interpolate variables
            context = {
                'client_name': invoice.client.name,
                'client_company': invoice.client.display_title,
                'invoice_number': invoice.invoice_number,
                'amount': f"{invoice.balance_due:,.2f}",
                'due_date': invoice.due_date.strftime("%B %d, %Y"),
                'freelancer_name': invoice.freelancer.display_name,
                'pay_link': f"{site_url}/invoicing/public/{invoice.public_token}/",
            }

            subject = cls.interpolate_template(rule.subject_template, context)
            body = cls.interpolate_template(rule.body_template, context)

            if dry_run:
                stats['dispatched'] += 1
                stats['details'].append({
                    'invoice': invoice.invoice_number,
                    'client': invoice.client.email,
                    'rule': rule.name,
                    'tone': rule.tone,
                    'subject': subject,
                    'dry_run': True
                })
            else:
                # Create log entry
                log_entry = ReminderLog(
                    invoice=invoice,
                    rule=rule,
                    scheduled_date=today,
                    channel=rule.channel,
                    tone=rule.tone,
                    recipient=invoice.client.email,
                    subject=subject,
                    message_body=body,
                )
                log_entry.save()

                # Dispatch notification via configured channel
                channel_handler = email_channel
                if rule.channel == ReminderChannelChoice.IN_APP:
                    channel_handler = InAppNotificationChannel()
                elif rule.channel in [ReminderChannelChoice.WHATSAPP, ReminderChannelChoice.TELEGRAM]:
                    channel_handler = WebhookBotNotificationChannel()

                sent = channel_handler.send(
                    recipient=invoice.client.email,
                    subject=subject,
                    body=body,
                    context={
                        'site_url': site_url,
                        'tracking_token': log_entry.tracking_token,
                        'invoice': invoice,
                        'freelancer': invoice.freelancer,
                        'channel': rule.channel,
                        'url': f"{site_url}/invoicing/public/{invoice.public_token}/",
                    }
                )

                if sent:
                    stats['dispatched'] += 1
                    stats['details'].append({
                        'invoice': invoice.invoice_number,
                        'recipient': invoice.client.email,
                        'tone': rule.tone,
                        'channel': rule.channel,
                        'log_id': str(log_entry.id)
                    })
                else:
                    log_entry.error_message = f'Failed to deliver notification via {rule.channel}.'
                    log_entry.save(update_fields=['error_message'])

        return stats
