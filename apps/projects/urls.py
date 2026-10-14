from django.urls import path

from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list_view, name='list'),
    path('new/', views.project_create_wizard_view, name='create'),
    path('timesheets/', views.timesheet_list_view, name='timesheets'),
    path('timesheets/new/', views.time_entry_create_view, name='time_entry_create'),
    path('timesheets/timer-save/', views.time_entry_save_timer_view, name='timer_save'),
    path('timesheets/<uuid:pk>/delete/', views.time_entry_delete_view, name='time_entry_delete'),
    path('<uuid:pk>/', views.project_detail_view, name='detail'),
    path('<uuid:project_pk>/milestones/new/', views.milestone_create_view, name='milestone_create'),
    path('<uuid:project_pk>/tasks/new/', views.task_create_view, name='task_create'),
    path('tasks/<uuid:task_pk>/status/', views.task_update_status_htmx, name='task_update_status'),
    path('milestones/<uuid:pk>/submit/', views.milestone_submit_deliverable_view, name='milestone_submit'),
    path('<uuid:project_pk>/attachments/upload/', views.attachment_upload_view, name='attachment_upload'),
    path('attachments/<uuid:pk>/delete/', views.attachment_delete_view, name='attachment_delete'),
    path('<uuid:pk>/comment/', views.project_comment_view, name='comment'),
]

