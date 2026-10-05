from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import User
from django.contrib import messages
from .models import *


def register_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        if not first_name:
            messages.error(request, 'First name is required.')
            return redirect('register')
        if not last_name:
            messages.error(request, 'Last name is required.')
            return redirect('register')
        if not username:
            messages.error(request, 'Username is required.')
            return redirect('register')
        if len(username) < 3:
            messages.error(request,'Username must be at least 3 characters long.')
            return redirect('register')
        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('register')
        if not email:
            messages.error(request, 'Email is required.')
            return redirect('register')
        if '@' not in email or '.' not in email.split('@')[-1]:
            messages.error(request,'Please enter a valid email address.')
            return redirect('register')
        if not password:
            messages.error(request, 'Password is required.')
            return redirect('register')
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('register')
        try:
            validate_password(password,user=User(username=username,first_name=first_name,last_name=last_name,email=email))
        except ValidationError as error:
            for message in error.messages:
                messages.error(request, message)
            return redirect('register')
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        login(request, user)
        return redirect('home')
    return render(request, 'register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request,username=username,password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('home')

def forgot_password_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        if not username:
            messages.error(request, 'Username is required.')
            return redirect('forgot_password')
        if not email:
            messages.error(request, 'Email is required.')
            return redirect('forgot_password')
        if not new_password:
            messages.error(request, 'New password is required.')
            return redirect('forgot_password')
        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('forgot_password')
        try:
            user = User.objects.get(username=username, email=email)
        except User.DoesNotExist:
            messages.error(request,'Username and email do not match our records.')
            return redirect('forgot_password')
        try:
            validate_password(new_password, user=user)
        except ValidationError as error:
            for message in error.messages:
                messages.error(request, message)
            return redirect('forgot_password')
        user.set_password(new_password)
        user.save()
        messages.success(request, 'Password reset successfully. You can now login with your new password.')
        return redirect('login')
    return render(request, 'forgot_password.html')

@login_required
def profile_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request,'profile.html',{'orders': orders})


def home_view(request):
    banners = Banner.objects.filter(is_active=True).order_by('-created_at')
    featured_products = Product.objects.filter(is_active=True,is_featured=True).order_by('-created_at')[:6]
    categories = Category.objects.all().order_by('name')
    return render(request, 'home.html', {'banners': banners,'featured_products': featured_products,'categories': categories,})


def products_view(request):
    products = Product.objects.filter(is_active=True)
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    return render(request, 'products.html', {'products': products})

def product_detail_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request,'product_detail.html',{'product': product})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    product_id = str(product_id)
    if product_id in cart:
        cart[product_id] += 1
    else:
        cart[product_id] = 1
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('cart')

@login_required
def cart(request):
    cart = request.session.get('cart', {})
    cart_products = []
    total = 0
    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        item_total = product.price * quantity
        cart_products.append({
            'product': product,
            'quantity': quantity,
            'item_total': item_total
        })
        total += item_total
    return render(request, 'cart.html', {'cart_products': cart_products,'total': total})

@login_required
def update_cart(request, product_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart = request.session.get('cart', {})
        product_id = str(product_id)
        if quantity > 0:
            cart[product_id] = quantity
        else:
            cart.pop(product_id, None)
        request.session['cart'] = cart
        request.session.modified = True
    return redirect('cart')

@login_required
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    product_id = str(product_id)
    cart.pop(product_id, None)
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('cart')

@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')
    cart_products = []
    total = 0
    for product_id, quantity in cart.items():
        product = get_object_or_404(Product,id=product_id)
        item_total = product.price * quantity
        cart_products.append({
            'product': product,
            'quantity': quantity,
            'item_total': item_total})
        total += item_total
    if request.method == 'POST':
        order = Order.objects.create(user=request.user,total_amount=total,status='Pending')
        for product_id, quantity in cart.items():
            product = get_object_or_404(Product,id=product_id)
            OrderItem.objects.create(order=order,product=product,quantity=quantity,price=product.price)
        request.session['cart'] = {}
        request.session.modified = True
        return redirect('order_success',order_id=order.id)
    return render(request,'checkout.html',{'cart_products': cart_products,'total': total})

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order,id=order_id,user=request.user)
    return render(request, 'order_success.html',{'order': order})


