from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from django.db.models import Q
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect
from django.conf import settings
from .models import ProductImage, Profile, Product, Cart, CartItem, Order, OrderItem, Review
import paypalrestsdk


#  PAYPAL CONFIG
paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET,
})

#  COMMON FUNCTION 
def get_categories():
    return Product.objects.values_list('category', flat=True).distinct()

#  HOME
def home(request):
    products = Product.objects.all().order_by('-id')
    return render(request, 'index.html', {
        'products': products,
        'categories': get_categories()
    })

#  REGISTER
def register_view(request):
    if request.method == 'POST':
        user = User.objects.create_user(
            username=request.POST['username'],
            password=request.POST['password']
        )
        Profile.objects.create(user=user, role='customer')
        return redirect('login')

    return render(request, 'register.html')

#  LOGIN
def login_view(request):

    if request.user.is_authenticated:
        if hasattr(request.user, 'profile') and request.user.profile.role == 'admin':
            return redirect('admin_dashboard')
        return redirect('customer_dashboard')

    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password')
        )

        if user:
            login(request, user)

            profile, _ = Profile.objects.get_or_create(user=user)

            if user.is_superuser:
                profile.role = 'admin'
                profile.save()

            if profile.role == 'admin':
                return redirect('admin_dashboard')
            return redirect('customer_dashboard')

        messages.error(request, "Invalid username or password")

    return render(request, 'login.html')

def forgot_password(request):
    if request.method == 'POST':
        username = request.POST.get('username')

        if User.objects.filter(username=username).exists():
            return redirect('set_new_password', username=username)
        else:
            messages.error(request, 'Username not found')

    return render(request, 'forgot_password.html')

def set_new_password(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        messages.error(request, 'Invalid user')
        return redirect('forgot_password')

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match')
        elif len(new_password) < 6:
            messages.error(request, 'Password must be at least 6 characters')
        else:
            user.password = make_password(new_password)
            user.save()
            messages.success(request, 'Password updated successfully')
            return redirect('login')

    return render(request, 'set_new_password.html', {'username': username})

#  LOGOUT
def logout_view(request):
    storage = messages.get_messages(request)
    storage.used = True
    logout(request)
    return redirect('login')


@login_required
def product_list(request):
    query = request.GET.get('q')
    category = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    products = Product.objects.all()

    #  SEARCH
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(category__icontains=query)
        )

    #  CATEGORY FILTER
    if category:
        products = products.filter(category__iexact=category)

    #  PRICE FILTER
    if min_price:
        products = products.filter(price__gte=min_price)

    if max_price:
        products = products.filter(price__lte=max_price)

    categories = Product.objects.values_list('category', flat=True).distinct()

    category_products = []
    for cat in categories:
        filtered = products.filter(category=cat)
        if filtered.exists():   
            category_products.append({
                'category': cat,
                'products': filtered
            })

    return render(request, 'product_list.html', {
        'category_products': category_products,
        'categories': categories
    })

#  PRODUCT DETAIL
@login_required
def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    reviews = product.reviews.all()

    #  ADD THIS BLOCK
    if request.method == 'POST':
        Review.objects.create(
            product=product,
            user=request.user,
            rating=request.POST.get('rating'),
            comment=request.POST.get('comment')
        )
        return redirect('product_detail', id=product.id)

    #  EXISTING RETURN
    return render(request, 'product_detail.html', {
        'product': product,
        'reviews': reviews,
        'categories': get_categories()
    })

#  ADMIN DASHBOARD
@login_required
def admin_dashboard(request):
    products = Product.objects.all()
    orders = Order.objects.all().order_by('-created_at')[:10]
    users = User.objects.all()

    context = {
        'products': products,
        'orders': orders,
        'products_count': products.count(),
        'orders_count': orders.count(),
        'users_count': users.count(),
    }

    return render(request, 'admin_dashboard.html', context)

#  ADD PRODUCT
def add_product(request):
    if request.user.profile.role != 'admin':
        return redirect('product_list')

    if request.method == 'POST':
        product = Product.objects.create(
            name=request.POST['name'],
            price=request.POST['price'],
            stock=request.POST['stock'],
            description=request.POST.get('description'),
            category=request.POST.get('category'),
            image=request.FILES.get('image')  # main image
        )

        #  MULTIPLE IMAGES
        images = request.FILES.getlist('images')

        for img in images:
            ProductImage.objects.create(product=product, image=img)

        return redirect('admin_dashboard')

    return render(request, 'add_product.html', {
        'categories': get_categories()
    })

#  ADD TO CART
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if product.stock <= 0:
        messages.error(request, "Out of stock")
        return redirect('product_list')

    cart, _ = Cart.objects.get_or_create(user=request.user)

    item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created and item.quantity < product.stock:
        item.quantity += 1
        item.save()

    return redirect('cart')

#  CART
@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = CartItem.objects.filter(cart=cart)

    total = sum(i.total_price() for i in items)

    return render(request, 'cart.html', {
        'cart_items': items,     
        'total_price': total,
        'categories': get_categories()
    })

# ➕ / ➖ QUANTITY
@login_required
def increase_quantity(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)

    if item.quantity < item.product.stock:
        item.quantity += 1
        item.save()

    return redirect('cart')

