from django.urls import path
from . import views 
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect


urlpatterns = [
    path('signup/', views.signup,name='signup'),
    path('login/', views.login_view,name='login'),
    path('home/', views.home,name='home'),
    path('verify-otp/',views.verify_otp, name='verify_otp'),
    path('profile/', views.user_profile, name='profile'),
    path('logout/', views.user_logout, name='logout'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('change-password/', views.change_password, name='change_password'),
]

