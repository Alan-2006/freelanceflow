from rest_framework import serializers

from apps.clients.models import Client
from apps.invoicing.models import Invoice, InvoiceLineItem
from apps.payments.models import Payment
from apps.projects.models import Milestone, Project, Task


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            'id', 'name', 'company', 'email', 'phone', 'currency',
            'reliability_score', 'reminders_paused', 'created_at'
        ]

class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = [
            'id', 'project', 'title', 'description', 'amount',
            'due_date', 'status', 'approved_at', 'order'
        ]

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'project', 'milestone', 'title', 'status', 'estimated_hours', 'due_date']

class ProjectSerializer(serializers.ModelSerializer):
    milestones = MilestoneSerializer(many=True, read_only=True)
    progress_percentage = serializers.ReadOnlyField()

    class Meta:
        model = Project
        fields = [
            'id', 'client', 'title', 'description', 'status',
            'billing_type', 'budget', 'start_date', 'end_date',
            'progress_percentage', 'milestones', 'created_at'
        ]

class InvoiceLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLineItem
        fields = ['id', 'description', 'quantity', 'unit_price', 'total']

class InvoiceSerializer(serializers.ModelSerializer):
    line_items = InvoiceLineItemSerializer(many=True, read_only=True)
    balance_due = serializers.ReadOnlyField()

    class Meta:
        model = Invoice
        fields = [
            'id', 'client', 'project', 'invoice_number', 'issue_date',
            'due_date', 'currency', 'status', 'subtotal', 'tax_amount',
            'total_amount', 'amount_paid', 'balance_due', 'line_items', 'created_at'
        ]

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'invoice', 'receipt_number', 'amount', 'currency',
            'method', 'status', 'paid_at', 'notes'
        ]
