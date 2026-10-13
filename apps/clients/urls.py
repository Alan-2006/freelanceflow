from django.urls import path

from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.client_list_view, name='list'),
    path('new/', views.client_create_view, name='create'),
    path('<uuid:pk>/', views.client_detail_view, name='detail'),
    path('<uuid:pk>/edit/', views.client_update_view, name='update'),
    path('<uuid:pk>/delete/', views.client_delete_view, name='delete'),
]
