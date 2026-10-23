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

from .models import (Application, ApplicationStatus, Driver, Organization, Points, pointLog, Sponsor, User, UserType,)
from django.utils import timezone
from datetime import date, datetime, time, timedelta


def _request_data(request):
    """Read a JSON object or ordinary Django form data."""
    if request.content_type == "application/json":
        try:
            data = json.loads(request.body or "{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

        if not isinstance(data, dict):
            return None

        return data

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
             "organization_id": application.organization_id,
            "organization": (
                application.organization.organization_name
                if application.organization_id is not None
                else None
            ),
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

    with transaction.atomic():
        try:
            application = Application.objects.select_for_update().get(
                id=application_id,
                organization=sponsor.organization,
            )
        except Application.DoesNotExist:
            return JsonResponse({
                "error": "Application not found."
            }, status=404)

        if application.application_status != ApplicationStatus.PENDING:
            return JsonResponse({
                "error": "This application has already been reviewed."
            }, status=409)

        if new_status == ApplicationStatus.APPROVED:
            driver = Driver.objects.select_for_update().get(
                id=application.driver_id
            )
            driver.organization = application.organization
            driver.save(update_fields=["organization"])

        application.application_status = new_status
        application.review_date = timezone.now()
        application.rejection_reason = (
            rejection_reason
            if new_status == ApplicationStatus.REJECTED
            else ""
        )
        application.save(update_fields=[
            "application_status",
            "review_date",
            "rejection_reason",
        ])

    return JsonResponse({
        "application": {
            "id": application.id,
            "status": application.application_status,
            "rejection_reason": application.rejection_reason,
            "reviewed_at": application.review_date,
        }
    })

@require_POST
def api_change_points(request, driver_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "You must be logged in."}, status=401)

    if request.user.user_type != UserType.SPONSOR:
        return JsonResponse(
            {"error": "Only sponsors can change points."},
            status=403,
        )

    try:
        sponsor = request.user.sponsor
    except Sponsor.DoesNotExist:
        return JsonResponse(
            {"error": "Sponsor profile not found."},
            status=404,
        )

    if sponsor.organization is None:
        return JsonResponse(
            {"error": "Sponsor is not connected to an organization."},
            status=400,
        )

    data = _request_data(request)
    if data is None or not hasattr(data, "get"):
        return JsonResponse({"error": "Invalid request data."}, status=400)

    raw_points = data.get("points_changed")
    try:
        if isinstance(raw_points, bool) or not isinstance(raw_points, (int, str)):
            raise ValueError
        points_changed = int(raw_points)
    except (TypeError, ValueError):
        return JsonResponse(
            {"error": "Points changed must be a whole number."},
            status=400,
        )

    if not -2147483648 <= points_changed <= 2147483647:
        return JsonResponse(
            {"error": "Point adjustment is outside the allowed range."},
            status=400,
        )

    reason = data.get("reason", "")
    if not isinstance(reason, str):
        return JsonResponse({"error": "Reason must be text."}, status=400)
    reason = reason.strip()

    if points_changed == 0:
        return JsonResponse(
            {"error": "Points changed cannot be zero."},
            status=400,
        )

    if not reason or len(reason) > 255:
        return JsonResponse(
            {"error": "A reason between 1 and 255 characters is required."},
            status=400,
        )

    with transaction.atomic():
        try:
            driver = Driver.objects.select_for_update().get(
                id=driver_id,
                organization=sponsor.organization,
            )
        except Driver.DoesNotExist:
            return JsonResponse(
                {"error": "Driver not found in your organization."},
                status=404,
            )

        balance, _ = Points.objects.select_for_update().get_or_create(
            driver=driver,
            organization=sponsor.organization,
        )

        new_balance = balance.points_balance + points_changed

        if new_balance < 0 or new_balance > 4294967295:
            return JsonResponse(
                {"error": "The resulting balance is outside the allowed range."},
                status=400,
            )

        balance.points_balance = new_balance
        balance.save()

        log = pointLog.objects.create(
            driver=driver,
            organization=sponsor.organization,
            changed_by=sponsor,
            points_changed=points_changed,
            action=reason,
        )

    return JsonResponse({
        "driver_id": driver.id,
        "points_balance": balance.points_balance,
        "points_changed": points_changed,
        "reason": log.action,
        "timestamp": log.timestamp,
    })

@require_GET
def api_my_points(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "You must be logged in."},
            status=401,
        )

    if request.user.user_type != UserType.DRIVER:
        return JsonResponse(
            {"error": "Only drivers can view their points here."},
            status=403,
        )

    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse(
            {"error": "Driver profile not found."},
            status=404,
        )

    if driver.organization_id is None:
        return JsonResponse({
            "organization_id": None,
            "organization": None,
            "points_balance": 0,
            "last_updated": None,
        })

    balance = Points.objects.filter(
        driver=driver,
        organization_id=driver.organization_id,
    ).first()

    return JsonResponse({
        "organization_id": driver.organization_id,
        "organization": driver.organization.organization_name,
        "points_balance": balance.points_balance if balance else 0,
        "last_updated": balance.last_updated if balance else None,
    })
