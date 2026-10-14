from decimal import Decimal

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.permissions import freelancer_required

from .forms import (
    AttachmentForm,
    DeliverableSubmissionForm,
    MilestoneForm,
    ProjectCreateWizardForm,
    TaskForm,
    TimeEntryForm,
)
from .models import (
    Attachment,
    Milestone,
    MilestoneStatus,
    Project,
    ProjectStatus,
    Task,
    TaskStatus,
    TimeEntry,
)
from .services import ProjectService


@freelancer_required
def project_list_view(request):
    freelancer = request.user.profile
    projects = Project.objects.filter(client__freelancer=freelancer)

    status_filter = request.GET.get('status')
    if status_filter and status_filter in ProjectStatus.values:
        projects = projects.filter(status=status_filter)

    return render(request, 'projects/list.html', {
        'projects': projects,
        'current_status': status_filter or 'All',
        'statuses': ProjectStatus.choices,
    })


@freelancer_required
def project_create_wizard_view(request):
    freelancer = request.user.profile

    if not freelancer.clients.exists():
        messages.warning(request, "Please create at least one client before launching a project.")
        return redirect('clients:create')

    if request.method == 'POST':
        form = ProjectCreateWizardForm(freelancer, request.POST)
        if form.is_valid():
            project = form.save()
            template_key = form.cleaned_data.get('template_type')
            if template_key:
                ProjectService.apply_template_to_project(project, template_key)

            ProjectService.log_activity(
                project=project,
                actor_name=freelancer.display_name,
                action_type='PROJECT_CREATED',
                details=f"Project '{project.title}' initialized."
            )
            messages.success(request, f"Project '{project.title}' launched successfully!")
            return redirect('projects:detail', pk=project.pk)
    else:
        form = ProjectCreateWizardForm(freelancer)

    return render(request, 'projects/wizard.html', {
        'form': form,
    })


@freelancer_required
def project_detail_view(request, pk):
    freelancer = request.user.profile
    project = get_object_or_404(Project, pk=pk, client__freelancer=freelancer)

    # Kanban tasks categorized by status
    tasks_todo = project.tasks.filter(status=TaskStatus.TODO)
    tasks_progress = project.tasks.filter(status=TaskStatus.IN_PROGRESS)
    tasks_review = project.tasks.filter(status=TaskStatus.REVIEW)
    tasks_done = project.tasks.filter(status=TaskStatus.DONE)

    task_form = TaskForm(project)
    milestone_form = MilestoneForm()
    attachment_form = AttachmentForm()

    return render(request, 'projects/detail.html', {
        'project': project,
        'milestones': project.milestones.all(),
        'tasks_todo': tasks_todo,
        'tasks_progress': tasks_progress,
        'tasks_review': tasks_review,
        'tasks_done': tasks_done,
        'task_form': task_form,
        'milestone_form': milestone_form,
        'attachment_form': attachment_form,
        'attachments': project.attachments.all(),
        'time_entries': project.time_entries.all()[:10],
        'activities': project.activities.all()[:20],
    })


@freelancer_required
@require_POST
def milestone_create_view(request, project_pk):
    freelancer = request.user.profile
    project = get_object_or_404(Project, pk=project_pk, client__freelancer=freelancer)

    form = MilestoneForm(request.POST)
    if form.is_valid():
        milestone = form.save(commit=False)
        milestone.project = project
        milestone.order = project.milestones.count() + 1
        milestone.save()
        messages.success(request, f"Milestone '{milestone.title}' added.")
    return redirect('projects:detail', pk=project.pk)


@freelancer_required
@require_POST
def task_create_view(request, project_pk):
    freelancer = request.user.profile
    project = get_object_or_404(Project, pk=project_pk, client__freelancer=freelancer)

    form = TaskForm(project, request.POST)
    if form.is_valid():
        task = form.save(commit=False)
        task.project = project
        task.save()
        messages.success(request, f"Task '{task.title}' added to Kanban.")
    return redirect('projects:detail', pk=project.pk)


@freelancer_required
@require_POST
def task_update_status_htmx(request, task_pk):
    """HTMX endpoint for dragging/moving Kanban cards between columns."""
    freelancer = request.user.profile
    task = get_object_or_404(Task, pk=task_pk, project__client__freelancer=freelancer)

    new_status = request.POST.get('status')
    if new_status in TaskStatus.values:
        task.status = new_status
        task.save(update_fields=['status'])

    # Return the updated task card HTML partial
    return render(request, 'projects/partials/kanban_card.html', {'task': task})


@freelancer_required
def milestone_submit_deliverable_view(request, pk):
    freelancer = request.user.profile
    milestone = get_object_or_404(Milestone, pk=pk, project__client__freelancer=freelancer)

    if request.method == 'POST':
        form = DeliverableSubmissionForm(request.POST, request.FILES, instance=milestone)
        if form.is_valid():
            m = form.save(commit=False)
            m.status = MilestoneStatus.SUBMITTED
            m.save()

            ProjectService.log_activity(
                project=milestone.project,
                actor_name=freelancer.display_name,
                action_type='DELIVERABLE_SUBMITTED',
                details=f"Milestone '{milestone.title}' submitted for client review."
            )
            messages.success(request, f"Milestone '{milestone.title}' submitted for review!")
            return redirect('projects:detail', pk=milestone.project.pk)
    else:
        form = DeliverableSubmissionForm(instance=milestone)

    return render(request, 'projects/deliverable_form.html', {
        'milestone': milestone,
        'form': form
    })


# --- Time Tracking & Timesheets ---

