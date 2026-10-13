from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views, viewsets

app_name = 'api'

router = DefaultRouter()
router.register(r'clients', viewsets.ClientViewSet, basename='client')
router.register(r'projects', viewsets.ProjectViewSet, basename='project')
router.register(r'milestones', viewsets.MilestoneViewSet, basename='milestone')
router.register(r'invoices', viewsets.InvoiceViewSet, basename='invoice')
router.register(r'payments', viewsets.PaymentViewSet, basename='payment')

urlpatterns = [
    path('docs/', views.api_docs_view, name='docs'),
    path('', include(router.urls)),
]
