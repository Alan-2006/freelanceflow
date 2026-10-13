from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.projects.models import Milestone
from core.permissions import freelancer_required

from .forms import InvoiceCreateForm
from .models import Invoice, InvoiceLineItem, InvoiceStatus
from .services.calculator import InvoiceCalculator
from .services.pdf_generator import InvoicePDFGenerator
from .services.qr_generator import QRGeneratorService


@freelancer_required
def invoice_list_view(request):
    freelancer = request.user.profile
    invoices = freelancer.invoices.all()

    status_filter = request.GET.get('status')
    if status_filter and status_filter in InvoiceStatus.values:
        invoices = invoices.filter(status=status_filter)

    return render(request, 'invoicing/list.html', {
        'invoices': invoices,
        'current_status': status_filter or 'All',
        'statuses': InvoiceStatus.choices,
    })


@freelancer_required
def invoice_create_view(request):
    freelancer = request.user.profile

    if not freelancer.clients.exists():
        messages.warning(request, "Please create at least one client before issuing invoices.")
        return redirect('clients:create')

    # Pre-select milestone if coming from approval flow
    pre_milestone_id = request.GET.get('milestone')
    pre_milestone = None
    if pre_milestone_id:
        pre_milestone = Milestone.objects.filter(id=pre_milestone_id, project__client__freelancer=freelancer).first()

    if request.method == 'POST':
        form = InvoiceCreateForm(freelancer, request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.freelancer = freelancer
            invoice.save()

            # Parse line items from POST
            descriptions = request.POST.getlist('item_desc[]')
            quantities = request.POST.getlist('item_qty[]')
            prices = request.POST.getlist('item_price[]')

            for desc, qty, price in zip(descriptions, quantities, prices):
                if desc.strip():
                    InvoiceLineItem.objects.create(
                        invoice=invoice,
                        description=desc.strip(),
                        quantity=Decimal(qty or '1'),
                        unit_price=Decimal(price or '0')
                    )

            # Link milestone if passed
            if pre_milestone:
                InvoiceLineItem.objects.create(
                    invoice=invoice,
                    description=f"Milestone: {pre_milestone.title}",
                    quantity=Decimal('1'),
                    unit_price=pre_milestone.amount,
                    milestone=pre_milestone
                )

            InvoiceCalculator.recalculate_invoice_totals(invoice)
            messages.success(request, f"Invoice {invoice.invoice_number} created successfully!")
            return redirect('invoicing:detail', pk=invoice.pk)
    else:
        initial_number = InvoiceCalculator.generate_next_invoice_number(freelancer)
        today = timezone.now().date()
        due_date = today + timedelta(days=freelancer.default_payment_terms_days)

        initial_client = pre_milestone.project.client if pre_milestone else freelancer.clients.first()
        initial_project = pre_milestone.project if pre_milestone else None

        form = InvoiceCreateForm(freelancer, initial={
            'invoice_number': initial_number,
            'issue_date': today,
            'due_date': due_date,
            'client': initial_client,
            'project': initial_project,
            'currency': freelancer.currency,
        })

    return render(request, 'invoicing/builder.html', {
        'form': form,
        'freelancer': freelancer,
        'pre_milestone': pre_milestone,
    })


@freelancer_required
def invoice_detail_view(request, pk):
    freelancer = request.user.profile
    invoice = get_object_or_404(Invoice, pk=pk, freelancer=freelancer)
    InvoiceCalculator.recalculate_invoice_totals(invoice)

    site_url = request.build_absolute_uri('/')[:-1]
    public_url = request.build_absolute_uri(f"/invoicing/public/{invoice.public_token}/")
    qr_code_base64 = QRGeneratorService.generate_invoice_qr_base64(invoice, site_url)

    return render(request, 'invoicing/detail.html', {
        'invoice': invoice,
        'public_url': public_url,
        'qr_code_base64': qr_code_base64,
        'payments': invoice.payments.all() if hasattr(invoice, 'payments') else [],
        'reminders': invoice.reminder_logs.all() if hasattr(invoice, 'reminder_logs') else [],
    })


@freelancer_required
def invoice_pdf_view(request, pk):
    freelancer = request.user.profile
    invoice = get_object_or_404(Invoice, pk=pk, freelancer=freelancer)

    site_url = request.build_absolute_uri('/')[:-1]
    pdf_bytes = InvoicePDFGenerator.generate_invoice_pdf(invoice, site_url)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    filename = f"{invoice.invoice_number}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


def invoice_public_view(request, public_token):
    """Client-facing public invoice page for downloading and payment."""
    invoice = get_object_or_404(Invoice, public_token=public_token)
    invoice.record_view()

    site_url = request.build_absolute_uri('/')[:-1]
    qr_code_base64 = QRGeneratorService.generate_invoice_qr_base64(invoice, site_url)

    return render(request, 'invoicing/public.html', {
        'invoice': invoice,
        'freelancer': invoice.freelancer,
        'client': invoice.client,
        'qr_code_base64': qr_code_base64,
        'site_url': site_url,
    })


@freelancer_required
@require_POST
def invoice_send_view(request, pk):
    freelancer = request.user.profile
    invoice = get_object_or_404(Invoice, pk=pk, freelancer=freelancer)
    if invoice.status == InvoiceStatus.DRAFT:
        invoice.status = InvoiceStatus.SENT
        invoice.save(update_fields=['status'])
        messages.success(request, f"Invoice {invoice.invoice_number} marked as Sent.")
    return redirect('invoicing:detail', pk=invoice.pk)


@freelancer_required
@require_POST
def invoice_convert_time_view(request, pk):
    freelancer = request.user.profile
    invoice = get_object_or_404(Invoice, pk=pk, freelancer=freelancer)
    if not invoice.project:
        messages.error(request, "This invoice is not linked to a project.")
        return redirect('invoicing:detail', pk=invoice.pk)

    added = InvoiceCalculator.convert_unbilled_time_to_line_items(invoice.project, invoice)
    if added > 0:
        messages.success(request, f"Converted {added} unbilled time entries into line items.")
    else:
        messages.info(request, "No unbilled time entries found for this project.")
    return redirect('invoicing:detail', pk=invoice.pk)
