from datetime import timedelta
from decimal import Decimal
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.invoicing.models import Invoice, InvoiceLineItem, InvoiceStatus
from apps.invoicing.services.calculator import InvoiceCalculator
from apps.invoicing.services.qr_generator import QRGeneratorService
from apps.projects.models import Attachment, Milestone, MilestoneFeedback, MilestoneStatus, Project
from apps.projects.services import ProjectService

from .decorators import portal_client_required
from .services import PortalAuthService



def portal_access_view(request, token):
    """Authenticate client portal session via secure signed token or tokenized link."""
    client = PortalAuthService.verify_magic_link_token(token)
    if not client:
        return render(request, 'portal/access_denied.html', {
            'message': 'Invalid or expired magic link. Please contact your freelancer for a new access link.'
        }, status=403)

    request.session['portal_client_id'] = str(client.id)
    messages.success(request, f"Welcome, {client.name}! Secure client portal session active.")
    return redirect('portal:dashboard')


@portal_client_required
def portal_dashboard_view(request):
    client = request.portal_client
    freelancer_profile = client.freelancer

    projects = client.projects.all()

    # Milestones requiring client review
    pending_reviews = Milestone.objects.filter(
        project__client=client,
        status=MilestoneStatus.SUBMITTED
    ).order_by('due_date')

    invoices = client.invoices.all() if hasattr(client, 'invoices') else []

    return render(request, 'portal/dashboard.html', {
        'client': client,
        'freelancer_profile': freelancer_profile,
        'projects': projects,
        'pending_reviews': pending_reviews,
        'invoices': invoices,
    })


@portal_client_required
def portal_project_detail_view(request, project_pk):
    client = request.portal_client
    project = get_object_or_404(Project, pk=project_pk, client=client)
    freelancer_profile = client.freelancer

    return render(request, 'portal/project_detail.html', {
        'client': client,
        'freelancer_profile': freelancer_profile,
        'project': project,
        'milestones': project.milestones.all(),
        'attachments': project.attachments.filter(is_shared_with_client=True),
        'activities': project.activities.filter(is_client_visible=True)[:20],
    })



@portal_client_required
def portal_milestone_review_view(request, milestone_pk):
    client = request.portal_client
    milestone = get_object_or_404(Milestone, pk=milestone_pk, project__client=client)
    freelancer_profile = client.freelancer
    feedbacks = milestone.feedbacks.all()

    return render(request, 'portal/milestone_review.html', {
        'client': client,
        'freelancer_profile': freelancer_profile,
        'milestone': milestone,
        'feedbacks': feedbacks,
    })


