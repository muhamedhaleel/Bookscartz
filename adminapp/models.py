from django.db import models
import os
from django.contrib.auth.models import AbstractUser

# admin


class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    groups = models.ManyToManyField(
        "auth.Group", related_name="+", blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission", related_name="+", blank=True
    )


    class Meta:
        db_table = 'adminapp_customuser'
        
    def __str__(self):
        return self.username


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    added_on = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='brands/', null=True, blank=True)
    added_on = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Language(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    is_active = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE, null=True, blank=True)
    image1 = models.ImageField(upload_to='products/')
    image2 = models.ImageField(upload_to='products/', null=True, blank=True)
    image3 = models.ImageField(upload_to='products/', null=True, blank=True)
    added_on = models.DateTimeField(auto_now_add=True)
    

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

