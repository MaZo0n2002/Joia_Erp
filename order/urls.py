from django.urls import path
from . import views

# app_name = 'order'
urlpatterns = [
    path('', views.create_quotation, name='create_quotation'),
    path('quotation/pdf/<int:quotation_id>/', views.generate_pdf, name='generate_pdf'),
    path('get_colors/', views.get_colors, name='get_colors'),
    path('manage/', views.manage_quotations, name='manage_quotations'),
    path('confirm/<int:quotation_id>/', views.confirm_quotation, name='confirm_quotation'),
    path('api/<int:quotation_id>/', views.quotation_api, name='quotation_api'),
    path('api/<int:quotation_id>/update/', views.update_quotation, name='update_quotation'),
]
