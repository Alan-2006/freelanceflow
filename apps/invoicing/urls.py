from django.urls import path

from . import views

app_name = 'invoicing'

urlpatterns = [
    path('', views.invoice_list_view, name='list'),
    path('new/', views.invoice_create_view, name='create'),
    path('<uuid:pk>/', views.invoice_detail_view, name='detail'),
    path('<uuid:pk>/pdf/', views.invoice_pdf_view, name='pdf'),
    path('<uuid:pk>/send/', views.invoice_send_view, name='send'),
    path('<uuid:pk>/convert-time/', views.invoice_convert_time_view, name='convert_time'),
    path('public/<str:public_token>/', views.invoice_public_view, name='public'),
]
