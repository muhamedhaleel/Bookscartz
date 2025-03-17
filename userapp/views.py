from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .forms import SignupForm
from adminapp.models import CustomUser, Brand, Product, Category, Language, Cart, CartItem, Address, Offer, Order, OrderItem, ReturnRequest
from django.core.exceptions import ValidationError
import json
from django.db.models import Q
from django.urls import reverse
from decimal import Decimal
from .utils import render_to_pdf
from django.db import transaction
from django.core.paginator import Paginator

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        try:
            if form.is_valid():
                user = form.save()
                request.session['email'] = user.email
                messages.success(request, 'Please check your email for OTP verification.')
                return redirect('verify_otp')
            else:
                # Handle form errors more explicitly
                for field, errors in form.errors.items():
                    for error in errors:
                        if field == '__all__':
                            messages.error(request, f"Error: {error}")
                        else:
                            messages.error(request, f"{field.replace('_', ' ').title()}: {error}")
                
                # If there are non-field errors, display them as well
                if form.non_field_errors():
                    for error in form.non_field_errors():
                        messages.error(request, f"Error: {error}")
                        
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                for field, errors in e.message_dict.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
            else:
                messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'An unexpected error occurred: {str(e)}')
    else:
        form = SignupForm()
    
    return render(request, 'signup.html', {'form': form})

def verify_otp(request):
    email = request.session.get('email')
    if not email:
        messages.error(request, 'Please sign up first.')
        return redirect('signup')

    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        
        if not otp_input:
            messages.error(request, 'Please enter the OTP.')
            return render(request, 'verify_otp.html')

        try:
            user = CustomUser.objects.get(email=email)
            if user.otp == otp_input:
                user.is_active = True
                user.is_verified = True
                user.otp = None  # Clear OTP after verification
                user.save()
                login(request, user)
                messages.success(request, 'Email verified successfully! Welcome to Bookscartz.')
                return redirect('home')
            else:
                messages.error(request, 'Invalid OTP. Please try again.')
        except CustomUser.DoesNotExist:
            messages.error(request, 'User not found. Please sign up again.')
            return redirect('signup')
        except Exception as e:
            messages.error(request, 'An error occurred during verification. Please try again.')
    
    return render(request, 'verify_otp.html')

@login_required
def home(request):
    brands = Brand.objects.filter(is_active=True)
    # Get the latest 4 active products
    latest_products = Product.objects.filter(is_active=True).order_by('-added_on')[:4]
    
    context = {
        'brands': brands,
        'latest_products': latest_products,
    }
    return render(request, 'home.html', context)

def login_view(request):
    # Redirect if already logged in
    if request.user.is_authenticated:
        if request.user.is_superuser:
            messages.error(request, 'Admin users cannot access customer login')
            return redirect('admin_dashboard')
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and not user.is_superuser:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'login.html')

@login_required
def user_profile(request):
    addresses = Address.objects.filter(user=request.user)
    if request.method == 'POST':
        username = request.POST.get('username')
        phone_number = request.POST.get('phone')
        user = request.user
        try:
            user.username = username
            user.phone_number = phone_number
            user.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')  # Redirect to the profile page
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
    return render(request, 'profile.html', {'user': request.user, 'addresses': addresses})

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')  # Redirect to the login page after logout

@login_required
def reset_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        user = request.user

        # Check if the current password is correct
        if user.check_password(current_password):
            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Your password has been changed successfully!')
                return redirect('profile')  # Redirect to the profile page
            else:
                messages.error(request, 'New passwords do not match.')
        else:
            messages.error(request, 'Current password is incorrect.')
    return render(request, 'profile.html', {'user': request.user})  # Render the profile page

@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        user = request.user

        # Check if the current password is correct
        if user.check_password(current_password):
            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Your password has been changed successfully!')
            else:
                messages.error(request, 'New passwords do not match.')
        else:
            messages.error(request, 'Current password is incorrect.')

    # Render the profile page with the user context and messages
    return render(request, 'profile.html', {'user': request.user})

