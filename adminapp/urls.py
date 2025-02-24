from django.urls import path
from . import views

urlpatterns = [
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-category/', views.category_list, name='category_list'),
    path('edit-category/<int:pk>/', views.edit_category, name='edit_category'),
    path('delete_category/<int:pk>/', views.delete_category, name='delete_category'),
    
    path('admin-publisher/', views.brand_list, name='brand_list'),
    path('add-brand/', views.add_brand, name='add_brand'),
    path('edit-brand/<int:pk>/', views.edit_brand, name='edit_brand'),
    path('toggle-brand-status/<int:pk>/', views.toggle_brand_status, name='toggle_brand_status'),


    
]
