from django.urls import path

from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list_view, name='list'),
    path('new/', views.project_create_wizard_view, name='create'),
    path('<uuid:pk>/', views.project_detail_view, name='detail'),
    path('<uuid:project_pk>/milestones/new/', views.milestone_create_view, name='milestone_create'),
    path('<uuid:project_pk>/tasks/new/', views.task_create_view, name='task_create'),
    path('tasks/<uuid:task_pk>/status/', views.task_update_status_htmx, name='task_update_status'),
    path('milestones/<uuid:pk>/submit/', views.milestone_submit_deliverable_view, name='milestone_submit'),
]
