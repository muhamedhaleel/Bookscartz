from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import SignupForm
from adminapp.models import CustomUser 


def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)  
            user.save()
            login(request, user)
            return redirect('home')  
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

def home(request):
    return render(request,'home.html')