@portal_client_required
@require_POST
def portal_milestone_action_view(request, milestone_pk):
    client = request.portal_client
    milestone = get_object_or_404(Milestone, pk=milestone_pk, project__client=client)
    action = request.POST.get('action')

    if action == 'approve':
        milestone.status = MilestoneStatus.APPROVED
        milestone.approved_at = timezone.now()
        milestone.client_feedback = ''
        milestone.save()

        # Log MilestoneFeedback record
        MilestoneFeedback.objects.create(
            milestone=milestone,
            author_name=client.name,
            is_client=True,
            feedback_text="Milestone approved by client.",
            status_at_time=MilestoneStatus.APPROVED
        )

        ProjectService.log_activity(
            project=milestone.project,
            actor_name=client.name,
            action_type='MILESTONE_APPROVED',
            details=f"Client '{client.name}' approved milestone '{milestone.title}' (${milestone.amount}).",
            is_client_visible=True
        )

        # Auto-generate or retrieve milestone invoice
        existing_line = milestone.invoice_lines.first()
        invoice = existing_line.invoice if existing_line else None
        if not invoice and milestone.amount > Decimal('0.00'):
            freelancer = milestone.project.client.freelancer
            inv_number = InvoiceCalculator.generate_next_invoice_number(freelancer)
            due_date = timezone.now().date() + timedelta(days=freelancer.default_payment_terms_days)
            invoice = Invoice.objects.create(
                freelancer=freelancer,
                client=milestone.project.client,
                project=milestone.project,
                invoice_number=inv_number,
                issue_date=timezone.now().date(),
                due_date=due_date,
                currency=milestone.project.client.currency or freelancer.currency,
                status=InvoiceStatus.SENT,
                notes=f"Auto-generated invoice for approved milestone '{milestone.title}'."
            )
            InvoiceLineItem.objects.create(
                invoice=invoice,
                description=f"Milestone: {milestone.title}",
                quantity=Decimal('1.00'),
                unit_price=milestone.amount,
                milestone=milestone
            )
            InvoiceCalculator.recalculate_invoice_totals(invoice)

        if invoice and invoice.balance_due > Decimal('0.00'):
            messages.success(request, f"Milestone '{milestone.title}' approved! Invoice {invoice.invoice_number} is generated. You can complete payment below.")
            return redirect('payments:checkout', invoice_pk=invoice.pk)

        messages.success(request, f"Milestone '{milestone.title}' has been successfully approved! Thank you.")
        return redirect('portal:project_detail', project_pk=milestone.project.pk)

    elif action == 'reject':
        feedback = request.POST.get('client_feedback', '').strip()
        if not feedback:
            messages.error(request, "Please provide comments explaining the changes requested.")
            return redirect('portal:milestone_review', milestone_pk=milestone.pk)

        milestone.status = MilestoneStatus.REJECTED
        milestone.client_feedback = feedback
        milestone.save()

        # Log MilestoneFeedback record
        MilestoneFeedback.objects.create(
            milestone=milestone,
            author_name=client.name,
            is_client=True,
            feedback_text=feedback,
            status_at_time=MilestoneStatus.REJECTED
        )

        ProjectService.log_activity(
            project=milestone.project,
            actor_name=client.name,
            action_type='CHANGES_REQUESTED',
            details=f"Client '{client.name}' requested changes on '{milestone.title}': {feedback}",
            is_client_visible=True
        )
        messages.info(request, f"Feedback submitted for '{milestone.title}'. Your freelancer has been notified.")
        return redirect('portal:project_detail', project_pk=milestone.project.pk)

    return redirect('portal:dashboard')


@portal_client_required
def portal_invoice_detail_view(request, invoice_pk):
    client = request.portal_client
    invoice = get_object_or_404(Invoice, pk=invoice_pk, client=client)
    invoice.record_view()

    site_url = request.build_absolute_uri('/')[:-1]
    qr_code_base64 = QRGeneratorService.generate_invoice_qr_base64(invoice, site_url)

    return render(request, 'portal/invoice_detail.html', {
        'client': client,
        'freelancer_profile': invoice.freelancer,
        'invoice': invoice,
        'qr_code_base64': qr_code_base64,
        'site_url': site_url,
    })


@portal_client_required
@require_POST
def portal_project_upload_view(request, project_pk):
    client = request.portal_client
    project = get_object_or_404(Project, pk=project_pk, client=client)
    uploaded_file = request.FILES.get('file')
    label = request.POST.get('name', '').strip()

    if uploaded_file:
        att = Attachment.objects.create(
            project=project,
            file=uploaded_file,
            name=label or uploaded_file.name,
            file_size_bytes=uploaded_file.size,
            is_shared_with_client=True
        )
        ProjectService.log_activity(
            project=project,
            actor_name=client.name,
            action_type='CLIENT_FILE_UPLOADED',
            details=f"Client '{client.name}' uploaded file '{att.name}'.",
            is_client_visible=True
        )
        messages.success(request, f"File '{att.name}' shared with your freelancer.")
    else:
        messages.error(request, "Please choose a valid file to upload.")

    return redirect('portal:project_detail', project_pk=project.pk)


@portal_client_required
@require_POST
def portal_project_comment_view(request, project_pk):
    client = request.portal_client
    project = get_object_or_404(Project, pk=project_pk, client=client)
    comment = request.POST.get('comment', '').strip()

    if comment:
        ProjectService.log_activity(
            project=project,
            actor_name=client.name,
            action_type='CLIENT_COMMENT',
            details=comment,
            is_client_visible=True
        )
        messages.success(request, "Your note was added to the project.")
    return redirect('portal:project_detail', project_pk=project.pk)


def portal_logout_view(request):
    request.session.pop('portal_client_id', None)
    messages.info(request, "You have been logged out of the client portal.")
    return render(request, 'portal/access_denied.html', {
        'message': 'You have successfully signed out of the Client Portal.'
    })

