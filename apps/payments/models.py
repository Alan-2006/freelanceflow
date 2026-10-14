from django.db import models
from django.utils import timezone

from apps.invoicing.models import Invoice
from core.models import TimeStampedModel
from core.utils import generate_random_token


class PaymentMethod(models.TextChoices):
    RAZORPAY = 'RAZORPAY', 'Razorpay (Card/NetBanking/UPI)'
    STRIPE = 'STRIPE', 'Stripe (Credit / Debit Card)'
    MANUAL_BANK = 'MANUAL_BANK', 'Manual - Bank Transfer / Wire'
    MANUAL_UPI = 'MANUAL_UPI', 'Manual - Direct UPI'
    MANUAL_CASH = 'MANUAL_CASH', 'Manual - Cash / Other'


class PaymentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    COMPLETED = 'COMPLETED', 'Completed'
    FAILED = 'FAILED', 'Failed'
    REFUNDED = 'REFUNDED', 'Refunded'


class Payment(TimeStampedModel):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    method = models.CharField(
        max_length=30,
        choices=PaymentMethod.choices,
        default=PaymentMethod.RAZORPAY
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True
    )
    gateway_order_id = models.CharField(max_length=100, blank=True, default='')
    gateway_payment_id = models.CharField(max_length=100, blank=True, default='', db_index=True)
    gateway_signature = models.CharField(max_length=255, blank=True, default='')
    paid_at = models.DateTimeField(default=timezone.now)
    proof_file = models.FileField(upload_to='payment_proofs/', blank=True, null=True)
    notes = models.TextField(blank=True, default='')
    receipt_number = models.CharField(max_length=50, blank=True, default='', unique=True)

    class Meta:
        ordering = ['-paid_at']

    def __str__(self):
        return f"Payment {self.receipt_number or self.id} - ${self.amount} for {self.invoice.invoice_number}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            year = timezone.now().year
            self.receipt_number = f"RCP-{year}-{generate_random_token(8).upper()}"
        super().save(*args, **kwargs)


class CreditNote(TimeStampedModel):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='credit_notes'
    )
    credit_note_number = models.CharField(max_length=50, unique=True, db_index=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    issued_date = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['-issued_date', '-created_at']

    def __str__(self):
        return f"{self.credit_note_number} (${self.amount}) for {self.invoice.invoice_number}"

    def save(self, *args, **kwargs):
        if not self.credit_note_number:
            year = timezone.now().year
            self.credit_note_number = f"CN-{year}-{generate_random_token(8).upper()}"
        super().save(*args, **kwargs)
