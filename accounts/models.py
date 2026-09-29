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