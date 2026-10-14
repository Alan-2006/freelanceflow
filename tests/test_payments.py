from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.clients.models import Client
from apps.invoicing.models import Invoice, InvoiceLineItem, InvoiceStatus
from apps.invoicing.services.calculator import InvoiceCalculator
from apps.payments.gateways.mock_gateway import MockPaymentGateway
from apps.payments.models import Payment, PaymentMethod
from apps.payments.services import PaymentService
from apps.projects.models import Milestone, MilestoneStatus, Project


@pytest.mark.django_db
class TestPayments:

    def test_payment_settles_invoice_and_milestone(self, auth_client):
        _, user = auth_client
        profile = user.profile

        client = Client.objects.create(freelancer=profile, name='Bruce Banner', email='hulk@avengers.com')
        project = Project.objects.create(client=client, title='Gamma Lab', budget=5000.00)
        milestone = Milestone.objects.create(
            project=project,
            title='Gamma Shield',
            amount=Decimal('2500.00'),
            due_date=timezone.now().date(),
            status=MilestoneStatus.APPROVED
        )

        invoice = Invoice.objects.create(
            freelancer=profile,
            client=client,
            project=project,
            invoice_number='INV-GAMMA-0001',
            due_date=timezone.now().date(),
            status=InvoiceStatus.SENT
        )
        InvoiceLineItem.objects.create(
            invoice=invoice,
            description='Milestone Gamma Shield',
            quantity=1,
            unit_price=2500,
            milestone=milestone
        )
        InvoiceCalculator.recalculate_invoice_totals(invoice)

        # Partial payment test
        PaymentService.record_payment(
            invoice=invoice,
            amount=Decimal('1000.00'),
            method=PaymentMethod.MANUAL_BANK,
            notes='Advance wire transfer'
        )

        invoice.refresh_from_db()
        assert invoice.amount_paid == Decimal('1000.00')
        assert invoice.balance_due == Decimal('1500.00')
        assert invoice.status == InvoiceStatus.PARTIALLY_PAID
        milestone.refresh_from_db()
        assert milestone.status == MilestoneStatus.APPROVED  # Not fully paid yet

        # Full settlement test
        PaymentService.record_payment(
            invoice=invoice,
            amount=Decimal('1500.00'),
            method=PaymentMethod.MANUAL_UPI,
            notes='Final balance settlement'
        )

        invoice.refresh_from_db()
        assert invoice.amount_paid == Decimal('2500.00')
        assert invoice.balance_due == Decimal('0.00')
        assert invoice.status == InvoiceStatus.PAID

        # Milestone should automatically be marked PAID!
        milestone.refresh_from_db()
        assert milestone.status == MilestoneStatus.PAID

    def test_payment_idempotency_prevents_duplicate_credits(self, auth_client):
        _, user = auth_client
        profile = user.profile
        client = Client.objects.create(freelancer=profile, name='Tony Stark', email='tony@stark.com')
        invoice = Invoice.objects.create(
            freelancer=profile,
            client=client,
            invoice_number='INV-STARK-0001',
            due_date=timezone.now().date(),
            total_amount=Decimal('1000.00'),
            amount_paid=Decimal('0.00'),
            status=InvoiceStatus.SENT
        )

        # First call with gateway payment id
        p1 = PaymentService.record_payment(
            invoice=invoice,
            amount=Decimal('1000.00'),
            method=PaymentMethod.RAZORPAY,
            gateway_payment_id='pay_rzp_unique_12345'
        )
        invoice.refresh_from_db()
        assert invoice.amount_paid == Decimal('1000.00')

        # Duplicate webhook or re-submission with same payment id
        p2 = PaymentService.record_payment(
            invoice=invoice,
            amount=Decimal('1000.00'),
            method=PaymentMethod.RAZORPAY,
            gateway_payment_id='pay_rzp_unique_12345'
        )
        invoice.refresh_from_db()
        # Must still be 1000.00, not 2000.00
        assert invoice.amount_paid == Decimal('1000.00')
        assert p1.id == p2.id

    def test_gateway_interface_and_signature(self):
        mock_gw = MockPaymentGateway()
        order = mock_gw.create_order(500.0, 'USD', 'INV-101')
        assert order['order_id'] == 'order_mock_INV-101'
        assert mock_gw.verify_payment_signature('order_1', 'pay_1', 'mock_sig_123') is True
        assert mock_gw.verify_payment_signature('order_1', 'pay_1', 'invalid_sig') is False

    def test_stripe_webhook_view(self, client, auth_client):
        import json
        _, user = auth_client
        profile = user.profile
        client_obj = Client.objects.create(freelancer=profile, name='Bruce Wayne', email='bruce@wayne.com')
        invoice = Invoice.objects.create(
            freelancer=profile,
            client=client_obj,
            invoice_number='INV-STRIPE-001',
            due_date=timezone.now().date(),
            total_amount=Decimal('450.00'),
            amount_paid=Decimal('0.00'),
            status=InvoiceStatus.SENT
        )

        payload = {
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': 'pi_test_stripe_123456',
                    'amount': 45000,
                    'currency': 'usd',
                    'metadata': {
                        'invoice_id': str(invoice.id)
                    }
                }
            }
        }

        url = reverse('payments:stripe_webhook')
        response = client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        assert response.status_code == 200
        invoice.refresh_from_db()
        assert invoice.amount_paid == Decimal('450.00')
        assert invoice.status == InvoiceStatus.PAID
        payment = Payment.objects.filter(gateway_payment_id='pi_test_stripe_123456').first()
        assert payment is not None
        assert payment.method == PaymentMethod.STRIPE

    def test_credit_note_creation_and_refund(self, auth_client):
        from apps.payments.models import CreditNote, PaymentStatus
        client_browser, user = auth_client
        profile = user.profile
        client_obj = Client.objects.create(freelancer=profile, name='Refund Client', email='refund@client.com')
        invoice = Invoice.objects.create(
            freelancer=profile,
            client=client_obj,
            invoice_number='INV-REFUND-001',
            due_date=timezone.now().date(),
            total_amount=Decimal('1000.00'),
            amount_paid=Decimal('1000.00'),
            status=InvoiceStatus.PAID
        )

        create_url = reverse('payments:credit_note_create')
        response = client_browser.post(create_url, {
            'invoice': str(invoice.id),
            'amount': '300.00',
            'reason': 'Partial project cancellation and scope adjustment.',
            'issued_date': str(timezone.now().date()),
        })
        assert response.status_code == 302
        invoice.refresh_from_db()
        assert invoice.amount_paid == Decimal('700.00')
        assert invoice.status == InvoiceStatus.PARTIALLY_PAID

        cn = CreditNote.objects.filter(invoice=invoice).first()
        assert cn is not None
        assert cn.amount == Decimal('300.00')
        assert 'CN-' in cn.credit_note_number

        refund_payment = Payment.objects.filter(invoice=invoice, status=PaymentStatus.REFUNDED).first()
        assert refund_payment is not None
        assert refund_payment.amount == Decimal('300.00')


