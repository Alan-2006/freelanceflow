import pytest
from django.urls import reverse

from apps.clients.models import Client
from apps.projects.models import Milestone, MilestoneStatus, Project


@pytest.mark.django_db
class TestClientPortal:

    def test_portal_magic_link_access(self, client, auth_client):
        _, user = auth_client
        profile = user.profile

        portal_client = Client.objects.create(
            freelancer=profile,
            name='Arthur Dent',
            company='Megadodo Publications',
            email='arthur@guide.com'
        )
        token = portal_client.get_or_create_portal_token()

        access_url = reverse('portal:access', kwargs={'token': token})
        response = client.get(access_url)
        assert response.status_code == 302
        assert response.url == reverse('portal:dashboard')

        # Check session
        assert client.session.get('portal_client_id') == str(portal_client.id)

        # Check dashboard loads cleanly
        dash_response = client.get(reverse('portal:dashboard'))
        assert dash_response.status_code == 200
        assert 'Megadodo Publications' in dash_response.content.decode()

    def test_portal_access_denied_invalid_token(self, client):
        bad_url = reverse('portal:access', kwargs={'token': 'invalid_secret_token_123'})
        response = client.get(bad_url)
        assert response.status_code == 403
        assert 'Invalid or expired magic link' in response.content.decode()

    def test_client_milestone_approval(self, client, auth_client):
        _, user = auth_client
        profile = user.profile

        portal_client = Client.objects.create(
            freelancer=profile,
            name='Ford Prefect',
            company='Sub-Etha Sensation',
            email='ford@subetha.com'
        )
        project = Project.objects.create(
            client=portal_client,
            title='Hitchhiker App',
            budget=4200.00
        )
        milestone = Milestone.objects.create(
            project=project,
            title='Electronic Thumb API',
            amount=2100.00,
            due_date='2026-10-30',
            status=MilestoneStatus.SUBMITTED,
            deliverable_notes='API live and tested on staging'
        )

        # Authenticate portal session
        session = client.session
        session['portal_client_id'] = str(portal_client.id)
        session.save()

        # Approve milestone
        action_url = reverse('portal:milestone_action', kwargs={'milestone_pk': milestone.pk})
        response = client.post(action_url, {'action': 'approve'})
        assert response.status_code == 302

        milestone.refresh_from_db()
        assert milestone.status == MilestoneStatus.APPROVED
        assert milestone.approved_at is not None
        assert milestone.feedbacks.count() >= 1
        assert milestone.invoice_lines.exists()

    def test_client_milestone_changes_requested(self, client, auth_client):
        _, user = auth_client
        profile = user.profile

        portal_client = Client.objects.create(
            freelancer=profile,
            name='Trillian Astra',
            company='Heart of Gold Labs',
            email='trillian@heartofgold.com'
        )
        project = Project.objects.create(
            client=portal_client,
            title='Infinite Improbability Engine',
            budget=8000.00
        )
        milestone = Milestone.objects.create(
            project=project,
            title='Quantum Drive Calibrations',
            amount=4000.00,
            due_date='2026-11-05',
            status=MilestoneStatus.SUBMITTED,
            deliverable_notes='Calibrations ready'
        )

        session = client.session
        session['portal_client_id'] = str(portal_client.id)
        session.save()

        # Reject with feedback
        action_url = reverse('portal:milestone_action', kwargs={'milestone_pk': milestone.pk})
        response = client.post(action_url, {
            'action': 'reject',
            'client_feedback': 'Trajectory error threshold must be under 0.001%'
        })
        assert response.status_code == 302

        milestone.refresh_from_db()
        assert milestone.status == MilestoneStatus.REJECTED
        assert 'Trajectory error' in milestone.client_feedback
