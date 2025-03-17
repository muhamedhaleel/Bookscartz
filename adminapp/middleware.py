from django.shortcuts import redirect
from django.urls import resolve
from django.contrib import messages

class RoleBasedAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip middleware for static files and media
        if request.path.startswith(('/static/', '/media/')):
            return self.get_response(request)

        # Get current URL name
        current_url = resolve(request.path_info).url_name

        # Define admin and user URL patterns
        admin_urls = ['admin_dashboard', 'admin_products', 'admin_customer', 
                     'admin_manage_orders', 'category_list', 'brand_list', 
                     'offer_list', 'admin_login']
        
        user_urls = ['home', 'product_list', 'cart', 'profile', 'login', 
                    'signup', 'user_orders']

        # Check if user is authenticated
        if request.user.is_authenticated:
            # If user is admin
            if request.user.is_superuser:
                # Redirect admin from user pages to admin dashboard
                if current_url in user_urls:
                    messages.error(request, 'Admin users cannot access customer pages')
                    return redirect('admin_dashboard')
            # If user is not admin
            else:
                # Redirect normal users from admin pages to home
                if current_url in admin_urls:
                    messages.error(request, 'Access denied. Admin privileges required.')
                    return redirect('home')

        response = self.get_response(request)
        return response 