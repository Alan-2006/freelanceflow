import base64

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.invoicing.models import Invoice
from core.permissions import freelancer_required

from .engine import PaymentReminderEngine
from .models import ReminderLog, ReminderTone

# 1x1 transparent GIF byte sequence
TRANSPARENT_1X1_GIF = base64.b64decode(
    b'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
)

def track_open_view(request, token):
    """Tracking pixel endpoint: logs open event and returns 1x1 GIF."""
    log_entry = ReminderLog.objects.filter(tracking_token=token).first()
    if log_entry:
        log_entry.record_open()
    return HttpResponse(TRANSPARENT_1X1_GIF, content_type='image/gif')


def track_click_view(request, token):
    """Link click tracker: records click and redirects to invoice checkout."""
    log_entry = ReminderLog.objects.filter(tracking_token=token).first()
    if log_entry:
        log_entry.record_click()
        return redirect('invoicing:public', public_token=log_entry.invoice.public_token)
    return redirect('home')


@freelancer_required
def reminder_dashboard_view(request):
    freelancer = request.user.profile
    PaymentReminderEngine.ensure_default_rules_exist(freelancer)

    rules = freelancer.reminder_rules.all()
    logs = ReminderLog.objects.filter(invoice__freelancer=freelancer)[:25]

    # Calculate open rate
    total_sent = logs.count()
    total_opened = logs.filter(opened=True).count()
    open_rate = round((total_opened / total_sent * 100), 1) if total_sent > 0 else 0

    return render(request, 'reminders/dashboard.html', {
        'rules': rules,
        'logs': logs,
        'total_sent': total_sent,
        'total_opened': total_opened,
        'open_rate': open_rate,
    })


@freelancer_required
@require_POST
def reminder_run_engine_view(request):
    """Manually trigger the reminder evaluation engine from the dashboard."""
    site_url = request.build_absolute_uri('/')[:-1]
    stats = PaymentReminderEngine.evaluate_invoices(dry_run=False, site_url=site_url)
    messages.success(
        request,
        f"Reminder engine finished: {stats['dispatched']} reminders sent, {stats['evaluated']} invoices evaluated."
    )
    return redirect('reminders:dashboard')


@freelancer_required
@require_POST
def reminder_toggle_pause_view(request, invoice_pk):
    freelancer = request.user.profile
    invoice = get_object_or_404(Invoice, pk=invoice_pk, freelancer=freelancer)
    invoice.reminders_paused = not invoice.reminders_paused
    invoice.save(update_fields=['reminders_paused'])

    status_str = "paused" if invoice.reminders_paused else "resumed"
    messages.info(request, f"Reminders {status_str} for invoice {invoice.invoice_number}.")
    return redirect('invoicing:detail', pk=invoice.pk)


@freelancer_required
def reminder_send_now_view(request, invoice_pk):
    freelancer = request.user.profile
    invoice = get_object_or_404(Invoice, pk=invoice_pk, freelancer=freelancer)
    site_url = request.build_absolute_uri('/')[:-1]

    if request.method == 'POST':
        tone = request.POST.get('tone', ReminderTone.FRIENDLY)
        rule = freelancer.reminder_rules.filter(tone=tone).first()

        context = {
            'client_name': invoice.client.name,
            'client_company': invoice.client.display_title,
            'invoice_number': invoice.invoice_number,
            'amount': f"{invoice.balance_due:,.2f}",
            'due_date': invoice.due_date.strftime("%B %d, %Y"),
            'freelancer_name': freelancer.display_name,
            'pay_link': f"{site_url}/invoicing/public/{invoice.public_token}/",
        }

        subj = rule.subject_template if rule else f"Payment Reminder: Invoice {invoice.invoice_number}"
        body = rule.body_template if rule else f"Hi {invoice.client.name}, please remember invoice {invoice.invoice_number}."

        subject = PaymentReminderEngine.interpolate_template(subj, context)
        message_body = PaymentReminderEngine.interpolate_template(body, context)

        log_entry = ReminderLog.objects.create(
            invoice=invoice,
            rule=rule,
            recipient=invoice.client.email,
            tone=tone,
            subject=subject,
            message_body=message_body,
        )

        from .channels.email import EmailNotificationChannel
        EmailNotificationChannel().send(
            recipient=invoice.client.email,
            subject=subject,
            body=message_body,
            context={
                'site_url': site_url,
                'tracking_token': log_entry.tracking_token,
            }
        )

        messages.success(request, f"Immediate {tone} reminder dispatched to {invoice.client.email}!")
        return redirect('invoicing:detail', pk=invoice.pk)

    return render(request, 'reminders/send_now.html', {
        'invoice': invoice,
        'tones': ReminderTone.choices,
    })
