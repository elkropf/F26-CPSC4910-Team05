from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from .models import User, Driver, Sponsor, Admin
from django.contrib.auth.decorators import login_required

# Create your views here.

def login_page(request):
    template = loader.get_template('login.html')
    return HttpResponse(template.render())

def register_page(request):
    template = loader.get_template('register.html')
    return HttpResponse(template.render())