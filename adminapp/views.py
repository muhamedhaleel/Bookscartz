from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
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
from django.db.models.functions import TruncDate, TruncMonth, TruncYear



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
    if not request.user.is_staff:
        messages.error(request, 'Unauthorized access')
        return redirect('admin_login')

    # Get search query
    search_query = request.GET.get('search', '')
    
    try:
        # Get all products with related data
        products = Product.objects.select_related('category', 'brand', 'primary_language', 'secondary_language', 'tertiary_language').order_by('-added_on')
        
        # Apply search filter if search query exists
        if search_query:
            products = products.filter(
                Q(name__icontains=search_query) |
                Q(category__name__icontains=search_query) |
                Q(brand__name__icontains=search_query) |
                Q(primary_language__name__icontains=search_query) |
                Q(secondary_language__name__icontains=search_query) |
                Q(tertiary_language__name__icontains=search_query)
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
        messages.error(request, f'Error loading products: {str(e)}')
        context = {
            'products': [],
            'categories': Category.objects.filter(is_active=True),
            'brands': Brand.objects.filter(is_active=True),
            'languages': Language.objects.filter(is_active=True),
            'search_query': search_query
        }
        return render(request, 'admin_product.html', context)

@login_required(login_url='admin_login')
def add_product(request):
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            description = request.POST.get('description')
            category_id = request.POST.get('category')
            brand_id = request.POST.get('brand')
            price = request.POST.get('price')
            stock = request.POST.get('stock')
            image1 = request.FILES.get('image1')
            image2 = request.FILES.get('image2')
            image3 = request.FILES.get('image3')
            
            # Get language IDs
            primary_language_id = request.POST.get('primary_language')
            secondary_language_id = request.POST.get('secondary_language')
            tertiary_language_id = request.POST.get('tertiary_language')
            
            if not all([name, description, category_id, brand_id, price, stock, image1]):
                messages.error(request, "Please fill all required fields")
                return redirect('admin_products')

            # Create product
            product = Product.objects.create(
                name=name,
                description=description,
                category_id=category_id,
                brand_id=brand_id,
                price=price,
                stock=stock,
                image1=image1,
                image2=image2,
                image3=image3,
                primary_language_id=primary_language_id if primary_language_id else None,
                secondary_language_id=secondary_language_id if secondary_language_id else None,
                tertiary_language_id=tertiary_language_id if tertiary_language_id else None,
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
            
            # Handle optional languages
            primary_language_id = request.POST.get('primary_language')
            secondary_language_id = request.POST.get('secondary_language')
            tertiary_language_id = request.POST.get('tertiary_language')
            
            # Set all languages as optional
            product.primary_language_id = primary_language_id if primary_language_id else None
            product.secondary_language_id = secondary_language_id if secondary_language_id else None
            product.tertiary_language_id = tertiary_language_id if tertiary_language_id else None
            
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
            'return_requests',
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
        return_requests = order.return_requests.select_related('order_item', 'order_item__product').all()
        
        if not return_requests:
            return JsonResponse({
                'status': 'error',
                'message': 'No return requests found'
            }, status=404)
        
        response_data = {
            'status': 'success',
            'order_id': order.id,
            'customer_name': f"{order.user.first_name} {order.user.last_name}",
            'items': []
        }
        
        for return_request in return_requests:
            item = return_request.order_item
            response_data['items'].append({
                'id': return_request.id,
                'name': item.product.name,
                'quantity': item.quantity,
                'price': str(item.price),
                'total': str(item.total_price),
                'image': request.build_absolute_uri(item.product.image1.url) if item.product.image1 else '',
                'return_status': return_request.status,
                'reason': return_request.get_reason_display(),
                'comments': return_request.comments
            })
        
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
            return_request_id = request.POST.get('return_request_id')
            
            if not return_request_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Return request ID is required'
                }, status=400)
            
            return_request = get_object_or_404(ReturnRequest, id=return_request_id, order=order)
            status = request.POST.get('return_status')
            admin_notes = request.POST.get('admin_notes', '').strip()
            
            if not status or status not in ['approved', 'rejected']:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid status'
                }, status=400)
            
            if not admin_notes:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Admin notes are required'
                }, status=400)
            
            # Update return request status and notes
            return_request.status = status
            return_request.admin_notes = admin_notes
            return_request.save()
            
            # Get the specific order item being returned
            order_item = return_request.order_item
            
            if status == 'approved':
                # Calculate refund amount for this item
                refund_amount = order_item.total_price
                
                # Update inventory
                product = order_item.product
                product.stock += order_item.quantity
                product.save()
                
                # Update item return status
                order_item.return_status = status
                order_item.save()
                
                # Add refund amount to user's wallet
                wallet, created = Wallet.objects.get_or_create(user=order.user)
                wallet.balance += refund_amount
                wallet.save()
                
                # Create wallet transaction record
                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=refund_amount,
                    type='credit',
                    order_id=str(order.id)
                )
                
                message = f'Return request approved. Refund amount of ₹{refund_amount} has been added to wallet.'
            else:
                # Update item return status to rejected
                order_item.return_status = status
                order_item.save()
                message = 'Return request has been rejected.'
            
            # Check if all items are returned and update order status
            order.check_return_status()
            
            return JsonResponse({
                'status': 'success',
                'message': message
            })
            
    except ReturnRequest.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Return request not found'
        }, status=404)
    except Exception as e:
        print(f"Error handling return: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
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
            page_number = data.get('page', 1)  # Get page number from request
            items_per_page = 10  # Number of orders per page

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

            # Query orders within date range with related data
            orders = Order.objects.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            ).select_related('user').prefetch_related('items').order_by('-created_at')

            # Calculate overall summary
            summary_data = orders.aggregate(
                total_orders=Count('id'),
                total_amount=Sum('total_amount'),
                total_discounts=Sum('coupon_discount')
            )

            summary = {
                'total_orders': summary_data['total_orders'] or 0,
                'total_sales': float(summary_data['total_amount'] or 0),
                'total_discounts': float(summary_data['total_discounts'] or 0)
            }

            # Apply pagination
            paginator = Paginator(orders, items_per_page)
            try:
                current_page = paginator.page(page_number)
            except:
                current_page = paginator.page(1)

            # Format order data for current page
            order_data = []
            for order in current_page:
                order_data.append({
                    'order_id': order.id,
                    'date': order.created_at.strftime('%Y-%m-%d %H:%M'),
                    'customer_name': f"{order.user.username}",
                    'items_count': order.items.count(),
                    'payment_method': order.payment_method,
                    'status': order.status,
                    'gross_amount': float(order.subtotal or 0),
                    'discounts': float(order.coupon_discount or 0),
                    'net_amount': float(order.total_amount or 0)
                })

            # Add pagination info
            pagination_info = {
                'current_page': current_page.number,
                'total_pages': paginator.num_pages,
                'has_next': current_page.has_next(),
                'has_previous': current_page.has_previous(),
                'total_items': paginator.count
            }

            return JsonResponse({
                'status': 'success',
                'summary': summary,
                'orders': order_data,
                'pagination': pagination_info
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

        # Query orders with related data
        orders = Order.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).select_related('user').prefetch_related('items').order_by('-created_at')

        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        # Container for PDF elements
        elements = []

        # Define theme colors
        PRIMARY_COLOR = colors.HexColor('#2c3e50')  # Dark blue-grey
        SECONDARY_COLOR = colors.HexColor('#34495e')  # Lighter blue-grey
        ACCENT_COLOR = colors.HexColor('#3498db')  # Bright blue
        TEXT_COLOR = colors.HexColor('#2c3e50')  # Dark text
        LIGHT_BG = colors.HexColor('#ecf0f1')  # Light background
        ALT_ROW_COLOR = colors.HexColor('#f9f9f9')  # Alternating row color

        # Custom styles
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='CompanyHeader',
            parent=styles['Heading1'],
            fontSize=28,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=PRIMARY_COLOR
        ))
        
        styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=styles['Heading2'],
            fontSize=18,
            spaceBefore=10,
            spaceAfter=25,
            alignment=TA_CENTER,
            textColor=SECONDARY_COLOR
        ))

        # Add company header with a line below
        elements.append(Paragraph("BOOKSCARTZ", styles['CompanyHeader']))
        elements.append(Table([['']], colWidths=[515], style=TableStyle([
            ('LINEBELOW', (0, 0), (-1, -1), 2, PRIMARY_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ])))
        
        # Add report title and date range
        title = f"Sales Report ({start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')})"
        elements.append(Paragraph(title, styles['ReportTitle']))

        # Calculate summary
        summary_data = orders.aggregate(
            total_orders=Count('id'),
            total_amount=Sum('total_amount'),
            total_subtotal=Sum('subtotal'),
            total_coupon_discount=Sum('coupon_discount')
        )

        # Add summary table with improved styling
        summary_table_data = [
            ['SUMMARY', ''],
            ['Total Orders:', str(summary_data['total_orders'] or 0)],
            ['Gross Sales:', f"{float(summary_data['total_subtotal'] or 0):,.2f}"],
            ['Total Discounts:', f"{float(summary_data['total_coupon_discount'] or 0):,.2f}"],
            ['Net Sales:', f"{float(summary_data['total_amount'] or 0):,.2f}"]
        ]
        
        summary_table = Table(summary_table_data, colWidths=[200, 200])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('SPAN', (0, 0), (1, 0)),  # Merge first row
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
            ('BACKGROUND', (0, 1), (-1, -1), LIGHT_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d7d7d7')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, PRIMARY_COLOR),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 30))

        # Add order details section title
        elements.append(Paragraph("ORDER DETAILS", ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading3'],
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=15,
            textColor=PRIMARY_COLOR
        )))

        # Create order details table with improved styling
        order_data = [['Order ID', 'Date & Time', 'Customer', 'Items', 'Payment', 'Status', 'Gross Amount', 'Discount', 'Net Amount']]
        
        # Add order rows with status color coding
        for order in orders:
            status_color = {
                'pending': colors.orange,
                'processing': ACCENT_COLOR,
                'shipped': colors.purple,
                'delivered': colors.green,
                'cancelled': colors.red,
                'returned': colors.grey,
            }.get(order.status, colors.black)

            order_data.append([
                f"#{order.id}",
                order.created_at.strftime('%d-%m-%Y %H:%M'),
                order.user.username,
                str(order.items.count()),
                order.payment_method,
                order.status.title(),
                f"{float(order.subtotal or 0):,.2f}",
                f"{float(order.coupon_discount or 0):,.2f}",
                f"{float(order.total_amount or 0):,.2f}"
            ])

        # Add totals row
        order_data.append([
            'TOTAL',
            '',
            '',
            str(sum(order.items.count() for order in orders)),
            '',
            '',
            f"{float(summary_data['total_subtotal'] or 0):,.2f}",
            f"{float(summary_data['total_coupon_discount'] or 0):,.2f}",
            f"{float(summary_data['total_amount'] or 0):,.2f}"
        ])

        # Create and style the order details table
        col_widths = [45, 75, 70, 35, 60, 55, 65, 55, 65]
        order_table = Table(order_data, colWidths=col_widths, repeatRows=1)
        order_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
            ('BACKGROUND', (0, 1), (-1, -2), colors.white),
            ('BACKGROUND', (0, -1), (-1, -1), LIGHT_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('ALIGN', (6, 1), (-1, -1), 'RIGHT'),  # Right align amount columns
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d7d7d7')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, PRIMARY_COLOR),
            ('LINEABOVE', (0, -1), (-1, -1), 2, PRIMARY_COLOR),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, ALT_ROW_COLOR]),
        ]))
        elements.append(order_table)

        # Add footer with generation info
        elements.append(Spacer(1, 30))
        elements.append(Table([['']], colWidths=[515], style=TableStyle([
            ('LINEABOVE', (0, 0), (-1, -1), 1, colors.HexColor('#d7d7d7')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ])))
        elements.append(Paragraph(
            f"Generated on: {timezone.now().strftime('%d-%m-%Y %H:%M:%S')}",
            ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=SECONDARY_COLOR,
                alignment=TA_RIGHT,
                spaceBefore=5
            )
        ))

        # Build PDF
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()

        # Create response
        response = HttpResponse(content_type='application/pdf')
        filename = f"Bookscartz_Sales_Report_{start_date.strftime('%d%m%Y')}_{end_date.strftime('%d%m%Y')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write(pdf)

        return response

    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return HttpResponse("Error generating PDF", status=500)

