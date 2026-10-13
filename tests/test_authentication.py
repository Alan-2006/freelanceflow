import pytest
from django.urls import reverse

from apps.authentication.models import User, UserRole


@pytest.mark.django_db
class TestAuthentication:

    def test_signup_creates_user_and_profile(self, client):
        url = reverse('authentication:signup')
        payload = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'business_name': 'Jane Design Studio',
            'email': 'jane@studio.com',
            'currency': 'EUR',
            'password': 'SecurePassword123!',
        }
        response = client.post(url, payload)
        assert response.status_code == 302
        assert response.url == reverse('analytics:dashboard')

        user = User.objects.get(email='jane@studio.com')
        assert user.role == UserRole.FREELANCER
        assert user.first_name == 'Jane'
        assert user.profile.business_name == 'Jane Design Studio'
        assert user.profile.currency == 'EUR'

    def test_login_and_logout(self, client):
        User.objects.create_user(
            username='sam@flow.com',
            email='sam@flow.com',
            password='TestPassword123!',
            role=UserRole.FREELANCER
        )

        login_url = reverse('authentication:login')
        response = client.post(login_url, {
            'email': 'sam@flow.com',
            'password': 'TestPassword123!'
        })
        assert response.status_code == 302
        assert response.url == reverse('analytics:dashboard')

        logout_url = reverse('authentication:logout')
        response = client.get(logout_url)
        assert response.status_code == 302
        assert response.url == reverse('authentication:login')

    def test_theme_toggle(self, client):
        toggle_url = reverse('authentication:toggle_theme')
        response = client.post(toggle_url, HTTP_REFERER='/')
        session = client.session
        assert session.get('theme') == 'light'

        response = client.post(toggle_url, HTTP_REFERER='/')
        assert response.status_code == 302
        session = client.session
        assert session.get('theme') == 'dark'

    def test_google_login_unconfigured_redirects(self, client, settings):
        settings.GOOGLE_CLIENT_ID = ''
        login_url = reverse('authentication:google_login')
        response = client.get(login_url)
        assert response.status_code == 302
        assert response.url == reverse('authentication:login')

    def test_google_login_redirects_to_accounts_google(self, client, settings):
        settings.GOOGLE_CLIENT_ID = 'test-google-client-id-123'
        login_url = reverse('authentication:google_login')
        response = client.get(login_url)
        assert response.status_code == 302
        assert 'accounts.google.com/o/oauth2/v2/auth' in response.url
        assert 'test-google-client-id-123' in response.url

    def test_google_callback_oauth_code_flow(self, client, settings, monkeypatch):
        settings.GOOGLE_CLIENT_ID = 'test-client-id'
        settings.GOOGLE_CLIENT_SECRET = 'test-client-secret'

        # Set session state
        session = client.session
        session['google_oauth_state'] = 'test-secret-state'
        session.save()

        # Mock requests.post (token exchange) and requests.get (userinfo)
        class MockTokenResponse:
            status_code = 200
            def json(self):
                return {'access_token': 'mock-access-token'}

        class MockUserInfoResponse:
            status_code = 200
            def json(self):
                return {
                    'email': 'google.developer@example.com',
                    'given_name': 'Google',
                    'family_name': 'Dev',
                    'name': 'Google Dev',
                }

        import requests
        def mock_post(*args, **kwargs):
            return MockTokenResponse()
        def mock_get(*args, **kwargs):
            return MockUserInfoResponse()

        monkeypatch.setattr(requests, 'post', mock_post)
        monkeypatch.setattr(requests, 'get', mock_get)

        callback_url = reverse('authentication:google_callback')
        response = client.get(callback_url, {'code': 'mock_code', 'state': 'test-secret-state'})
        assert response.status_code == 302
        assert response.url == reverse('analytics:dashboard')

        user = User.objects.get(email='google.developer@example.com')
        assert user.first_name == 'Google'
        assert user.role == UserRole.FREELANCER
        assert user.profile.business_name == 'Google Dev'

    def test_google_callback_one_tap_credential(self, client, settings, monkeypatch):
        settings.GOOGLE_CLIENT_ID = 'test-client-id'

        class MockTokenInfoResponse:
            status_code = 200
            def json(self):
                return {
                    'aud': 'test-client-id',
                    'email': 'onetap.user@example.com',
                    'given_name': 'OneTap',
                    'family_name': 'User',
                    'name': 'OneTap User',
                }

        import requests
        def mock_get(*args, **kwargs):
            return MockTokenInfoResponse()

        monkeypatch.setattr(requests, 'get', mock_get)

        callback_url = reverse('authentication:google_callback')
        response = client.post(callback_url, {'credential': 'mock_jwt_token_payload'})
        assert response.status_code == 302
        assert response.url == reverse('analytics:dashboard')

        user = User.objects.get(email='onetap.user@example.com')
        assert user.first_name == 'OneTap'
        assert user.role == UserRole.FREELANCER
