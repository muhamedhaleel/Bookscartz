from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from .forms import SignupForm
from adminapp.models import CustomUser
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required

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

@login_required
def home(request):
    return render(request, 'home.html', {'user': request.user})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Log the user in
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')  # Replace 'home' with the name of your desired URL pattern
        else:
            # Add error message for invalid credentials
            messages.error(request, "Invalid username or password. Please try again.")
    
    return render(request, 'login.html')

@login_required
def user_profile(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        phone_number = request.POST.get('phone')
        user = request.user
        try:
            user.username = username
            user.phone_number = phone_number
            user.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')  # Redirect to the profile page
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
    return render(request, 'profile.html', {'user': request.user})

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')  # Redirect to the login page after logout

@login_required
def reset_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        user = request.user

        # Check if the current password is correct
        if user.check_password(current_password):
            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Your password has been changed successfully!')
                return redirect('profile')  # Redirect to the profile page
            else:
                messages.error(request, 'New passwords do not match.')
        else:
            messages.error(request, 'Current password is incorrect.')
    return render(request, 'profile.html', {'user': request.user})  # Render the profile page

@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        user = request.user

        # Check if the current password is correct
        if user.check_password(current_password):
            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Your password has been changed successfully!')
            else:
                messages.error(request, 'New passwords do not match.')
        else:
            messages.error(request, 'Current password is incorrect.')

    # Render the profile page with the user context and messages
    return render(request, 'profile.html', {'user': request.user})

