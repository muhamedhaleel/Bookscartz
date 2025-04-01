from django.db import models
from django.contrib.auth import get_user_model
from adminapp.models import Product, Language, Cart

User = get_user_model()

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='user_cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    selected_language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, related_name='cart_items')
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.cart.user.username}'s cart - {self.product.name}"

    def get_total_price(self):
        if self.product.offer_price:
            return self.product.offer_price * self.quantity
        return self.product.price * self.quantity

    class Meta:
        ordering = ['-added_at']