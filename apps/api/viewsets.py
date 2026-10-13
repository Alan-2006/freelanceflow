from rest_framework import permissions, viewsets

from apps.clients.models import Client
from apps.invoicing.models import Invoice
from apps.payments.models import Payment
from apps.projects.models import Milestone, Project

from .serializers import (
    ClientSerializer,
    InvoiceSerializer,
    MilestoneSerializer,
    PaymentSerializer,
    ProjectSerializer,
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