@login_required
def product_list(request):
    # Get filter parameters from request
    category_id = request.GET.get('category')
    brand_id = request.GET.get('brand')
    language_id = request.GET.get('language')
    search_query = request.GET.get('search')

    # Start with all active products
    products = Product.objects.filter(is_active=True)

    # Apply filters if they exist
    if category_id:
        products = products.filter(category_id=category_id)
    if brand_id:
        products = products.filter(brand_id=brand_id)
    if language_id:
        products = products.filter(language_id=language_id)
    if search_query:
        products = products.filter(name__icontains=search_query)

    # Get all active categories, brands, and languages for filters
    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)
    languages = Language.objects.filter(is_active=True)

    # Get all active offers
    product_offers = Offer.objects.filter(is_active=True, offer_type='product')
    category_offers = Offer.objects.filter(is_active=True, offer_type='category')
    
    # Calculate discounted prices for each product
    for product in products:
        max_discount = 0
        
        # Check product-specific offers
        for offer in product_offers:
            if str(product.id) == str(offer.offer_items):
                max_discount = max(max_discount, float(offer.discount))
        
        # Check category offers
        for offer in category_offers:
            if str(product.category.id) == str(offer.offer_items):
                max_discount = max(max_discount, float(offer.discount))
        
        if max_discount > 0:
            # Calculate discounted price
            product.discount = max_discount
            original_price = float(str(product.price))  # Convert Decimal to float
            discount_amount = (original_price * max_discount) / 100
            product.offer_price = round(original_price - discount_amount, 2)
        else:
            product.offer_price = None
            product.discount = None

    context = {
        'products': products,
        'categories': categories,
        'brands': brands,
        'languages': languages,
    }
    return render(request, 'product_list.html', context)

@login_required
def product_detail(request, product_id):
    # Get the product or return 404 if not found
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    # Get active offers
    product_offers = Offer.objects.filter(is_active=True, offer_type='product')
    category_offers = Offer.objects.filter(is_active=True, offer_type='category')
    
    # Calculate maximum discount for the product
    max_discount = 0
    
    # Check product-specific offers
    for offer in product_offers:
        if str(product.id) == str(offer.offer_items):
            max_discount = max(max_discount, float(offer.discount))
    
    # Check category offers
    for offer in category_offers:
        if str(product.category.id) == str(offer.offer_items):
            max_discount = max(max_discount, float(offer.discount))
    
    # Calculate discounted price if there's a discount
    if max_discount > 0:
        product.discount = max_discount
        original_price = float(str(product.price))
        discount_amount = (original_price * max_discount) / 100
        product.offer_price = round(original_price - discount_amount, 2)
    else:
        product.offer_price = None
        product.discount = None
    
    # Get user's cart item quantity if it exists
    cart_item = None
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart_item = CartItem.objects.filter(cart=cart, product=product).first()
    
    context = {
        'product': product,
        'cart_item': cart_item,
    }
    return render(request, 'product_detail.html', context)

@require_POST
@login_required
def add_to_cart(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        quantity = int(request.POST.get('quantity', 1))
        
        # Validate quantity
        if quantity < 1:
            return JsonResponse({
                'success': False,
                'message': 'Quantity must be at least 1'
            })
        
        max_allowed = min(3, product.stock)
        if quantity > max_allowed:
            return JsonResponse({
                'success': False,
                'message': f'Maximum {max_allowed} items allowed'
            })
        
        # Get or create cart
        cart, _ = Cart.objects.get_or_create(user=request.user)
        
        # Get or create cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Update existing cart item
            new_quantity = cart_item.quantity + quantity
            if new_quantity > max_allowed:
                return JsonResponse({
                    'success': False,
                    'message': f'Cart would exceed maximum limit of {max_allowed} items'
                })
            cart_item.quantity = new_quantity
            cart_item.save()
        
        # Update product stock
        product.stock -= quantity
        product.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Added to cart successfully',
            'new_stock': product.stock,
            'cart_quantity': cart_item.quantity
        })
        
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Product not found'
        })
    except ValueError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid quantity'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
