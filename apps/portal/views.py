from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.projects.models import Milestone, MilestoneStatus, Project
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
        'activities': project.activities.filter(is_client_visible=True)[:10],
    })


@portal_client_required
def portal_milestone_review_view(request, milestone_pk):
    client = request.portal_client
    milestone = get_object_or_404(Milestone, pk=milestone_pk, project__client=client)
    freelancer_profile = client.freelancer

    return render(request, 'portal/milestone_review.html', {
        'client': client,
        'freelancer_profile': freelancer_profile,
        'milestone': milestone,
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

        ProjectService.log_activity(
            project=milestone.project,
            actor_name=client.name,
            action_type='MILESTONE_APPROVED',
            details=f"Client '{client.name}' approved milestone '{milestone.title}' (${milestone.amount}).",
            is_client_visible=True
        )
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


def portal_logout_view(request):
    request.session.pop('portal_client_id', None)
    messages.info(request, "You have been logged out of the client portal.")
    return render(request, 'portal/access_denied.html', {
        'message': 'You have successfully signed out of the Client Portal.'
    })
