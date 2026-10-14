import csv
import json

from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.permissions import freelancer_required

from .forms import ExpenseForm
from .models import Expense, ExpenseCategory
from .services import AnalyticsService


@freelancer_required
def dashboard_view(request):
    freelancer = request.user.profile

    kpis = AnalyticsService.get_kpi_metrics(freelancer)
    revenue_chart = AnalyticsService.get_revenue_by_month(freelancer, months_count=6)
    client_chart = AnalyticsService.get_income_by_client(freelancer)
    cash_flow = AnalyticsService.get_cash_flow_forecast(freelancer)
    expense_categories = AnalyticsService.get_expenses_by_category(freelancer)

    recent_invoices = freelancer.invoices.all()[:5]

    return render(request, 'analytics/dashboard.html', {
        'kpis': kpis,
        'revenue_chart_json': json.dumps(revenue_chart),
        'client_chart_json': json.dumps(client_chart),
        'expense_categories_json': json.dumps(expense_categories),
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


# --- Expense Management ---

@freelancer_required
def expense_list_view(request):
    freelancer = request.user.profile
    expenses = freelancer.expenses.all().select_related('project')

    category_filter = request.GET.get('category')
    if category_filter and category_filter in ExpenseCategory.values:
        expenses = expenses.filter(category=category_filter)

    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0.00
    form = ExpenseForm(freelancer)

    return render(request, 'analytics/expenses.html', {
        'expenses': expenses,
        'total_expenses': total_expenses,
        'form': form,
        'categories': ExpenseCategory.choices,
        'current_category': category_filter or 'All',
    })


@freelancer_required
@require_POST
def expense_create_view(request):
    freelancer = request.user.profile
    form = ExpenseForm(freelancer, request.POST, request.FILES)
    if form.is_valid():
        exp = form.save(commit=False)
        exp.freelancer = freelancer
        exp.save()
        messages.success(request, f"Expense of ${exp.amount} for '{exp.vendor}' recorded.")
    else:
        messages.error(request, "Failed to record expense. Please check the entered data.")
    return redirect('analytics:expenses')


@freelancer_required
@require_POST
def expense_delete_view(request, pk):
    freelancer = request.user.profile
    exp = get_object_or_404(Expense, pk=pk, freelancer=freelancer)
    vendor = exp.vendor
    exp.delete()
    messages.success(request, f"Expense for '{vendor}' removed.")
    return redirect('analytics:expenses')


@freelancer_required
def export_expenses_csv_view(request):
    freelancer = request.user.profile
    expenses = freelancer.expenses.all().select_related('project')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="expenses_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Vendor', 'Category', 'Description', 'Amount', 'Currency', 'Project', 'Tax Deductible'])

    for exp in expenses:
        writer.writerow([
            exp.date.strftime("%Y-%m-%d"),
            exp.vendor,
            exp.get_category_display(),
            exp.description,
            exp.amount,
            exp.currency,
            exp.project.title if exp.project else 'General',
            'Yes' if exp.is_tax_deductible else 'No'
        ])

    return response

