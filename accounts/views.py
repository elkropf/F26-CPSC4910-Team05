import json

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.template import loader
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .models import Application, Driver, Organization, User, UserType


def _request_data(request):
    """Read either JSON sent by React or ordinary Django form data."""
    if request.content_type == "application/json":
        try:
            return json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return None
    return request.POST


def _user_data(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "user_type": user.user_type,
    }


# JSON authentication endpoints for the React frontend.

@require_GET
@ensure_csrf_cookie
def api_csrf(request):
    return JsonResponse({"detail": "CSRF cookie set."})


@require_POST
def api_register(request):
    data = _request_data(request)
    if data is None:
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    email = str(data.get("email", "")).strip()

    if not username or not password:
        return JsonResponse(
            {"error": "Username and password are required."},
            status=400,
        )

    if User.objects.filter(username__iexact=username).exists():
        return JsonResponse({"error": "Username already exists."}, status=409)

    try:
        validate_password(password)
    except ValidationError as error:
        return JsonResponse({"error": error.messages}, status=400)

    with transaction.atomic():
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            user_type=UserType.DRIVER,
        )
        Driver.objects.create(user=user)

    auth_login(request, user)
    return JsonResponse({"user": _user_data(user)}, status=201)


@require_POST
def api_login(request):
    data = _request_data(request)
    if data is None:
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    if not username or not password:
        return JsonResponse(
            {"error": "Username and password are required."},
            status=400,
        )

    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse(
            {"error": "Invalid username or password."},
            status=401,
        )

    if not user.is_active:
        return JsonResponse({"error": "This account is inactive."}, status=403)

    auth_login(request, user)
    return JsonResponse({"user": _user_data(user)})


@require_POST
def api_logout(request):
    auth_logout(request)
    return JsonResponse({"detail": "Logged out successfully."})


@require_GET
def api_current_user(request):
    if not request.user.is_authenticated:
        return JsonResponse({"authenticated": False}, status=401)

    return JsonResponse(
        {
            "authenticated": True,
            "user": _user_data(request.user),
        }
    )


# Existing server-rendered pages.

def app_page(request):
    template = loader.get_template("application.html")
    context = {
        "organization": Organization.objects.order_by("-id"),
    }
    return HttpResponse(template.render(context, request))


def apply(request):
    raise Http404("Not implemented yet")


def app_status(request):
    template = loader.get_template("app_status.html")
    context = {
        "show_search": True,
    }
    return HttpResponse(template.render(context, request))


def check_status(request):
    try:
        application = Application.objects.get(id=request.GET["app_id"])
        return render(
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
        return render(
            request,
            "app_status.html",
            {
                "show_search": True,
                "error_message": "Could not find your application ID in our database.",
            },
        )


def login_page(request):
    template = loader.get_template("login.html")
    return HttpResponse(template.render())


def login(request):
    """Legacy template login route; the React frontend should use api_login."""
    username = request.POST.get("user_in", "")
    password = request.POST.get("pass_in", "")
    user = authenticate(request, username=username, password=password)

    if user is None:
        return render(
            request,
            "login.html",
            {"error_message": "Username and password do not match."},
        )

    auth_login(request, user)
    homepage = {
        UserType.DRIVER: "accounts:driver_homepage",
        UserType.SPONSOR: "accounts:sponsor_homepage",
        UserType.ADMIN: "accounts:admin_homepage",
    }.get(user.user_type, "accounts:login_page")
    return HttpResponseRedirect(reverse(homepage))


def register_page(request):
    template = loader.get_template("register.html")
    return HttpResponse(template.render())


@csrf_protect
def register(request):
    """Legacy template registration route; the React frontend should use api_register."""
    username = request.POST.get("user_in", "").strip()
    password = request.POST.get("pass_in", "")

    if not username or not password:
        return render(
            request,
            "register.html",
            {"error_message": "Username and password are required."},
        )

    if User.objects.filter(username__iexact=username).exists():
        return render(
            request,
            "register.html",
            {"error_message": "Username already exists. Are you trying to log in?"},
        )

    try:
        validate_password(password)
    except ValidationError as error:
        return render(
            request,
            "register.html",
            {"error_message": " ".join(error.messages)},
        )

    with transaction.atomic():
        user = User.objects.create_user(
            username=username,
            password=password,
            user_type=UserType.DRIVER,
        )
        Driver.objects.create(user=user)

    auth_login(request, user)
    return HttpResponseRedirect(reverse("accounts:driver_homepage"))


def driver_homepage(request):
    template = loader.get_template("driver_home.html")
    context = {
        "username": request.user.username if request.user.is_authenticated else "username",
    }
    return HttpResponse(template.render(context, request))


def sponsor_homepage(request):
    template = loader.get_template("sponsor_home.html")
    context = {
        "username": request.user.username if request.user.is_authenticated else "username",
    }
    return HttpResponse(template.render(context, request))


def admin_homepage(request):
    template = loader.get_template("admin_home.html")
    context = {
        "username": request.user.username if request.user.is_authenticated else "username",
    }
    return HttpResponse(template.render(context, request))
