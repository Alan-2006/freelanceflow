from functools import wraps

from django.shortcuts import render

from apps.clients.models import Client


def portal_client_required(view_func):
    """Decorator ensuring that the visitor has an active Client Portal session."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        client_id = request.session.get('portal_client_id')
        if not client_id:
            return render(request, 'portal/access_denied.html', {
                'message': 'Your client portal access session has expired or is invalid. Please request a fresh magic link.'
            }, status=403)

        client = Client.objects.filter(id=client_id).first()
        if not client:
            return render(request, 'portal/access_denied.html', {
                'message': 'Client record not found.'
            }, status=404)

        request.portal_client = client
        return view_func(request, *args, **kwargs)
    return _wrapped_view
