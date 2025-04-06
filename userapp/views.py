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
from .utils import render_to_pdf, create_order
from django.db import transaction
from django.core.paginator import Paginator
from django.utils import timezone
import random
from .userotp import generateAndSendOtp  # Add this import
import razorpay
from django.conf import settings
import time
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

def generate_otp():
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            # Don't save the user yet, store the form data in session
            user_data = {
                'username': form.cleaned_data['username'],
                'email': form.cleaned_data['email'],
                'phone_number': form.cleaned_data['phone_number'],
                'password': form.cleaned_data['password1']
            }
            request.session['user_data'] = user_data
            
            # Generate and send OTP using the existing function
            email = user_data['email']
            otp = generateAndSendOtp(email, length=6)  # This will also print OTP to console
            
            # Store OTP in session
            request.session['otp'] = otp
            
            messages.success(request, f'Please check your email ({email}) for OTP verification.')
            return redirect('verify_otp')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = SignupForm()
    
    return render(request, 'signup.html', {'form': form})

def verify_otp(request):
    # Check if we have user data in session
    user_data = request.session.get('user_data')
    stored_otp = request.session.get('otp')
    
    if not user_data or not stored_otp:
        messages.error(request, 'Please sign up first.')
        return redirect('signup')

    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        
        if not otp_input:
            messages.error(request, 'Please enter the OTP.')
            return render(request, 'verify_otp.html')

        if otp_input == stored_otp:
            try:
                # Create the user only after OTP verification
                user = CustomUser.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    phone_number=user_data['phone_number'],
                    password=user_data['password']
                )
                user.is_active = True
                user.is_verified = True
                user.save()
                
                # Clear session data
                del request.session['user_data']
                del request.session['otp']
                
                messages.success(request, 'Account created successfully! Please login.')
                return redirect('login')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
                return redirect('signup')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
    
    # Show email in template for better UX
    email = user_data.get('email') if user_data else ''
    return render(request, 'verify_otp.html', {'email': email})

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
    
    # Check if product is in user's wishlist
    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist_product_ids = list(Wishlist.objects.filter(
            user=request.user
        ).values_list('product_id', flat=True))
    
    context = {
        'product': product,
        'cart_item': cart_item,
        'wishlist_product_ids': wishlist_product_ids,
    }
    return render(request, 'product_detail.html', context)

