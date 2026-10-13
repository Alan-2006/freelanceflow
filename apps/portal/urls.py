from django.urls import path

from . import views

app_name = 'portal'

urlpatterns = [
    path('access/<str:token>/', views.portal_access_view, name='access'),
    path('', views.portal_dashboard_view, name='dashboard'),
    path('projects/<uuid:project_pk>/', views.portal_project_detail_view, name='project_detail'),
    path('milestones/<uuid:milestone_pk>/review/', views.portal_milestone_review_view, name='milestone_review'),
    path('milestones/<uuid:milestone_pk>/action/', views.portal_milestone_action_view, name='milestone_action'),
    path('logout/', views.portal_logout_view, name='logout'),
]
