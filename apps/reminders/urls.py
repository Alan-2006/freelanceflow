from django.urls import path

from . import views

app_name = 'reminders'

urlpatterns = [
    path('', views.reminder_dashboard_view, name='dashboard'),
    path('run/', views.reminder_run_engine_view, name='run'),
    path('pause/<uuid:invoice_pk>/', views.reminder_toggle_pause_view, name='toggle_pause'),
    path('send-now/<uuid:invoice_pk>/', views.reminder_send_now_view, name='send_now'),
    path('track/open/<str:token>/', views.track_open_view, name='track_open'),
    path('track/click/<str:token>/', views.track_click_view, name='track_click'),
]