@login_required
@require_POST
def add_to_cart(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        language_id = request.POST.get('selected_language')
        quantity = int(request.POST.get('quantity', 1))
        
        if not language_id:
            return JsonResponse({
                'success': False,
                'message': 'Please select a language'
            })

        # Get or create cart
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Check if item already exists in cart with the same product AND language
        existing_item = CartItem.objects.filter(
            cart=cart,
            product=product,
            selected_language_id=language_id
        ).first()
        
        if existing_item:
            # Update quantity for existing item
            new_quantity = existing_item.quantity + quantity
            if new_quantity > 3:
                new_quantity = 3
                
            existing_item.quantity = new_quantity
            existing_item.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Cart updated successfully',
                'new_stock': product.stock
            })
        else:
            # Create new cart item
            CartItem.objects.create(
                cart=cart,
                product=product,
                selected_language_id=language_id,
                quantity=min(quantity, 3)
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Added to cart successfully',
            'new_stock': product.stock
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
def cart_view(request):
    # Get cart for the user
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Get cart items through the cart relationship using new related_name
    cart_items = cart.user_cart_items.select_related(
        'product',
        'product__category',
        'product__brand',
        'product__primary_language',
        'product__secondary_language',
        'product__tertiary_language'
    ).all()
    
    # Calculate total price
    total_price = sum(item.get_total_price() for item in cart_items)
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price,
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

        # Calculate updated prices
        cart = cart_item.cart
        cart_items = cart.user_cart_items.all()
        
        # Calculate totals including offer prices
        total_price = 0
        original_total = 0
        
        for item in cart_items:
            original_price = float(item.product.price * item.quantity)
            original_total += original_price
            
            if hasattr(item.product, 'offer_price') and item.product.offer_price:
                total_price += float(item.product.offer_price * item.quantity)
            else:
                total_price += original_price
        
        # Calculate item specific data
        item_original_price = float(cart_item.product.price * cart_item.quantity)
        item_final_price = float(cart_item.product.offer_price * cart_item.quantity) if hasattr(cart_item.product, 'offer_price') and cart_item.product.offer_price else item_original_price
        
        item_data = {
            'quantity': cart_item.quantity,
            'has_offer': hasattr(cart_item.product, 'offer_price') and cart_item.product.offer_price,
            'original_subtotal': item_original_price,
            'final_subtotal': item_final_price
        }

        # Calculate cart summary data
        cart_data = {
            'original_total': original_total,
            'total_price': total_price,
            'total_discount': original_total - total_price if original_total > total_price else 0
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Cart updated successfully',
            'item_data': item_data,
            'cart_data': cart_data
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
        cart = cart_item.cart
        
        # Delete cart item
        cart_item.delete()
        
        # Calculate updated cart totals
        remaining_items = cart.user_cart_items.all()
        cart_empty = not remaining_items.exists()
        
        if not cart_empty:
            total_price = sum(item.get_total_price() for item in remaining_items)
            original_total = sum(item.product.price * item.quantity for item in remaining_items)
            cart_data = {
                'original_total': float(original_total),
                'total_price': float(total_price),
                'total_discount': float(original_total - total_price) if original_total > total_price else 0,
                'cart_empty': False
            }
        else:
            cart_data = {'cart_empty': True}
        
        return JsonResponse({
            'success': True,
            'message': 'Item removed from cart',
            'cart_data': cart_data
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
            address = Address.objects.create(
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
            messages.success(request, 'Address added successfully!')
            return redirect('checkout')
        except Exception as e:
            messages.error(request, f'Error adding address: {str(e)}')
    
    return redirect('checkout')

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
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.user_cart_items.all()
        wallet = Wallet.objects.get_or_create(user=request.user)[0]
        addresses = Address.objects.filter(user=request.user)

        # Calculate totals
        total_price = sum(item.product.price * item.quantity for item in cart_items)
        
        # Get coupon discount from session instead of cart  
        coupon_code = request.session.get('coupon_code')
        discount = Decimal(request.session.get('coupon_discount', '0'))

        shipping_cost = Decimal('50') if total_price < 999 else Decimal('0')
        final_total = total_price - discount + shipping_cost

        context = {
            'cart': cart,
            'cart_items': cart_items,
            'addresses': addresses,
            'wallet': wallet,
            'total_price': total_price,
            'discount': discount,
            'coupon_code': coupon_code,
            'shipping_cost': shipping_cost,
            'final_total': final_total,
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'valid_coupons': Coupon.objects.filter(
                is_active=True,
                min_amount__lte=total_price
            ),
        }
        return render(request, 'checkout.html', context)
    except Cart.DoesNotExist:
        messages.error(request, 'No active cart found')
        return redirect('cart')

@login_required
def place_order(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from request body
            data = json.loads(request.body)
            payment_method = data.get('payment_method')
            address_id = data.get('address_id')

            # Validate the address
            try:
                address = Address.objects.get(id=address_id, user=request.user)
            except Address.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid delivery address'
                }, status=400)

            # Get cart and validate
            cart = Cart.objects.get(user=request.user)
            if not cart.user_cart_items.exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Your cart is empty'
                })

            # Calculate totals
            subtotal = cart.get_subtotal()
            shipping_cost = Decimal('50') if subtotal < 999 else Decimal('0')
            total_amount = subtotal + shipping_cost

            # Check if COD is allowed based on total amount
            if payment_method == 'cod' and total_amount > 1000:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Cash on Delivery is only available for orders up to ₹1,000'
                }, status=400)

            # Handle COD payment
            if payment_method == 'cod':
                try:
                    with transaction.atomic():
                        # Create order
                        order = Order.objects.create(
                            user=request.user,
                            billing_address=address,
                            payment_method='cod',
                            total_amount=total_amount,
                            subtotal=subtotal,
                            shipping_cost=shipping_cost
                        )

                        # Create order items
                        for item in cart.user_cart_items.all():
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

                        # Clear cart
                        cart.user_cart_items.all().delete()

                        return JsonResponse({
                            'status': 'success',
                            'order_id': order.id
                        })

                except Exception as e:
                    print(f"Error creating COD order: {str(e)}")
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Error creating order'
                    }, status=400)

            # Handle wallet payment
            elif payment_method == 'wallet':
                wallet = Wallet.objects.get(user=request.user)
                if wallet.balance < total_amount:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Insufficient wallet balance. Required: ₹{total_amount}, Available: ₹{wallet.balance}'
                    })

                try:
                    with transaction.atomic():
                        # Create order
                        order = Order.objects.create(
                            user=request.user,
                            billing_address=address,
                            payment_method='wallet',
                            total_amount=total_amount,
                            subtotal=subtotal,
                            shipping_cost=shipping_cost
                        )

                        # Create order items
                        for item in cart.user_cart_items.all():
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

                        # Clear cart
                        cart.user_cart_items.all().delete()

                        return JsonResponse({
                            'status': 'success',
                            'order_id': order.id
                        })

                except Exception as e:
                    print(f"Error processing wallet payment: {str(e)}")
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Error processing payment'
                    }, status=400)

            # Handle other payment methods...
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid payment method'
                })

        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            print(f"Error in place_order: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Error processing your order'
            }, status=500)

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)

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
    # Get the order with related items
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), id=order_id, user=request.user)
    
    # Calculate totals
    subtotal = sum(item.total_price for item in order.items.all())
    shipping = 50 if subtotal < 999 else 0
    
    # Prepare context with all necessary data
    context = {
        'order': order,
        'order_items': order.items.all(),
        'company_name': 'Bookscartz',
        'company_address': '123 Book Street, Reading Lane',
        'company_phone': '+91 9876543210',
        'company_email': 'info@bookscartz.com',
        'invoice_number': f'INV-{order.id:06d}',
        'date': order.created_at.strftime('%B %d, %Y'),
        'payment_method': order.payment_method,
        
        # Order details
        'subtotal': order.subtotal,
        'shipping_cost': order.shipping_cost,
        'total_amount': order.total_amount,
        'coupon_discount': order.coupon_discount if order.coupon else 0,
        
        # Status information
        'order_status': order.status,
        'order_date': order.created_at.strftime('%B %d, %Y'),
    }
    
    # Generate PDF
    pdf = render_to_pdf('invoice_template.html', context)
    
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        
        filename = f"Bookscartz_Invoice_{order.id}.pdf"
        content = f"attachment; filename={filename}"
        response['Content-Disposition'] = content
        return response
    
    return HttpResponse("Error generating PDF", status=500)

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
@require_POST
def request_return(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # Check if order is eligible for return
        if order.status != 'delivered':
            return JsonResponse({
                'status': 'error',
                'message': 'Order is not eligible for return'
            }, status=400)

        # Get form data
        item_id = request.POST.get('item_id')
        reason = request.POST.get('reason')
        comments = request.POST.get('comments')

        if not item_id or not reason or not comments:
            return JsonResponse({
                'status': 'error',
                'message': 'All fields are required'
            }, status=400)

        # Validate reason choice
        valid_reasons = [choice[0] for choice in ReturnRequest.REASON_CHOICES]
        if reason not in valid_reasons:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid reason selected'
            }, status=400)

        # Get the order item
        order_item = get_object_or_404(OrderItem, id=item_id, order=order)

        # Check if item already has a return request
        if order_item.return_requested:
            return JsonResponse({
                'status': 'error',
                'message': 'Return request already exists for this item'
            }, status=400)

        with transaction.atomic():
            # Create return request
            return_request = ReturnRequest.objects.create(
                order=order,
                order_item=order_item,
                reason=reason,
                comments=comments,
                status='pending',
                admin_notes=''  # Initialize empty admin notes
            )

            # Update order item status
            order_item.return_requested = True
            order_item.return_status = 'pending'
            order_item.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Return request submitted successfully'
        })

    except Exception as e:
        print(f"Error processing return request: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while processing your request'
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

def password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            # Generate and send OTP
            otp = generateAndSendOtp(email)
            
            # Store email and OTP in session for verification
            request.session['reset_email'] = email
            request.session['reset_otp'] = otp
            
            messages.success(request, 'OTP has been sent to your email.')
            return redirect('password_reset_verify_otp')
        except CustomUser.DoesNotExist:
            messages.error(request, 'No user found with this email address.')
    
    return render(request, 'password_reset.html')

def password_reset_verify_otp(request):
    reset_email = request.session.get('reset_email')
    if not reset_email:
        messages.error(request, 'Please start password reset process again.')
        return redirect('password_reset')

    if request.method == 'POST':
        otp = request.POST.get('otp')
        stored_otp = request.session.get('reset_otp')
        
        if otp == stored_otp:
            return redirect('password_reset_confirm')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')

    return render(request, 'password_reset_verify_otp.html', {'email': reset_email})

def password_reset_confirm(request):
    reset_email = request.session.get('reset_email')
    if not reset_email:
        messages.error(request, 'Please start password reset process again.')
        return redirect('password_reset')

    if request.method == 'POST':
        password1 = request.POST.get('new_password1')
        password2 = request.POST.get('new_password2')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'password_reset_confirm.html')
        
        try:
            user = CustomUser.objects.get(email=reset_email)
            user.set_password(password1)
            user.save()
            
            # Clear session data
            del request.session['reset_email']
            del request.session['reset_otp']
            
            messages.success(request, 'Your password has been reset successfully.')
            return redirect('password_reset_complete')
        except CustomUser.DoesNotExist:
            messages.error(request, 'Error resetting password. Please try again.')
    
    return render(request, 'password_reset_confirm.html')

