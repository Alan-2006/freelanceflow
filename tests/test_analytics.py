from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.analytics.services import AnalyticsService
from apps.clients.models import Client
from apps.invoicing.models import Invoice, InvoiceStatus
from apps.payments.models import Payment, PaymentStatus


@pytest.mark.django_db
class TestAnalytics:

    def test_kpi_calculations_and_collection_health_meter(self, auth_client):
        _, user = auth_client
        profile = user.profile

        client = Client.objects.create(freelancer=profile, name='Bruce Banner', email='bruce@lab.com')
        today = timezone.now().date()

        # Paid invoice
        inv1 = Invoice.objects.create(
            freelancer=profile,
            client=client,
            invoice_number='INV-AN-0001',
            issue_date=today - timedelta(days=20),
            due_date=today - timedelta(days=10),
            total_amount=Decimal('2000.00'),
            amount_paid=Decimal('2000.00'),
            status=InvoiceStatus.PAID
        )
        Payment.objects.create(
            invoice=inv1,
            amount=Decimal('2000.00'),
            paid_at=timezone.now() - timedelta(days=5),
            status=PaymentStatus.COMPLETED
        )

        # Overdue invoice
        Invoice.objects.create(
            freelancer=profile,
            client=client,
            invoice_number='INV-AN-0002',
            issue_date=today - timedelta(days=40),
            due_date=today - timedelta(days=15),
            total_amount=Decimal('1000.00'),
            amount_paid=Decimal('0.00'),
            status=InvoiceStatus.OVERDUE
        )

        kpis = AnalyticsService.get_kpi_metrics(profile)
        assert kpis['total_revenue'] == Decimal('2000.00')
        assert kpis['outstanding'] == Decimal('1000.00')
        assert kpis['overdue_amount'] == Decimal('1000.00')
        # Collection rate = 2000 / (2000 + 1000) * 100 = 66.7%
        assert kpis['collection_health_rate'] == 66.7

    def test_aging_report_buckets(self, auth_client):
        _, user = auth_client
        profile = user.profile
        client = Client.objects.create(freelancer=profile, name='Tony Stark', email='tony@stark.com')
        today = timezone.now().date()

        # 15 days overdue -> 0_30 bucket
        Invoice.objects.create(
            freelancer=profile,
            client=client,
            invoice_number='INV-AGE-15',
            due_date=today - timedelta(days=15),
            total_amount=Decimal('500.00'),
            status=InvoiceStatus.OVERDUE
        )

        # 45 days overdue -> 31_60 bucket
        Invoice.objects.create(
            freelancer=profile,
            client=client,
            invoice_number='INV-AGE-45',
            due_date=today - timedelta(days=45),
            total_amount=Decimal('1200.00'),
            status=InvoiceStatus.OVERDUE
        )

        buckets = AnalyticsService.get_aging_report(profile)
        assert buckets['0_30']['count'] == 1
        assert buckets['0_30']['amount'] == Decimal('500.00')
        assert buckets['31_60']['count'] == 1
        assert buckets['31_60']['amount'] == Decimal('1200.00')

    def test_csv_exports(self, auth_client):
        client_browser, user = auth_client
        profile = user.profile
        client = Client.objects.create(freelancer=profile, name='Natasha Romanoff', email='nat@shield.gov')
        Invoice.objects.create(
            freelancer=profile,
            client=client,
            invoice_number='INV-CSV-001',
            due_date=timezone.now().date(),
            total_amount=Decimal('3000.00')
        )

        # Aging CSV
        aging_res = client_browser.get(reverse('analytics:export_aging_csv'))
        assert aging_res.status_code == 200
        assert aging_res['Content-Type'] == 'text/csv'

        # Invoices CSV
        inv_res = client_browser.get(reverse('analytics:export_invoices_csv'))
        assert inv_res.status_code == 200
        assert inv_res['Content-Type'] == 'text/csv'
        assert 'INV-CSV-001' in inv_res.content.decode()
