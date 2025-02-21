# from django.shortcuts import render
# # Create your views here.
# from django.shortcuts import render, redirect
# from django.contrib.auth import authenticate, login
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages
# from django.http import HttpResponse
# from django.contrib.auth.decorators import login_required
# from django.shortcuts import render, redirect, get_object_or_404
# from .models import Category
# from .forms import CategoryForm
# from django.contrib import messages



# # Admin Login
# def admin_login(request):
#     if request.method == 'POST':
#         username = request.POST['username']
#         password = request.POST['password']
#         user = authenticate(request, username=username, password=password)

#         if user is not None and user.is_staff:
#             login(request, user)
#             return redirect('admin_dashboard')
#         else:
#             messages.error(request, 'Invalid Credentials or Not an Admin')

#     return render(request, 'admin_login.html')  # ✅ App folder included



# # Admin Dashboard
# @login_required(login_url='admin_login')
# def admin_dashboard(request):
#     return render(request,'admi_home.html')
# def admin_category(request):
#     return render(request,'admin_category.html')
# def admin_brand(request):
#     return render(request,'admin_brand.html')
# def admin_products(request):
#     return render(request,'admin_products.html')
# def admin_caustomers(request):
#     return render(request,'admin_caustomer.html')

# def category_list(request):
#     categories = Category.objects.all().order_by('-added_on')
#     form = CategoryForm()
#     if request.method == 'POST':
#         form = CategoryForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Category added successfully!')
#             return redirect('category_list')
#     return render(request, 'admin/category.html', {'categories': categories, 'form': form})

# def toggle_category_status(request, pk):
#     category = get_object_or_404(Category, pk=pk)
#     category.is_active = not category.is_active
#     category.save()
#     status = "Unblocked" if category.is_active else "Blocked"
#     messages.success(request, f'Category {status} successfully!')
#     return redirect('category_list')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Category
from .forms import CategoryForm

# ----------------------------
# ✅ Admin Authentication
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
# ✅ Admin Dashboard
# ----------------------------
@login_required(login_url='admin_login')
def admin_dashboard(request):
    return render(request, 'admin_home.html')  


# ----------------------------
# ✅ Category List & Add
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

    return render(request,'admin_category.html', {'categories': categories, 'form': form})


# ----------------------------
# ✅ Toggle Category Status (Block/Unblock)
# ----------------------------
@login_required(login_url='admin_login')
def toggle_category_status(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.is_active = not category.is_active
    category.save()
    status = "Unblocked" if category.is_active else "Blocked"
    messages.success(request, f'Category {status} successfully!')
    return redirect('category_list')


 
# ✅ Other Admin Views
# ----------------------------
@login_required(login_url='admin_login')
def admin_dashboard(request):
     return render(request,'admi_home.html')  

@login_required(login_url='admin_login')
def admin_brand(request):
     return render(request,'admin_brand.html')

@login_required(login_url='admin_login')
def admin_products(request):
    return render(request,'admin_addproducts.html')

@login_required(login_url='admin_login')
def admin_customers(request):
    return render(request,'admin_caustomer.html')  # Corrected typo in filename
