from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .forms import SignupForm
from adminapp.models import (
    CustomUser, Brand, Product, Category, Language, Cart, CartItem, 
    Address, Offer, Order, OrderItem, ReturnRequest, Wishlist, 
    Coupon, CouponUsage, Wallet, WalletTransaction
)
from django.core.exceptions import ValidationError
import json
from django.db.models import Q
from django.urls import reverse
from decimal import Decimal
from .utils import render_to_pdf
from django.db import transaction
from django.core.paginator import Paginator
from django.utils import timezone

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

    # Get wishlist products
    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist_product_ids = list(Wishlist.objects.filter(
            user=request.user
        ).values_list('product_id', flat=True))

    context = {
        'products': products,
        'categories': categories,
        'brands': brands,
        'languages': languages,
        'wishlist_product_ids': wishlist_product_ids,
        'search_query': search_query,
        'selected_category': category_id,
        'selected_brand': brand_id,
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
    if request.method == 'POST':
        try:
            product = Product.objects.get(id=product_id)
            
            # Remove from wishlist if exists
            Wishlist.objects.filter(user=request.user, product=product).delete()
            
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
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

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
    
    # Calculate totals using the same method as cart
    original_total = sum(item.get_original_total() for item in cart.items.all())
    total_discount = sum(item.get_discount_amount() for item in cart.items.all())
    total_price = sum(item.get_total_price() for item in cart.items.all())
    
    # Get wallet
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    
    # Get coupon details from session
    coupon_discount = Decimal(request.session.get('coupon_discount', '0'))
    coupon_code = request.session.get('coupon_code')
    
    # Calculate final total
    final_total = total_price - coupon_discount
    shipping_cost = Decimal('50') if final_total < 999 else Decimal('0')
    final_total += shipping_cost
    
    context = {
        'cart': cart,
        'addresses': Address.objects.filter(user=request.user),
        'original_total': original_total,
        'total_discount': total_discount,
        'total_price': total_price,
        'discount': coupon_discount,
        'coupon_code': coupon_code,
        'final_total': final_total,
        'shipping_cost': shipping_cost,
        'valid_coupons': Coupon.objects.filter(
            is_active=True,
            min_amount__lte=total_price
        ),
        'wallet': wallet,
    }
    return render(request, 'checkout.html', context)

@login_required
def place_order(request):
    if request.method == 'POST':
        try:
            # Parse JSON data if it's JSON request
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                address_id = data.get('address')
                payment_method = data.get('payment')
            else:
                # Handle form data
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
            
            # Calculate totals
            subtotal = cart.get_subtotal()
            
            # Get coupon details from session
            coupon_id = request.session.get('coupon_id')
            coupon_discount = Decimal(request.session.get('coupon_discount', '0'))
            
            # Calculate final total with shipping
            final_total = subtotal - coupon_discount
            shipping_cost = Decimal('50') if final_total < 999 else Decimal('0')
            total_amount = final_total + shipping_cost

            # Handle wallet payment
            if payment_method == 'wallet':
                wallet = Wallet.objects.get(user=request.user)
                if wallet.balance < total_amount:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Insufficient wallet balance. Required: ₹{total_amount}, Available: ₹{wallet.balance}'
                    })
                
                # Create order first to get the order ID
                with transaction.atomic():
                    # Create order
                    order = Order.objects.create(
                        user=request.user,
                        billing_address=address,
                        payment_method=payment_method,
                        total_amount=total_amount,
                        subtotal=subtotal,
                        shipping_cost=shipping_cost,
                        coupon_id=coupon_id,
                        coupon_discount=coupon_discount
                    )

                    # Create order items
                    for item in cart_items:
                        OrderItem.objects.create(
                            order=order,
                            product=item.product,
                            quantity=item.quantity,
                            price=item.product.price,
                            total_price=item.get_total_price()
                        )
                        
                        # Update product stock
                        product = item.product
                        product.stock -= item.quantity
                        product.save()

                    # Deduct amount from wallet
                    wallet.balance -= total_amount
                    wallet.save()

                    # Create wallet transaction
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        amount=total_amount,
                        type='debit',
                        order_id=str(order.id)
                    )

                    # Record coupon usage if coupon was used
                    if coupon_id:
                        CouponUsage.objects.create(
                            user=request.user,
                            coupon_id=coupon_id,
                            order=order
                        )

                    # Clear cart and coupon
                    cart.items.all().delete()
                    request.session.pop('coupon_id', None)
                    request.session.pop('coupon_discount', None)
                    request.session.pop('coupon_code', None)

                    return JsonResponse({
                        'status': 'success',
                        'message': 'Order placed successfully!',
                        'order_id': order.id
                    })
            else:
                # Handle other payment methods (COD, etc.)
                with transaction.atomic():
                    # Create order
                    order = Order.objects.create(
                        user=request.user,
                        billing_address=address,
                        payment_method=payment_method,
                        total_amount=total_amount,
                        subtotal=subtotal,
                        shipping_cost=shipping_cost,
                        coupon_id=coupon_id,
                        coupon_discount=coupon_discount
                    )

                    # Create order items
                    for item in cart_items:
                        OrderItem.objects.create(
                            order=order,
                            product=item.product,
                            quantity=item.quantity,
                            price=item.product.price,
                            total_price=item.get_total_price()
                        )
                        
                        # Update product stock
                        product = item.product
                        product.stock -= item.quantity
                        product.save()

                    # Record coupon usage if coupon was used
                    if coupon_id:
                        CouponUsage.objects.create(
                            user=request.user,
                            coupon_id=coupon_id,
                            order=order
                        )

                    # Clear cart and coupon
                    cart.items.all().delete()
                    request.session.pop('coupon_id', None)
                    request.session.pop('coupon_discount', None)
                    request.session.pop('coupon_code', None)

                    return JsonResponse({
                        'status': 'success',
                        'message': 'Order placed successfully!',
                        'order_id': order.id
                    })

        except Exception as e:
            print(f"Error in place_order: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Error processing your order'
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

@login_required
def wishlist_view(request):
    # Get all wishlist items
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related(
        'product', 
        'product__brand'
    ).order_by('-added_at')

    # Add pagination - 8 items per page
    paginator = Paginator(wishlist_items, 8)  # Show 8 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculate discounts for each product
    for item in page_obj:
        max_discount = 0
        product = item.product
        
        # Check product-specific offers
        product_offers = Offer.objects.filter(is_active=True, offer_type='product')
        for offer in product_offers:
            if str(product.id) == str(offer.offer_items):
                max_discount = max(max_discount, float(offer.discount))
        
        # Check category offers
        category_offers = Offer.objects.filter(is_active=True, offer_type='category')
        for offer in category_offers:
            if str(product.category.id) == str(offer.offer_items):
                max_discount = max(max_discount, float(offer.discount))
        
        # Calculate discounted price if there's a discount
        if max_discount > 0:
            product.discount_percentage = max_discount
            original_price = float(str(product.price))
            discount_amount = (original_price * max_discount) / 100
            product.offer_price = round(original_price - discount_amount, 2)
        else:
            product.offer_price = None
            product.discount_percentage = None

    context = {
        'wishlist_items': page_obj,  # Use page_obj instead of wishlist_items
        'page_obj': page_obj,  # Add this for pagination template
    }
    return render(request, 'wishlist.html', context)

@login_required
def add_to_wishlist(request, product_id):
        try:
            product = Product.objects.get(id=product_id)
            wishlist_item, created = Wishlist.objects.get_or_create(
                user=request.user,
                product=product
            )
            return JsonResponse({
                    'status': 'success',
                    'message': 'Added to wishlist'
            })
        except Product.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Product not found'
        })