@require_GET
def api_my_point_history(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "You must be logged in."},
            status=401,
        )

    if request.user.user_type != UserType.DRIVER:
        return JsonResponse(
            {"error": "Only drivers can view their point history here."},
            status=403,
        )

    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse(
            {"error": "Driver profile not found."},
            status=404,
        )

    logs = pointLog.objects.filter(
        driver=driver,
    ).select_related(
        "organization",
        "changed_by__user",
    ).order_by("-timestamp", "-id")

    history = [
        {
            "id": log.id,
            "organization_id": log.organization_id,
            "organization": log.organization.organization_name,
            "points_changed": log.points_changed,
            "reason": log.action,
            "changed_by": (
                log.changed_by.user.username
                if log.changed_by_id is not None
                else None
            ),
            "timestamp": log.timestamp,
        }
        for log in logs
    ]

    return JsonResponse({"history": history})

@require_GET
def api_sponsor_point_tracking(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "You must be logged in."},
            status=401,
        )

    if request.user.user_type != UserType.SPONSOR:
        return JsonResponse(
            {"error": "Only sponsors can view this report."},
            status=403,
        )

    try:
        sponsor = request.user.sponsor
    except Sponsor.DoesNotExist:
        return JsonResponse(
            {"error": "Sponsor profile not found."},
            status=404,
        )

    if sponsor.organization_id is None:
        return JsonResponse(
            {"error": "Sponsor is not connected to an organization."},
            status=400,
        )

    drivers = Driver.objects.filter(
        organization_id=sponsor.organization_id,
    ).select_related("user").order_by("user__username")

    balances = dict(
        Points.objects.filter(
            organization_id=sponsor.organization_id,
        ).values_list("driver_id", "points_balance")
    )

    logs = pointLog.objects.filter(
        organization_id=sponsor.organization_id,
        driver__organization_id=sponsor.organization_id,
    ).select_related("changed_by__user").order_by("-timestamp", "-id")

    driver_id = request.GET.get("driver_id")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if driver_id is not None:
        try:
            driver_id = int(driver_id)
            if driver_id <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return JsonResponse(
                {"error": "Driver ID must be a positive whole number."},
                status=400,
            )

        drivers = drivers.filter(id=driver_id)

        if not drivers.exists():
            return JsonResponse(
                {"error": "Driver not found in your organization."},
                status=404,
            )

        logs = logs.filter(driver_id=driver_id)

    try:
        start = date.fromisoformat(start_date) if start_date else None
        end = date.fromisoformat(end_date) if end_date else None
    except ValueError:
        return JsonResponse(
            {"error": "Dates must use YYYY-MM-DD format."},
            status=400,
        )

    if start and end and start > end:
        return JsonResponse(
            {"error": "Start date must be on or before end date."},
            status=400,
        )

    current_timezone = timezone.get_current_timezone()

    if start:
        start_time = timezone.make_aware(
            datetime.combine(start, time.min),
            current_timezone,
        )
        logs = logs.filter(timestamp__gte=start_time)

    if end:
        try:
            next_day = end + timedelta(days=1)
        except OverflowError:
            return JsonResponse(
                {"error": "End date is outside the supported range."},
                status=400,
            )

        end_time = timezone.make_aware(
            datetime.combine(next_day, time.min),
            current_timezone,
        )
        logs = logs.filter(timestamp__lt=end_time)

    history_by_driver = {}

    for log in logs:
        history_by_driver.setdefault(log.driver_id, []).append({
            "id": log.id,
            "points_changed": log.points_changed,
            "reason": log.action,
            "changed_by": (
                log.changed_by.user.username
                if log.changed_by_id is not None
                else None
            ),
            "timestamp": log.timestamp,
        })

    return JsonResponse({
        "organization_id": sponsor.organization_id,
        "drivers": [
            {
                "driver_id": driver.id,
                "username": driver.user.username,
                "name": driver.user.get_full_name() or driver.user.username,
                "points_balance": balances.get(driver.id, 0),
                "history": history_by_driver.get(driver.id, []),
            }
            for driver in drivers
        ],
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


@require_GET
def check_status(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("accounts:login_page"))

    if request.user.user_type != UserType.DRIVER:
        return HttpResponse("Only drivers can check application status.", status=403)

    try:
        application_id = int(request.GET.get("app_id", ""))
    except (TypeError, ValueError):
        application_id = None

    application = Application.objects.filter(
        id=application_id,
        driver__user=request.user,
    ).first()

    if application is None:
        return render(
            request,
            "app_status.html",
            {
                "show_search": True,
                "error_message": "Could not find that application in your account.",
            },
        )

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


def login_page(request):
    return render(request, "login.html")


@require_POST
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
    return render(request, "register.html")


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


def _role_homepage(request, required_role, template_name):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("accounts:login_page"))

    if request.user.user_type != required_role:
        return HttpResponse("You do not have access to this page.", status=403)

    return render(
        request,
        template_name,
        {"username": request.user.username},
    )

@require_GET
def driver_homepage(request):
    return _role_homepage(
        request, UserType.DRIVER, "driver_home.html"
    )


@require_GET
def sponsor_homepage(request):
    return _role_homepage(
        request, UserType.SPONSOR, "sponsor_home.html"
    )

@require_GET
def admin_homepage(request):
    return _role_homepage(
        request, UserType.ADMIN, "admin_home.html"
    )