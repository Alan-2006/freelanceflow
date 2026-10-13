from django.urls import path

from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.payment_list_view, name='list'),
    path('record/', views.manual_payment_record_view, name='record'),
    path('checkout/<uuid:invoice_pk>/', views.checkout_view, name='checkout'),
    path('verify/<uuid:invoice_pk>/', views.razorpay_verify_view, name='verify'),
    path('webhook/razorpay/', views.razorpay_webhook_view, name='razorpay_webhook'),
]