@login_required
def create_razorpay_order(request):
    try:
        data = json.loads(request.body)
        
        # Get cart and calculate total
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.user_cart_items.all()
        
        # Calculate total price
        total_price = sum(item.product.price * item.quantity for item in cart_items)
        
        # Get coupon discount from session
        discount = Decimal(request.session.get('coupon_discount', '0'))
        
        # Apply shipping cost
        shipping_cost = Decimal('50') if total_price < 999 else Decimal('0')
        
        # Calculate final amount
        final_amount = total_price - discount + shipping_cost
        
        # Convert to paise for Razorpay (multiply by 100)
        amount = int(final_amount * 100)
        
        # Initialize Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Create Razorpay order
        payment_data = {
            'amount': amount,
            'currency': 'INR',
            'receipt': f'order_rcptid_{int(time.time())}'
        }
        order = client.order.create(data=payment_data)
        
        return JsonResponse({
            'status': 'success',
            'order_id': order['id'],
            'amount': amount
        })
    except Exception as e:
        print(f"Error in create_razorpay_order: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@login_required
def verify_razorpay_payment(request):
    try:
        data = json.loads(request.body)
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Verify signature
        params_dict = {
            'razorpay_payment_id': data.get('razorpay_payment_id'),
            'razorpay_order_id': data.get('razorpay_order_id'),
            'razorpay_signature': data.get('razorpay_signature')
        }
        
        # Verify the payment signature
        client.utility.verify_payment_signature(params_dict)
        
        try:
            # Create order using the create_order function
            order = create_order(
                user=request.user,
                address_id=data.get('address_id'),
                payment_method='razorpay',
                transaction_id=params_dict['razorpay_payment_id'],  # Use payment_id as transaction_id
                request=request
            )
            
            # Clear cart and session data
            cart = Cart.objects.get(user=request.user)
            cart.user_cart_items.all().delete()
            
            # Clear coupon data from session
            request.session.pop('coupon_code', None)
            request.session.pop('coupon_discount', None)
            request.session.modified = True
            
            return JsonResponse({
                'status': 'success',
                'redirect_url': reverse('order_confirmation', args=[order.id])
            })
            
        except Exception as e:
            print(f"Error creating order: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Error creating order: {str(e)}'
            }, status=400)
            
    except Exception as e:
        print(f"Error in payment verification: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@login_required
def order_confirmation(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        # Change orderitem_set to items (or the correct related_name from your OrderItem model)
        order_items = OrderItem.objects.filter(order=order)
        context = {
            'order': order,
            'order_items': order_items
        }
        return render(request, 'order_confirmation.html', context)
    except Order.DoesNotExist:
        messages.error(request, 'Order not found')
        return redirect('user_orders')