from datetime import datetime
from datetime import timezone as dt_timezone
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.invoicing.models import InvoiceStatus
from apps.payments.models import Payment


class AnalyticsService:

    @staticmethod
    def get_kpi_metrics(freelancer):
        invoices = freelancer.invoices.exclude(status=InvoiceStatus.CANCELLED)

        # 1. Total revenue collected
        total_revenue = invoices.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')

        # 2. Total outstanding billed
        total_billed = invoices.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        outstanding = max(Decimal('0.00'), total_billed - total_revenue)

        # 3. Overdue amount
        today = timezone.now().date()
        overdue_invoices = invoices.filter(
            due_date__lt=today
        ).exclude(status=InvoiceStatus.PAID)
        overdue_amount = Decimal('0.00')
        for inv in overdue_invoices:
            overdue_amount += inv.balance_due

        # 4. Average days to pay
        paid_invoices = invoices.filter(status=InvoiceStatus.PAID)
        days_diffs = []
        for inv in paid_invoices:
            if hasattr(inv, 'payments') and inv.payments.exists():
                last_p = inv.payments.order_by('-paid_at').first()
                diff = (last_p.paid_at.date() - inv.issue_date).days
                days_diffs.append(max(0, diff))
        avg_days_to_pay = round(sum(days_diffs) / len(days_diffs), 1) if days_diffs else 0

        # 5. Monthly Recurring Revenue (from active recurring templates)
        mrr = freelancer.recurring_templates.filter(is_active=True).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

        # 6. Overall Collection Health Rate (0-100%)
        # Collection Rate = (Paid / (Paid + Overdue)) * 100
        denom = total_revenue + overdue_amount
        collection_health_rate = round(float((total_revenue / denom) * 100), 1) if denom > 0 else 100.0

        # 7. Total Business Expenses & Net Profit
        total_expenses = Decimal('0.00')
        if hasattr(freelancer, 'expenses'):
            total_expenses = freelancer.expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        net_profit = total_revenue - total_expenses
        profit_margin_pct = round(float((net_profit / total_revenue) * 100), 1) if total_revenue > 0 else 0.0

        # 8. Multi-currency breakdown
        currency_breakdown = list(
            invoices.values('currency').annotate(
                total_billed=Sum('total_amount'),
                total_paid=Sum('amount_paid')
            ).order_by('-total_paid')
        )

        return {
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'net_profit': net_profit,
            'profit_margin_pct': profit_margin_pct,
            'outstanding': outstanding,
            'overdue_amount': overdue_amount,
            'avg_days_to_pay': avg_days_to_pay,
            'mrr': mrr,
            'collection_health_rate': collection_health_rate,
            'currency_breakdown': currency_breakdown,
            'active_projects_count': freelancer.clients.aggregate(
                total=Count('projects', filter=Q(projects__status='Active'))
            )['total'] or 0
        }


    @staticmethod
    def get_revenue_by_month(freelancer, months_count: int = 6):
        """Aggregate settled payments over the last N months."""
        labels = []
        data = []
        expense_data = []
        today = timezone.now().date()

        for i in range(months_count - 1, -1, -1):
            year = today.year
            month = today.month - i
            while month <= 0:
                month += 12
                year -= 1

            month_start = datetime(year, month, 1, tzinfo=dt_timezone.utc)
            if month == 12:
                next_month = datetime(year + 1, 1, 1, tzinfo=dt_timezone.utc)
            else:
                next_month = datetime(year, month + 1, 1, tzinfo=dt_timezone.utc)

            monthly_sum = Payment.objects.filter(
                invoice__freelancer=freelancer,
                paid_at__gte=month_start,
                paid_at__lt=next_month
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            m_exp = Decimal('0.00')
            if hasattr(freelancer, 'expenses'):
                m_exp = freelancer.expenses.filter(
                    date__gte=month_start.date(),
                    date__lt=next_month.date()
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            labels.append(month_start.strftime("%b %Y"))
            data.append(float(monthly_sum))
            expense_data.append(float(m_exp))

        return {'labels': labels, 'data': data, 'expense_data': expense_data}

    @staticmethod
    def get_expenses_by_category(freelancer):
        if not hasattr(freelancer, 'expenses'):
            return {'labels': [], 'data': []}
        from .models import ExpenseCategory
        cat_map = dict(ExpenseCategory.choices)
        grouped = freelancer.expenses.values('category').annotate(total=Sum('amount')).order_by('-total')
        labels = [cat_map.get(g['category'], g['category']) for g in grouped]
        data = [float(g['total']) for g in grouped]
        return {'labels': labels, 'data': data}


    @staticmethod
    def get_income_by_client(freelancer):
        """Breakdown of collected earnings per client."""
        client_totals = []
        for client in freelancer.clients.all():
            total = client.invoices.aggregate(paid=Sum('amount_paid'))['paid'] or Decimal('0.00')
            if total > Decimal('0.00'):
                client_totals.append({
                    'name': client.display_title,
                    'amount': float(total)
                })

        client_totals.sort(key=lambda x: x['amount'], reverse=True)
        return {
            'labels': [c['name'] for c in client_totals[:6]],
            'data': [c['amount'] for c in client_totals[:6]]
        }

    @staticmethod
    def get_aging_report(freelancer):
        """Aging buckets for overdue receivables: 0-30, 31-60, 61-90, 90+ days."""
        today = timezone.now().date()
        unpaid = freelancer.invoices.filter(
            due_date__lt=today
        ).exclude(status__in=[InvoiceStatus.PAID, InvoiceStatus.CANCELLED])

        buckets = {
            '0_30': {'label': '1 - 30 Days', 'amount': Decimal('0.00'), 'count': 0, 'invoices': []},
            '31_60': {'label': '31 - 60 Days', 'amount': Decimal('0.00'), 'count': 0, 'invoices': []},
            '61_90': {'label': '61 - 90 Days', 'amount': Decimal('0.00'), 'count': 0, 'invoices': []},
            '90_plus': {'label': '90+ Days', 'amount': Decimal('0.00'), 'count': 0, 'invoices': []},
        }

        for inv in unpaid:
            days = (today - inv.due_date).days
            bal = inv.balance_due
            if days <= 30:
                key = '0_30'
            elif days <= 60:
                key = '31_60'
            elif days <= 90:
                key = '61_90'
            else:
                key = '90_plus'

            buckets[key]['amount'] += bal
            buckets[key]['count'] += 1
            buckets[key]['invoices'].append(inv)

        return buckets

    @staticmethod
    def get_cash_flow_forecast(freelancer):
        """
        Next 30, 60, 90 days projected cash flow based on due dates
        weighted by client reliability scores.
        """
        today = timezone.now().date()
        unsettled = freelancer.invoices.exclude(
            status__in=[InvoiceStatus.PAID, InvoiceStatus.CANCELLED]
        )

        f_30 = Decimal('0.00')
        f_60 = Decimal('0.00')
        f_90 = Decimal('0.00')

        for inv in unsettled:
            # Days from today until due date
            days_until = (inv.due_date - today).days
            weight = Decimal(str(inv.client.reliability_score / 100.0))
            projected = inv.balance_due * weight

            if days_until <= 30:
                f_30 += projected
            elif days_until <= 60:
                f_60 += projected
            elif days_until <= 90:
                f_90 += projected

        return {
            'next_30_days': round(f_30, 2),
            'next_60_days': round(f_60, 2),
            'next_90_days': round(f_90, 2),
            'total_runway': round(f_30 + f_60 + f_90, 2)
        }
