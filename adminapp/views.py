

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Category
from .forms import CategoryForm
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Brand



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

    return render(request, 'admin_category.html', {'categories': categories, 'form': form})


@login_required(login_url='admin_login')
def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=category)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('category_list')
        else:
            messages.error(request, 'Error updating category.')

    return render(request, 'admin_edit_category.html', {'form': form, 'category': category})


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
def brand_list(request):
    search_query = request.GET.get('q', '')
    brand_list = Brand.objects.filter(name__icontains=search_query).order_by('-added_on')

    paginator = Paginator(brand_list, 10)  # 10 brands per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin_publisher.html', {'page_obj': page_obj, 'search_query': search_query})

# Add Brand View
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

        Brand.objects.create(name=name, image=image)
        messages.success(request, "Brand added successfully.")
        return redirect('brand_list')

    return redirect('brand_list')  

# Edit Brand View
def edit_brand(request, pk):
    brand = get_object_or_404(Brand, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name')
        image = request.FILES.get('image')

        if name and len(name) >= 3:
            brand.name = name
        if image:
            brand.image = image

        brand.save()
        messages.success(request, "Brand updated successfully.")
        return redirect('brand_list')

    return redirect('brand_list')  # Redirect if not a POST request

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
def admin_dashboard(request):
     return render(request,'admi_home.html')  

@login_required(login_url='admin_login')
def admin_publisher(request):
     return render(request,'admin_publisher.html')

@login_required(login_url='admin_login')
def admin_products(request):
    return render(request,'admin_addproducts.html')

@login_required(login_url='admin_login')
def admin_customers(request):
    return render(request,'admin_caustomer.html')  # Corrected typo in filename

