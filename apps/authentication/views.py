from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import FreelancerProfileForm, FreelancerSignUpForm, LoginForm


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('analytics:dashboard')

    if request.method == 'POST':
        form = FreelancerSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to FreelanceFlow, {user.first_name or user.username}!")
            return redirect('analytics:dashboard')
    else:
        form = FreelancerSignUpForm()

    return render(request, 'authentication/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('analytics:dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.user
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next') or 'analytics:dashboard'
            return redirect(next_url)
    else:
        form = LoginForm()

    return render(request, 'authentication/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('authentication:login')


@login_required
def profile_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = FreelancerProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile and branding settings have been updated.")
            return redirect('authentication:profile')
    else:
        form = FreelancerProfileForm(instance=profile)

    return render(request, 'authentication/profile.html', {
        'form': form,
        'profile': profile
    })


@require_POST
def toggle_theme_view(request):
    """Toggle between dark and light theme in user session."""
    current_theme = request.session.get('theme', 'dark')
    new_theme = 'light' if current_theme == 'dark' else 'dark'
    request.session['theme'] = new_theme

    if request.headers.get('HX-Request'):
        return HttpResponse(status=204)
    return redirect(request.META.get('HTTP_REFERER', '/'))


def google_login_view(request):
    """Initiate Google OAuth 2.0 authorization code flow."""
    import secrets
    import urllib.parse

    from django.conf import settings

    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '').strip()
    if not client_id:
        messages.warning(
            request,
            "Google Authentication is not configured yet. Please configure GOOGLE_CLIENT_ID in environment variables."
        )
        return redirect('authentication:login')

    state = secrets.token_urlsafe(32)
    request.session['google_oauth_state'] = state

    redirect_uri = getattr(settings, 'GOOGLE_OAUTH_REDIRECT_URI', '').strip()
    if not redirect_uri:
        redirect_uri = request.build_absolute_uri(reverse('authentication:google_callback'))
        if request.is_secure() or request.headers.get('x-forwarded-proto') == 'https':
            redirect_uri = redirect_uri.replace('http://', 'https://')

    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'online',
        'prompt': 'select_account',
    }
    google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return redirect(google_auth_url)


def google_callback_view(request):
    """Handle Google OAuth callback (standard code redirect or GSI token post)."""
    import requests
    from django.conf import settings

    from .models import FreelancerProfile, User, UserRole

    user_info = None

    # Case 1: POST from Google Identity Services button / One-Tap
    if request.method == 'POST' and 'credential' in request.POST:
        credential = request.POST.get('credential')
        try:
            resp = requests.get(
                'https://oauth2.googleapis.com/tokeninfo',
                params={'id_token': credential},
                timeout=10
            )
            if resp.status_code == 200:
                payload = resp.json()
                client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '').strip()
                if client_id and payload.get('aud') != client_id:
                    messages.error(request, "Google authentication audience mismatch.")
                    return redirect('authentication:login')
                user_info = payload
            else:
                messages.error(request, "Failed to verify Google credential token.")
                return redirect('authentication:login')
        except Exception as e:
            messages.error(request, f"Google authentication error: {str(e)}")
            return redirect('authentication:login')

    # Case 2: Standard OAuth2 Code Flow (GET)
    else:
        error = request.GET.get('error')
        if error:
            messages.error(request, f"Google login was cancelled or failed: {error}")
            return redirect('authentication:login')

        code = request.GET.get('code')
        state = request.GET.get('state')
        saved_state = request.session.get('google_oauth_state')

        if not code:
            messages.error(request, "No authorization code returned from Google.")
            return redirect('authentication:login')

        if not saved_state or state != saved_state:
            messages.error(request, "Invalid OAuth state token. Possible CSRF attack detected.")
            return redirect('authentication:login')

        request.session.pop('google_oauth_state', None)

        client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '').strip()
        client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', '').strip()
        redirect_uri = getattr(settings, 'GOOGLE_OAUTH_REDIRECT_URI', '').strip()
        if not redirect_uri:
            redirect_uri = request.build_absolute_uri(reverse('authentication:google_callback'))
            if request.is_secure() or request.headers.get('x-forwarded-proto') == 'https':
                redirect_uri = redirect_uri.replace('http://', 'https://')

        try:
            token_resp = requests.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'code': code,
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'redirect_uri': redirect_uri,
                    'grant_type': 'authorization_code',
                },
                headers={'Accept': 'application/json'},
                timeout=10
            )
            token_data = token_resp.json()
            if 'error' in token_data:
                err_msg = token_data.get('error_description', token_data['error'])
                messages.error(request, f"Google token exchange failed: {err_msg}")
                return redirect('authentication:login')

            access_token = token_data.get('access_token')
            userinfo_resp = requests.get(
                'https://openidconnect.googleapis.com/v1/userinfo',
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10
            )
            if userinfo_resp.status_code != 200:
                messages.error(request, "Failed to retrieve user profile from Google.")
                return redirect('authentication:login')
            user_info = userinfo_resp.json()
        except Exception as e:
            messages.error(request, f"Error communicating with Google servers: {str(e)}")
            return redirect('authentication:login')

    if not user_info or not user_info.get('email'):
        messages.error(request, "Could not obtain a verified email address from Google.")
        return redirect('authentication:login')

    email = user_info['email'].strip().lower()
    first_name = user_info.get('given_name') or user_info.get('name', '').split(' ')[0] or ''
    last_name = user_info.get('family_name') or ''
    full_name = user_info.get('name') or f"{first_name} {last_name}".strip()

    user = User.objects.filter(email__iexact=email).first()
    if not user:
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        user = User.objects.create(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            role=UserRole.FREELANCER,
        )
        user.set_unusable_password()
        user.save()

    profile, _ = FreelancerProfile.objects.get_or_create(user=user)
    if not profile.business_name:
        profile.business_name = full_name or user.username
        profile.save()

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    messages.success(request, f"Successfully signed in with Google as {user.email}!")
    return redirect('analytics:dashboard')


@login_required
def notifications_list_view(request):
    """Full notifications center view."""
    filter_type = request.GET.get('filter', 'all')
    notifications = Notification.objects.filter(user=request.user)

    if filter_type == 'unread':
        notifications = notifications.filter(is_read=False)

    return render(request, 'authentication/notifications.html', {
        'notifications': notifications,
        'filter_type': filter_type,
    })


@login_required
def notification_mark_read_view(request, pk):
    """Mark a notification as read and redirect to target URL or back."""
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save()

    if request.headers.get('HX-Request') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok'})

    if notif.url:
        return redirect(notif.url)
    return redirect(request.META.get('HTTP_REFERER', 'authentication:notifications_list'))


@login_required
@require_POST
def notification_mark_all_read_view(request):
    """Mark all notifications as read."""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect(request.META.get('HTTP_REFERER', 'authentication:notifications_list'))


@login_required
def change_password_view(request):
    """Dedicated password change view."""
    from django.contrib.auth import update_session_auth_hash
    from django.contrib.auth.forms import PasswordChangeForm

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated!")
            return redirect('authentication:profile')
        else:
            messages.error(request, "Please correct the password errors below.")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'authentication/change_password.html', {'form': form})

