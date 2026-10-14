from django.urls import path

from . import views

app_name = 'invoicing'

urlpatterns = [
    path('', views.invoice_list_view, name='list'),
    path('new/', views.invoice_create_view, name='create'),
    path('recurring/', views.recurring_invoice_list_view, name='recurring_list'),
    path('recurring/new/', views.recurring_invoice_create_view, name='recurring_create'),
    path('recurring/<uuid:pk>/toggle/', views.recurring_invoice_toggle_view, name='recurring_toggle'),
    path('recurring/<uuid:pk>/delete/', views.recurring_invoice_delete_view, name='recurring_delete'),
    path('recurring/<uuid:pk>/generate/', views.recurring_invoice_generate_now_view, name='recurring_generate'),
    path('<uuid:pk>/', views.invoice_detail_view, name='detail'),
    path('<uuid:pk>/edit/', views.invoice_edit_view, name='edit'),
    path('<uuid:pk>/duplicate/', views.invoice_duplicate_view, name='duplicate'),
    path('<uuid:pk>/delete/', views.invoice_delete_view, name='delete'),
    path('<uuid:pk>/pdf/', views.invoice_pdf_view, name='pdf'),
    path('<uuid:pk>/send/', views.invoice_send_view, name='send'),
    path('<uuid:pk>/convert-time/', views.invoice_convert_time_view, name='convert_time'),
    path('public/<str:public_token>/', views.invoice_public_view, name='public'),

    # Proposals / Estimates
    path('proposals/', views.proposal_list_view, name='proposal_list'),
    path('proposals/new/', views.proposal_create_view, name='proposal_create'),
    path('proposals/<uuid:pk>/', views.proposal_detail_view, name='proposal_detail'),
    path('proposals/<uuid:pk>/convert/', views.proposal_convert_to_project_view, name='proposal_convert'),
    path('proposals/public/<str:public_token>/', views.proposal_public_view, name='proposal_public'),
    path('proposals/public/<str:public_token>/action/', views.proposal_client_action_view, name='proposal_client_action'),
]

