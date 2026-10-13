# models.py
from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self): return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    stock = models.IntegerField(default=0)
    def __str__(self): return self.name


# views.py
from django.shortcuts import render, get_object_or_404, redirect

def product_list(request):
    products = Product.objects.filter(stock__gt=0)
    return render(request, 'shop/list.html', {'products': products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'shop/detail.html', {'product': product})

def add_to_cart(request, pk):
    cart = request.session.get('cart', {})
    cart[str(pk)] = cart.get(str(pk), 0) + 1
    request.session['cart'] = cart
    return redirect('cart')

def cart_view(request):
    cart = request.session.get('cart', {})
    items = []
    total = 0
    for pid, qty in cart.items():
        product = Product.objects.get(pk=pid)
        subtotal = product.price * qty
        total += subtotal
        items.append({'product': product, 'qty': qty, 'subtotal': subtotal})
    return render(request, 'shop/cart.html', {'items': items, 'total': total})


# urls.py
from django.urls import path
urlpatterns = [
    path('', product_list, name='product_list'),
    path('product/<int:pk>/', product_detail, name='product_detail'),
    path('cart/add/<int:pk>/', add_to_cart, name='add_to_cart'),
    path('cart/', cart_view, name='cart'),
]

# Run: python manage.py makemigrations && python manage.py migrate && python manage.py runserver
