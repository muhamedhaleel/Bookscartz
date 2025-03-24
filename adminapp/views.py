from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Category, Brand, Product, Language, Offer, Order, ReturnRequest, OrderItem, Coupon, Wallet, WalletTransaction
from .forms import CategoryForm
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
import os
from django.db.models import Q, Sum, Count
from django.core.files.images import get_image_dimensions
from PIL import Image
import os
from django.http import JsonResponse
from django.db.models.query import Prefetch
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
import json
from io import BytesIO
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT



# ----------------------------
# Admin Authentication
# ----------------------------
def admin_login(request):
    # Redirect if already logged in as admin
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_superuser:
            login(request, user)
            messages.success(request, 'Welcome back, Admin!')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid admin credentials')
    
    return render(request, 'admin_login.html')

@login_required(login_url='admin_login')
def admin_logout(request):
    logout(request)
    return redirect('admin_login')

# ----------------------------
#  Admin Dashboard
# ----------------------------
@login_required(login_url='admin_login')
def admin_dashboard(request):
    if not request.user.is_staff:
        logout(request)
        messages.error(request, 'Unauthorized access')
        return redirect('admin_login')
    
    # Get counts for dashboard
    try:
        product_count = Product.objects.count()
        category_count = Category.objects.count()
        brand_count = Brand.objects.count()
        offer_count = Offer.objects.filter(is_active=True).count()
        
        # Get initial sales data
        today = timezone.now().date()
        orders = Order.objects.filter(created_at__date=today)
        
        context = {
            'product_count': product_count,
            'category_count': category_count,
            'brand_count': brand_count,
            'offer_count': offer_count,
        }
        return render(request, 'admin_home.html', context)
    except Exception as e:
        messages.error(request, f'Error loading dashboard: {str(e)}')
    return render(request, 'admin_home.html')


# 
#  
# ----------------------------
#  Category List, Add, Edit & Delete
# ----------------------------
@login_required(login_url='admin_login')
def category_list(request):
    search_query = request.GET.get('search', '')
    
    # Filter categories based on search query
    if search_query:
        categories = Category.objects.filter(name__icontains=search_query).order_by('-added_on')
    else:
        categories = Category.objects.all().order_by('-added_on')
    
    form = CategoryForm()

    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Category added successfully!')
            except Exception as e:
                messages.error(request, f'Error adding category: {str(e)}')
            return redirect('category_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')

    context = {
        'categories': categories,
        'form': form,
        'search_query': search_query
    }
    
    return render(request, 'admin_category.html', context)


@login_required(login_url='admin_login')
def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        name = request.POST.get('name').strip()
    
        if not name:
            messages.error(request, 'Category name cannot be empty.')
        elif name.lower() == category.name.lower():
            messages.warning(request, 'No changes were made.')
        elif Category.objects.filter(name__iexact=name).exclude(pk=pk).exists():
                messages.error(request, 'A category with this name already exists.')
        else:
            try:
                category.name = name
                category.save()
                messages.success(request, 'Category updated successfully!')
            except Exception as e:
                messages.error(request, f'Error updating category: {str(e)}')
        return redirect('category_list')

    return redirect('category_list')



@login_required(login_url='admin_login')
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    try:
        category.is_active = not category.is_active
        category.save()
        status = "activated" if category.is_active else "blocked"
        messages.success(request, f'Category {status} successfully!')
    except Exception as e:
        messages.error(request, f'Error updating category status: {str(e)}')
    return redirect('category_list')


# ----------------------------
#  Toggle Category Status (Block/Unblock)
# ----------------------------
@login_required(login_url='admin_login')
def toggle_category_status(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.is_active = not category.is_active
    category.save()
    status = "Unblocked" if category.is_active else "Blocked"
    messages.success(request, f'Category {status} successfully!')
    return redirect('category_list')



# Brand List View
@login_required(login_url='admin_login')
def brand_list(request):
    search_query = request.GET.get('search', '')
    
    # Filter brands based on search query
    if search_query:
        brand_list = Brand.objects.filter(name__icontains=search_query).order_by('-added_on')
    else:
        brand_list = Brand.objects.all().order_by('-added_on')

    # Pagination
    paginator = Paginator(brand_list, 10)  # 10 brands per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query
    }
    
    return render(request, 'admin_publisher.html', context)

