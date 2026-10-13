from django.conf import settings


def freelanceflow_context(request):
    """Global template context for user profile, theme, and brand."""
    profile = None
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        profile = request.user.profile

    return {
        'APP_NAME': 'FreelanceFlow',
        'SITE_URL': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
        'freelancer_profile': profile,
        'user_theme': request.session.get('theme', 'dark') if hasattr(request, 'session') else 'dark',
        'GOOGLE_CLIENT_ID': getattr(settings, 'GOOGLE_CLIENT_ID', ''),
    }
