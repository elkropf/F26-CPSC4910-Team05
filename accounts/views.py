from django.shortcuts import render
from django.http import HttpResponse
from .models import User, Driver, Sponsor, Admin
from django.contrib.auth.decorators import login_required

# Create your views here.

def login_page(request):
    return HttpResponse("Enter login details")