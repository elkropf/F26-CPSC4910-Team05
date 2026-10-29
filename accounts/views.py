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

from .models import (Application, ApplicationStatus, BulkImportJob, Driver, DriverOrganization, Organization, Points, User, UserType, Sponsor, pointLog,)
from django.utils import timezone
from datetime import date, datetime, time, timedelta
from django.http import StreamingHttpResponse
from .bulk_import import process_import_file
from django.db.models import Q
from .account_setup import send_account_setup_email
from django.http import FileResponse
from .audit import record_event
from django.core.paginator import Paginator
from .audit import can_view_audit_log, filter_audit_logs, csv_text
from django.core.exceptions import PermissionDenied, ValidationError
import csv
from .notifications import create_notification
from .models import notification

#Read JSON / form data from a request
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

#format user info for api
def _user_data(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "user_type": user.user_type,
    }

# JSON authentication endpoints for the React frontend.

#set csrf cookie for React frontend
@require_GET
@ensure_csrf_cookie

#set csrf cookie for React frontend
def api_csrf(request):
    return JsonResponse({"detail": "CSRF cookie set."})

#register a new driver account
@require_POST
def api_register(request):
    data = _request_data(request)
    if data is None:
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    email = str(data.get("email", "")).strip()
    user_type = str(data.get("user_type", "")).strip()

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
            user_type=UserType.SPONSOR if user_type == "Sponsor" else UserType.DRIVER,
        )
        if user_type == "Sponsor":
            Sponsor.objects.create(user=user)
        else:
            Driver.objects.create(user=user)
        record_event(
            action="user.registered",
            actor=user,
            record_type="user",
            record_id=user.id,
            description=f"New {user_type} account created with username '{username}'."
        )

    auth_login(request, user)
    return JsonResponse({"user": _user_data(user)}, status=201)

#authenticate and start new user sesssio
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
        record_event(
            action="user.login_failed",
            actor=None,
            record_type="user",
            record_id=None,
            description=f"Failed login attempt for username '{username}'."
        )
        return JsonResponse(
            {"error": "Invalid username or password."},
            status=401,
        )

    if not user.is_active:
        return JsonResponse({"error": "This account is inactive."}, status=403)

    auth_login(request, user)
    record_event(
        action="user.logged_in",
        actor=user,
        record_type="user",
        record_id=user.id,
        description=f"User '{username}' logged in."
    )
    return JsonResponse({"user": _user_data(user)})

#end current user session
@require_POST
def api_logout(request):
    auth_logout(request)
    record_event(
        action="user.logged_out",
        actor=user,
        record_type="user",
        record_id=request.user.id,
        description=f"User '{user.username}' logged out."
    )
    return JsonResponse({"detail": "Logged out successfully."})

#return currentuser signed in info
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

#list active sponsor organizations
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

#submit driver applicationto an org
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
    record_event(
        action="application.submitted",
        actor=request.user,
        organization=organization,
        record_type="application",
        record_id=application.id,
        description=f"Driver {driver.id} ({driver.user.username}) submitted an application to organization {organization.id} ({organization.organization_name})."
    )

    return JsonResponse({
        "application": {
            "id": application.id,
            "organization": organization.organization_name,
            "status": application.application_status,
            "message": application.application_message,
        }
    }, status=201)

#list driver applications submitted by current user
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

#list pending applications for the sponsor's organization
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

#approve / rehject and application and add approved membership
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
            DriverOrganization.objects.get_or_create(
                driver=driver,
                organization_id=application.organization_id,
            )

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
        record_event(
            action="application.status_changed",
            actor=request.user,
            organization=sponsor.organization,
            record_type="application",
            record_id=application.id,
            description=f"Application status changed to {new_status} for application {application.id}."
        )
        organization_name = application.organization.organization_name
        message = f"Your application to " f"{organization_name} " f"was {new_status}."

        if new_status == ApplicationStatus.REJECTED:
            message += f" Reason {rejection_reason}"

            create_notification(
                user=application.driver.user,
                notification_type="application",
                organization=application.organization,
                message=message,
            )

    return JsonResponse({
        "application": {
            "id": application.id,
            "status": application.application_status,
            "rejection_reason": application.rejection_reason,
            "reviewed_at": application.review_date,
        }
    })