@login_required
def remove_from_wishlist(request, product_id):
        try:
            wishlist_item = Wishlist.objects.get(
                user=request.user,
                product_id=product_id
            )
            wishlist_item.delete()
            return JsonResponse({
                'status': 'success',
                'message': 'Removed from wishlist'
            })
        except Wishlist.DoesNotExist:
            return JsonResponse({
                'status': 'error',
            'message': 'Item not found in wishlist'
        })

@login_required
def apply_coupon(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.body else request.POST
            coupon_code = data.get('code')
            
            if not coupon_code:
                raise ValidationError('Coupon code is required')

            # Get the coupon
            coupon = get_object_or_404(Coupon, code=coupon_code, is_active=True)
            
            # Check if coupon is expired
            if coupon.valid_to and coupon.valid_to < timezone.now().date():
                raise ValidationError('This coupon has expired')

            # Check usage limit per user
            usage_count = CouponUsage.objects.filter(user=request.user, coupon=coupon).count()
            if usage_count >= 2:
                raise ValidationError('You have already used this coupon the maximum number of times')

            # Get cart and calculate total
            cart = Cart.objects.get(user=request.user)
            cart_total = cart.get_subtotal()

            # Check minimum purchase amount
            if cart_total < coupon.min_amount:
                raise ValidationError(f'Minimum purchase amount of ₹{coupon.min_amount} required')

            # Calculate discount
            if coupon.type == 'percentage':
                discount = (cart_total * Decimal(coupon.value)) / 100
            else:
                discount = Decimal(coupon.value)

            # Store coupon info in session
            request.session['coupon_id'] = coupon.id
            request.session['coupon_code'] = coupon.code
            request.session['coupon_discount'] = str(discount)

            return JsonResponse({
                'status': 'success',
                'message': 'Coupon applied successfully',
                'discount': float(discount)
            })

        except ValidationError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
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

@require_POST
def remove_coupon(request):
    try:
        # Remove coupon details from session
        request.session.pop('coupon_id', None)
        request.session.pop('coupon_discount', None)
        request.session.pop('coupon_code', None)
        
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Coupon removed successfully'
            })
        else:
            # Redirect back to checkout page for normal form submission
            messages.success(request, 'Coupon removed successfully')
            return redirect('checkout')
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
        else:
            messages.error(request, f'Error removing coupon: {str(e)}')
            return redirect('checkout')

@login_required
def wallet_view(request):
    # Get or create wallet for the user
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    # Get all transactions for this wallet
    transactions = WalletTransaction.objects.filter(wallet=wallet)
    
    context = {
        'wallet': wallet,
        'transactions': transactions
    }
    return render(request, 'wallet.html', context)