@login_required(login_url='admin_login')
def add_brand(request):
    if not request.user.is_staff:
        messages.error(request, 'Unauthorized access')
        return redirect('admin_login')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        image = request.FILES.get('image')

        # Validate brand name
        if not name:
            messages.error(request, "Brand name is required.")
            return redirect('brand_list')

        if Brand.objects.filter(name__iexact=name).exists():
            messages.error(request, "A brand with this name already exists.")
            return redirect('brand_list')

        # Validate image
        if not image:
            messages.error(request, "Brand image is required.")
            return redirect('brand_list')

        # Validate file size (max 2MB)
        if image.size > 2 * 1024 * 1024:
            messages.error(request, "Image file size must be less than 2MB.")
            return redirect('brand_list')

        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif']
        if image.content_type not in allowed_types:
            messages.error(request, "Only JPEG, PNG, and GIF images are allowed.")
            return redirect('brand_list')

        try:
            brand = Brand.objects.create(
                name=name,
                image=image
            )
            messages.success(request, f'Brand "{name}" added successfully!')
        except Exception as e:
            messages.error(request, f'Error adding brand: {str(e)}')

        return redirect('brand_list')

    return redirect('brand_list')

@login_required(login_url='admin_login')
def edit_brand(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Unauthorized access')
        return redirect('admin_login')

    brand = get_object_or_404(Brand, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        image = request.FILES.get('image')

        # Validate brand name
        if not name:
            messages.error(request, "Brand name is required.")
            return redirect('brand_list')

        # Check if name exists for other brands
        if Brand.objects.filter(name__iexact=name).exclude(pk=pk).exists():
            messages.error(request, "A brand with this name already exists.")
            return redirect('brand_list')

        try:
            brand.name = name
            if image:
                # Validate file size
                if image.size > 2 * 1024 * 1024:
                    messages.error(request, "Image file size must be less than 2MB.")
                    return redirect('brand_list')

                # Validate file type
                allowed_types = ['image/jpeg', 'image/png', 'image/gif']
                if image.content_type not in allowed_types:
                    messages.error(request, "Only JPEG, PNG, and GIF images are allowed.")
                    return redirect('brand_list')

                brand.image = image

            brand.save()
            messages.success(request, f'Brand "{name}" updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating brand: {str(e)}')

        return redirect('brand_list')

# Toggle Brand Status View
def toggle_brand_status(request, pk):
    brand = get_object_or_404(Brand, pk=pk)

    if request.method == 'POST':
        brand.is_active = not brand.is_active
        brand.save()
        status = "activated" if brand.is_active else "blocked"
        messages.success(request, f"Brand {status} successfully.")
        return redirect('brand_list')

    return redirect('brand_list')  # Redirect if not a POST request



 
#  Other Admin Views
# ----------------------------
@login_required(login_url='admin_login')
def admin_publisher(request):
     return render(request,'admin_publisher.html')


    
    # Filter products based on search query
    


@login_required(login_url='admin_login')
def admin_customer(request):
    if not request.user.is_staff:
        messages.error(request, 'Unauthorized access')
        return redirect('admin_login')
    
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Get all users except superusers
    User = get_user_model()
    users = User.objects.filter(is_superuser=False).order_by('-date_joined')
    
    # Apply search filter
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(users, 10)  # Show 10 users per page
    page = request.GET.get('page')
    users = paginator.get_page(page)
    
    context = {
        'users': users,
        'search_query': search_query
    }
    
    return render(request, 'user_details.html', context)

@login_required(login_url='admin_login')
def toggle_user_status(request, user_id):
    if not request.user.is_staff:
        messages.error(request, 'Unauthorized access')
        return redirect('admin_login')
    
    if request.method == 'POST':
        try:
            User = get_user_model()
            user = get_object_or_404(User, id=user_id)
            
            # Don't allow toggling superuser status
            if user.is_superuser:
                messages.error(request, 'Cannot modify superuser status')
                return redirect('admin_customer')
            
            user.is_active = not user.is_active
            user.save()
            
            status = "activated" if user.is_active else "deactivated"
            messages.success(request, f'User {user.username} has been {status}')
            
        except Exception as e:
            messages.error(request, f'Error updating user status: {str(e)}')
    
    return redirect('admin_customer')



#  Other Admin Views
# ----------------------------
@login_required(login_url='admin_login')
def admin_publisher(request):
     return render(request,'admin_publisher.html')


    
    # Filter products based on search query
    



@login_required(login_url='admin_login')

def admin_products(request):
    try:
        # Get search query
        search_query = request.GET.get('search', '')
        
        # Get all products with related data
        products = Product.objects.select_related('category', 'brand', 'language').order_by('-added_on')
        
        # Apply search filter if search query exists
        if search_query:
            products = products.filter(
                Q(name__icontains=search_query) |
                Q(category__name__icontains=search_query) |
                Q(brand__name__icontains=search_query) |
                Q(language__name__icontains=search_query)
            )
        
        # Get active categories, brands, and languages for the forms
        categories = Category.objects.filter(is_active=True)
        brands = Brand.objects.filter(is_active=True)
        languages = Language.objects.filter(is_active=True)
        
        context = {
            'products': products,
            'categories': categories,
            'brands': brands,
            'languages': languages,
            'search_query': search_query
        }
        
        return render(request, 'admin_product.html', context)
        
    except Exception as e:
        print(f"Error in admin_products view: {str(e)}")  # Add this for debugging
        messages.error(request, f"Error: {str(e)}")
        return redirect('admin_dashboard')

@login_required(login_url='admin_login')
def add_product(request):
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            description = request.POST.get('description')
            category_id = request.POST.get('category')
            brand_id = request.POST.get('brand')
            language_id = request.POST.get('language')
            price = request.POST.get('price')
            stock = request.POST.get('stock')
            image1 = request.FILES.get('image1')
            image2 = request.FILES.get('image2')
            image3 = request.FILES.get('image3')
            
            
            if not all([name, description, category_id, brand_id, language_id, price, stock, image1]):
                messages.error(request, "Please fill all required fields")
                return redirect('admin_products')

            # Get language instance
            language = get_object_or_404(Language, id=language_id)
            
            # Create product
            product = Product.objects.create(
                name=name,
                description=description,
                category_id=category_id,
                brand_id=brand_id,
                language=language,
                price=price,
                stock=stock,
                image1=image1,
                image2=image2,
                image3=image3,
                is_active=True
            )
            messages.success(request, "Product added successfully!")
            
        except Exception as e:
            messages.error(request, f"Error adding product: {str(e)}")
        
    return redirect('admin_products')

@login_required(login_url='admin_login')
def edit_product(request, pk):
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, pk=pk)
            
            # Update basic fields
            product.name = request.POST.get('name')
            product.description = request.POST.get('description')
            product.category_id = request.POST.get('category')
            product.brand_id = request.POST.get('brand')
            product.price = request.POST.get('price')
            product.stock = request.POST.get('stock')
            
            # Handle language
            language_id = request.POST.get('language')
            language = get_object_or_404(Language, id=language_id)
            product.language = language
            
            # Handle images
            image1 = request.FILES.get('image1')
            image2 = request.FILES.get('image2')
            image3 = request.FILES.get('image3')
            
            if image1:
                if product.image1:
                    if os.path.isfile(product.image1.path):
                        os.remove(product.image1.path)
                product.image1 = image1
            
            if image2:
                if product.image2:
                    if os.path.isfile(product.image2.path):
                        os.remove(product.image2.path)
                product.image2 = image2
            
            if image3:
                if product.image3:
                    if os.path.isfile(product.image3.path):
                        os.remove(product.image3.path)
                product.image3 = image3
                
            product.save()
            messages.success(request, "Product updated successfully!")
            
        except Exception as e:
            messages.error(request, f"Error updating product: {str(e)}")
        
    return redirect('admin_products')

# Toggle product status
@login_required(login_url='admin_login')
def toggle_product_status(request, pk):
    try:
        product = get_object_or_404(Product, pk=pk)
        product.is_active = not product.is_active
        product.save()
        
        status = "activated" if product.is_active else "blocked"
        messages.success(request, f"Product {status} successfully!")
    except Exception as e:
        messages.error(request, f"Error toggling product status: {str(e)}")
    
    return redirect('admin_products')

@login_required(login_url='admin_login')
def variant_list(request):
    try:
        # Get search query
        search_query = request.GET.get('search', '')
        
        # Get all variants ordered by name
        variants = Language.objects.all().order_by('name')
        
        # Apply search filter if search query exists
        if search_query:
            variants = variants.filter(name__icontains=search_query)
        
        context = {
            'variants': variants,
            'search_query': search_query
        }
        
        return render(request, 'admin_varient.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading variants: {str(e)}")
        return redirect('admin_dashboard')

@login_required(login_url='admin_login')
def add_variant(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            
            if not name:
                messages.error(request, "Variant name cannot be empty")
                return redirect('admin_products')
            
            if Language.objects.filter(name__iexact=name).exists():
                messages.error(request, "A variant with this name already exists")
                return redirect('admin_products')
            
            Language.objects.create(
                name=name,
                is_active=True
            )
            
            messages.success(request, "Language variant added successfully!")
            
        except Exception as e:
            messages.error(request, f"Error adding variant: {str(e)}")
    
    return redirect('admin_products')

@login_required(login_url='admin_login')
def edit_variant(request, pk):
    if request.method == 'POST':
        try:
            variant = get_object_or_404(Language, pk=pk)
            name = request.POST.get('name', '').strip()
            
            if not name:
                messages.error(request, "Variant name cannot be empty")
                return redirect('admin_products')
            
            if Language.objects.filter(name__iexact=name).exclude(pk=pk).exists():
                messages.error(request, "A variant with this name already exists")
                return redirect('admin_products')
            
            if variant.product_set.exists() and variant.name.lower() != name.lower():
                messages.error(request, "Cannot change name of variant that is being used by products")
                return redirect('admin_products')
            
            variant.name = name
            variant.save()
            
            messages.success(request, "Language variant updated successfully!")
            
        except Exception as e:
            messages.error(request, f"Error updating variant: {str(e)}")
    
    return redirect('admin_products')

@login_required(login_url='admin_login')
def toggle_variant_status(request, pk):
    if request.method == 'POST':
        try:
            variant = get_object_or_404(Language, pk=pk)
            
            if variant.is_active and variant.product_set.exists():
                messages.error(request, "Cannot deactivate variant that is being used by products")
                return redirect('admin_products')
            
            variant.is_active = not variant.is_active
            variant.save()
            
            status = "activated" if variant.is_active else "deactivated"
            messages.success(request, f"Language variant {status} successfully!")
            
        except Exception as e:
            messages.error(request, f"Error toggling variant status: {str(e)}")
    
    return redirect('admin_products')

@login_required(login_url='admin_login')
def delete_variant(request, pk):
    if request.method == 'POST':
        try:
            variant = get_object_or_404(Language, pk=pk)
            
            # Check if variant is being used by any products
            if variant.product_set.exists():
                messages.error(request, "Cannot delete variant that is being used by products")
                return redirect('variant_list')
            
            # Delete variant
            variant.delete()
            messages.success(request, "Language variant deleted successfully!")
            
        except Exception as e:
            messages.error(request, f"Error deleting variant: {str(e)}")
    
    return redirect('variant_list')

@login_required(login_url='admin_login')
def offer_list(request):
    print("Debug: Entering offer_list view")
    
    if not request.user.is_staff:
        messages.error(request, 'Unauthorized access')
        return redirect('admin_login')
    
    try:
        search_query = request.GET.get('search', '')
        print(f"Debug: Search query: {search_query}")
        
        # Get all offers
        offers_list = Offer.objects.all().order_by('-created_at')
        
        # Process each offer to get readable names
        for offer in offers_list:
            if offer.offer_type == 'product':
                try:
                    product = Product.objects.get(id=offer.offer_items)
                    offer.item_name = product.name
                except Product.DoesNotExist:
                    offer.item_name = "Product not found"
            elif offer.offer_type == 'category':
                try:
                    category = Category.objects.get(id=offer.offer_items)
                    offer.item_name = category.name
                except Category.DoesNotExist:
                    offer.item_name = "Category not found"
        
        # Apply search filter if search query exists
        if search_query:
            offers_list = offers_list.filter(
                Q(offer_type__icontains=search_query) |
                Q(offer_items__icontains=search_query)
            )
        
        # Pagination
        paginator = Paginator(offers_list, 10)
        page = request.GET.get('page')
        offers = paginator.get_page(page)
        
        context = {
            'offers': offers,
            'search_query': search_query
        }
        
        return render(request, 'offer.html', context)
        
    except Exception as e:
        print(f"Debug: Error in offer_list view: {str(e)}")
        messages.error(request, f'Error: {str(e)}')
        return redirect('admin_dashboard')

@login_required(login_url='admin_login')
def add_offer(request):
    if not request.user.is_staff:
        messages.error(request, 'Unauthorized access')
        return redirect('admin_login')
    
    if request.method == 'POST':
        try:
            offer_type = request.POST.get('offer_type')
            offer_items = request.POST.get('offer_items')
            discount = request.POST.get('discount')
            is_active = request.POST.get('is_active') == 'on'
            
            # Validate required fields
            if not all([offer_type, offer_items, discount]):
                messages.error(request, 'Please fill all required fields')
                return redirect('offer_list')
            
            # Create new offer
            Offer.objects.create(
                offer_type=offer_type,
                offer_items=offer_items,
                discount=discount,
                is_active=is_active
            )
            
            messages.success(request, 'Offer added successfully!')
            
        except Exception as e:
            messages.error(request, f'Error adding offer: {str(e)}')
        
    return redirect('offer_list')

@login_required(login_url='admin_login')
def edit_offer(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Unauthorized access')
        return redirect('admin_login')
    
    offer = get_object_or_404(Offer, pk=pk)
    
    if request.method == 'POST':
        try:
            offer_type = request.POST.get('offer_type')
            offer_items = request.POST.get('offer_items')
            discount = request.POST.get('discount')
            is_active = request.POST.get('is_active') == 'on'
            
            # Validate required fields
            if not all([offer_type, offer_items, discount]):
                messages.error(request, 'Please fill all required fields')
                return redirect('offer_list')
            
            # Update offer
            offer.offer_type = offer_type
            offer.offer_items = offer_items
            offer.discount = discount
            offer.is_active = is_active
            offer.save()
            
            messages.success(request, 'Offer updated successfully!')
            
        except Exception as e:
            messages.error(request, f'Error updating offer: {str(e)}')
        
    return redirect('offer_list')

@login_required(login_url='admin_login')
def delete_offer(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Unauthorized access')
        return redirect('admin_login')
    
    if request.method == 'POST':
        try:
            offer = get_object_or_404(Offer, pk=pk)
            offer.delete()
            messages.success(request, 'Offer deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting offer: {str(e)}')
    
    return redirect('offer_list')

@login_required(login_url='admin_login')
def toggle_offer_status(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Unauthorized access')
        return redirect('admin_login')
    
    if request.method == 'POST':
        try:
            offer = get_object_or_404(Offer, pk=pk)
            offer.is_active = not offer.is_active
            offer.save()
            status = "activated" if offer.is_active else "deactivated"
            messages.success(request, f'Offer {status} successfully!')
        except Exception as e:
            messages.error(request, f'Error updating offer status: {str(e)}')
    
    return redirect('offer_list')

@login_required(login_url='admin_login')
def get_offer_items(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    offer_type = request.GET.get('type')
    items = []
    
    try:
        if offer_type == 'product':
            products = Product.objects.filter(is_active=True).values('id', 'name')
            items = [{'id': str(p['id']), 'name': f"{p['name']}"} for p in products]
        elif offer_type == 'category':
            categories = Category.objects.filter(is_active=True).values('id', 'name')
            items = [{'id': str(c['id']), 'name': f"{c['name']}"} for c in categories]
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse(items, safe=False)

@login_required(login_url='admin_login')
def admin_manage_orders(request):
    if not request.user.is_staff:
        messages.error(request, 'Unauthorized access')
        return redirect('admin_login')
        
    # Get all orders with related data
    orders = Order.objects.all()\
        .select_related('user')\
        .prefetch_related(
            'items__product',
            'return_request',
            Prefetch('items', queryset=OrderItem.objects.filter(return_requested=True), to_attr='returned_items')
        ).order_by('-created_at')
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'orders': page_obj,
        'current_status': status,
        'status_choices': Order._meta.get_field('status').choices
    }
    return render(request, 'admin_mange_order.html', context)

@login_required(login_url='admin_login')
def get_return_details(request, order_id):
    if not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
    
    try:
        order = get_object_or_404(Order, id=order_id)
        return_request = order.return_request.select_related('order').first()
        
        if not return_request:
            return JsonResponse({
                'status': 'error',
                'message': 'Return request not found'
            }, status=404)
            
        # Calculate refund amount
        refund_amount = order.calculate_return_refund_amount()
        
        response_data = {
            'status': 'success',
            'order_id': order.id,
            'customer_name': f"{order.user.first_name} {order.user.last_name}",
            'created_at': return_request.created_at.strftime('%B %d, %Y'),
            'status': return_request.status,
            'reason': return_request.get_reason_display(),
            'comments': return_request.comments,
            'refund_amount': float(refund_amount),
            'items': []
        }
        
        # Add item details
        for item in order.items.filter(return_requested=True).select_related('product'):
            item_data = {
                'name': item.product.name,
                'quantity': item.quantity,
                'price': str(item.price),
                'total': str(item.total_price),
                'image': request.build_absolute_uri(item.product.image1.url) if item.product.image1 else '',
                'return_status': item.return_status
            }
            response_data['items'].append(item_data)
        
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"Error in get_return_details: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to load return details'
        }, status=500)

@login_required(login_url='admin_login')
@require_http_methods(["POST"])
def admin_handle_return(request, order_id):
    if not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
        
    try:
        with transaction.atomic():
            order = get_object_or_404(Order, id=order_id)
            return_request = order.return_request.first()
            
            if not return_request:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Return request not found'
                }, status=404)
            
            status = request.POST.get('return_status')
            admin_notes = request.POST.get('admin_notes', '')
            
            if status not in ['approved', 'rejected']:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid status'
                }, status=400)
            
            # Update return request
            return_request.status = status
            return_request.admin_notes = admin_notes
            return_request.save()
            
            # Calculate total refund amount first
            total_refund_amount = Decimal('0.00')
            
            # Get all items that were requested for return
            returned_items = order.items.filter(return_requested=True)
            
            for item in returned_items:
                if status == 'approved':
                    # Calculate refund amount for this item
                    total_refund_amount += item.total_price
                    
                    # Update inventory
                    product = item.product
                    product.stock += item.quantity
                    product.save()
                
                # Update item return status
                item.return_status = status
                item.save()
            
            # If approved, add refund amount to user's wallet
            if status == 'approved' and total_refund_amount > 0:
                # Get or create user's wallet
                wallet, created = Wallet.objects.get_or_create(user=order.user)
                
                # Add refund amount to wallet
                wallet.balance += total_refund_amount
                wallet.save()
                
                # Create wallet transaction record
                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=total_refund_amount,
                    type='credit',
                    order_id=str(order.id)
                )
                
                # Update order status to 'returned' when return is approved
                order.status = 'returned'
                order.save()
            
            return JsonResponse({
                'status': 'success',
                'message': f'Return request has been {status} successfully. Refund amount of ₹{total_refund_amount} has been added to wallet.'
            })
            
    except Exception as e:
        print(f"Error handling return: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Error processing return request'
        }, status=500)

