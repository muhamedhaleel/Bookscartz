from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import SignupForm
from adminapp.models import CustomUser
from django.core.exceptions import ValidationError

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        try:
            if form.is_valid():
                user = form.save()
                request.session['email'] = user.email
                messages.success(request, 'Please check your email for OTP verification.')
                return redirect('verify_otp')
            else:
                # Handle form errors more explicitly
                for field, errors in form.errors.items():
                    for error in errors:
                        if field == '__all__':
                            messages.error(request, f"Error: {error}")
                        else:
                            messages.error(request, f"{field.replace('_', ' ').title()}: {error}")
                
                # If there are non-field errors, display them as well
                if form.non_field_errors():
                    for error in form.non_field_errors():
                        messages.error(request, f"Error: {error}")
                        
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                for field, errors in e.message_dict.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
            else:
                messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'An unexpected error occurred: {str(e)}')
    else:
        form = SignupForm()
    
    return render(request, 'signup.html', {'form': form})

def verify_otp(request):
    email = request.session.get('email')
    if not email:
        messages.error(request, 'Please sign up first.')
        return redirect('signup')

    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        
        if not otp_input:
            messages.error(request, 'Please enter the OTP.')
            return render(request, 'verify_otp.html')

        try:
            user = CustomUser.objects.get(email=email)
            if user.otp == otp_input:
                user.is_active = True
                user.is_verified = True
                user.otp = None  # Clear OTP after verification
                user.save()
                login(request, user)
                messages.success(request, 'Email verified successfully! Welcome to Bookscartz.')
                return redirect('home')
            else:
                messages.error(request, 'Invalid OTP. Please try again.')
        except CustomUser.DoesNotExist:
            messages.error(request, 'User not found. Please sign up again.')
            return redirect('signup')
        except Exception as e:
            messages.error(request, 'An error occurred during verification. Please try again.')
    
    return render(request, 'verify_otp.html')

def home(request):
    return render(request, 'home.html')