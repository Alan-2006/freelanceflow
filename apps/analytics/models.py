from decimal import Decimal

from django.db import models
from django.utils import timezone

from apps.authentication.models import FreelancerProfile
from apps.projects.models import Project
from core.models import TimeStampedModel


class ExpenseCategory(models.TextChoices):
    SOFTWARE = 'SOFTWARE', 'Software & SaaS'
    CONTRACTOR = 'CONTRACTOR', 'Subcontractors & Labor'
    HARDWARE = 'HARDWARE', 'Hardware & Equipment'
    TRAVEL = 'TRAVEL', 'Travel & Meals'
    OFFICE = 'OFFICE', 'Office & Utilities'
    MARKETING = 'MARKETING', 'Advertising & Marketing'
    OTHER = 'OTHER', 'Other Business Expenses'


class Expense(TimeStampedModel):
    freelancer = models.ForeignKey(
        FreelancerProfile,
        on_delete=models.CASCADE,
        related_name='expenses'
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses'
    )
    category = models.CharField(
        max_length=30,
        choices=ExpenseCategory.choices,
        default=ExpenseCategory.SOFTWARE,
        db_index=True
    )
    vendor = models.CharField(max_length=150, help_text='e.g. AWS, Figma, GitHub, Adobe')
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=10, default='USD')
    date = models.DateField(default=timezone.now)
    receipt_file = models.FileField(upload_to='receipts/', blank=True, null=True)
    is_tax_deductible = models.BooleanField(default=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.vendor} - ${self.amount} ({self.get_category_display()})"