#adjust drivers organization sepcific points and log change
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

    if not reason:
        return JsonResponse(
            {"error": "A reason is required."},
            status=400,
        )

    with transaction.atomic():
        try:
            driver = Driver.objects.select_for_update().get(
                id=driver_id,
                memberships__organization_id=sponsor.organization_id,
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
            changed_by_user=request.user,
            points_changed=points_changed,
            action=reason,
        )
        record_event(
            action="points.adjusted",
            actor=request.user,
            organization=sponsor.organization,
            record_type="pointLog",
            record_id=log.id,
            description=f"Points changed by {points_changed} for driver {driver.id} ({driver.user.username}) in organization {sponsor.organization_id}. Reason: {reason}",
        )
        create_notification(
            user=driver.user,
            notification_type="points",
            organization=sponsor.organization,
            message=(
                f"{sponsor.organization.organization_name} changed"
                f"your points by {points_changed}. "
                f"Reason: {reason}. "
                f"New balance: {new_balance}. "
            )
        )


    return JsonResponse({
        "driver_id": driver.id,
        "points_balance": balance.points_balance,
        "points_changed": points_changed,
        "reason": log.action,
        "timestamp": log.timestamp,
    })

#return signed in drivers points balance
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

    memberships = DriverOrganization.objects.filter(
        driver=driver,
    ).select_related("organization").order_by(
        "organization__organization_name", "organization_id"
    )

    balances = {
        balance.organization_id: balance
        for balance in Points.objects.filter(driver=driver)
    }

    organizations = []

    for membership in memberships:
        organization = membership.organization
        balance = balances.get(organization.id)

        organizations.append({
            "organization_id": organization.id,
            "organization": organization.organization_name,
            "points_balance": balance.points_balance if balance else 0,
            "last_updated": balance.last_updated if balance else None,
        })

    return JsonResponse({"organizations": organizations})

#drivers point change history
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
        "changed_by_user",
    ).order_by("-timestamp", "-id")

    organization_id = request.GET.get("organization_id")

    if organization_id is not None:
        try:
            organization_id = int(organization_id)
            if organization_id <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return JsonResponse(
                {"error": "Organization ID must be a positive whole number."},
                status=400,
            )

        logs = logs.filter(organization_id=organization_id)

    history = [
        {
            "id": log.id,
            "organization_id": log.organization_id,
            "organization": log.organization.organization_name,
            "points_changed": log.points_changed,
            "reason": log.action,
            "changed_by": (
                log.changed_by_user.username
                if log.changed_by_user_id is not None
                else None
            ),
            "timestamp": log.timestamp,
        }
        for log in logs
    ]

    return JsonResponse({"history": history})

#report driver balance and history for sponsor's organization
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
        memberships__organization_id=sponsor.organization_id,
    ).select_related("user").order_by("user__username")

    balances = dict(
        Points.objects.filter(
            organization_id=sponsor.organization_id,
        ).values_list("driver_id", "points_balance")
    )

    logs = pointLog.objects.filter(
        organization_id=sponsor.organization_id,
        driver__memberships__organization_id=sponsor.organization_id,
    ).select_related("changed_by_user").order_by("-timestamp", "-id")

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
                log.changed_by_user.username
                if log.changed_by_user_id is not None
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

