from django.urls import path
from . import views

urlpatterns = [

    path('', views.home, name='home'),

    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('set-password/<str:username>/', views.set_new_password, name='set_new_password'),

    path('product-list/', views.product_list, name='product_list'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),

    path('add-product/', views.add_product, name='add_product'),

    path('cart/', views.cart_view, name='cart'),
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('increase/<int:item_id>/', views.increase_quantity, name='increase'),
    path('decrease/<int:item_id>/', views.decrease_quantity, name='decrease'),

    path('orders/', views.orders_view, name='orders'),

    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('customer-dashboard/', views.customer_dashboard, name='customer_dashboard'),

    # path('paypal/', views.paypal_payment, name='paypal'),
    path('paypal/<int:order_id>/', views.paypal_payment, name='paypal_payment'),
    path('success/<int:order_id>/', views.payment_success, name='success'),
    path('cancel/', views.payment_cancel, name='cancel'),

    path('edit-product/<int:id>/', views.edit_product, name='edit_product'),
    path('delete-product/<int:id>/', views.delete_product, name='delete_product'),

    path('update-order-status/<int:id>/', views.update_order_status, name='update_order_status'),
    path('checkout/', views.checkout, name='checkout'),
    path('order-success/', views.order_success, name='order_success'),

    path('buy-now/<int:product_id>/', views.buy_now, name='buy_now'),
    path('cancel-order/<int:id>/', views.cancel_order, name='cancel_order'),
    path('return-order/<int:id>/', views.return_order, name='return_order'),
    path('admin-orders/', views.admin_orders, name='admin_orders'),

]