def sales_analytics(request):
    period = request.GET.get('period', 'yearly')
    
    if period == 'yearly':
        orders = Order.objects.annotate(
            date=TruncYear('created_at')
        ).values('date').annotate(
            total=Sum('total_amount')
        ).order_by('date')
    elif period == 'monthly':
        orders = Order.objects.annotate(
            date=TruncMonth('created_at')
        ).values('date').annotate(
            total=Sum('total_amount')
        ).order_by('date')
    elif period == 'weekly':
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=12)
        orders = Order.objects.filter(
            created_at__range=[start_date, end_date]
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            total=Sum('total_amount')
        ).order_by('date')
    else:  # daily
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        orders = Order.objects.filter(
            created_at__range=[start_date, end_date]
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            total=Sum('total_amount')
        ).order_by('date')

    labels = [order['date'].strftime('%Y-%m-%d') for order in orders]
    values = [float(order['total']) for order in orders]

    return JsonResponse({
        'labels': labels,
        'values': values
    })

def top_products(request):
    products = OrderItem.objects.values(
        'product__name'
    ).annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:10]

    return JsonResponse({
        'labels': [item['product__name'] for item in products],
        'values': [item['total_quantity'] for item in products]
    })

def top_categories(request):
    categories = OrderItem.objects.values(
        'product__category__name'
    ).annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:10]

    return JsonResponse({
        'labels': [item['product__category__name'] for item in categories],
        'values': [item['total_quantity'] for item in categories]
    })

def top_publishers(request):
    publishers = OrderItem.objects.values(
        'product__brand__name'
    ).annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:10]

    return JsonResponse({
        'labels': [item['product__brand__name'] for item in publishers],
        'values': [item['total_quantity'] for item in publishers]
    })

def is_admin(user):
    return user.is_authenticated and user.is_superuser

@login_required(login_url='admin_login')
@user_passes_test(is_admin)
def admin_wallets(request):
    # Get all wallet transactions ordered by date (most recent first)
    transactions = WalletTransaction.objects.select_related(
        'wallet', 
        'wallet__user'
    ).order_by('-date')
    
    # Pagination
    paginator = Paginator(transactions, 10)  # Show 10 transactions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'transactions': page_obj,
    }
    return render(request, 'admin_wallets.html', context)