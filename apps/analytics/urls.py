from django.urls import path

from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('expenses/', views.expense_list_view, name='expenses'),
    path('expenses/new/', views.expense_create_view, name='expense_create'),
    path('expenses/<uuid:pk>/delete/', views.expense_delete_view, name='expense_delete'),
    path('expenses/export/csv/', views.export_expenses_csv_view, name='export_expenses_csv'),
    path('reports/', views.reports_view, name='reports'),
    path('reports/aging/csv/', views.export_aging_csv_view, name='export_aging_csv'),
    path('reports/invoices/csv/', views.export_invoices_csv_view, name='export_invoices_csv'),
]

