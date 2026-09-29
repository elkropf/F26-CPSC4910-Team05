from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Create your models here.

# Type of User Roles. First value is the actual value to be set on the model, second value is the human-readable name.
class UserType(models.TextChoices):
    DRIVER = 'driver', 'Driver'
    SPONSOR = 'sponsor', 'Sponsor'
    ADMIN = 'admin', 'Admin'

# Base class that all users will inherit from.
class User(AbstractUser):
    user_type = models.CharField(max_length=20, choices=UserType.choices)

# Driver Class
class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) 

    # Sponsor connection to Driver.
    sponsor = models.ForeignKey('Sponsor', on_delete=models.SET_NULL, null=True, blank=True, related_name = 'drivers')    

    def __str__(self):
        return self.user.username

# Sponsor Class
class Sponsor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) 

    def __str__(self):
        return self.user.username

# Admin Class
class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) 

    def __str__(self):
        return self.user.username

#application status choice
class ApplicationStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'

#submitted driver applications
class Application(models.Model):
    driver = models.ForeignKey(
        Driver,
        on_delete=models.CASCADE,
        related_name="applications"
    )
    sponsor = models.ForeignKey(
        Sponsor,
        on_delete=models.CASCADE,
        related_name="applications"
    )
    application_status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.PENDING
    )
    application_message = models.TextField(blank=True)
    submission_date = models.DateTimeField(auto_now_add=True)
    review_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["driver", "sponsor"],
                name="unique_driver_sponsor_application"
            )
        ]

    def __str__(self):
        return f"{self.driver} - {self.sponsor}"


#sponsor chosen products
class Product(models.Model):
    sponsor = models.ForeignKey(
        Sponsor,
        on_delete=models.CASCADE,
        related_name="products"
    )
    product_name = models.CharField(max_length=255)
    product_description = models.TextField(blank=True)
    points_value = models.PositiveIntegerField()
    instock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_name

    
#order status options
class OrderStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    APPROVED = 'approved', 'Approved'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


#orders placed by drivers
class Order(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.PROTECT, related_name='orders')
    sponsor = models.ForeignKey(Sponsor, on_delete=models.PROTECT, related_name='orders')
    total_points = models.PositiveIntegerField()
    order_status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} - {self.driver}"


#products included in each order
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)
    points_cost = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['order', 'product'], name='unique_product_per_order'),
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name='quantity_greater_than_zero')
        ]

    def __str__(self):
        return f"{self.quantity} x {self.product}"

#points
class Points(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='points')
    sponsor = models.ForeignKey(Sponsor, on_delete=models.CASCADE, related_name='points')
    points_balance = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['driver', 'sponsor'], name='unique_driver_sponsor_points')
        ]

    def __str__(self):
        return f"{self.driver} - {self.sponsor}: {self.points_balance} points"
    
#driver log
class driverLog(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='driver_logs')
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.driver} - {self.action} at {self.timestamp}"

#sponsor log
class sponsorLog(models.Model):
    sponsor = models.ForeignKey(Sponsor, on_delete=models.CASCADE, related_name='sponsor_logs')
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sponsor} - {self.action} at {self.timestamp}"

#admin log
class adminLog(models.Model):
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE, related_name='admin_logs')
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin} - {self.action} at {self.timestamp}"
    
#point log
class pointLog(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='point_logs')
    sponsor = models.ForeignKey(Sponsor, on_delete=models.CASCADE, related_name='point_logs')
    points_changed = models.IntegerField()
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.driver} - {self.sponsor}: {self.points_changed} points changed for {self.action} at {self.timestamp}"

#audit logs
class auditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} at {self.timestamp}"
    
#notifications
class notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username} - Read: {self.is_read}"