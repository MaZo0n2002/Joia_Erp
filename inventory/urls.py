from django.urls import path
from . import views

urlpatterns = [
    path('stock/', views.stock, name='stock'), 
    path('transfer-dpl/', views.transfer_dpl_stock, name='transfer_dpl_stock'),
    ]