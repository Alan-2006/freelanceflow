from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.permissions import freelancer_required

from .forms import DeliverableSubmissionForm, MilestoneForm, ProjectCreateWizardForm, TaskForm
from .models import Milestone, MilestoneStatus, Project, ProjectStatus, Task, TaskStatus
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

    return render(request, 'projects/detail.html', {
        'project': project,
        'milestones': project.milestones.all(),
        'tasks_todo': tasks_todo,
        'tasks_progress': tasks_progress,
        'tasks_review': tasks_review,
        'tasks_done': tasks_done,
        'task_form': task_form,
        'milestone_form': milestone_form,
        'activities': project.activities.all()[:15],
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
