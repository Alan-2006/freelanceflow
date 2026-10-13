import pytest
from django.urls import reverse

from apps.clients.models import Client, ReminderChannel


@pytest.mark.django_db
class TestClients:

    def test_client_crud_and_portal_token(self, auth_client):
        client_browser, user = auth_client
        profile = user.profile

        # Create client via form
        create_url = reverse('clients:create')
        payload = {
            'name': 'Sarah Connor',
            'company': 'Cyberdyne Systems',
            'email': 'sarah@cyberdyne.com',
            'phone': '+1 555-0199',
            'address': 'Los Angeles, CA',
            'currency': 'USD',
            'timezone': 'America/Los_Angeles',
            'preferred_channel': ReminderChannel.EMAIL,
            'tags': 'VIP, Enterprise',
            'notes': 'Key enterprise account',
        }
        response = client_browser.post(create_url, payload)
        assert response.status_code == 302

        client = Client.objects.get(email='sarah@cyberdyne.com')
        assert client.freelancer == profile
        assert client.portal_token is not None
        assert 'VIP' in client.tag_list
        assert client.reliability_score == 100
        assert client.reliability_badge['label'] == 'Gold'

        # Test detail view
        detail_url = reverse('clients:detail', kwargs={'pk': client.pk})
        response = client_browser.get(detail_url)
        assert response.status_code == 200
        assert 'Cyberdyne Systems' in response.content.decode()

    def test_client_search_and_filter(self, auth_client):
        client_browser, user = auth_client
        profile = user.profile

        Client.objects.create(
            freelancer=profile,
            name='Alice Smith',
            company='Alpha Corp',
            email='alice@alpha.com',
            tags='VIP'
        )
        Client.objects.create(
            freelancer=profile,
            name='Bob Jones',
            company='Beta LLC',
            email='bob@beta.com',
            tags='Retainer'
        )

        list_url = reverse('clients:list')

        # Search query
        res = client_browser.get(f"{list_url}?q=Alpha")
        assert 'Alpha Corp' in res.content.decode()
        assert 'Beta LLC' not in res.content.decode()

        # Tag filter
        res_tag = client_browser.get(f"{list_url}?tag=Retainer")
        assert 'Beta LLC' in res_tag.content.decode()
        assert 'Alpha Corp' not in res_tag.content.decode()
