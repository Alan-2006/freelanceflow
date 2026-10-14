from django.urls import path

from . import views

app_name = 'portal'

urlpatterns = [
    path('access/<str:token>/', views.portal_access_view, name='access'),
    path('', views.portal_dashboard_view, name='dashboard'),
    path('invoices/<uuid:invoice_pk>/', views.portal_invoice_detail_view, name='invoice_detail'),
    path('projects/<uuid:project_pk>/', views.portal_project_detail_view, name='project_detail'),
    path('projects/<uuid:project_pk>/upload/', views.portal_project_upload_view, name='project_upload'),
    path('projects/<uuid:project_pk>/comment/', views.portal_project_comment_view, name='project_comment'),
    path('milestones/<uuid:milestone_pk>/review/', views.portal_milestone_review_view, name='milestone_review'),
    path('milestones/<uuid:milestone_pk>/action/', views.portal_milestone_action_view, name='milestone_action'),
    path('logout/', views.portal_logout_view, name='logout'),
]

