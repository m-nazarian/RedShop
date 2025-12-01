from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path("checkout/address/", views.checkout_address, name="checkout_address"),
    path("checkout/review/", views.checkout_review, name="checkout_review"),
    path("checkout/create/", views.checkout_create_order, name="checkout_create"),
    path('checkout/complete/', views.checkout_complete, name='checkout_complete'),
    path('checkout/create/', views.checkout_create_order, name='checkout_create_order'),
    path('my-orders/', views.user_orders, name='user_orders'),
    path('api/my-orders/', views.user_orders_partial, name='user_orders_partial'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
    path('api/order-detail/<int:order_id>/', views.order_detail_partial, name='order_detail_partial'),
]