@login_required(login_url='admin_login')
def update_order_status(request, order_id):
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

    try:
        order = Order.objects.get(id=order_id)
        new_status = request.POST.get('status')

        if not new_status:
            return JsonResponse({
                'status': 'error',
                'message': 'Status is required'
            }, status=400)

        if order.update_status(new_status):
            return JsonResponse({
                'status': 'success',
                'message': f'Order status updated to {new_status}'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': f'Cannot change status from {order.status} to {new_status}'
            }, status=400)

    except Order.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Order not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required(login_url='admin_login')
def coupon_list(request):
    search_query = request.GET.get('search', '')
    
    if search_query:
        coupons = Coupon.objects.filter(
            Q(code__icontains=search_query) |
            Q(type__icontains=search_query)
        ).order_by('-created_at')
    else:
        coupons = Coupon.objects.all().order_by('-created_at')
    
    paginator = Paginator(coupons, 10)
    page = request.GET.get('page')
    coupons = paginator.get_page(page)
    
    # Get current date and default valid_to
    current_date = timezone.now().date()
    default_valid_to = current_date + timezone.timedelta(days=30)
    
    context = {
        'coupons': coupons,
        'search_query': search_query,
        'default_valid_to': default_valid_to,
        'now': current_date
    }
    return render(request, 'coupon.html', context)

