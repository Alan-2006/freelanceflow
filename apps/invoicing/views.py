from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.projects.models import Milestone, MilestoneStatus, Project
from core.permissions import freelancer_required

from .forms import InvoiceCreateForm, ProposalCreateForm, RecurringInvoiceForm
from .models import (
    Invoice,
    InvoiceLineItem,
    InvoiceStatus,
    Proposal,
    ProposalLineItem,
    ProposalStatus,
    RecurringInvoice,
)
from .services.calculator import InvoiceCalculator
from .services.email_service import InvoiceEmailService
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
@freelancer_required
def invoice_edit_view(request, pk):
    freelancer = request.user.profile
    invoice = get_object_or_404(Invoice, pk=pk, freelancer=freelancer)

    if request.method == 'POST':
        form = InvoiceCreateForm(freelancer, request.POST, instance=invoice)
        if form.is_valid():
            inv = form.save()

            descriptions = request.POST.getlist('item_desc[]')
            quantities = request.POST.getlist('item_qty[]')
            prices = request.POST.getlist('item_price[]')

            if descriptions:
                inv.line_items.all().delete()
                for desc, qty, price in zip(descriptions, quantities, prices):
                    if desc.strip():
                        InvoiceLineItem.objects.create(
                            invoice=inv,
                            description=desc.strip(),
                            quantity=Decimal(qty or '1'),
                            unit_price=Decimal(price or '0')
                        )

            InvoiceCalculator.recalculate_invoice_totals(inv)
            messages.success(request, f"Invoice {inv.invoice_number} updated.")
            return redirect('invoicing:detail', pk=inv.pk)
    else:
        form = InvoiceCreateForm(freelancer, instance=invoice)

    return render(request, 'invoicing/builder.html', {
        'form': form,
        'freelancer': freelancer,
        'invoice': invoice,
        'is_edit': True,
        'existing_lines': invoice.line_items.all(),
    })


@freelancer_required
@require_POST
def invoice_duplicate_view(request, pk):
    freelancer = request.user.profile
    original = get_object_or_404(Invoice, pk=pk, freelancer=freelancer)
    new_number = InvoiceCalculator.generate_next_invoice_number(freelancer)

    today = timezone.now().date()
    new_inv = Invoice.objects.create(
        freelancer=freelancer,
        client=original.client,
        project=original.project,
        invoice_number=new_number,
        issue_date=today,
        due_date=today + timedelta(days=freelancer.default_payment_terms_days),
        currency=original.currency,
        status=InvoiceStatus.DRAFT,
        tax_rate=original.tax_rate,
        discount_amount=original.discount_amount,
        late_fee_rate=original.late_fee_rate,
        notes=original.notes,
        payment_terms=original.payment_terms,
    )
    for line in original.line_items.all():
        InvoiceLineItem.objects.create(
            invoice=new_inv,
            description=line.description,
            quantity=line.quantity,
            unit_price=line.unit_price,
            tax_rate=line.tax_rate,
            total=line.total,
        )
    InvoiceCalculator.recalculate_invoice_totals(new_inv)
    messages.success(request, f"Duplicated invoice {original.invoice_number} to {new_inv.invoice_number}!")
    return redirect('invoicing:detail', pk=new_inv.pk)


@freelancer_required
@require_POST
def invoice_delete_view(request, pk):
    freelancer = request.user.profile
    invoice = get_object_or_404(Invoice, pk=pk, freelancer=freelancer)
    number = invoice.invoice_number

    if invoice.status in [InvoiceStatus.PAID, InvoiceStatus.PARTIALLY_PAID]:
        invoice.status = InvoiceStatus.CANCELLED
        invoice.save(update_fields=['status'])
        messages.warning(request, f"Invoice {number} has payments, so it has been marked as Cancelled.")
    else:
        invoice.delete()
        messages.success(request, f"Invoice {number} deleted successfully.")
    return redirect('invoicing:list')


@freelancer_required
@require_POST
def invoice_send_view(request, pk):
    freelancer = request.user.profile
    invoice = get_object_or_404(Invoice, pk=pk, freelancer=freelancer)
    site_url = request.build_absolute_uri('/')[:-1]

    email_sent = InvoiceEmailService.send_invoice_email(invoice, site_url)
    invoice.status = InvoiceStatus.SENT
    invoice.save(update_fields=['status'])

    if email_sent:
        messages.success(request, f"Invoice {invoice.invoice_number} sent to {invoice.client.email} successfully!")
    else:
        messages.warning(request, f"Invoice {invoice.invoice_number} marked as Sent (Email simulation mode).")
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


