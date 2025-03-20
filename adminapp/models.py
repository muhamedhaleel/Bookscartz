from django.db import models
import os
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.conf import settings


# admin


class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True)
    otp = models.CharField(max_length=6, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    groups = models.ManyToManyField(
        "auth.Group", related_name="+", blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission", related_name="+", blank=True
    )

    def clean(self):
        super().clean()
        if self.phone_number:
            # Remove any non-digit characters
            self.phone_number = ''.join(filter(str.isdigit, self.phone_number))
            if len(self.phone_number) < 10:
                raise ValidationError('Phone number must be at least 10 digits long.')

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
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
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
        
    def save(self, *args, **kwargs):
        # Calculate offer price if discount percentage is provided
        if self.discount_percentage:
            self.offer_price = round(self.price - (self.price * self.discount_percentage / 100), 2)
        super().save(*args, **kwargs)

    def get_final_price(self):
        """Returns the final price (offer price if available, otherwise regular price)"""
        return self.offer_price if self.offer_price else self.price

    def get_discount_percentage(self):
        """Calculate and return the discount percentage"""
        if self.offer_price and self.price:
            discount = ((self.price - self.offer_price) / self.price) * 100
            return round(discount, 0)
        return 0

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='carts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())

    def get_total_price(self):
        return sum(item.quantity * item.product.price for item in self.items.all())

    class Meta:
        db_table = 'adminapp_cart'

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'adminapp_cartitem'
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in {self.cart}"

    def get_total_price(self):
        return self.quantity * self.product.price

class Address(models.Model):
    ADDRESS_TYPES = (
        ('home', 'Home'),
        ('work', 'Work'),
        ('other', 'Other'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    type = models.CharField(max_length=10, choices=ADDRESS_TYPES, default='home')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'adminapp_address'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.full_name}'s {self.type} address"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Set all other addresses of this user to non-default
            Address.objects.filter(user=self.user).update(is_default=False)
        super().save(*args, **kwargs)

class Offer(models.Model):
    OFFER_TYPES = (
        ('percentage', 'Percentage Discount'),
        ('fixed', 'Fixed Amount'),
        ('buyget', 'Buy X Get Y'),
    )
    
    OFFER_ITEMS = (
        ('all', 'All Products'),
        ('category', 'Specific Category'),
        ('product', 'Specific Product'),
    )
    
    offer_type = models.CharField(max_length=20, choices=OFFER_TYPES)
    offer_items = models.CharField(max_length=20, choices=OFFER_ITEMS)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_offer_type_display()} - {self.discount}%"

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned')
    ]

    VALID_STATUS_TRANSITIONS = {
        'pending': ['processing', 'cancelled'],
        'processing': ['shipped', 'cancelled'],
        'shipped': ['delivered', 'cancelled'],
        'delivered': ['returned'],
        'cancelled': [],
        'returned': []
    }

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    billing_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    payment_method = models.CharField(max_length=50)
    original_total = models.DecimalField(max_digits=10, decimal_places=2)
    total_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Order #{self.id} by {self.customer_name}"

    def can_transition_to(self, new_status):
        """Check if the status transition is valid"""
        return new_status in self.VALID_STATUS_TRANSITIONS.get(self.status, [])

    def update_status(self, new_status):
        """Update order status with validation"""
        if self.can_transition_to(new_status):
            self.status = new_status
            self.save()
            return True
        return False

class OrderItem(models.Model):
    RETURN_STATUS_CHOICES = (
        ('none', 'No Return'),
        ('requested', 'Return Requested'),
        ('approved', 'Return Approved'),
        ('rejected', 'Return Rejected')
    )
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    return_requested = models.BooleanField(default=False)
    return_status = models.CharField(
        max_length=20, 
        choices=RETURN_STATUS_CHOICES,
        default='none'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order #{self.order.id}"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.price
        super().save(*args, **kwargs)

class ReturnRequest(models.Model):
    REASON_CHOICES = [
        ('defective', 'Product is defective'),
        ('wrong_item', 'Received wrong item'),
        ('not_as_described', 'Product not as described'),
        ('damaged', 'Product is damaged'),
        ('other', 'Other')
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='return_request')
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    comments = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    admin_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Return Request for Order #{self.order.id}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        
        if is_new:
            # Update order items marked for return
            for item in self.order.items.all():
                item.return_requested = True
                item.return_status = 'requested'
                item.save()

class Wishlist(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username}'s wishlist - {self.product.name}"

    def get_product_details(self):
        """Get all relevant product details including pricing"""
        return {
            'id': self.product.id,
            'name': self.product.name,
            'price': self.product.price,
            'offer_price': self.product.offer_price,
            'discount': self.product.get_discount_percentage(),
            'stock': self.product.stock,
        }

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code


