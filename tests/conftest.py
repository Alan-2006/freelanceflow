import pytest
from django.test import Client


@pytest.fixture
def client():
    return Client()

@pytest.fixture
def auth_client(client, db):
    from apps.authentication.models import User, UserRole
    user = User.objects.create_user(
        username='testfreelancer@example.com',
        email='testfreelancer@example.com',
        password='TestPassword123!',
        first_name='Alex',
        last_name='Dev',
        role=UserRole.FREELANCER
    )
    client.force_login(user)
    return client, user
