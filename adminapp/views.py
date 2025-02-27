from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Category, Brand,Product, Language
from .forms import CategoryForm
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
import os
from django.db.models import Q




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


# ----------------------------
#  Category List & Add
# ----------------------------
# @login_required(login_url='admin_login')
# def category_list(request):
#     categories = Category.objects.all().order_by('-added_on')
#     form = CategoryForm()

#     if request.method == 'POST':
#         form = CategoryForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Category added successfully!')
#             # return redirect('category_list')
#         else:
#             messages.error(request, 'Error adding category. Please try again.')

#     return render(request,'admin_category.html', {'categories': categories, 'form': form})

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
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added successfully!')
            return redirect('category_list')
        else:
            messages.error(request, 'Error adding category. Please try again.')

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
        name = request.POST.get('name')
        if name:
            # Check if the new name already exists for other categories
            if Category.objects.filter(name=name).exclude(pk=pk).exists():
                messages.error(request, 'A category with this name already exists.')
            else:
                category.name = name
                category.save()
                messages.success(request, 'Category updated successfully!')
        return redirect('category_list')

    return redirect('category_list')


@login_required(login_url='admin_login')
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.is_active = not category.is_active
    category.save()
    messages.success(request, 'Category deleted successfully!')
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
        name = request.POST.get('name')
        image = request.FILES.get('image')

        if not name or len(name) < 3:
            messages.error(request, "Brand name must be at least 3 characters.")
            return redirect('brand_list')

        if Brand.objects.filter(name=name).exists():
            messages.error(request, "Brand already exists.")
            return redirect('brand_list')

        try:
            brand = Brand.objects.create(name=name, image=image)
            messages.success(request, "Brand added successfully.")
        except Exception as e:
            messages.error(request, f"Error adding brand: {str(e)}")
        
        return redirect('brand_list')

# Edit Brand View
@login_required(login_url='admin_login')
def edit_brand(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        image = request.FILES.get('image')
        
        if not name or len(name) < 3:
            messages.error(request, "Brand name must be at least 3 characters.")
            return redirect('brand_list')

        # Check if the new name already exists for other brands
        if Brand.objects.filter(name=name).exclude(pk=pk).exists():
            messages.error(request, "A brand with this name already exists.")
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
            messages.success(request, "Brand updated successfully.")
        except Exception as e:
            messages.error(request, f"Error updating brand: {str(e)}")
        
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
def admin_customers(request):
    return render(request,'admin_caustomer.html')  # Corrected typo in filename



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
            language_name = request.POST.get('language')
            price = request.POST.get('price')
            stock = request.POST.get('stock')
            image1 = request.FILES.get('image1')
            image2 = request.FILES.get('image2')
            image3 = request.FILES.get('image3')

            # Validate required fields
            if not all([name, description, category_id, brand_id, language_name, price, stock, image1]):
                messages.error(request, "Please fill all required fields")
                return redirect('admin_products')

            # Get or create language with just the name
            language, _ = Language.objects.get_or_create(
                name=language_name.strip(),
                defaults={'is_active': True}
            )

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
            language_name = request.POST.get('language')
            language, _ = Language.objects.get_or_create(name=language_name.strip())
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