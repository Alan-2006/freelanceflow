import pytest
from django.urls import reverse

from apps.clients.models import Client
from apps.projects.models import Project


@pytest.mark.django_db
class TestAPI:

    def test_api_clients_endpoint(self, auth_client):
        client_browser, user = auth_client
        profile = user.profile
        Client.objects.create(freelancer=profile, name='API Client 1', email='api1@client.com')

        url = reverse('api:client-list')
        response = client_browser.get(url)
        assert response.status_code == 200
        data = response.json()
        assert len(data['results']) == 1
        assert data['results'][0]['name'] == 'API Client 1'

    def test_api_projects_endpoint(self, auth_client):
        client_browser, user = auth_client
        profile = user.profile
        client = Client.objects.create(freelancer=profile, name='API Client 2', email='api2@client.com')
        Project.objects.create(client=client, title='API Project 1', budget=2000.00)

        url = reverse('api:project-list')
        response = client_browser.get(url)
        assert response.status_code == 200
        data = response.json()
        assert len(data['results']) == 1
        assert data['results'][0]['title'] == 'API Project 1'

    def test_api_docs_endpoint(self, client):
        docs_url = reverse('api:docs')
        response = client.get(docs_url)
        assert response.status_code == 200
        assert 'REST API Reference' in response.content.decode()
