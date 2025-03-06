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
]