@login_required
def decrease_quantity(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)

    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()

    return redirect('cart')


#  PAYPAL
@login_required
def paypal_payment(request, order_id):
    order = Order.objects.get(id=order_id)
    cart = Cart.objects.get(user=request.user)
    items = CartItem.objects.filter(cart=cart)

    total = sum(i.total_price() for i in items)

    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {"payment_method": "paypal"},
        "redirect_urls": {
            "return_url": request.build_absolute_uri(reverse('success', args=[order.id])),
            "cancel_url": request.build_absolute_uri(reverse('cancel')),
        },
        "transactions": [{
            "amount": {"total": f"{total:.2f}", "currency": "USD"},
            "description": "Order Payment"
        }]
    })

    if payment.create():
        for link in payment.links:
            if link.rel == "approval_url":
                return HttpResponseRedirect(link.href)

    return redirect('cart')


#  PAYMENT SUCCESS
@login_required
def payment_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if not order.is_paid:
        order.is_paid = True
        order.save()

        cart = Cart.objects.get(user=request.user)
        items = CartItem.objects.filter(cart=cart)

        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity
            )

            item.product.stock -= item.quantity
            item.product.save()

        items.delete()

    return render(request, 'payment_success.html', {'order': order})


#  PAYMENT CANCEL
@login_required
def payment_cancel(request):
    return render(request, 'payment_cancel.html')


#  ORDERS
@login_required
def orders_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders.html', {
        'orders': orders,
        'categories': get_categories()
    })


#  CUSTOMER DASHBOARD
@login_required
def customer_dashboard(request):
    if request.user.profile.role != 'customer':
        return redirect('admin_dashboard')

    orders = Order.objects.filter(user=request.user)

    total_spent = sum(o.total_price for o in orders if o.is_paid)

    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_count = CartItem.objects.filter(cart=cart).count()

    return render(request, 'customer_dashboard.html', {
        'orders': orders[:5],
        'total_spent': total_spent,
        'cart_count': cart_count,
        'categories': get_categories()
    })

def edit_product(request, id):
    product = get_object_or_404(Product, id=id)

    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.price = request.POST.get('price')
        product.stock = request.POST.get('stock')
        product.description = request.POST.get('description')

        #  Handle image update
        if request.FILES.get('image'):
            product.image = request.FILES.get('image')

        product.save()
        messages.success(request, "Product updated successfully!")

        return redirect('admin_dashboard')

    return render(request, 'edit_product.html', {'product': product})

def delete_product(request, id):
    product = get_object_or_404(Product, id=id)

    product.delete()
    messages.success(request, "Product deleted successfully!")

    return redirect('admin_dashboard')

@require_POST
def update_order_status(request, id):
    order = get_object_or_404(Order, id=id)
    new_status = request.POST.get('status')

    order.status = new_status
    order.save()

    return redirect('admin_dashboard')

#  CHECKOUT
@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    items = CartItem.objects.filter(cart=cart)

    if request.method == "POST":
        payment_method = request.POST.get('payment_method')

        total = sum(i.product.price * i.quantity for i in items)

        order = Order.objects.create(
            user=request.user,
            full_name=request.POST.get('full_name'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            pincode=request.POST.get('pincode'),
            payment_method=payment_method,
            total_price=total
        )

        #  COD
        if payment_method == "COD":
            for i in items:
                OrderItem.objects.create(
                    order=order,
                    product=i.product,
                    quantity=i.quantity,
                    # price=i.product.price
                )

            items.delete()
            return redirect('order_success')

        #  PAYPAL
        return redirect('paypal_payment', order.id)

    return render(request, 'checkout.html', {'items': items})

#  SUCCESS PAGE
def order_success(request):
    return render(request, 'order_success.html')

@login_required
def buy_now(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if product.stock <= 0:
        messages.error(request, "Out of stock")
        return redirect('product_list')

    cart, _ = Cart.objects.get_or_create(user=request.user)

    #  IMPORTANT: clear old cart (for direct purchase)
    CartItem.objects.filter(cart=cart).delete()

    # Add only this product
    CartItem.objects.create(
        cart=cart,
        product=product,
        quantity=1
    )

    return redirect('checkout')

@login_required
def cancel_order(request, id):
    order = get_object_or_404(Order, id=id, user=request.user)

    if order.status in ['Placed', 'Processing']:
        order.status = 'Cancelled'
        order.save()

        #  RESTORE STOCK
        for item in order.items.all():
            item.product.stock += item.quantity
            item.product.save()

        messages.success(request, "Order cancelled successfully")

    return redirect('orders')


@login_required
def return_order(request, id):
    order = get_object_or_404(Order, id=id, user=request.user)

    if order.status == 'Delivered':
        order.status = 'Returned'
        order.save()

        #  RESTORE STOCK
        for item in order.items.all():
            item.product.stock += item.quantity
            item.product.save()

        messages.success(request, "Return request placed")

    return redirect('orders')

@login_required
def admin_orders(request):

    #  allow only admin
    if request.user.profile.role != 'admin':
        return redirect('customer_dashboard')

    orders = Order.objects.all().order_by('-created_at')

    return render(request, 'admin_orders.html', {
        'orders': orders
    })