from django.urls import path
from . import views

urlpatterns = [
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-home/', views.admin_dashboard, name='admin_home'),
    path('admin-products/', views.admin_products, name='admin_products'),
    path('admin-category/', views.category_list, name='category_list'),
    path('admin-brand/', views.brand_list, name='brand_list'),
    path('admin-customer/', views.admin_customer, name='admin_customer'),
    path('add-brand/', views.add_brand, name='add_brand'),
    path('edit-brand/<int:pk>/', views.edit_brand, name='edit_brand'),
    path('toggle-brand-status/<int:pk>/', views.toggle_brand_status, name='toggle_brand_status'),
    path('edit-category/<int:pk>/', views.edit_category, name='edit_category'),
    path('delete-category/<int:pk>/', views.delete_category, name='delete_category'),
    path('add-product/', views.add_product, name='add_product'),
    path('edit-product/<int:pk>/', views.edit_product, name='edit_product'),
    path('toggle-product-status/<int:pk>/', views.toggle_product_status, name='toggle_product_status'),
    path('admin-variants/', views.variant_list, name='variant_list'),
    path('add-variant/', views.add_variant, name='add_variant'),
    path('edit-variant/<int:pk>/', views.edit_variant, name='edit_variant'),
    path('toggle-variant-status/<int:pk>/', views.toggle_variant_status, name='toggle_variant_status'),
    path('delete-variant/<int:pk>/', views.delete_variant, name='delete_variant'),
    path('toggle-user-status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    
    # Offer URLs - Updated for consistency
    path('admin-offers/', views.offer_list, name='offer_list'),
    path('admin-offers/add/', views.add_offer, name='add_offer'),
    path('admin-offers/edit/<int:pk>/', views.edit_offer, name='edit_offer'),
    path('admin-offers/delete/<int:pk>/', views.delete_offer, name='delete_offer'),
    path('admin-offers/toggle/<int:pk>/', views.toggle_offer_status, name='toggle_offer_status'),
    path('get-offer-items/', views.get_offer_items, name='get_offer_items'),
    path('orders/', views.admin_manage_orders, name='admin_manage_orders'),
    path('orders/update-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('orders/get-return-details/<int:order_id>/', views.get_return_details, name='get_return_details'),
    path('orders/handle-return/<int:order_id>/', views.admin_handle_return, name='admin_handle_return'),
]