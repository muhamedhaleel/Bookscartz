from django.shortcuts import render
from django.shortcuts import render, redirect
from .forms import SignupForm
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import LoginForm
from django.shortcuts import render
from django.shortcuts import render
#from .models import Category,Book



def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully!')
            return redirect('login')  # Redirect to login after successful signup
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SignupForm()
    return render(request,'signup.html',{'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('home')  # Redirect to a homepage or dashboard
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid login details.')
    else:
        form = LoginForm()
    return render(request,'login.html',{'form': form})

def home(request):
    # categories = Category.objects.all()
    # # Assuming 'category_type' is a field in the Book model
    # best_sellers = Book.objects.filter(category_type='best_seller')
    # new_releases = Book.objects.filter(category_type='new_release')
    # new_launches = Book.objects.filter(category_type='new_launch')

    # context = {
    #     'categories': categories,
    #     'best_sellers': best_sellers,
    #     'new_releases': new_releases,
    #     'new_launches': new_launches,
    # }
    return render(request, 'home.html')

