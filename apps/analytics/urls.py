from django.urls import path

from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('reports/', views.reports_view, name='reports'),
    path('reports/aging/csv/', views.export_aging_csv_view, name='export_aging_csv'),
    path('reports/invoices/csv/', views.export_invoices_csv_view, name='export_invoices_csv'),
]
