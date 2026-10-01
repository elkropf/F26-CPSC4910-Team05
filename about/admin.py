from django.contrib import admin
from .models import AboutProductInfo, AboutSprintInfo
# Register your models here.

# make the About model visible in the Django admin interface
admin.site.register(AboutProductInfo)
admin.site.register(AboutSprintInfo)