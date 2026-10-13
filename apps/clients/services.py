from django.db.models import Sum
from django.utils import timezone


class ClientService:
    @staticmethod
    def get_client_financial_summary(client):
        """Compute live financial overview for a specific client."""
        if not hasattr(client, 'invoices'):
            return {
                'total_billed': 0,
                'total_paid': 0,
                'total_outstanding': 0,
                'avg_days_to_pay': 0,
                'invoices_count': 0,
                'projects_count': client.projects.count(),
            }

        invoices = client.invoices.all()

        total_billed = invoices.exclude(status='Cancelled').aggregate(
            total=Sum('total_amount')
        )['total'] or 0

        total_paid = invoices.exclude(status='Cancelled').aggregate(
            total=Sum('amount_paid')
        )['total'] or 0

        total_outstanding = max(0, total_billed - total_paid)

        # Average days to pay
        paid_invoices = invoices.filter(status='Paid')
        avg_days = 0
        if paid_invoices.exists():
            days_diffs = []
            for inv in paid_invoices:
                if hasattr(inv, 'payments') and inv.payments.exists():
                    latest_payment = inv.payments.order_by('-paid_at').first()
                    diff = (latest_payment.paid_at.date() - inv.issue_date).days
                    days_diffs.append(max(0, diff))
            if days_diffs:
                avg_days = round(sum(days_diffs) / len(days_diffs), 1)

        return {
            'total_billed': total_billed,
            'total_paid': total_paid,
            'total_outstanding': total_outstanding,
            'avg_days_to_pay': avg_days,
            'invoices_count': invoices.count(),
            'projects_count': client.projects.count(),
        }

    @staticmethod
    def recalculate_reliability_score(client) -> int:
        """Calculate score 0-100 based on payment punctuality."""
        if not hasattr(client, 'invoices'):
            return client.reliability_score

        invoices = client.invoices.exclude(status__in=['Draft', 'Cancelled'])
        if not invoices.exists():
            return 100

        score = 100.0

        for inv in invoices:
            if inv.status == 'Overdue':
                days_overdue = (timezone.now().date() - inv.due_date).days
                score -= min(35, max(10, days_overdue * 2))
            elif inv.status == 'Paid':
                last_payment = inv.payments.order_by('-paid_at').first()
                if last_payment and last_payment.paid_at.date() > inv.due_date:
                    days_late = (last_payment.paid_at.date() - inv.due_date).days
                    score -= min(25, days_late * 1.5)

        normalized_score = max(10, min(100, int(score)))
        client.reliability_score = normalized_score
        client.save(update_fields=['reliability_score'])
        return normalized_score
