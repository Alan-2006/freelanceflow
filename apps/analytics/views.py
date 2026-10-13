import csv
import json

from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from core.permissions import freelancer_required

from .services import AnalyticsService


@freelancer_required
def dashboard_view(request):
    freelancer = request.user.profile

    kpis = AnalyticsService.get_kpi_metrics(freelancer)
    revenue_chart = AnalyticsService.get_revenue_by_month(freelancer, months_count=6)
    client_chart = AnalyticsService.get_income_by_client(freelancer)
    cash_flow = AnalyticsService.get_cash_flow_forecast(freelancer)

    recent_invoices = freelancer.invoices.all()[:5]

    return render(request, 'analytics/dashboard.html', {
        'kpis': kpis,
        'revenue_chart_json': json.dumps(revenue_chart),
        'client_chart_json': json.dumps(client_chart),
        'cash_flow': cash_flow,
        'recent_invoices': recent_invoices,
    })


@freelancer_required
def reports_view(request):
    freelancer = request.user.profile
    aging_buckets = AnalyticsService.get_aging_report(freelancer)
    cash_flow = AnalyticsService.get_cash_flow_forecast(freelancer)

    return render(request, 'analytics/reports.html', {
        'aging_buckets': aging_buckets,
        'cash_flow': cash_flow,
    })


@freelancer_required
def export_aging_csv_view(request):
    freelancer = request.user.profile
    aging = AnalyticsService.get_aging_report(freelancer)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="aging_report_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Bucket', 'Invoice Number', 'Client', 'Due Date', 'Days Overdue', 'Balance Due'])

    today = timezone.now().date()
    for bucket_key, data in aging.items():
        for inv in data['invoices']:
            days = (today - inv.due_date).days
            writer.writerow([
                data['label'],
                inv.invoice_number,
                inv.client.display_title,
                inv.due_date.strftime("%Y-%m-%d"),
                days,
                inv.balance_due
            ])

    return response


@freelancer_required
def export_invoices_csv_view(request):
    freelancer = request.user.profile
    invoices = freelancer.invoices.all()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="invoices_summary_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Invoice #', 'Client', 'Project', 'Issue Date', 'Due Date', 'Status', 'Total', 'Paid', 'Balance Due'])

    for inv in invoices:
        writer.writerow([
            inv.invoice_number,
            inv.client.display_title,
            inv.project.title if inv.project else 'N/A',
            inv.issue_date.strftime("%Y-%m-%d"),
            inv.due_date.strftime("%Y-%m-%d"),
            inv.status,
            inv.total_amount,
            inv.amount_paid,
            inv.balance_due
        ])

    return response
