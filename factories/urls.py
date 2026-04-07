from django.urls import path
from . import views

urlpatterns = [
    path('', views.factories, name='factories'),
    path('edit/<int:factory_id>/', views.edit_factory, name='edit_factory'),
    path('delete/<int:factory_id>/', views.delete_factory, name='delete_factory'),
]