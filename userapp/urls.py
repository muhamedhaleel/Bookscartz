from django.urls import path
from . import views

urlpatterns = [
    path('sign/', views.signup,name='signup_view'),
    path('login/', views.login_view,name='login_view'),
    path('home/', views.home,name='home'),
]

