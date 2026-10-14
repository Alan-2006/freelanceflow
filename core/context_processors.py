from django.conf import settings


def freelanceflow_context(request):
    """Global template context for user profile, theme, and brand."""
    profile = None
    active_projects = []
    unread_notifications_count = 0
    recent_notifications = []

    if request.user.is_authenticated:
        if hasattr(request.user, 'profile'):
            profile = request.user.profile
            try:
                from apps.projects.models import Project
                active_projects = list(Project.objects.filter(client__freelancer=profile).only('id', 'title'))
            except Exception:
                active_projects = []

        try:
            from apps.authentication.models import Notification
            unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()
            recent_notifications = list(Notification.objects.filter(user=request.user).order_by('-created_at')[:5])
        except Exception:
            unread_notifications_count = 0
            recent_notifications = []

    return {
        'APP_NAME': 'FreelanceFlow',
        'SITE_URL': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
        'freelancer_profile': profile,
        'active_projects': active_projects,
        'unread_notifications_count': unread_notifications_count,
        'recent_notifications': recent_notifications,
        'user_theme': request.session.get('theme', 'dark') if hasattr(request, 'session') else 'dark',
        'GOOGLE_CLIENT_ID': getattr(settings, 'GOOGLE_CLIENT_ID', ''),
    }


