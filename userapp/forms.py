from django import forms
from django.contrib.auth.forms import UserCreationForm
from adminapp.models import CustomUser

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(required=False)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone_number', 'password1', 'password2']
