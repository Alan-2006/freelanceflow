from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.clients.services import ClientService
from apps.invoicing.models import Invoice, InvoiceStatus
from apps.projects.models import MilestoneStatus

from .models import Payment, PaymentMethod, PaymentStatus


class PaymentService:

    @staticmethod
    @transaction.atomic
    def record_payment(
        invoice: Invoice,
        amount: Decimal,
        method: str = PaymentMethod.MANUAL_BANK,
        gateway_order_id: str = '',
        gateway_payment_id: str = '',
        gateway_signature: str = '',
        proof_file=None,
        notes: str = ''
    ) -> Payment:
        """
        Record a payment transaction idempotently and update invoice balances.
        """
        # Idempotency check: if payment_id already recorded, return it
        if gateway_payment_id:
            existing = Payment.objects.filter(gateway_payment_id=gateway_payment_id).first()
            if existing:
                return existing

        amount = Decimal(str(amount))
        payment = Payment.objects.create(
            invoice=invoice,
            amount=amount,
            currency=invoice.currency,
            method=method,
            status=PaymentStatus.COMPLETED,
            gateway_order_id=gateway_order_id,
            gateway_payment_id=gateway_payment_id,
            gateway_signature=gateway_signature,
            proof_file=proof_file,
            notes=notes,
            paid_at=timezone.now()
        )

        # Update invoice amount_paid
        invoice.amount_paid = (invoice.amount_paid or Decimal('0.00')) + amount

        if invoice.balance_due <= Decimal('0.00'):
            invoice.status = InvoiceStatus.PAID
            # If linked to milestone, mark milestone as Paid
            for item in invoice.line_items.all():
                if item.milestone:
                    item.milestone.status = MilestoneStatus.PAID
                    item.milestone.save(update_fields=['status'])
        else:
            invoice.status = InvoiceStatus.PARTIALLY_PAID

        invoice.save(update_fields=['amount_paid', 'status'])

        # Recalculate client reliability score
        ClientService.recalculate_reliability_score(invoice.client)
        return payment
