from django import forms
from django.contrib.auth.forms import UserCreationForm
from adminapp.models import CustomUser
import random
from django.core.mail import send_mail
from django.conf import settings

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(required=False)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone_number', 'password1', 'password2']
def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False 
        
        
        otp = str(random.randint(100000, 999999))
        user.otp = otp

        if commit:
            user.save()
        
        subject = 'Your OTP Code'
        message = f'Your OTP is {otp}'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list)

        return user