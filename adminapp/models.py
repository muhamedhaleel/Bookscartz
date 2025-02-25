from django.db import models
import os

# Create your models here.
from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    added_on = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='brands/', null=True, blank=True)
    added_on = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Language(models.Model):
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    brand = models.ForeignKey('Brand', on_delete=models.CASCADE)
    language = models.ForeignKey('Language', on_delete=models.CASCADE, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image1 = models.ImageField(upload_to='products/')
    image2 = models.ImageField(upload_to='products/', null=True, blank=True)
    image3 = models.ImageField(upload_to='products/', null=True, blank=True)
    added_on = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        # Delete image files
        if self.image1:
            if os.path.isfile(self.image1.path):
                os.remove(self.image1.path)
        if self.image2:
            if os.path.isfile(self.image2.path):
                os.remove(self.image2.path)
        if self.image3:
            if os.path.isfile(self.image3.path):
                os.remove(self.image3.path)
        super().delete(*args, **kwargs)

    class Meta:
        db_table = 'adminapp_product'

