from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import SignupForm
from adminapp.models import CustomUser 
from .forms import SignupForm

def signup(request):
    if request.method == 'POST':
        print("posted?????????")
        form = SignupForm(request.POST)
        if form.is_valid():
            print("...........valid and saved")
            user = form.save(commit=True)  
            user.save()
            request.session['email'] = user.email 
            return redirect('verify_otp')
        else:
            print("form is invalid...")
            for field, errors in form.errors.items():
                print(f"Validation error in {field}: {errors}")
    else:
        print(".............is unvalid")
        
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

def home(request):
    return render(request,'home.html')

def verify_otp(request):
    if request.method == 'POST':
        email = request.session.get('email')
        otp_input = request.POST.get('otp')
        try:
            user = CustomUser.objects.get(email=email)
            if user.otp == otp_input:
                user.is_active = True
                user.is_verified = True
                user.otp = None  # Clear OTP after verification
                user.save()
                login(request, user)
                return redirect('home')
            else:
                return render(request, 'verify_otp.html', {'error': 'Invalid OTP'})
        except CustomUser.DoesNotExist:
            return redirect('signup')
    return render(request, 'verify_otp.html')