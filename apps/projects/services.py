from datetime import timedelta

from django.utils import timezone

from .models import ActivityLog, Milestone, MilestoneStatus, Project, Task, TaskStatus

PROJECT_TEMPLATES = {
    'web_development': {
        'name': 'Website Design & Development',
        'milestones': [
            {'title': 'Wireframes & UI Mockups', 'days_offset': 7, 'percent': 25},
            {'title': 'Frontend & Backend Implementation', 'days_offset': 21, 'percent': 40},
            {'title': 'Testing & Client Review', 'days_offset': 28, 'percent': 20},
            {'title': 'Production Launch & Handover', 'days_offset': 35, 'percent': 15},
        ]
    },
    'branding': {
        'name': 'Brand Identity & Guidelines',
        'milestones': [
            {'title': 'Moodboard & Visual Direction', 'days_offset': 5, 'percent': 30},
            {'title': 'Primary Logo & Variants Concept', 'days_offset': 14, 'percent': 40},
            {'title': 'Typography, Color Palette & Brand Book', 'days_offset': 21, 'percent': 30},
        ]
    },
    'consulting': {
        'name': 'Sprint Consulting & Audit',
        'milestones': [
            {'title': 'Discovery & Technical Audit', 'days_offset': 5, 'percent': 50},
            {'title': 'Architecture Recommendations & Final Roadmap', 'days_offset': 12, 'percent': 50},
        ]
    }
}

class ProjectService:

    @staticmethod
    def apply_template_to_project(project: Project, template_key: str):
        """Populate milestones for a project based on a pre-defined template."""
        template = PROJECT_TEMPLATES.get(template_key)
        if not template:
            return

        now = timezone.now().date()
        budget = float(project.budget)

        for idx, m_data in enumerate(template['milestones'], start=1):
            amount = round((budget * m_data['percent']) / 100, 2) if budget > 0 else 0.00
            due_date = now + timedelta(days=m_data['days_offset'])
            Milestone.objects.create(
                project=project,
                title=m_data['title'],
                amount=amount,
                due_date=due_date,
                order=idx,
                status=MilestoneStatus.PENDING
            )

    @staticmethod
    def log_activity(project: Project, actor_name: str, action_type: str, details: str, is_client_visible: bool = True):
        return ActivityLog.objects.create(
            project=project,
            actor_name=actor_name,
            action_type=action_type,
            details=details,
            is_client_visible=is_client_visible
        )

    @staticmethod
    def update_task_kanban(task_id: str, new_status: str, new_order: int = 1):
        task = Task.objects.get(id=task_id)
        if new_status in TaskStatus.values:
            task.status = new_status
            task.order = new_order
            task.save(update_fields=['status', 'order'])
        return task
