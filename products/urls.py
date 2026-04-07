from django.urls import path
from . import views

urlpatterns = [
    path('', views.products_view, name='products'),
    path('products/update-price/', views.update_price, name='update_price'),
   

]
