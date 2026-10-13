from decimal import Decimal

from django.utils import timezone

from apps.invoicing.models import Invoice, InvoiceLineItem
from apps.projects.models import TimeEntry


class InvoiceCalculator:

    @staticmethod
    def generate_next_invoice_number(freelancer_profile) -> str:
        """Generate formatted invoice number like INV-2026-0001."""
        year = timezone.now().year
        prefix = f"INV-{year}-"

        # Count existing invoices with this prefix for this freelancer
        count = Invoice.objects.filter(
            freelancer=freelancer_profile,
            invoice_number__startswith=prefix
        ).count() + 1

        return f"{prefix}{count:04d}"

    @staticmethod
    def recalculate_invoice_totals(invoice: Invoice) -> Invoice:
        """Compute subtotal, tax, discount, late fee, and final total."""
        line_items = invoice.line_items.all()
        subtotal = Decimal('0.00')

        for item in line_items:
            item_total = round(item.quantity * item.unit_price, 2)
            item.total = item_total
            item.save(update_fields=['total'])
            subtotal += item_total

        invoice.subtotal = subtotal

        # Tax calculation
        if invoice.tax_rate > Decimal('0.00'):
            invoice.tax_amount = round((subtotal * invoice.tax_rate) / Decimal('100.00'), 2)
        else:
            invoice.tax_amount = Decimal('0.00')

        # Late fee calculation if overdue
        if invoice.is_overdue and invoice.late_fee_rate > Decimal('0.00'):
            invoice.late_fee_amount = round((subtotal * invoice.late_fee_rate) / Decimal('100.00'), 2)
        else:
            invoice.late_fee_amount = Decimal('0.00')

        # Total amount
        invoice.total_amount = max(
            Decimal('0.00'),
            (invoice.subtotal + invoice.tax_amount + invoice.late_fee_amount) - invoice.discount_amount
        )
        invoice.save(update_fields=['subtotal', 'tax_amount', 'late_fee_amount', 'total_amount'])
        return invoice

    @staticmethod
    def convert_unbilled_time_to_line_items(project, invoice: Invoice) -> int:
        """Find unbilled time entries for project and create corresponding invoice line items."""
        unbilled_entries = TimeEntry.objects.filter(
            project=project,
            is_billable=True,
            is_invoiced=False
        )

        created_count = 0
        for entry in unbilled_entries:
            hours = Decimal(str(round(entry.duration_seconds / 3600, 2)))
            if hours <= Decimal('0.00'):
                continue
            rate = Decimal(str(entry.hourly_rate)) if entry.hourly_rate > 0 else Decimal(str(project.hourly_rate))
            desc = f"Time: {entry.task.title if entry.task else project.title}"
            if entry.note:
                desc += f" - {entry.note}"

            InvoiceLineItem.objects.create(
                invoice=invoice,
                description=desc,
                quantity=hours,
                unit_price=rate,
                total=round(hours * rate, 2)
            )
            entry.is_invoiced = True
            entry.save(update_fields=['is_invoiced'])
            created_count += 1

        if created_count > 0:
            InvoiceCalculator.recalculate_invoice_totals(invoice)
        return created_count
