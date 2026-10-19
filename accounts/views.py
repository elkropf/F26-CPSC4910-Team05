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

from .models import (Application, ApplicationStatus, Driver, Organization, Sponsor, User, UserType,)
from django.utils import timezone


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

@require_GET
def api_organizations(request):
    organizations = Organization.objects.filter(
        is_active=True
    ).order_by("organization_name")

    organization_list = []

    for organization in organizations:
        organization_list.append({
            "id": organization.id,
            "name": organization.organization_name,
            "description": organization.organization_description,
        })

    return JsonResponse({
        "organizations": organization_list
    })

@require_POST
def api_submit_application(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            "error": "You must be logged in to apply."
        }, status=401)

    if request.user.user_type != UserType.DRIVER:
        return JsonResponse({
            "error": "Only drivers can submit applications."
        }, status=403)

    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            "error": "Driver profile not found."
        }, status=404)
    
    data = _request_data(request)

    if data is None:
        return JsonResponse({
            "error": "Invalid JSON."
        }, status=400)

    try:
        organization_id = int(data.get("organization_id"))
    except (TypeError, ValueError):
        return JsonResponse({
            "error": "A valid organization ID is required."
        }, status=400)

    try:
        organization = Organization.objects.get(
            id=organization_id,
            is_active=True
        )
    except Organization.DoesNotExist:
        return JsonResponse({
            "error": "Organization not found."
        }, status=404)
    if Application.objects.filter(
        driver=driver,
        organization=organization
    ).exists():
        return JsonResponse({
            "error": "You already applied to this organization."
        }, status=409)

    application = Application.objects.create(
        driver=driver,
        organization=organization,
        application_message=data.get("message", "")
    )

    return JsonResponse({
        "application": {
            "id": application.id,
            "organization": organization.organization_name,
            "status": application.application_status,
            "message": application.application_message,
        }
    }, status=201)
    
@require_GET
def api_my_applications(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            "error": "You must be logged in."
        }, status=401)

    if request.user.user_type != UserType.DRIVER:
        return JsonResponse({
            "error": "Only drivers can view this application list."
        }, status=403)

    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            "error": "Driver profile not found."
        }, status=404)

    applications = Application.objects.filter(
        driver=driver
    ).select_related("organization").order_by("-submission_date")

    application_list = []

    for application in applications:
        application_list.append({
            "id": application.id,
            "organization_id": application.organization.id,
            "organization": application.organization.organization_name,
            "status": application.application_status,
            "message": application.application_message,
            "submitted_at": application.submission_date,
            "reviewed_at": application.review_date,
        })

    return JsonResponse({
        "applications": application_list
    })

@require_GET
def api_sponsor_applications(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            "error": "You must be logged in."
        }, status=401)

    if request.user.user_type != UserType.SPONSOR:
        return JsonResponse({
            "error": "Only sponsors can view pending applications."
        }, status=403)

    try:
        sponsor = request.user.sponsor
    except Sponsor.DoesNotExist:
        return JsonResponse({
            "error": "Sponsor profile not found."
        }, status=404)

    if sponsor.organization is None:
        return JsonResponse({
            "error": "Sponsor is not connected to an organization."
        }, status=400)

    applications = Application.objects.filter(
        organization=sponsor.organization,
        application_status=ApplicationStatus.PENDING
    ).select_related("driver__user").order_by("submission_date")

    application_list = []

    for application in applications:
        application_list.append({
            "id": application.id,
            "driver_id": application.driver.id,
            "username": application.driver.user.username,
            "message": application.application_message,
            "status": application.application_status,
            "submitted_at": application.submission_date,
        })

    return JsonResponse({
        "applications": application_list
    })

@require_POST
def api_review_application(request, application_id):
    if not request.user.is_authenticated:
        return JsonResponse({
            "error": "You must be logged in."
        }, status=401)

    if request.user.user_type != UserType.SPONSOR:
        return JsonResponse({
            "error": "Only sponsors can review applications."
        }, status=403)

    try:
        sponsor = request.user.sponsor
    except Sponsor.DoesNotExist:
        return JsonResponse({
            "error": "Sponsor profile not found."
        }, status=404)

    if sponsor.organization is None:
        return JsonResponse({
            "error": "Sponsor is not connected to an organization."
        }, status=400)

    data = _request_data(request)

    if data is None:
        return JsonResponse({
            "error": "Invalid JSON."
        }, status=400)

    new_status = str(data.get("status", "")).lower()
    rejection_reason = str(data.get("rejection_reason", "")).strip()

    if new_status not in [
        ApplicationStatus.APPROVED,
        ApplicationStatus.REJECTED
    ]:
        return JsonResponse({
            "error": "Status must be approved or rejected."
        }, status=400)

    if (
        new_status == ApplicationStatus.REJECTED
        and not rejection_reason
    ):
        return JsonResponse({
            "error": "A rejection reason is required."
        }, status=400)

    try:
        application = Application.objects.select_related(
            "driver",
            "organization"
        ).get(
            id=application_id,
            organization=sponsor.organization
        )
    except Application.DoesNotExist:
        return JsonResponse({
            "error": "Application not found."
        }, status=404)

    if application.application_status != ApplicationStatus.PENDING:
        return JsonResponse({
            "error": "This application has already been reviewed."
        }, status=409)

    with transaction.atomic():
        application.application_status = new_status
        application.review_date = timezone.now()
        application.rejection_reason = (
            rejection_reason
            if new_status == ApplicationStatus.REJECTED
            else ""
        )
        application.save()

        if new_status == ApplicationStatus.APPROVED:
            application.driver.organization = application.organization
            application.driver.save()

    return JsonResponse({
        "application": {
            "id": application.id,
            "status": application.application_status,
            "rejection_reason": application.rejection_reason,
            "reviewed_at": application.review_date,
        }
    })

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
