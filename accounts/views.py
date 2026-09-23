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

def driver_homepage(request):
    template = loader.get_template('driver_home.html')
    context = {
        'username': 'username', #Driver.__str__(self), #Should be replaced with something dynamically updating
        # 'points': 0,
    }
    return HttpResponse(template.render(context, request))

def sponsor_homepage(request):
    template = loader.get_template('sponsor_home.html')
    context = {
        'username': 'username', #Should be replaced with something dynamically updating
    }
    return HttpResponse(template.render(context, request))

def admin_homepage(request):
    template = loader.get_template('admin_home.html')
    context = {
        'username': 'username', #Should be replaced with something dynamically updating
    }
    return HttpResponse(template.render(context, request))