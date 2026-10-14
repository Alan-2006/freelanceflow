from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.invoicing.models import Invoice, InvoiceLineItem, InvoiceStatus, RecurringInvoice
from apps.invoicing.services.calculator import InvoiceCalculator


class Command(BaseCommand):
    help = 'Process all due active recurring invoice templates and generate invoices'

    def handle(self, *args, **options):
        today = timezone.now().date()
        due_templates = RecurringInvoice.objects.filter(
            is_active=True,
            next_run_date__lte=today
        ).select_related('freelancer', 'client', 'project')

        count = 0
        for rec in due_templates:
            freelancer = rec.freelancer
            new_num = InvoiceCalculator.generate_next_invoice_number(freelancer)

            due_date = today + timedelta(days=freelancer.default_payment_terms_days)
            inv = Invoice.objects.create(
                freelancer=freelancer,
                client=rec.client,
                project=rec.project,
                invoice_number=new_num,
                issue_date=today,
                due_date=due_date,
                currency=rec.client.currency,
                status=InvoiceStatus.DRAFT,
                notes=f"Automated generation from recurring schedule: {rec.title}",
            )
            InvoiceLineItem.objects.create(
                invoice=inv,
                description=f"Retainer: {rec.title}",
                quantity=Decimal('1.00'),
                unit_price=rec.amount
            )
            InvoiceCalculator.recalculate_invoice_totals(inv)

            # Advance next_run_date
            if rec.frequency == 'WEEKLY':
                rec.next_run_date = today + timedelta(days=7)
            elif rec.frequency == 'QUARTERLY':
                rec.next_run_date = today + timedelta(days=90)
            else:
                rec.next_run_date = today + timedelta(days=30)
            rec.save(update_fields=['next_run_date'])

            count += 1
            self.stdout.write(self.style.SUCCESS(
                f"Generated invoice {inv.invoice_number} for client '{rec.client.name}' from schedule '{rec.title}'"
            ))

        self.stdout.write(self.style.SUCCESS(f"Finished. Total recurring invoices generated: {count}"))
