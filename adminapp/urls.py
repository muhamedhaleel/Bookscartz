from django.urls import path
from . import views

urlpatterns = [
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-category/', views.category_list, name='admin_category'),
    path('admin-brand/', views.admin_brand, name='admin_brand'),
    path('admin-products/', views.admin_products, name='admin_products'),
    # path('admin-caustomers/', views.admin_caustomers, name='admin_caustomers'),
     path('admin/categories/toggle/<int:pk>/', views.toggle_category_status, name='toggle_category_status'),
]