def cart_view(request):
    cart = Cart.objects.filter(user=request.user).first()
    cart_items = []
    total_price = 0
    total_discount = 0

    if cart:
        cart_items = cart.items.select_related('product', 'product__category', 'product__language').all()
        
        # Get active offers
        product_offers = Offer.objects.filter(is_active=True, offer_type='product')
        category_offers = Offer.objects.filter(is_active=True, offer_type='category')
        
        # Calculate discounts for each cart item
        for item in cart_items:
            max_discount = 0
            
            # Check product-specific offers
            for offer in product_offers:
                if str(item.product.id) == str(offer.offer_items):
                    max_discount = max(max_discount, float(offer.discount))
            
            # Check category offers
            for offer in category_offers:
                if str(item.product.category.id) == str(offer.offer_items):
                    max_discount = max(max_discount, float(offer.discount))
            
            # Calculate discounted price if there's a discount
            original_price = float(str(item.product.price))
            item_total = original_price * item.quantity
            item.original_total = round(item_total, 2)
            
            if max_discount > 0:
                item.product.discount = max_discount
                discount_amount = (original_price * max_discount) / 100
                item.product.offer_price = round(original_price - discount_amount, 2)
                discounted_total = item.product.offer_price * item.quantity
                item.discount_amount = round(item_total - discounted_total, 2)
                total_discount += item.discount_amount
            else:
                item.product.offer_price = None
                item.product.discount = None
                item.discount_amount = 0
                discounted_total = item_total
            
            item.total_price = round(discounted_total, 2)
            total_price += item.total_price
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': round(total_price, 2),
        'total_discount': round(total_discount, 2),
        'original_total': round(total_price + total_discount, 2)
    }
    return render(request, 'cart.html', context)

@require_POST
@login_required
def update_cart(request, item_id):
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        
        cart_item = CartItem.objects.select_related('product').get(id=item_id, cart__user=request.user)
        
        if quantity < 1:
            return JsonResponse({
                'success': False,
                'message': 'Quantity must be at least 1'
            })
        
        max_allowed = min(3, cart_item.product.stock)
        if quantity > max_allowed:
            return JsonResponse({
                'success': False,
                'message': f'Maximum {max_allowed} items allowed'
            })
        
        # Update quantity
        cart_item.quantity = quantity
        cart_item.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Cart updated successfully'
        })
        
    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Item not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@require_POST
@login_required
def remove_from_cart(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
        
        # Update product stock
        cart_item.product.stock += cart_item.quantity
        cart_item.product.save()
        
        # Delete cart item
        cart_item.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Item removed from cart'
        })
        
    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Item not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
def add_address(request):
    if request.method == 'POST':
        try:
            address = Address(
                user=request.user,
                full_name=request.POST.get('full_name'),
                phone=request.POST.get('phone'),
                address_line1=request.POST.get('address_line1'),
                address_line2=request.POST.get('address_line2'),
                city=request.POST.get('city'),
                state=request.POST.get('state'),
                pincode=request.POST.get('pincode'),
                type=request.POST.get('type'),
                is_default=request.POST.get('is_default') == 'on'
            )
            address.save()
            messages.success(request, 'Address added successfully!')
        except Exception as e:
            messages.error(request, f'Error adding address: {str(e)}')
    return redirect('profile')

@login_required
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        try:
            address.full_name = request.POST.get('full_name')
            address.phone = request.POST.get('phone')
            address.address_line1 = request.POST.get('address_line1')
            address.address_line2 = request.POST.get('address_line2')
            address.city = request.POST.get('city')
            address.state = request.POST.get('state')
            address.pincode = request.POST.get('pincode')
            address.type = request.POST.get('type')
            address.is_default = request.POST.get('is_default') == 'on'
            address.save()
            messages.success(request, 'Address updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating address: {str(e)}')
    return redirect('profile')

@login_required
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    try:
        address.delete()
        messages.success(request, 'Address deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting address: {str(e)}')
    return redirect('profile')

