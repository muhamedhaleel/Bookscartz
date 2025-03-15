from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Category, Brand, Product, Language, Offer, Order, ReturnRequest, OrderItem
from .forms import CategoryForm
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
import os
from django.db.models import Q
from django.core.files.images import get_image_dimensions
from PIL import Image
import os
from django.http import JsonResponse
from django.db.models.query import Prefetch
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie



# ----------------------------
# Admin Authentication
# ----------------------------
def admin_login(request):
    # If user is already logged in and is staff, redirect to dashboard
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid Credentials or Not an Admin')

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
        
        context = {
            'product_count': product_count,
            'category_count': category_count,
            'brand_count': brand_count,
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
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        image = request.FILES.get('image')

        if not name or len(name) < 3:
            messages.error(request, "Brand name must be at least 3 characters.")
            return redirect('brand_list')

        if Brand.objects.filter(name=name).exists():
            messages.error(request, "Brand already exists.")
            return redirect('brand_list')

        if image:
            # Validate file size
            if image.size > 1 * 1024 * 1024:  # 1 MB
                messages.error(request, "Image file size must be less than 1 MB.")
                return redirect('brand_list')

            # Validate file type
            try:
                img = Image.open(image)
                img.verify()
                img_format = img.format.lower()
                if img_format not in ['jpeg', 'png', 'gif']:
                    messages.error(request, "Unsupported file type. Only JPEG, PNG, and GIF are allowed.")
                    return redirect('brand_list')
            except Exception as e:
                messages.error(request, "Invalid image file.")
            return redirect('brand_list')

        try:
            brand = Brand.objects.create(name=name, image=image)
            messages.success(request, "Publisher added successfully!")
        except Exception as e:
            messages.error(request, f"Error adding publisher: {str(e)}")
        
        return redirect('brand_list')

    return render(request, 'add_brand.html')

@login_required(login_url='admin_login')
def edit_brand(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        image = request.FILES.get('image')
        
        if not name or len(name) < 3:
            messages.error(request, "Publisher name must be at least 3 characters.")
            return redirect('brand_list')

        # Check if the new name already exists for other brands
        if Brand.objects.filter(name=name).exclude(pk=pk).exists():
            messages.error(request, "A publisher with this name already exists.")
            return redirect('brand_list')

        try:
            brand.name = name
            if image:
                # Delete old image if it exists
                if brand.image:
                    if os.path.isfile(brand.image.path):
                        os.remove(brand.image.path)
                brand.image = image
            brand.save()
            messages.success(request, "Publisher updated successfully!")
        except Exception as e:
            messages.error(request, f"Error updating publisher: {str(e)}")
        
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
            
            # Validate required fields
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
        'status_choices': Order.STATUS_CHOICES
    }
    return render(request, 'admin_mange_order.html', context)

@login_required(login_url='admin_login')
def get_return_details(request, order_id):
    if not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
    
    try:
        # Get order and return request
        order = get_object_or_404(Order, id=order_id)
        return_request = order.return_request.select_related('order').first()
        
        if not return_request:
            return JsonResponse({
                'status': 'error',
                'message': 'Return request not found'
            }, status=404)
            
        # Get returned items with their details
        returned_items = order.items.filter(return_requested=True).select_related('product')
        
        # Format the response data
        response_data = {
            'status': 'success',
            'order_id': order.id,
            'customer_name': f"{order.user.first_name} {order.user.last_name}",
            'created_at': return_request.created_at.strftime('%B %d, %Y'),
            'status': return_request.status,
            'reason': return_request.get_reason_display(),
            'comments': return_request.comments,
            'items': []
        }
        
        # Add item details
        for item in returned_items:
            try:
                item_data = {
                    'name': item.product.name,
                    'quantity': item.quantity,
                    'price': str(item.price),
                    'image': request.build_absolute_uri(item.product.image1.url) if item.product.image1 else '',
                    'return_status': item.return_status
                }
                response_data['items'].append(item_data)
            except Exception as e:
                print(f"Error processing item {item.id}: {str(e)}")
                continue
        
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
            
            # Update order items and inventory
            returned_items = order.items.filter(return_requested=True)
            all_items_returned = True  # Flag to check if all items are returned
            
            for item in returned_items:
                item.return_status = status
                item.save()
                
                if status == 'approved':
                    # Update inventory - add back to stock
                    product = item.product
                    product.stock += item.quantity
                    product.save()
                else:
                    all_items_returned = False
            
            # Update order status if all items are approved for return
            if status == 'approved' and all_items_returned:
                order.status = 'returned'
                order.save()
            
            # Send notification to user (you can implement this)
            message = 'Return request approved' if status == 'approved' else 'Return request rejected'
            if admin_notes:
                message += f"\nAdmin Notes: {admin_notes}"
            
            return JsonResponse({
                'status': 'success',
                'message': f'Return request has been {status} successfully'
            })
            
    except Exception as e:
        print(f"Error handling return: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Error processing return request'
        }, status=500)

@login_required(login_url='admin_login')
def update_order_status(request, order_id):
    if not request.user.is_staff:
        messages.error(request, 'Unauthorized access')
        return redirect('admin_login')
        
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        
        # Don't allow status changes for cancelled orders
        if order.status == 'cancelled':
            messages.error(request, 'Cannot modify cancelled orders')
            return redirect('admin_manage_orders')
            
        # Define valid status transitions
        valid_transitions = {
            'pending': ['conformed'],
            'conformed': ['shipped'],
            'shipped': ['delivered'],
            'delivered': []  # Remove the returned option
        }
        
        # Check if the transition is valid
        if order.status in valid_transitions and new_status in valid_transitions.get(order.status, []):
            order.status = new_status
            order.save()
            messages.success(request, f'Order #{order.id} status updated to {order.get_status_display()}')
        else:
            messages.error(request, f'Invalid status transition from {order.get_status_display()} to {new_status}')
            
    return redirect('admin_manage_orders')
