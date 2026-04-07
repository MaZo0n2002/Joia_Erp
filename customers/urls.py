from django.urls import path
from . import views

urlpatterns = [
    path('', views.customers, name='customers'),
    path('customers/edit/<int:customer_id>/', views.edit_customer, name='edit_customer'),
    path('customers/delete/<int:customer_id>/', views.delete_customer, name='delete_customer'),]