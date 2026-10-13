from django.urls import path

from . import views

app_name = 'authentication'

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('theme/toggle/', views.toggle_theme_view, name='toggle_theme'),
    path('google/login/', views.google_login_view, name='google_login'),
    path('google/callback/', views.google_callback_view, name='google_callback'),
]
