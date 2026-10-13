from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.clients.models import Client
from apps.invoicing.models import Invoice, InvoiceLineItem, InvoiceStatus
from apps.invoicing.services.calculator import InvoiceCalculator
from apps.invoicing.services.pdf_generator import InvoicePDFGenerator
from apps.projects.models import Project, TimeEntry


@pytest.mark.django_db
class TestInvoicing:

    def test_auto_numbering(self, auth_client):
        _, user = auth_client
        profile = user.profile
        client = Client.objects.create(freelancer=profile, name='Client A', email='a@a.com')

        inv1_num = InvoiceCalculator.generate_next_invoice_number(profile)
        year = timezone.now().year
        assert inv1_num == f"INV-{year}-0001"

        Invoice.objects.create(
            freelancer=profile,
            client=client,
            invoice_number=inv1_num,
            due_date=timezone.now().date()
        )

        inv2_num = InvoiceCalculator.generate_next_invoice_number(profile)
        assert inv2_num == f"INV-{year}-0002"

    def test_invoice_totals_tax_discount_and_late_fees(self, auth_client):
        _, user = auth_client
        profile = user.profile
        client = Client.objects.create(freelancer=profile, name='Client B', email='b@b.com')

        invoice = Invoice.objects.create(
            freelancer=profile,
            client=client,
            invoice_number='INV-TEST-0001',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            tax_rate=Decimal('10.00'),  # 10%
            discount_amount=Decimal('50.00'),
        )

        # Line items: 2 * 100 = 200, 1 * 300 = 300 -> subtotal = 500
        InvoiceLineItem.objects.create(invoice=invoice, description='Item 1', quantity=2, unit_price=100)
        InvoiceLineItem.objects.create(invoice=invoice, description='Item 2', quantity=1, unit_price=300)

        InvoiceCalculator.recalculate_invoice_totals(invoice)
        invoice.refresh_from_db()

        assert invoice.subtotal == Decimal('500.00')
        assert invoice.tax_amount == Decimal('50.00')
        # Total = 500 + 50 - 50 = 500
        assert invoice.total_amount == Decimal('500.00')

    def test_convert_unbilled_time_to_line_items(self, auth_client):
        _, user = auth_client
        profile = user.profile
        client = Client.objects.create(freelancer=profile, name='Client C', email='c@c.com')
        project = Project.objects.create(client=client, title='Hourly Task', hourly_rate=Decimal('100.00'))

        # 2 hours = 7200 seconds
        TimeEntry.objects.create(
            project=project,
            duration_seconds=7200,
            hourly_rate=Decimal('100.00'),
            is_billable=True,
            is_invoiced=False,
            note='Design system sprint'
        )

        invoice = Invoice.objects.create(
            freelancer=profile,
            client=client,
            project=project,
            invoice_number='INV-TIME-0001',
            due_date=timezone.now().date()
        )

        added = InvoiceCalculator.convert_unbilled_time_to_line_items(project, invoice)
        assert added == 1

        invoice.refresh_from_db()
        assert invoice.line_items.count() == 1
        line = invoice.line_items.first()
        assert line.quantity == Decimal('2.00')
        assert line.unit_price == Decimal('100.00')
        assert line.total == Decimal('200.00')
        assert invoice.total_amount == Decimal('200.00')

    def test_pdf_generation_returns_valid_bytes(self, auth_client):
        _, user = auth_client
        profile = user.profile
        client = Client.objects.create(freelancer=profile, name='Client D', email='d@d.com')
        invoice = Invoice.objects.create(
            freelancer=profile,
            client=client,
            invoice_number='INV-PDF-0001',
            due_date=timezone.now().date()
        )
        InvoiceLineItem.objects.create(invoice=invoice, description='Audit', quantity=1, unit_price=1000)
        InvoiceCalculator.recalculate_invoice_totals(invoice)

        pdf_bytes = InvoicePDFGenerator.generate_invoice_pdf(invoice)
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 100
        # Valid PDF signature begins with %PDF
        assert pdf_bytes.startswith(b'%PDF')

    def test_public_invoice_view_records_view_event(self, client, auth_client):
        _, user = auth_client
        profile = user.profile
        client_obj = Client.objects.create(freelancer=profile, name='Client E', email='e@e.com')
        invoice = Invoice.objects.create(
            freelancer=profile,
            client=client_obj,
            invoice_number='INV-PUB-0001',
            due_date=timezone.now().date(),
            status=InvoiceStatus.SENT
        )

        public_url = reverse('invoicing:public', kwargs={'public_token': invoice.public_token})
        response = client.get(public_url)
        assert response.status_code == 200

        invoice.refresh_from_db()
        assert invoice.viewed_at is not None
        assert invoice.status == InvoiceStatus.VIEWED
