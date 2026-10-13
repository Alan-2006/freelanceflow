from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path


def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('analytics:dashboard')
    return redirect('authentication:login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_redirect, name='home'),
    path('auth/', include('apps.authentication.urls')),
    path('clients/', include('apps.clients.urls')),
    path('projects/', include('apps.projects.urls')),
    path('invoicing/', include('apps.invoicing.urls')),
    path('payments/', include('apps.payments.urls')),
    path('reminders/', include('apps.reminders.urls')),
    path('analytics/', include('apps.analytics.urls')),
    path('portal/', include('apps.portal.urls')),
    path('api/v1/', include('apps.api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
