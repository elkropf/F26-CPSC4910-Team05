from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, Http404
from django.template import loader
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from .models import *
from django.contrib.auth.decorators import login_required

# Create your views here.

def app_page(request):
    template = loader.get_template('application.html')
    return HttpResponse(template.render())

def apply(request):
    raise Http404("Not implemented yet")
    #Application.objects.create(
    #    'application_message': request.POST["email"],
    #    'application_status': 'pending',
    #)

def app_status(request):
    template = loader.get_template('app_status.html')
    context = {
        'show_search': True,
    }
    return HttpResponse(template.render(context, request))

def check_status(request):
    try:
        application = Application.objects.get(id=request.GET["app_id"])
        return render (
            request,
            "app_status.html",
            {
                "show_search": True,
                "error_message": "",
                "app_number": application.id,
                "app_stat": application.application_status,
            },
        )
    except (KeyError, Application.DoesNotExist):
        return render (
            request,
            "app_status.html",
            {
                "show_search": True,
                "error_message": "Could not find your application ID in our database.",
            },
        )

def login_page(request):
    template = loader.get_template('login.html')
    return HttpResponse(template.render())

def login(request):
    try:
        user_info = User.objects.get(username=request.GET["user_in"])
        if user_info.hashed_pass != hash(request.GET["pass_in"]):
            return render (
                request,
                "login.html",
                {
                    "error_message": "Username and password do not match."
                }
            )
        else:
            match user_info.user_type:
                case 'driver':
                    template = loader.get_template('driver_home.html')
                    context = {
                        'username': user_info.username
                    }
                    return HttpResponse(template.render(context, request))
                case 'sponsor':
                    template = loader.get_template('sponsor_home.html')
                    context = {
                        'username': user_info.username
                    }
                    return HttpResponse(template.render(context, request))
                case 'admin':
                    template = loader.get_template('admin_home.html')
                    context = {
                        'username': user_info.username
                    }
                    return HttpResponse(template.render(context, request))
    except (KeyError, User.DoesNotExist):
        return render (
            request,
            "login.html",
            {
                "error_message": "Username was not found. Are you trying to register?"
            }
        )

def register_page(request):
    template = loader.get_template('register.html')
    return HttpResponse(template.render())

@csrf_protect
def register(request):
    try:
        if request.POST["user_in"] <= 0 or request.POST["pass_in"] <= 0:
            return render (
                request,
                "register.html",
                {
                    "error_message": "Username and password are required."
                }
            )

        user_info = User.objects.get(username=request.POST["user_in"])
    except (KeyError, User.DoesNotExist):
        User.objects.create(
            username = request.POST["user_in"],
            hashed_pass = hash(request.POST["pass_in"]),
            user_type = 'driver'
        )
        return HttpResponseRedirect(reverse("accounts:driver_homepage", query={"username": request.POST["user_in"]}))
    else:
        return render (
            request,
            "register.html",
            {
                "error_message": "Username already exists. Are you trying to log in?"
            }
        )

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