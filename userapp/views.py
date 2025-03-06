from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import SignupForm
from adminapp.models import CustomUser
from django.core.exceptions import ValidationError
import random

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        try:
            if form.is_valid():
                # Don't save the user yet, store form data in session
                user_data = {
                    'username': form.cleaned_data['username'],
                    'email': form.cleaned_data['email'],
                    'phone_number': form.cleaned_data['phone_number'],
                    'password': form.cleaned_data['password1']
                }
                request.session['user_data'] = user_data
                
                # Generate OTP
                otp = str(random.randint(100000, 999999))
                request.session['otp'] = otp
                
                # Send OTP email (you can customize this part)
                try:
                    from django.core.mail import send_mail
                    subject = 'Your OTP for Bookscartz Registration'
                    message = f'Your OTP is: {otp}'
                    from_email = 'your-email@example.com'  # Update with your email
                    recipient_list = [user_data['email']]
                    send_mail(subject, message, from_email, recipient_list)
                    messages.success(request, 'Please check your email for OTP verification.')
                except Exception as e:
                    messages.error(request, f'Error sending OTP: {str(e)}')
                    return render(request, 'signup.html', {'form': form})
                
                return redirect('verify_otp')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        if field == '__all__':
                            messages.error(request, f"Error: {error}")
                        else:
                            messages.error(request, f"{field.replace('_', ' ').title()}: {error}")
                
        except Exception as e:
            messages.error(request, f'An unexpected error occurred: {str(e)}')
    else:
        form = SignupForm()
    
    return render(request, 'signup.html', {'form': form})

def verify_otp(request):
    user_data = request.session.get('user_data')
    stored_otp = request.session.get('otp')
    
    if not user_data or not stored_otp:
        messages.error(request, 'Please sign up first.')
        return redirect('signup')

    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        
        if not otp_input:
            messages.error(request, 'Please enter the OTP.')
            return render(request, 'verify_otp.html')

        if otp_input == stored_otp:
            try:
                # Create and save the user
                user = CustomUser.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    phone_number=user_data['phone_number'],
                    password=user_data['password']
                )
                user.is_active = True
                user.is_verified = True
                user.save()
                
                # Clear session data
                del request.session['user_data']
                del request.session['otp']
                
                # Log the user in
                login(request, user)
                messages.success(request, 'Account created successfully! Welcome to Bookscartz.')
                return redirect('home')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
    
    return render(request, 'verify_otp.html')

def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            # First try to get the user by username
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_verified:
                    login(request, user)
                    messages.success(request, 'Login successful!')
                    return redirect('home')
                else:
                    messages.error(request, 'Please verify your email first.')
            else:
                # If username login fails, try with email
                try:
                    user_obj = CustomUser.objects.get(email=username)
                    user = authenticate(request, username=user_obj.username, password=password)
                    if user is not None:
                        if user.is_verified:
                            login(request, user)
                            messages.success(request, 'Login successful!')
                            return redirect('home')
                        else:
                            messages.error(request, 'Please verify your email first.')
                    else:
                        messages.error(request, "Invalid credentials.")
                except CustomUser.DoesNotExist:
                    messages.error(request, "Invalid credentials.")
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
    
    return render(request, 'login.html')

@login_required(login_url='login_user')
def home(request):
    return render(request, 'home.html', {'user': request.user})

@login_required(login_url='login_user')
def profile(request):
    user = request.user
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            try:
                # Update user information
                user.phone_number = request.POST.get('phone_number', user.phone_number)
                user.address = request.POST.get('address', '')
                user.city = request.POST.get('city', '')
                user.state = request.POST.get('state', '')
                user.pincode = request.POST.get('pincode', '')
                
                # Handle date of birth
                date_of_birth = request.POST.get('date_of_birth')
                if date_of_birth:
                    user.date_of_birth = date_of_birth
                
                user.save()
                messages.success(request, 'Profile updated successfully!')
                
            except Exception as e:
                messages.error(request, f'Error updating profile: {str(e)}')
        
        elif action == 'change_password':
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not user.check_password(old_password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
            else:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password changed successfully! Please login again.')
                return redirect('login_user')

    context = {
        'user': user,
        'profile_data': {
            'username': user.username,
            'email': user.email,
            'phone_number': user.phone_number,
            'address': getattr(user, 'address', ''),
            'city': getattr(user, 'city', ''),
            'state': getattr(user, 'state', ''),
            'pincode': getattr(user, 'pincode', ''),
            'date_of_birth': getattr(user, 'date_of_birth', None),
            'date_joined': user.date_joined,
            'is_verified': user.is_verified,
            'last_login': user.last_login
        },
        'activity_data': {
            'total_orders': 0,  # You can add real data here when implemented
            'wishlist_items': 0,  # You can add real data here when implemented
            'recent_orders': [],  # You can add real data here when implemented
        }
    }
    return render(request, 'profile.html', context)

@login_required(login_url='login_user')
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login_user')