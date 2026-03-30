from django.db import models
from django.contrib.auth.models import User


#  PROFILE 
class Profile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('customer', 'Customer'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')

    def __str__(self):
        return f"{self.user.username} - {self.role}"


#  PRODUCT 
class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    description = models.TextField()  # ✅ NEW
    category = models.CharField(max_length=100)  # ✅ NEW
    image = models.ImageField(upload_to='products/')
    created_at = models.DateTimeField(auto_now_add=True)  # ✅ NEW

    def __str__(self):
        return self.name
    
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')

    def __str__(self):
        return self.product.name


# CART
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username


# CART ITEM
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def total_price(self):
        return self.product.price * self.quantity


# Order
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    #  Delivery
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)

    #  Payment
    PAYMENT_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('PAYPAL', 'PayPal'),
    ]
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES)
    is_paid = models.BooleanField(default=False)

    total_price = models.FloatField()
    STATUS_CHOICES = [
    ('Placed', 'Placed'),
    ('Processing', 'Processing'),
    ('Shipped', 'Shipped'),
    ('Delivered', 'Delivered'),
    ('Cancelled', 'Cancelled'),
    ('Returned', 'Returned'),
]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Placed')
    created_at = models.DateTimeField(auto_now_add=True)


# ORDER ITEMS 
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def total_price(self):
        return self.product.price * self.quantity


#  REVIEWS 
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()  # 1–5
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.rating}"
    