#upload bulk-import file and stream line-numbered results
@require_POST
def api_bulk_import(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "You must be logged in."},
            status=401,
        )

    if request.user.user_type not in (
        UserType.SPONSOR,
        UserType.ADMIN,
    ):
        return JsonResponse(
            {"error": "Only sponsors and admins can import users."},
            status=403,
        )

    if request.user.user_type == UserType.SPONSOR:
        try:
            sponsor = request.user.sponsor
        except Sponsor.DoesNotExist:
            return JsonResponse(
                {"error": "Sponsor profile not found."},
                status=404,
            )

        if sponsor.organization_id is None:
            return JsonResponse(
                {"error": "Sponsor has no organization."},
                status=400,
            )

        if not sponsor.organization.is_active:
            return JsonResponse(
                {"error": "Your organization is inactive."},
                status=403,
            )

    uploaded_file = request.FILES.get("file")

    if uploaded_file is None:
        return JsonResponse(
            {"error": "Upload a file using the field named 'file'."},
            status=400,
        )

    if uploaded_file.size == 0:
        return JsonResponse(
            {"error": "The uploaded file is empty."},
            status=400,
        )

    job = BulkImportJob(
        uploaded_by=request.user,
        organization=(sponsor.organization
                    if request.user.user_type == UserType.SPONSOR
                    else None
                    ),
    )

    try:
        job.source_file.save(
            uploaded_file.name,
            uploaded_file,
            save=False,
        )
        job.save()

        record_event(
            action="bulk_import.submitted",
            actor=request.user,
            organization=job.organization,
            record_type="bulk_import_job",
            record_id=job.id,
            description=f"Bulk import job {job.id} submitted by user {request.user.id} ({request.user.username})."
        )

    except Exception:
        #remove the stored file if creating its job failed.
        if job.source_file.name:
            job.source_file.delete(save=False)
        raise

    response = JsonResponse(
        {
            "job_id": job.id,
            "status": job.status,
            "detail": "File uploaded and queued for processing.",
        },
        status=202,
    )
    response["Cache-Control"] = "no-store"
    return response

#resend setup instructions
@require_POST
def api_resend_account_setup(request, user_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "You must be logged in."}, status=401)

    if request.user.user_type not in (UserType.ADMIN, UserType.SPONSOR):
        return JsonResponse({"error": "Access denied."}, status=403)

    users = User.objects.filter(
        id=user_id,
        is_active=True,
        user_type__in=[UserType.DRIVER, UserType.SPONSOR],
    )

    if request.user.user_type == UserType.SPONSOR:
        try:
            organization_id = request.user.sponsor.organization_id
        except Sponsor.DoesNotExist:
            return JsonResponse({"error": "Sponsor profile not found."}, status=404)

        if organization_id is None:
            return JsonResponse({"error": "Sponsor has no organization."}, status=400)

        users = users.filter(
            Q(driver__memberships__organization_id=organization_id)
            | Q(sponsor__organization_id=organization_id)
        )

    user = users.distinct().first()

    if user is None:
        return JsonResponse({"error": "Account not found."}, status=404)

    if user.has_usable_password():
        return JsonResponse(
            {"error": "Account setup is complete. Use password reset instead."},
            status=409,
        )

    if not user.email:
        return JsonResponse({"error": "Account has no email address."}, status=400)

    try:
        send_account_setup_email(user, request.build_absolute_uri("/"))
    except Exception:
        return JsonResponse(
            {"error": "Setup email could not be sent. Please try again later."},
            status=503,
        )
    record_event(
        action="user.account_setup_email_sent",
        actor=request.user,
        record_type="user",
        record_id=user.id,
        description=f"Account setup email resent to user {user.id} ({user.username})."
    )
    return JsonResponse({"detail": "Setup email submitted successfully."})

