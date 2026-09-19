from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

# Type of User Roles. First value is the actual value to be set on the model, second value is the human-readable name.
class UserType(models.TextChoices):
    DRIVER = 'driver', 'Driver'
    SPONSOR = 'sponsor', 'Sponsor'
    ADMIN = 'admin', 'Admin'

# Base class that all users will inherit from.
class User(AbstractUser):
    user_type = models.CharField(max_length=20, choices=UserType.choices)
