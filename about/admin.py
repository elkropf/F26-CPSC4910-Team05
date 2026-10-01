from django.contrib import admin
from .models import About
# Register your models here.

# make the About model visible in the Django admin interface
admin.site.register(About)