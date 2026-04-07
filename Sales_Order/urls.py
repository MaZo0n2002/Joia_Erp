from django.urls import path
from . import views

urlpatterns = [
    path('', views.sales_orders_list, name='sales_orders_list'),
    path('<int:order_id>/', views.sales_order_detail, name='sales_order_detail'),
    # path('line/<int:line_id>/start_preparing/', views.start_preparing, name='start_preparing'),
    path("deliver/<int:line_id>/", views.deliver_line, name="deliver_line"),
    path('confirm-final/<int:order_id>/', views.confirm_final_order, name='confirm_final_order'),
    path('invoice/pdf/<int:invoice_id>/', views.generate_invoice_pdf, name='invoice_pdf'),
    path('update-price/<int:line_id>/', views.update_price, name='update_price'),
    
]