#list users notifications
@require_GET
def api_notifications(request):
    notifications = notification.objects.filter(user=request.user).select_related("organization")

    unread_count = notifications.filter(is_read=False).count()

    paginator = Paginator(notifications, 25)
    page = paginator.get_page(request.GET.get("page",1))

    notification_list = []

    for item in page:
        organization_name = None

        if item.organization is not None:
            organization_name = item.organization.organization_name

        notification_list.append({
            "id": item.id,
            "type": item.notification_type,
            "message": item.message,
            "organization": organization_name,
            "organization_id": item.organization_id,
            "is_read": item.is_read,
            "created_at": item.created_at,
        })

    response = JsonResponse({
        "notifications": notification_list,
        "unread_count": unread_count,
        "page": page.number,
        "total_pages": paginator.num_pages,
    })
    response["Cache-Control"] = "no-store"
    return response


# Existing server-rendered pages.

#display application form
def app_page(request):
    template = loader.get_template("application.html")
    context = {
        "organization": Organization.objects.order_by("-id"),
    }
    return HttpResponse(template.render(context, request))

#placeholder legacy application search page
def apply(request):
    raise Http404("Not implemented yet")

#placwehokder for legacy application submision
def app_status(request):
    template = loader.get_template("app_status.html")
    context = {
        "show_search": True,
    }
    return HttpResponse(template.render(context, request))

#look up for application for driver
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

#django login form with csrf protection
def login_page(request):
    return render(request, "login.html")

#process form and redirect by role
@require_POST
def login(request):
    """Legacy template login route; the React frontend should use api_login."""
    username = request.POST.get("user_in", "")
    password = request.POST.get("pass_in", "")
    user = authenticate(request, username=username, password=password)

    if user is None:
        record_event(
                    action="user.login_failed",
                    actor=None,
                    record_type="user",
                    record_id=None,
                    description=f"Failed login attempt for username '{username}'."
                )
        return render(
            request,
            "login.html",
            {"error_message": "Username and password do not match."},
        )

    auth_login(request, user)
    record_event(
        action="user.logged_in",
        actor=user,
        record_type="user",
        record_id=user.id,
        description=f"User '{username}' logged in.",
    )
    homepage = {
        UserType.DRIVER: "accounts:driver_homepage",
        UserType.SPONSOR: "accounts:sponsor_homepage",
        UserType.ADMIN: "accounts:admin_homepage",
    }.get(user.user_type, "accounts:login_page")
    return HttpResponseRedirect(reverse(homepage))

#display django registration form
def register_page(request):
    return render(request, "register.html")

#process django registration form and create new driver account
@csrf_protect
def register(request):
    """Legacy template registration route; the React frontend should use api_register."""
    username = request.POST.get("user_in", "").strip()
    password = request.POST.get("pass_in", "")
    user_type = request.POST.get("user_type", "")

    if not username or not password or not user_type:
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
            user_type=UserType.SPONSOR if user_type == "Sponsor" else UserType.DRIVER,
        )
        if user_type == "Sponsor":
            org = Organization.objects.get(organization_name="Test Organizzation")
            Sponsor.objects.create(user=user, organization=org)
        else:
            Driver.objects.create(user=user)

    auth_login(request, user)
    link = "accounts:sponsor_homepage" if user_type == "Sponsor" else "accounts:driver_homepage"
    return HttpResponseRedirect(reverse(link))

#display role specific homepage for driver, sponsor, or admin
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

#display driver homepage
@require_GET
def driver_homepage(request):
    return _role_homepage(
        request, UserType.DRIVER, "driver_home.html"
    )

#displat sponsor homepage
@require_GET
def sponsor_homepage(request):
    return _role_homepage(
        request, UserType.SPONSOR, "sponsor_home.html"
    )

#display admin homepage
@require_GET
def admin_homepage(request):
    return _role_homepage(
        request, UserType.ADMIN, "admin_home.html"
    )

