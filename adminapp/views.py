from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
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
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid Credentials or Not an Admin')

    return render(request, 'admin_login.html')  


# ----------------------------
#  Admin Dashboard
# ----------------------------
@login_required(login_url='admin_login')
def admin_dashboard(request):
    return render(request, 'admi_home.html')  


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
def admin_dashboard(request):
     return render(request,'admi_home.html')  

@login_required(login_url='admin_login')
def admin_publisher(request):
     return render(request,'admin_publisher.html')


    
    # Filter products based on search query
    



login_required(login_url='admin_login')
def admin_products(request):
    try:
        search_query = request.GET.get('search', '')
        products = Product.objects.select_related('category', 'brand', 'language').all()
        
        if search_query:
            products = products.filter(
                Q(name__icontains=search_query) |
                Q(category__name__icontains=search_query) |
                Q(brand__name__icontains=search_query)
            )
        
        # Get active categories, brands and languages for the modal
        categories = Category.objects.filter(is_active=True)
        brands = Brand.objects.filter(is_active=True)
        languages = Language.objects.filter(is_active=True)
        
        context = {
            'products': products,
            'search_query': search_query,
            'categories': categories,
            'brands': brands,
            'languages': languages
        }
        return render(request, 'admin_product.html', context)
    except Exception as e:
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
            if not all([name, description, category_id, brand_id, price, stock, image1]):
                messages.error(request, "Please fill all required fields")
                return redirect('admin_product')

            # Create new product
            product = Product.objects.create(
                name=name,
                description=description,
                category_id=category_id,
                brand_id=brand_id,
                language_id=language_id if language_id else None,
                price=price,
                stock=stock,
                image1=image1,
                image2=image2,
                image3=image3
            )
            messages.success(request, "Product added successfully!")
            
        except Exception as e:
            messages.error(request, f"Error adding product: {str(e)}")
        
        return redirect('admin_product')

    # If GET request, redirect to products page
    return redirect('admin_products')