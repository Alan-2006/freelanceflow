from decimal import Decimal

from django.db import models
from django.utils import timezone

from apps.authentication.models import FreelancerProfile
from apps.clients.models import Client
from apps.projects.models import Milestone, Project
from core.models import TimeStampedModel
from core.utils import generate_random_token


class InvoiceStatus(models.TextChoices):
    DRAFT = 'Draft', 'Draft'
    SENT = 'Sent', 'Sent'
    VIEWED = 'Viewed', 'Viewed by Client'
    PARTIALLY_PAID = 'Partially Paid', 'Partially Paid'
    PAID = 'Paid', 'Paid'
    OVERDUE = 'Overdue', 'Overdue'
    CANCELLED = 'Cancelled', 'Cancelled'

class RecurringFrequency(models.TextChoices):
    WEEKLY = 'WEEKLY', 'Weekly'
    MONTHLY = 'MONTHLY', 'Monthly'
    QUARTERLY = 'QUARTERLY', 'Quarterly'


class Invoice(TimeStampedModel):
    freelancer = models.ForeignKey(
        FreelancerProfile,
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices'
    )
    invoice_number = models.CharField(max_length=50, db_index=True)
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    currency = models.CharField(max_length=10, default='USD')
    status = models.CharField(
        max_length=20,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.DRAFT,
        db_index=True
    )
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    late_fee_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    late_fee_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    notes = models.TextField(blank=True, default='')
    payment_terms = models.TextField(blank=True, default='')
    public_token = models.CharField(max_length=64, unique=True, db_index=True, blank=True)
    viewed_at = models.DateTimeField(null=True, blank=True)
    reminders_paused = models.BooleanField(default=False)

    class Meta:
        ordering = ['-issue_date', '-created_at']
        unique_together = ('freelancer', 'invoice_number')

    def __str__(self):
        return f"{self.invoice_number} - {self.client.display_title} (${self.total_amount})"

    def save(self, *args, **kwargs):
        if not self.public_token:
            self.public_token = generate_random_token(40)
        super().save(*args, **kwargs)

    @property
    def balance_due(self) -> Decimal:
        return max(Decimal('0.00'), self.total_amount - self.amount_paid)

    @property
    def is_overdue(self) -> bool:
        if self.status in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]:
            return False
        return self.due_date < timezone.now().date()

    @property
    def days_overdue(self) -> int:
        if not self.is_overdue:
            return 0
        return (timezone.now().date() - self.due_date).days

    def record_view(self):
        """Mark invoice as viewed if currently Sent."""
        if not self.viewed_at:
            self.viewed_at = timezone.now()
            if self.status == InvoiceStatus.SENT:
                self.status = InvoiceStatus.VIEWED
            self.save(update_fields=['viewed_at', 'status'])


class InvoiceLineItem(TimeStampedModel):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='line_items'
    )
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('1.00'))
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    milestone = models.ForeignKey(
        Milestone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice_lines'
    )

    def __str__(self):
        return f"{self.description} (${self.total})"

    def calculate_total(self) -> Decimal:
        base = self.quantity * self.unit_price
        tax = (base * self.tax_rate) / Decimal('100.00')
        return round(base + tax, 2)


class RecurringInvoice(TimeStampedModel):
    freelancer = models.ForeignKey(
        FreelancerProfile,
        on_delete=models.CASCADE,
        related_name='recurring_templates'
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='recurring_templates'
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recurring_templates'
    )
    title = models.CharField(max_length=200)
    frequency = models.CharField(
        max_length=20,
        choices=RecurringFrequency.choices,
        default=RecurringFrequency.MONTHLY
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    next_run_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"[Recurring] {self.title} - ${self.amount} ({self.frequency})"
