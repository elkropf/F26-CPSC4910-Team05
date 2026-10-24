from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from uuid import uuid4

# Create your models here.

# Type of User Roles. First value is the actual value to be set on the model, second value is the human-readable name.
class UserType(models.TextChoices):
    DRIVER = 'driver', 'Driver'
    SPONSOR = 'sponsor', 'Sponsor'
    ADMIN = 'admin', 'Admin'

# Base class that all users will inherit from.
class User(AbstractUser):
    user_type = models.CharField(max_length=20, choices=UserType.choices)

    #bulk needs longer username field
    first_name = models.TextField(blank=True)
    last_name = models.TextField(blank=True)
    email = models.TextField(blank=True)

# Driver Class
class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Sponsor connection to Driver.

    def __str__(self):
        return self.user.username

# sponsor organization
class Organization(models.Model):
    organization_name = models.TextField()

    #num of points = to 1 dollar
    points_per_dollar = models.DecimalField(max_digits=12,decimal_places=4,default=100)

    organization_description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.organization_name

#driver organization memberships
class DriverOrganization(models.Model):
    driver = models.ForeignKey(
        Driver,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="driver_memberships",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["driver", "organization"],
                name="unique_driver_organization_membership",
            )
        ]

    def __str__(self):
        return f"{self.driver} - {self.organization}"

# Sponsor Class
class Sponsor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="sponsors",
        null=True,
        blank=True
    )

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

# submitted driver applications
class Application(models.Model):
    driver = models.ForeignKey(
        Driver,
        on_delete=models.CASCADE,
        related_name="applications"
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="applications",
        null=True,
        blank=True
    )
    application_status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.PENDING
    )
    application_message = models.TextField(blank=True)
    submission_date = models.DateTimeField(auto_now_add=True)
    review_date = models.DateTimeField(null=True, blank=True)

    rejection_reason = models.TextField(blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["driver", "organization"],
                name="unique_driver_organization_application"
            )
        ]

    def __str__(self):
        return f"{self.driver} - {self.organization}"

#sponsor chosen products
class Product(models.Model):
    organization = models.ForeignKey(
    Organization,
    on_delete=models.CASCADE,
    related_name="products",
    null=True,
    blank=True
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
    organization = models.ForeignKey(
    Organization,
    on_delete=models.PROTECT,
    related_name="orders",
    null=True,
    blank=True
)
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
    driver = models.ForeignKey(
        Driver,
        on_delete=models.CASCADE,
        related_name="points"
    )
    organization = models.ForeignKey(
    Organization,
    on_delete=models.CASCADE,
    related_name="points",
    null=True,
    blank=True
    )
    points_balance = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["driver", "organization"],
                name="unique_driver_organization_points"
            )
        ]

    def __str__(self):
        return (
            f"{self.driver} - {self.organization}: "
            f"{self.points_balance} points"
        )

#driver log
class driverLog(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='driver_logs')
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.driver} - {self.action} at {self.timestamp}"

#organization log
class sponsorLog(models.Model):
    sponsor = models.ForeignKey(
        Sponsor,
        on_delete=models.CASCADE,
        related_name="sponsor_logs"
    )
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
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name="point_logs")
    organization = models.ForeignKey(Organization,on_delete=models.CASCADE,related_name="point_logs")
    changed_by_user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name="point_changes")

    points_changed = models.IntegerField()
    action = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

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

#import files need filenames
def bulk_import_path(instance, filename):
    return f"bulk_imports/{uuid4().hex}.txt"


# Track an uploaded file while a background worker processes it
class BulkImportJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bulk_import_jobs",
    )
    source_file = models.FileField(upload_to=bulk_import_path)
    result_file = models.FileField(
        upload_to=bulk_import_path,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    processed_rows = models.PositiveBigIntegerField(default=0)
    successful_rows = models.PositiveBigIntegerField(default=0)
    failed_rows = models.PositiveBigIntegerField(default=0)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    organization = models.ForeignKey(Organization,on_delete=models.PROTECT,null=True,blank=True,related_name="bulk_import_jobs")