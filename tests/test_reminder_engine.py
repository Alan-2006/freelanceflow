from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.clients.models import Client
from apps.invoicing.models import Invoice, InvoiceStatus
from apps.reminders.engine import PaymentReminderEngine
from apps.reminders.models import ReminderLog, ReminderRule, ReminderTone


@pytest.mark.django_db
class TestReminderEngine:

    def test_rule_matching_and_variable_interpolation(self, auth_client):
        _, user = auth_client
        profile = user.profile
        client = Client.objects.create(
            freelancer=profile,
            name='Peter Parker',
            company='Daily Bugle',
            email='peter@bugle.com',
            timezone='UTC'
        )

        today = timezone.now().date()
        # Invoice due in 3 days -> offset = -3
        due_date = today + timedelta(days=3)

        invoice = Invoice.objects.create(
            freelancer=profile,
            client=client,
            invoice_number='INV-REM-0001',
            issue_date=today,
            due_date=due_date,
            total_amount=Decimal('1500.00'),
            amount_paid=Decimal('0.00'),
            status=InvoiceStatus.SENT
        )

        # Seed default rules
        PaymentReminderEngine.ensure_default_rules_exist(profile)
        rule_minus3 = profile.reminder_rules.get(trigger_offset_days=-3)
        assert rule_minus3.tone == ReminderTone.FRIENDLY

        # Dry run evaluation
        stats = PaymentReminderEngine.evaluate_invoices(dry_run=True)
        assert stats['evaluated'] >= 1
        assert stats['dispatched'] == 1
        detail = stats['details'][0]
        assert detail['invoice'] == 'INV-REM-0001'
        assert detail['tone'] == ReminderTone.FRIENDLY

        # Test quiet hours detection
        assert PaymentReminderEngine.is_in_quiet_hours('UTC') == (timezone.now().hour < 9 or timezone.now().hour >= 19)

        # Live run evaluation with ignore_quiet_hours=True
        stats_live = PaymentReminderEngine.evaluate_invoices(dry_run=False, ignore_quiet_hours=True)
        assert stats_live['dispatched'] == 1
        assert ReminderLog.objects.filter(invoice=invoice).count() == 1

        log = ReminderLog.objects.get(invoice=invoice)
        assert 'Peter Parker' in log.message_body
        assert 'INV-REM-0001' in log.message_body
        assert '1,500.00' in log.message_body
        assert log.opened is False

    def test_reminder_idempotency(self, auth_client):
        _, user = auth_client
        profile = user.profile
        client = Client.objects.create(freelancer=profile, name='Miles Morales', email='miles@spider.com', timezone='UTC')
        today = timezone.now().date()

        invoice = Invoice.objects.create(
            freelancer=profile,
            client=client,
            invoice_number='INV-IDEM-0001',
            due_date=today + timedelta(days=3),
            total_amount=Decimal('500.00'),
            status=InvoiceStatus.SENT
        )

        PaymentReminderEngine.ensure_default_rules_exist(profile)

        # First dispatch
        stats1 = PaymentReminderEngine.evaluate_invoices(dry_run=False, ignore_quiet_hours=True)
        assert stats1['dispatched'] == 1

        # Second dispatch on the same day -> must skip as idempotent!
        stats2 = PaymentReminderEngine.evaluate_invoices(dry_run=False, ignore_quiet_hours=True)
        assert stats2['dispatched'] == 0
        assert stats2['skipped_idempotent'] == 1
        assert ReminderLog.objects.filter(invoice=invoice).count() == 1

    def test_pause_and_paid_stops_reminders(self, auth_client):
        _, user = auth_client
        profile = user.profile
        client = Client.objects.create(freelancer=profile, name='Gwen Stacy', email='gwen@spider.com', timezone='UTC')
        today = timezone.now().date()

        invoice = Invoice.objects.create(
            freelancer=profile,
            client=client,
            invoice_number='INV-PAUSE-0001',
            due_date=today + timedelta(days=3),
            total_amount=Decimal('800.00'),
            status=InvoiceStatus.SENT,
            reminders_paused=True  # Paused!
        )

        PaymentReminderEngine.ensure_default_rules_exist(profile)
        stats = PaymentReminderEngine.evaluate_invoices(dry_run=False)
        assert stats['dispatched'] == 0
        assert stats['skipped_paused'] == 1

        # Unpause, but mark as Paid
        invoice.reminders_paused = False
        invoice.status = InvoiceStatus.PAID
        invoice.amount_paid = Decimal('800.00')
        invoice.save()

        stats_paid = PaymentReminderEngine.evaluate_invoices(dry_run=False)
        assert stats_paid['dispatched'] == 0

    def test_open_and_click_tracking_endpoints(self, client, auth_client):
        _, user = auth_client
        profile = user.profile
        client_obj = Client.objects.create(freelancer=profile, name='Eddie Brock', email='eddie@venom.com')
        invoice = Invoice.objects.create(
            freelancer=profile,
            client=client_obj,
            invoice_number='INV-TRACK-0001',
            due_date=timezone.now().date(),
            total_amount=Decimal('600.00')
        )
        log = ReminderLog.objects.create(
            invoice=invoice,
            recipient=client_obj.email,
            subject='Reminder',
            message_body='Please pay'
        )

        # Test open tracking pixel
        open_url = reverse('reminders:track_open', kwargs={'token': log.tracking_token})
        resp = client.get(open_url)
        assert resp.status_code == 200
        assert resp['Content-Type'] == 'image/gif'

        log.refresh_from_db()
        assert log.opened is True
        assert log.opened_at is not None

        # Test click tracking redirect
        click_url = reverse('reminders:track_click', kwargs={'token': log.tracking_token})
        resp_click = client.get(click_url)
        assert resp_click.status_code == 302
        assert invoice.public_token in resp_click.url

        log.refresh_from_db()
        assert log.clicked is True
        assert log.clicked_at is not None

    def test_in_app_reminder_channel_creates_notification(self, auth_client):
        from apps.authentication.models import Notification
        from apps.reminders.models import ReminderChannelChoice
        _, user = auth_client
        profile = user.profile
        client_obj = Client.objects.create(freelancer=profile, name='InApp Client', email='inapp@client.com')
        invoice = Invoice.objects.create(
            freelancer=profile,
            client=client_obj,
            invoice_number='INV-INAPP-001',
            due_date=timezone.now().date(),
            total_amount=Decimal('350.00'),
            amount_paid=Decimal('0.00'),
            status=InvoiceStatus.SENT
        )

        rule = ReminderRule.objects.create(
            freelancer=profile,
            name='In-App Due Notice',
            trigger_offset_days=0,
            channel=ReminderChannelChoice.IN_APP,
            subject_template='In-App Due: {{invoice_number}}',
            body_template='Please settle {{amount}}',
            is_active=True
        )

        stats = PaymentReminderEngine.evaluate_invoices(dry_run=False, ignore_quiet_hours=True)
        assert stats['dispatched'] >= 1
        notif = Notification.objects.filter(user=user, title__contains='INV-INAPP-001').first()
        assert notif is not None
        assert notif.message == 'Please settle 350.00'