@login_required(login_url='admin_login')
def add_coupon(request):
    if request.method == 'POST':
        try:
            code = request.POST.get('code')
            type = request.POST.get('type')
            value = request.POST.get('value')
            min_amount = request.POST.get('min_amount')
            valid_from = request.POST.get('valid_from')
            valid_to = request.POST.get('valid_to')
            is_active = request.POST.get('is_active') == 'on'
            
            # Basic validation
            if not code:
                messages.error(request, 'Coupon code is required')
                return redirect('coupon_list')
            
            # Handle dates
            current_date = timezone.now().date()
            
            # Set valid_from to current date if not provided
            if not valid_from:
                valid_from = current_date
            else:
                valid_from = timezone.datetime.strptime(valid_from, '%Y-%m-%d').date()
            
            # Set valid_to to 30 days from now if not provided
            if not valid_to:
                valid_to = current_date + timezone.timedelta(days=30)
            else:
                valid_to = timezone.datetime.strptime(valid_to, '%Y-%m-%d').date()
                
            # Validate dates
            if valid_from > valid_to:
                messages.error(request, 'Valid from date must be before valid to date')
                return redirect('coupon_list')
                
            # Validate coupon code uniqueness
            if Coupon.objects.filter(code__iexact=code).exists():
                messages.error(request, 'A coupon with this code already exists')
                return redirect('coupon_list')
            
            # Create coupon
            coupon = Coupon.objects.create(
                code=code,
                type=type,
                value=value,
                min_amount=min_amount,
                valid_from=valid_from,
                valid_to=valid_to,
                is_active=is_active
            )
            
            messages.success(request, f'Coupon "{code}" added successfully!')
            
        except Exception as e:
            messages.error(request, f'Error adding coupon: {str(e)}')
            
    return redirect('coupon_list')