# --- Recurring Invoices ---

@freelancer_required
def recurring_invoice_list_view(request):
    freelancer = request.user.profile
    recurring = freelancer.recurring_templates.all().select_related('client', 'project')
    return render(request, 'invoicing/recurring_list.html', {
        'recurring_templates': recurring,
    })


@freelancer_required
def recurring_invoice_create_view(request):
    freelancer = request.user.profile
    if request.method == 'POST':
        form = RecurringInvoiceForm(freelancer, request.POST)
        if form.is_valid():
            rec = form.save(commit=False)
            rec.freelancer = freelancer
            rec.save()
            messages.success(request, f"Recurring schedule '{rec.title}' created!")
            return redirect('invoicing:recurring_list')
    else:
        form = RecurringInvoiceForm(freelancer, initial={
            'next_run_date': timezone.now().date() + timedelta(days=30),
        })
    return render(request, 'invoicing/recurring_form.html', {
        'form': form,
    })


@freelancer_required
@require_POST
def recurring_invoice_toggle_view(request, pk):
    freelancer = request.user.profile
    rec = get_object_or_404(RecurringInvoice, pk=pk, freelancer=freelancer)
    rec.is_active = not rec.is_active
    rec.save(update_fields=['is_active'])
    status_label = "activated" if rec.is_active else "paused"
    messages.info(request, f"Recurring schedule '{rec.title}' {status_label}.")
    return redirect('invoicing:recurring_list')


@freelancer_required
@require_POST
def recurring_invoice_delete_view(request, pk):
    freelancer = request.user.profile
    rec = get_object_or_404(RecurringInvoice, pk=pk, freelancer=freelancer)
    title = rec.title
    rec.delete()
    messages.success(request, f"Recurring schedule '{title}' removed.")
    return redirect('invoicing:recurring_list')


@freelancer_required
@require_POST
def recurring_invoice_generate_now_view(request, pk):
    freelancer = request.user.profile
    rec = get_object_or_404(RecurringInvoice, pk=pk, freelancer=freelancer)

    new_num = InvoiceCalculator.generate_next_invoice_number(freelancer)
    today = timezone.now().date()
    inv = Invoice.objects.create(
        freelancer=freelancer,
        client=rec.client,
        project=rec.project,
        invoice_number=new_num,
        issue_date=today,
        due_date=today + timedelta(days=freelancer.default_payment_terms_days),
        currency=rec.client.currency,
        status=InvoiceStatus.DRAFT,
        notes=f"Generated from recurring retainer schedule: {rec.title}",
    )
    InvoiceLineItem.objects.create(
        invoice=inv,
        description=f"Retainer: {rec.title}",
        quantity=Decimal('1.00'),
        unit_price=rec.amount
    )
    InvoiceCalculator.recalculate_invoice_totals(inv)

    if rec.frequency == 'WEEKLY':
        rec.next_run_date = today + timedelta(days=7)
    elif rec.frequency == 'QUARTERLY':
        rec.next_run_date = today + timedelta(days=90)
    else:
        rec.next_run_date = today + timedelta(days=30)
    rec.save(update_fields=['next_run_date'])

    messages.success(request, f"Generated invoice {inv.invoice_number} from '{rec.title}'!")
    return redirect('invoicing:detail', pk=inv.pk)


@freelancer_required
def proposal_list_view(request):
    freelancer = request.user.profile
    proposals = freelancer.proposals.all()
    status_filter = request.GET.get('status')
    if status_filter and status_filter in ProposalStatus.values:
        proposals = proposals.filter(status=status_filter)

    return render(request, 'invoicing/proposals/list.html', {
        'proposals': proposals,
        'current_status': status_filter or 'All',
        'statuses': ProposalStatus.choices,
    })


