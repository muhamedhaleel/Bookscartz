from django import forms
from .models import Category

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