@freelancer_required
def timesheet_list_view(request):
    freelancer = request.user.profile
    entries = TimeEntry.objects.filter(project__client__freelancer=freelancer).select_related('project', 'task', 'project__client')

    project_filter = request.GET.get('project')
    if project_filter:
        entries = entries.filter(project__id=project_filter)

    billable_filter = request.GET.get('billable')
    if billable_filter == 'yes':
        entries = entries.filter(is_billable=True)
    elif billable_filter == 'no':
        entries = entries.filter(is_billable=False)

    invoiced_filter = request.GET.get('invoiced')
    if invoiced_filter == 'yes':
        entries = entries.filter(is_invoiced=True)
    elif invoiced_filter == 'no':
        entries = entries.filter(is_invoiced=False)

    total_seconds = sum(e.duration_seconds for e in entries)
    total_hours = round(total_seconds / 3600, 2)
    unbilled_entries = entries.filter(is_billable=True, is_invoiced=False)
    unbilled_amount = sum(e.billable_amount for e in unbilled_entries)

    form = TimeEntryForm(freelancer)
    projects = freelancer.projects.all() if hasattr(freelancer, 'projects') else Project.objects.filter(client__freelancer=freelancer)

    return render(request, 'projects/timesheets.html', {
        'entries': entries,
        'total_hours': total_hours,
        'unbilled_amount': unbilled_amount,
        'form': form,
        'projects': projects,
        'current_project': project_filter,
    })


@freelancer_required
@require_POST
def time_entry_create_view(request):
    freelancer = request.user.profile
    form = TimeEntryForm(freelancer, request.POST)
    if form.is_valid():
        entry = form.save(commit=False)
        hours = form.cleaned_data.get('hours', Decimal('1.0'))
        entry.duration_seconds = int(hours * 3600)
        if not entry.hourly_rate:
            entry.hourly_rate = entry.project.hourly_rate or Decimal('0.00')
        entry.save()
        messages.success(request, f"Logged {hours} hrs to {entry.project.title}.")
    else:
        messages.error(request, "Failed to log time entry. Please check the values entered.")
    return redirect('projects:timesheets')


@freelancer_required
@require_POST
def time_entry_save_timer_view(request):
    """Endpoint called by the persistent navbar timer to log elapsed seconds directly."""
    freelancer = request.user.profile
    project_id = request.POST.get('project_id')
    task_id = request.POST.get('task_id')
    seconds = int(request.POST.get('seconds', 0))
    note = request.POST.get('note', '').strip()
    is_billable = request.POST.get('is_billable', 'true') == 'true'

    if not project_id or seconds <= 0:
        return JsonResponse({'success': False, 'error': 'Invalid project or duration.'}, status=400)

    project = get_object_or_404(Project, pk=project_id, client__freelancer=freelancer)
    task = project.tasks.filter(pk=task_id).first() if task_id else None

    entry = TimeEntry.objects.create(
        project=project,
        task=task,
        duration_seconds=seconds,
        hourly_rate=project.hourly_rate or Decimal('0.00'),
        is_billable=is_billable,
        note=note or f"Timer session on {project.title}",
        start_time=timezone.now() - timezone.timedelta(seconds=seconds),
        end_time=timezone.now()
    )

    minutes = max(1, seconds // 60)
    return JsonResponse({
        'success': True,
        'entry_id': str(entry.id),
        'message': f"Saved {minutes}m to {project.title}!"
    })


@freelancer_required
@require_POST
def time_entry_delete_view(request, pk):
    freelancer = request.user.profile
    entry = get_object_or_404(TimeEntry, pk=pk, project__client__freelancer=freelancer)
    if entry.is_invoiced:
        messages.error(request, "Cannot delete an entry that has already been billed on an invoice.")
    else:
        entry.delete()
        messages.success(request, "Time entry removed.")
    return redirect('projects:timesheets')


# --- Attachments & Collaboration ---

@freelancer_required
@require_POST
def attachment_upload_view(request, project_pk):
    freelancer = request.user.profile
    project = get_object_or_404(Project, pk=project_pk, client__freelancer=freelancer)

    form = AttachmentForm(request.POST, request.FILES)
    if form.is_valid():
        att = form.save(commit=False)
        att.project = project
        if att.file:
            att.file_size_bytes = att.file.size
        if not att.name:
            att.name = att.file.name
        att.save()

        ProjectService.log_activity(
            project=project,
            actor_name=freelancer.display_name,
            action_type='FILE_UPLOADED',
            details=f"Uploaded file '{att.name}'.",
            is_client_visible=att.is_shared_with_client
        )
        messages.success(request, f"File '{att.name}' attached to project.")
    else:
        messages.error(request, "Failed to upload file. Please select a valid file.")

    return redirect('projects:detail', pk=project.pk)


@freelancer_required
@require_POST
def attachment_delete_view(request, pk):
    freelancer = request.user.profile
    att = get_object_or_404(Attachment, pk=pk, project__client__freelancer=freelancer)
    project_pk = att.project.pk
    name = att.name
    att.delete()
    messages.success(request, f"Attachment '{name}' removed.")
    return redirect('projects:detail', pk=project_pk)


@freelancer_required
@require_POST
def project_comment_view(request, pk):
    freelancer = request.user.profile
    project = get_object_or_404(Project, pk=pk, client__freelancer=freelancer)
    comment = request.POST.get('comment', '').strip()
    is_client_visible = request.POST.get('is_client_visible', 'true') == 'true'

    if comment:
        ProjectService.log_activity(
            project=project,
            actor_name=freelancer.display_name,
            action_type='COMMENT_POSTED',
            details=comment,
            is_client_visible=is_client_visible
        )
        messages.success(request, "Update posted to project feed.")
    return redirect('projects:detail', pk=project.pk)

