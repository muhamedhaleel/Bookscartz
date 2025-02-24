from django import forms
from .models import Category,Brand

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'border border-gray-300 rounded-lg px-4 py-2 w-full',
                'placeholder': 'Enter Category Name'
            })
        }

class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded mb-4',
                'placeholder': 'Brand Name'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'w-full px-4 py-2 border rounded mb-4'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'ml-2'
            }),
        }
        labels = {
            'name': 'Brand Name',
            'image': 'Brand Image',
            'is_active': 'Is Active',
        }
