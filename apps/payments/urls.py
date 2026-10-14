from django.urls import path

from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.payment_list_view, name='list'),
    path('record/', views.manual_payment_record_view, name='record'),
    path('checkout/<uuid:invoice_pk>/', views.checkout_view, name='checkout'),
    path('verify/<uuid:invoice_pk>/', views.razorpay_verify_view, name='verify'),
    path('verify-stripe/<uuid:invoice_pk>/', views.stripe_verify_view, name='verify_stripe'),
    path('webhook/razorpay/', views.razorpay_webhook_view, name='razorpay_webhook'),
    path('webhook/stripe/', views.stripe_webhook_view, name='stripe_webhook'),
    path('credit-notes/', views.credit_note_list_view, name='credit_note_list'),
    path('credit-notes/new/', views.credit_note_create_view, name='credit_note_create'),
]