@login_required
def checkout_view(request):
    cart = Cart.objects.filter(user=request.user).first()
    addresses = Address.objects.filter(user=request.user)
    cart_items = []
    total_price = 0
    total_discount = 0

    if not cart:
        messages.warning(request, 'Your cart is empty')
        return redirect('cart')

    cart_items = cart.items.select_related('product', 'product__category', 'product__language').all()
    
    if not cart_items:
        messages.warning(request, 'Your cart is empty')
        return redirect('cart')

    # Get active offers
    product_offers = Offer.objects.filter(is_active=True, offer_type='product')
    category_offers = Offer.objects.filter(is_active=True, offer_type='category')
    
    # Calculate discounts for each cart item
    for item in cart_items:
        max_discount = 0
        
        # Check product-specific offers
        for offer in product_offers:
            if str(item.product.id) == str(offer.offer_items):
                max_discount = max(max_discount, float(offer.discount))
        
        # Check category offers
        for offer in category_offers:
            if str(item.product.category.id) == str(offer.offer_items):
                max_discount = max(max_discount, float(offer.discount))
        
        # Calculate discounted price if there's a discount
        original_price = float(str(item.product.price))
        item_total = original_price * item.quantity
        item.original_total = round(item_total, 2)
        
        if max_discount > 0:
            item.product.discount = max_discount
            discount_amount = (original_price * max_discount) / 100
            item.product.offer_price = round(original_price - discount_amount, 2)
            discounted_total = item.product.offer_price * item.quantity
            item.discount_amount = round(item_total - discounted_total, 2)
            total_discount += item.discount_amount
        else:
            item.product.offer_price = None
            item.product.discount = None
            item.discount_amount = 0
            discounted_total = item_total
        
        item.total_price = round(discounted_total, 2)
        total_price += item.total_price

    if request.method == 'POST':
        address_id = request.POST.get('address')
        payment_method = request.POST.get('payment')
        
        if not address_id:
            messages.error(request, 'Please select a delivery address')
            return redirect('checkout')
        
        try:
            address = Address.objects.get(id=address_id, user=request.user)
            # Here you would create the order and handle payment
            # This is where you'd integrate with Razorpay if selected
            messages.success(request, 'Order placed successfully!')
            return redirect('order_confirmation')  # Create this view
        except Address.DoesNotExist:
            messages.error(request, 'Selected address not found')
            return redirect('checkout')
        except Exception as e:
            messages.error(request, f'Error placing order: {str(e)}')
            return redirect('checkout')
    
    context = {
        'cart_items': cart_items,
        'addresses': addresses,
        'total_price': round(total_price, 2),
        'total_discount': round(total_discount, 2),
        'original_total': round(total_price + total_discount, 2),
        'shipping_cost': 0 if total_price >= 999 else 50,
    }
    
    return render(request, 'checkout.html', context)

