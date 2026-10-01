from django.shortcuts import render
from .models import AboutSprintInfo

# Create your views here.

accountsSprintInfo = AboutSprintInfo.objects.order_by('sprint_number').first()