@freelancer_required
def proposal_create_view(request):
    freelancer = request.user.profile
    if not freelancer.clients.exists():
        messages.warning(request, "Please add a client before creating proposals.")
        return redirect('clients:create')

    if request.method == 'POST':
        form = ProposalCreateForm(freelancer, request.POST)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.freelancer = freelancer
            proposal.save()

            descriptions = request.POST.getlist('item_desc[]')
            quantities = request.POST.getlist('item_qty[]')
            prices = request.POST.getlist('item_price[]')

            subtotal = Decimal('0.00')
            for desc, qty, price in zip(descriptions, quantities, prices):
                if desc.strip():
                    item_qty = Decimal(qty or '1')
                    item_price = Decimal(price or '0')
                    item_total = round(item_qty * item_price, 2)
                    ProposalLineItem.objects.create(
                        proposal=proposal,
                        description=desc.strip(),
                        quantity=item_qty,
                        unit_price=item_price,
                        total=item_total
                    )
                    subtotal += item_total

            proposal.subtotal = subtotal
            if proposal.tax_rate > Decimal('0.00'):
                proposal.tax_amount = round((subtotal * proposal.tax_rate) / Decimal('100.00'), 2)
            else:
                proposal.tax_amount = Decimal('0.00')
            proposal.total_amount = proposal.subtotal + proposal.tax_amount
            proposal.save(update_fields=['subtotal', 'tax_amount', 'total_amount'])

            messages.success(request, f"Proposal {proposal.proposal_number} created!")
            return redirect('invoicing:proposal_detail', pk=proposal.pk)
    else:
        year = timezone.now().year
        count = Proposal.objects.filter(freelancer=freelancer, proposal_number__startswith=f"PROP-{year}-").count() + 1
        prop_num = f"PROP-{year}-{count:04d}"
        today = timezone.now().date()
        valid_until = today + timedelta(days=30)
        form = ProposalCreateForm(freelancer, initial={
            'proposal_number': prop_num,
            'issue_date': today,
            'valid_until': valid_until,
            'currency': freelancer.currency,
        })

    return render(request, 'invoicing/proposals/create.html', {
        'form': form,
    })


@freelancer_required
def proposal_detail_view(request, pk):
    freelancer = request.user.profile
    proposal = get_object_or_404(Proposal, pk=pk, freelancer=freelancer)
    site_url = request.build_absolute_uri('/')[:-1]
    public_url = f"{site_url}/invoicing/proposals/public/{proposal.public_token}/"

    return render(request, 'invoicing/proposals/detail.html', {
        'proposal': proposal,
        'public_url': public_url,
    })


@freelancer_required
@require_POST
def proposal_convert_to_project_view(request, pk):
    freelancer = request.user.profile
    proposal = get_object_or_404(Proposal, pk=pk, freelancer=freelancer)

    if proposal.converted_project:
        messages.info(request, "This proposal has already been converted to a project.")
        return redirect('projects:detail', pk=proposal.converted_project.pk)

    # Create project from proposal
    project = Project.objects.create(
        client=proposal.client,
        title=proposal.title,
        description=f"{proposal.overview}\n\nScope of Work:\n{proposal.scope_of_work}",
        budget=proposal.total_amount,
        start_date=timezone.now().date(),
    )

    # Convert line items into milestones
    idx = 1
    for item in proposal.line_items.all():
        Milestone.objects.create(
            project=project,
            title=item.description,
            amount=item.total,
            due_date=timezone.now().date() + timedelta(days=14 * idx),
            order=idx,
            status=MilestoneStatus.PENDING
        )
        idx += 1

    proposal.status = ProposalStatus.ACCEPTED
    proposal.converted_project = project
    proposal.save(update_fields=['status', 'converted_project'])

    messages.success(request, f"Proposal successfully converted to Project '{project.title}' with {proposal.line_items.count()} milestones!")
    return redirect('projects:detail', pk=project.pk)


def proposal_public_view(request, public_token):
    proposal = get_object_or_404(Proposal, public_token=public_token)
    return render(request, 'invoicing/proposals/public.html', {
        'proposal': proposal,
        'freelancer': proposal.freelancer,
        'client': proposal.client,
    })


@require_POST
def proposal_client_action_view(request, public_token):
    proposal = get_object_or_404(Proposal, public_token=public_token)
    action = request.POST.get('action')

    if action == 'accept':
        proposal.status = ProposalStatus.ACCEPTED
        proposal.save(update_fields=['status'])
        messages.success(request, "Proposal accepted! Your freelancer has been notified.")
    elif action == 'decline':
        proposal.status = ProposalStatus.DECLINED
        proposal.save(update_fields=['status'])
        messages.info(request, "You have declined the proposal.")

    return redirect('invoicing:proposal_public', public_token=proposal.public_token)