@login_required
def place_order(request):
    if request.method == 'POST':
        try:
            # Get the selected address and payment method
            address_id = request.POST.get('address')
            payment_method = request.POST.get('payment')
            
            if not address_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Please select a delivery address'
                })
            
            # Get the address
            address = get_object_or_404(Address, id=address_id, user=request.user)
            
            # Get the cart
            cart = Cart.objects.get(user=request.user)
            cart_items = CartItem.objects.filter(cart=cart)
            
            if not cart_items.exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Your cart is empty'
                })
            
            # Get active offers
            product_offers = Offer.objects.filter(is_active=True, offer_type='product')
            category_offers = Offer.objects.filter(is_active=True, offer_type='category')
            
            # Calculate totals
            original_total = 0
            total_discount = 0
            
            for item in cart_items:
                # Calculate price with offers
                max_discount = 0
                
                # Check product-specific offers
                for offer in product_offers:
                    if str(item.product.id) == str(offer.offer_items):
                        max_discount = max(max_discount, float(offer.discount))
                
                # Check category offers
                for offer in category_offers:
                    if str(item.product.category.id) == str(offer.offer_items):
                        max_discount = max(max_discount, float(offer.discount))
                
                # Calculate item total
                item_price = float(str(item.product.price))
                item_total = item_price * item.quantity
                original_total += item_total
                
                if max_discount > 0:
                    discount_amount = (item_total * max_discount) / 100
                    total_discount += discount_amount
            
            subtotal = original_total - total_discount
            shipping_cost = 0 if subtotal >= 999 else 50
            total_amount = subtotal + shipping_cost
            
            # Create the order
            order = Order.objects.create(
                user=request.user,
                customer_name=address.full_name,
                phone=address.phone,
                billing_address=address,
                payment_method=payment_method,
                original_total=original_total,
                total_discount=total_discount,
                subtotal=subtotal,
                shipping_cost=shipping_cost,
                total_amount=total_amount
            )
            
            # Create order items and clear cart
            for cart_item in cart_items:
                # Calculate final price for this item
                max_discount = 0
                
                # Check product-specific offers
                for offer in product_offers:
                    if str(cart_item.product.id) == str(offer.offer_items):
                        max_discount = max(max_discount, float(offer.discount))
                
                # Check category offers
                for offer in category_offers:
                    if str(cart_item.product.category.id) == str(offer.offer_items):
                        max_discount = max(max_discount, float(offer.discount))
                
                # Calculate final price
                item_price = float(str(cart_item.product.price))
                if max_discount > 0:
                    discount_amount = (item_price * max_discount) / 100
                    final_price = item_price - discount_amount
                else:
                    final_price = item_price
                
                # Create order item
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=final_price,
                    total_price=final_price * cart_item.quantity
                )
            
            # Clear the cart
            cart_items.delete()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Order placed successfully',
                'order_id': order.id,
                'redirect_url': f'/order-details/{order.id}/'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })

@login_required
def order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_details.html', {'order': order})

@login_required(login_url='user_login')
def user_orders(request):
    status = request.GET.get('status')
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    if status:
        orders = orders.filter(status=status)
    
    # Add pagination - 10 orders per page
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)
    
    context = {
        'orders': orders,
        'status': status,
    }
    return render(request, 'user_orders.html', context)

@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Generate PDF
    pdf = render_to_pdf('invoice_template.html', {
        'order': order,
    })
    
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Invoice_{order.id}.pdf"
        content = f"attachment; filename={filename}"
        response['Content-Disposition'] = content
        return response
    
    return HttpResponse("Error generating PDF", status=404)

@require_POST
@login_required
def cancel_order(request, order_id):
    try:
        with transaction.atomic():
            order = get_object_or_404(Order, id=order_id, user=request.user)
            
            # Check if order can be cancelled
            if order.status in ['delivered', 'cancelled']:
                return JsonResponse({
                    'status': 'error',
                    'message': 'This order cannot be cancelled.'
                })
            
            # Update order status
            order.status = 'cancelled'
            order.save()
            
            # Increment product stock
            for item in order.items.all():
                product = item.product
                product.stock += item.quantity
                product.save()
            
            messages.success(request, 'Order cancelled successfully.')
            return JsonResponse({
                'status': 'success',
                'message': 'Order cancelled successfully'
            })
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
def request_return(request, order_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
        
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # Check if order is eligible for return
        if order.status != 'delivered':
            return JsonResponse({
                'status': 'error',
                'message': 'Order is not eligible for return'
            }, status=400)
            
        # Check if return request already exists
        if order.return_request.exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Return request already exists for this order'
            }, status=400)
            
        reason = request.POST.get('reason')
        comments = request.POST.get('comments')
        
        if not reason:
            return JsonResponse({
                'status': 'error',
                'message': 'Return reason is required'
            }, status=400)
            
        with transaction.atomic():
            # Create return request
            return_request = ReturnRequest.objects.create(
                order=order,
                reason=reason,
                comments=comments,
                status='pending'
            )
            
            # Mark items as return requested
            for item in order.items.all():
                item.return_requested = True
                item.return_status = 'requested'
                item.save()
            
        return JsonResponse({
            'status': 'success',
            'message': 'Return request submitted successfully'
        })
        
    except Exception as e:
        print(f"Error processing return request: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Error processing return request'
        }, status=500)
