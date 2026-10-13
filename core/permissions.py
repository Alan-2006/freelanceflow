from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def freelancer_required(view_func):
    """Decorator to ensure only logged-in Freelancers can access the view."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('authentication:login')
        if not (request.user.is_freelancer or request.user.is_superuser):
            messages.error(request, "This area is reserved for freelancers.")
            return redirect('authentication:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
