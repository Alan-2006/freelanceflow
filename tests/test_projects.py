import pytest
from django.urls import reverse

from apps.clients.models import Client
from apps.projects.models import Milestone, MilestoneStatus, Project, Task, TaskStatus


@pytest.mark.django_db
class TestProjects:

    def test_project_wizard_creates_project_and_template_milestones(self, auth_client):
        client_browser, user = auth_client
        profile = user.profile

        client = Client.objects.create(
            freelancer=profile,
            name='Bruce Wayne',
            company='Wayne Enterprises',
            email='bruce@wayne.com'
        )

        wizard_url = reverse('projects:create')
        payload = {
            'client': str(client.pk),
            'title': 'Wayne Enterprises Redesign',
            'description': 'Full redesign and CMS integration',
            'billing_type': 'Fixed',
            'budget': '10000.00',
            'hourly_rate': '100.00',
            'start_date': '2026-10-01',
            'end_date': '2026-11-15',
            'color_code': '#6366F1',
            'template_type': 'web_development',
        }

        response = client_browser.post(wizard_url, payload)
        assert response.status_code == 302

        project = Project.objects.get(title='Wayne Enterprises Redesign')
        assert project.client == client
        assert project.milestones.count() == 4
        assert project.budget == 10000.00

        # Check template percentage split (25%, 40%, 20%, 15%)
        m1 = project.milestones.get(order=1)
        assert m1.amount == 2500.00
        assert m1.status == MilestoneStatus.PENDING

    def test_kanban_task_status_htmx_update(self, auth_client):
        client_browser, user = auth_client
        profile = user.profile

        client = Client.objects.create(
            freelancer=profile,
            name='Clark Kent',
            company='Daily Planet',
            email='clark@planet.com'
        )
        project = Project.objects.create(
            client=client,
            title='Planet Portal',
            budget=5000.00
        )
        task = Task.objects.create(
            project=project,
            title='Setup database schema',
            status=TaskStatus.TODO,
            estimated_hours=4.0
        )

        update_url = reverse('projects:task_update_status', kwargs={'task_pk': task.pk})
        response = client_browser.post(update_url, {'status': TaskStatus.IN_PROGRESS})
        assert response.status_code == 200

        task.refresh_from_db()
        assert task.status == TaskStatus.IN_PROGRESS

    def test_milestone_deliverable_submission(self, auth_client):
        client_browser, user = auth_client
        profile = user.profile

        client = Client.objects.create(
            freelancer=profile,
            name='Diana Prince',
            company='Themyscira Arts',
            email='diana@art.com'
        )
        project = Project.objects.create(
            client=client,
            title='Exhibition Gallery',
            budget=3000.00
        )
        milestone = Milestone.objects.create(
            project=project,
            title='Frontend Prototypes',
            amount=1500.00,
            due_date='2026-10-20',
            status=MilestoneStatus.PENDING
        )

        submit_url = reverse('projects:milestone_submit', kwargs={'pk': milestone.pk})
        response = client_browser.post(submit_url, {
            'deliverable_notes': 'Prototype live on https://staging.gallery.dev with credentials demo/demo'
        })
        assert response.status_code == 302

        milestone.refresh_from_db()
        assert milestone.status == MilestoneStatus.SUBMITTED
        assert 'staging.gallery.dev' in milestone.deliverable_notes