#show import progresse
@require_GET
def api_bulk_import_status(request, job_id):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "You must be logged in."},
            status=401,
        )

    if request.user.user_type not in (
        UserType.SPONSOR,
        UserType.ADMIN,
    ):
        return JsonResponse(
            {"error": "Access denied."},
            status=403,
        )

    job = BulkImportJob.objects.filter(
        id=job_id,
        uploaded_by=request.user,
    ).first()

    if job is None:
        return JsonResponse(
            {"error": "Import job not found."},
            status=404,
        )

    response = JsonResponse({
        "job_id": job.id,
        "status": job.status,
        "processed_rows": job.processed_rows,
        "successful_rows": job.successful_rows,
        "failed_rows": job.failed_rows,
        "error": job.error_message,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
        "results_available": bool(job.result_file.name),
    })
    response["Cache-Control"] = "no-store"
    return response

#download bulk import results file
@require_GET
def api_bulk_import_results(request, job_id):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "You must be logged in."},
            status=401,
        )

    if request.user.user_type not in (
        UserType.SPONSOR,
        UserType.ADMIN,
    ):
        return JsonResponse(
            {"error": "Access denied."},
            status=403,
        )

    job = BulkImportJob.objects.filter(
        id=job_id,
        uploaded_by=request.user,
    ).first()

    if job is None:
        return JsonResponse(
            {"error": "Import job not found."},
            status=404,
        )

    if job.status not in (
        BulkImportJob.Status.COMPLETED,
        BulkImportJob.Status.FAILED,
    ) or not job.result_file.name:
        return JsonResponse(
            {"error": "Results are not available yet."},
            status=409,
        )

    try:
        result_file = job.result_file.open("rb")
    except FileNotFoundError:
        return JsonResponse(
            {"error": "The results file could not be found."},
            status=404,
        )

    response = FileResponse(
        result_file,
        as_attachment=True,
        filename=f"bulk-import-{job.id}-results.ndjson",
        content_type="application/x-ndjson",
    )
    response["Cache-Control"] = "no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response

#show audit logs wiht filters and pagination
def api_audit_logs(request):
    try:
        logs = can_view_audit_log(request.user)
    except PermissionDenied:
        return JsonResponse({"Error":" You cannot view these logs"}, status=403)

    try:
        logs = filter_audit_logs(logs, request.GET)
    except ValueError:
        return JsonResponse({"Error":" Check user ID and date filters"}, status=400)

    paginator = Paginator(logs, 50)
    page = paginator.get_page(request.GET.get("page", 1))
    log_list = []
    for log in page:
        username = None
        if log.user is not None:
            username = log.user.username

        log_list.append({
            "id": log.id,
            "username": username,
            "actor_role": log.actor_role,
            "action": log.action,
            "organization_id": log.organization_id,
            "record_type": log.record_type,
            "record_id": log.record_id,
            "description": log.description,
            "timestamp": log.timestamp,
        })

        response = JsonResponse({
            "logs": log_list,
            "page": page.number,
            "total_pages": paginator.num_pages,
            "total_logs": paginator.count,
        })
        response["Cache-Control"] = "no-store"
        return response

#download logs matching filters
@require_GET
def api_audit_logs_download(request):
    if not request.user.is_authenticated:
        return JsonResponse({"Error" : "You need to be logged in"}, status=401)
    try:
        logs = can_view_audit_log(request.user)
        logs = filter_audit_logs(logs, request.GET)
    except PermissionDenied:
        return JsonResponse({"error":"Access denied"}, status=403)
    except ValueError:
        return JsonResponse({"error":"Check your filters"}, status=400)

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="audit-logs.csv"'
    response["Cache-Control"] = "no-store"

    writer = csv.writer(response)
    writer.writerow(["ID", "Username", "Action", "Organization ID", "Record Type", "Record ID", "Description", "Timestamp (UTC)"])

    for log in logs.iterator():
        username = ""
        if log.user is not None:
            username = log.user.username

        writer.writerow([
            log.id,
            csv_text(username),
            csv_text(log.action),
            log.organization_id,
            csv_text(log.record_type),
            log.record_id,
            csv_text(log.description),
            log.timestamp.isoformat(),
        ])
        return response