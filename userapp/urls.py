from django.urls import path
from . import views 
from django.contrib.auth import login, authenticate


urlpatterns = [
    path('signup/', views.signup,name='signup'),
    path('login/', views.login_view,name='login'),
    path('home/', views.home,name='home'),
    path('verify-otp/',views.verify_otp, name='verify_otp'),
    path('profile/', views.user_profile, name='profile'),
    path('logout/', views.user_logout, name='logout'),
]