@login_required(login_url='admin_login')
def edit_coupon(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    
    if request.method == 'POST':
        try:
            code = request.POST.get('code')
            type = request.POST.get('type')
            value = request.POST.get('value')
            min_amount = request.POST.get('min_amount')
            valid_from = request.POST.get('valid_from')
            valid_to = request.POST.get('valid_to')
            is_active = request.POST.get('is_active') == 'on'
            
            # Validate coupon code uniqueness
            if Coupon.objects.filter(code__iexact=code).exclude(pk=pk).exists():
                messages.error(request, 'A coupon with this code already exists')
                return redirect('coupon_list')
            
            # Update coupon
            coupon.code = code
            coupon.type = type
            coupon.value = value
            coupon.min_amount = min_amount
            coupon.valid_from = valid_from
            coupon.valid_to = valid_to
            coupon.is_active = is_active
            coupon.save()
            
            messages.success(request, 'Coupon updated successfully!')
            
        except Exception as e:
            messages.error(request, f'Error updating coupon: {str(e)}')
            
    return redirect('coupon_list')

@login_required(login_url='admin_login')
def delete_coupon(request, pk):
    try:
        coupon = get_object_or_404(Coupon, pk=pk)
        coupon.delete()
        messages.success(request, 'Coupon deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting coupon: {str(e)}')
    
    return redirect('coupon_list')

@login_required(login_url='admin_login')
def toggle_coupon_status(request, pk):
    try:
        coupon = get_object_or_404(Coupon, pk=pk)
        coupon.is_active = not coupon.is_active
        coupon.save()
        status = "activated" if coupon.is_active else "deactivated"
        messages.success(request, f'Coupon {status} successfully!')
    except Exception as e:
        messages.error(request, f'Error toggling coupon status: {str(e)}')
    
    return redirect('coupon_list')

@login_required(login_url='admin_login')
def generate_sales_report(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            report_type = data.get('report_type')
            start_date = data.get('start_date')
            end_date = data.get('end_date')

            # Set date range based on report type
            today = timezone.now().date()
            if report_type == 'daily':
                start_date = today
                end_date = today
            elif report_type == 'weekly':
                start_date = today - timedelta(days=6)
                end_date = today
            elif report_type == 'monthly':
                start_date = today - timedelta(days=29)
                end_date = today
            elif report_type == 'custom':
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            # Query orders within date range
            orders = Order.objects.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            ).exclude(status='cancelled')

            # Calculate overall summary
            summary_data = orders.aggregate(
                total_orders=Count('id'),
                total_amount=Sum('total_amount'),
                total_subtotal=Sum('subtotal'),
                total_coupon_discount=Sum('coupon_discount')
            )

            summary = {
                'total_orders': summary_data['total_orders'] or 0,
                'total_sales': float(summary_data['total_amount'] or 0),
                'total_discounts': float(summary_data['total_coupon_discount'] or 0)
            }

            # Get daily breakdown only for days with orders
            daily_data = []
            
            # Get unique dates that have orders
            order_dates = orders.values('created_at__date').distinct()
            
            for date_dict in order_dates:
                current_date = date_dict['created_at__date']
                daily_orders = orders.filter(created_at__date=current_date)
                
                daily_totals = daily_orders.aggregate(
                    order_count=Count('id'),
                    gross_sales=Sum('subtotal'),
                    coupon_discount=Sum('coupon_discount'),
                    net_sales=Sum('total_amount')
                )

                if daily_totals['order_count'] > 0:  # Only add if there are orders
                    daily_stats = {
                        'date': current_date.strftime('%d-%m-%Y'),
                        'orders': daily_totals['order_count'],
                        'gross_sales': float(daily_totals['gross_sales'] or 0),
                        'discounts': 0,  # Since we don't have total_discount field
                        'coupon_deductions': float(daily_totals['coupon_discount'] or 0),
                        'net_sales': float(daily_totals['net_sales'] or 0)
                    }
                    daily_data.append(daily_stats)

            # Sort daily data in reverse chronological order
            daily_data.sort(key=lambda x: datetime.strptime(x['date'], '%d-%m-%Y'), reverse=True)

            return JsonResponse({
                'status': 'success',
                'summary': summary,
                'details': daily_data
            })

        except Exception as e:
            print(f"Error in generate_sales_report: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)

@login_required(login_url='admin_login')
def download_sales_report_pdf(request):
    try:
        # Get filter parameters from request
        report_type = request.GET.get('report_type', 'daily')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        # Set date range based on report type
        today = timezone.now().date()
        if report_type == 'daily':
            start_date = today
            end_date = today
        elif report_type == 'weekly':
            start_date = today - timedelta(days=6)
            end_date = today
        elif report_type == 'monthly':
            start_date = today - timedelta(days=29)
            end_date = today
        elif report_type == 'custom' and start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        # Query orders
        orders = Order.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).exclude(status='cancelled')

        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )

        # Container for PDF elements
        elements = []

        # Styles
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            alignment=TA_CENTER
        ))

        # Add company header
        elements.append(Paragraph("BOOKSCARTZ", styles['CustomTitle']))
        elements.append(Spacer(1, 10))
        
        # Add report title and date range
        title = f"Sales Report ({start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')})"
        elements.append(Paragraph(title, ParagraphStyle(
            'SubTitle',
            parent=styles['Heading2'],
            fontSize=14,
            alignment=TA_CENTER,
            spaceAfter=20
        )))

        # Calculate summary
        summary_data = orders.aggregate(
            total_orders=Count('id'),
            total_amount=Sum('total_amount'),
            total_subtotal=Sum('subtotal'),
            total_coupon_discount=Sum('coupon_discount')
        )

        # Add summary table
        summary_table_data = [
            ['Summary', ''],
            ['Total Orders:', str(summary_data['total_orders'] or 0)],
            ['Gross Sales:', f"{float(summary_data['total_subtotal'] or 0):.2f}"],
            ['Total Discounts:', f"{float(summary_data['total_coupon_discount'] or 0):.2f}"],
            ['Net Sales:', f"{float(summary_data['total_amount'] or 0):.2f}"]
        ]
        
        summary_table = Table(summary_table_data, colWidths=[200, 200])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('SPAN', (0, 0), (1, 0)),  # Merge first row
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),  # Center the merged cell
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 1), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 30))

        # Add daily breakdown table
        daily_data = [['Date', 'Orders', 'Gross Sales', 'Discounts', 'Net Sales']]
        
        # Get unique dates that have orders
        order_dates = orders.values('created_at__date').distinct().order_by('-created_at__date')
        
        for date_dict in order_dates:
            current_date = date_dict['created_at__date']
            daily_orders = orders.filter(created_at__date=current_date)
            
            daily_totals = daily_orders.aggregate(
                order_count=Count('id'),
                gross_sales=Sum('subtotal'),
                coupon_discount=Sum('coupon_discount'),
                net_sales=Sum('total_amount')
            )

            if daily_totals['order_count'] > 0:
                daily_data.append([
                    current_date.strftime('%d-%m-%Y'),
                    str(daily_totals['order_count']),
                    f"₹{float(daily_totals['gross_sales'] or 0):.2f}",
                    f"₹{float(daily_totals['coupon_discount'] or 0):.2f}",
                    f"₹{float(daily_totals['net_sales'] or 0):.2f}"
                ])

        # Add table header
        elements.append(Paragraph("Daily Sales Breakdown", ParagraphStyle(
            'TableTitle',
            parent=styles['Heading3'],
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=10
        )))

        table = Table(daily_data, colWidths=[100, 80, 100, 100, 100])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),  # Right align amounts
        ]))
        elements.append(table)

        # Add footer
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(
            f"Generated on: {timezone.now().strftime('%d-%m-%Y %H:%M:%S')}",
            ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_RIGHT
            )
        ))

        # Build PDF
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()

        # Create response
        response = HttpResponse(content_type='application/pdf')
        filename = f"Bookscartz_Sales_Report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write(pdf)

        return response

    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return HttpResponse("Error generating PDF", status=500)