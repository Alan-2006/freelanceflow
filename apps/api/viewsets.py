from rest_framework import permissions, viewsets

from apps.analytics.models import Expense
from apps.clients.models import Client
from apps.invoicing.models import Invoice
from apps.payments.models import Payment
from apps.projects.models import Milestone, Project, Task, TimeEntry

from .serializers import (
    ClientSerializer,
    ExpenseSerializer,
    InvoiceSerializer,
    MilestoneSerializer,
    PaymentSerializer,
    ProjectSerializer,
    TaskSerializer,
    TimeEntrySerializer,
)


class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Client.objects.filter(freelancer__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(freelancer=self.request.user.profile)


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(client__freelancer__user=self.request.user)


class MilestoneViewSet(viewsets.ModelViewSet):
    serializer_class = MilestoneSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Milestone.objects.filter(project__client__freelancer__user=self.request.user)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(project__client__freelancer__user=self.request.user)


class TimeEntryViewSet(viewsets.ModelViewSet):
    serializer_class = TimeEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TimeEntry.objects.filter(project__client__freelancer__user=self.request.user)

    def perform_create(self, serializer):
        from rest_framework.exceptions import PermissionDenied
        project = serializer.validated_data.get('project')
        if project and project.client.freelancer.user != self.request.user:
            raise PermissionDenied("You do not have permission to log time on this project.")
        serializer.save()


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Expense.objects.filter(freelancer__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(freelancer=self.request.user.profile)


class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Invoice.objects.filter(freelancer__user=self.request.user)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(invoice__freelancer__user=self.request.user)

