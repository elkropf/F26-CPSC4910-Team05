import csv
import json
from decimal import Decimal, InvalidOperation
from functools import wraps

from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Sum
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.decorators.http import require_GET, require_POST

from .audit import csv_text, record_event
from .models import (
    Admin, Application, ApplicationStatus, Driver, DriverOrganization,
    Order, Organization, Points, Product, Sponsor, User, UserType,
)


def admin_only(fn):
    @wraps(fn)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Login required."}, status=401)
        if not request.user.is_active or request.user.user_type != UserType.ADMIN:
            return JsonResponse({"error": "Admin permission required."}, status=403)
        return fn(request, *args, **kwargs)
    return wrapped


def payload(request):
    try:
        result = json.loads(request.body or b"{}")
    except (ValueError, UnicodeDecodeError):
        return None
    return result if isinstance(result, dict) else None


def error(message, code=400):
    return JsonResponse({"error": message}, status=code)


def user_info(user):
    return {
        "id": user.pk, "username": user.username,
        "email": user.email, "first_name": user.first_name,
        "last_name": user.last_name, "is_active": user.is_active,
        "user_type": user.user_type,
    }


def sponsor_info(sponsor):
    info = user_info(sponsor.user)
    info.update({
        "sponsor_id": sponsor.pk,
        "organization_id": sponsor.organization_id,
        "organization": (sponsor.organization.organization_name
                         if sponsor.organization else None),
        "fee_percentage": str(sponsor.fee_percentage),
    })
    return info


def driver_info(driver):
    info = user_info(driver.user)
    info["driver_id"] = driver.pk
    memberships = list(driver.memberships.select_related("organization").all())
    info["organizations"] = [
        {"id": m.organization_id, "name": m.organization.organization_name}
        for m in memberships
    ]
    return info


@require_GET
@admin_only
def overview(request):
    return JsonResponse({"summary": {
        "drivers": Driver.objects.count(),
        "sponsors": Sponsor.objects.count(),
        "admins": Admin.objects.count(),
        "organizations": Organization.objects.count(),
        "orders": Order.objects.count(),
        "total_points_outstanding": Points.objects.aggregate(total=Sum("points_balance"))["total"] or 0,
    }})


@require_GET
@admin_only
def directory(request):
    # Small course-project directory. Extend with pagination if dataset is large.
    sponsors = Sponsor.objects.select_related("user", "organization").order_by("user__username")[:1000]
    drivers = Driver.objects.select_related("user").prefetch_related("memberships__organization").order_by("user__username")[:1000]
    admins = Admin.objects.select_related("user").order_by("user__username")[:1000]
    organizations = Organization.objects.order_by("organization_name")[:1000]
    return JsonResponse({
        "sponsors": [sponsor_info(s) for s in sponsors],
        "drivers": [driver_info(d) for d in drivers],
        "admins": [user_info(a.user) for a in admins],
        "organizations": [{"id": o.pk, "name": o.organization_name,
                           "is_active": o.is_active} for o in organizations],
    })


def validate_new_user(data):
    username = str(data.get("username") or "").strip()
    password = data.get("password")
    email = str(data.get("email") or "").strip()
    if not username or not isinstance(password, str) or not password:
        return None, "Username and password are required."
    if User.objects.filter(username__iexact=username).exists():
        return None, "Username already exists."
    try:
        validate_password(password)
    except ValidationError as exc:
        return None, " ".join(exc.messages)
    return {
        "username": username, "password": password, "email": email,
        "first_name": str(data.get("first_name") or "").strip(),
        "last_name": str(data.get("last_name") or "").strip(),
    }, None


@require_POST
@admin_only
def create_sponsor(request):
    data = payload(request)
    if data is None:
        return error("Invalid JSON.")
    user_fields, validation_error = validate_new_user(data)
    if validation_error:
        return error(validation_error)

    organization_id = data.get("organization_id")
    organization_name = str(data.get("organization_name") or "").strip()
    if not organization_id and not organization_name:
        return error("Choose an existing organization or enter a new organization name.")
    with transaction.atomic():
        if organization_id:
            try:
                organization = Organization.objects.get(pk=int(organization_id), is_active=True)
            except (ValueError, TypeError, Organization.DoesNotExist):
                return error("Active organization not found.", 404)
        else:
            if Organization.objects.filter(organization_name__iexact=organization_name).exists():
                return error("This organization already exists. Choose it from the list.", 409)
            organization = Organization.objects.create(organization_name=organization_name)
        user = User.objects.create_user(user_type=UserType.SPONSOR, **user_fields)
        sponsor = Sponsor.objects.create(user=user, organization=organization)
        record_event(action="admin.sponsor_created", actor=request.user,
                     organization=organization, record_type="sponsor", record_id=sponsor.pk,
                     description=f"Created sponsor {user.username}.")
    return JsonResponse({"sponsor": sponsor_info(sponsor)}, status=201)


@require_POST
@admin_only
def create_admin(request):
    data = payload(request)
    if data is None:
        return error("Invalid JSON.")
    fields, validation_error = validate_new_user(data)
    if validation_error:
        return error(validation_error)
    with transaction.atomic():
        user = User.objects.create_user(user_type=UserType.ADMIN, **fields)
        Admin.objects.create(user=user)
        record_event(action="admin.account_created", actor=request.user,
                     record_type="user", record_id=user.pk,
                     description=f"Created administrator {user.username}.")
    return JsonResponse({"admin": user_info(user)}, status=201)


@require_POST
@admin_only
def update_fee(request, sponsor_id):
    data = payload(request)
    if data is None:
        return error("Invalid JSON.")
    raw = data.get("fee_percentage")
    if isinstance(raw, bool) or raw is None:
        return error("Fee must be a percentage between 0 and 100.")
    try:
        fee = Decimal(str(raw))
        if not fee.is_finite() or fee < 0 or fee > 100 or fee.as_tuple().exponent < -2:
            raise InvalidOperation
    except (InvalidOperation, ValueError):
        return error("Fee must be 0 to 100 with up to two decimal places.")
    try:
        sponsor = Sponsor.objects.select_related("organization", "user").get(pk=sponsor_id)
    except Sponsor.DoesNotExist:
        return error("Sponsor not found.", 404)
    sponsor.fee_percentage = fee
    sponsor.save(update_fields=["fee_percentage"])
    record_event(action="admin.sponsor_fee_changed", actor=request.user,
                 organization=sponsor.organization, record_type="sponsor", record_id=sponsor.pk,
                 description=f"Fee set to {fee}% for {sponsor.user.username}.")
    return JsonResponse({"sponsor": sponsor_info(sponsor)})


@require_POST
@admin_only
def assign_driver(request, driver_id):
    data = payload(request)
    if data is None:
        return error("Invalid JSON.")
    try:
        sponsor_id = int(data.get("sponsor_id"))
    except (TypeError, ValueError):
        return error("Choose a sponsor.")
    with transaction.atomic():
        try:
            driver = Driver.objects.select_for_update().select_related("user").get(pk=driver_id)
            sponsor = Sponsor.objects.select_related("organization", "user").get(pk=sponsor_id)
        except (Driver.DoesNotExist, Sponsor.DoesNotExist):
            return error("Driver or sponsor not found.", 404)
        if not sponsor.user.is_active or not sponsor.organization or not sponsor.organization.is_active:
            return error("Sponsor must belong to an active organization.")
        # DriverOrganization permits multiple orgs in main. The administrator
        # assignment keeps exactly one membership, preserving old Points/Orders.
        DriverOrganization.objects.filter(driver=driver).exclude(
            organization=sponsor.organization).delete()
        DriverOrganization.objects.get_or_create(driver=driver, organization=sponsor.organization)
        Application.objects.filter(driver=driver, application_status=ApplicationStatus.APPROVED).exclude(
            organization=sponsor.organization).update(
                application_status=ApplicationStatus.REJECTED,
                rejection_reason="Reassigned by administrator.", review_date=timezone.now())
        application, _ = Application.objects.get_or_create(
            driver=driver, organization=sponsor.organization)
        application.application_status = ApplicationStatus.APPROVED
        application.rejection_reason = ""
        application.review_date = timezone.now()
        application.save(update_fields=["application_status", "rejection_reason", "review_date"])
        Points.objects.get_or_create(driver=driver, organization=sponsor.organization)
        record_event(action="admin.driver_assigned", actor=request.user,
                     organization=sponsor.organization, record_type="driver", record_id=driver.pk,
                     description=f"Assigned {driver.user.username} to sponsor {sponsor.user.username}.")
    return JsonResponse({"driver": driver_info(driver)})


@require_GET
@admin_only
def preview(request, role, user_id):
    if role == "sponsor":
        try:
            sponsor = Sponsor.objects.select_related("user", "organization").get(user_id=user_id)
        except Sponsor.DoesNotExist:
            return error("Sponsor not found.", 404)
        organization = sponsor.organization
        if organization is None:
            return JsonResponse({"role": "sponsor", "account": sponsor_info(sponsor),
                                 "drivers": [], "products": [], "pending_applications": 0})
        drivers = DriverOrganization.objects.filter(organization=organization).select_related("driver__user")
        products = Product.objects.filter(organization=organization, is_active=True)[:30]
        return JsonResponse({"role": "sponsor", "account": sponsor_info(sponsor),
                             "drivers": [m.driver.user.username for m in drivers],
                             "products": [{"name": p.product_name, "points": p.points_value} for p in products],
                             "pending_applications": Application.objects.filter(
                                 organization=organization, application_status=ApplicationStatus.PENDING).count()})
    if role == "driver":
        try:
            driver = Driver.objects.select_related("user").get(user_id=user_id)
        except Driver.DoesNotExist:
            return error("Driver not found.", 404)
        balances = Points.objects.filter(driver=driver).select_related("organization")
        recent_orders = Order.objects.filter(driver=driver).order_by("-created_at")[:10]
        return JsonResponse({"role": "driver", "account": driver_info(driver),
                             "balances": [{"organization": p.organization.organization_name if p.organization else "None",
                                           "points": p.points_balance} for p in balances],
                             "orders": [{"id": order.pk, "status": order.order_status,
                                         "points": order.total_points} for order in recent_orders]})
    return error("Preview role must be sponsor or driver.", 404)


@require_POST
@admin_only
def send_driver_reset(request, driver_id):
    try:
        driver = Driver.objects.select_related("user").get(pk=driver_id)
    except Driver.DoesNotExist:
        return error("Driver not found.", 404)
    user = driver.user
    if not user.email:
        return error("Driver has no email address. Add one before requesting a reset.")
    if not user.is_active:
        return error("Inactive accounts cannot request password resets.")
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    url = request.build_absolute_uri(reverse(
        "accounts:account_setup", kwargs={"uidb64": uid, "token": token}))
    try:
        send_mail(
            "Reset your Good Driver Incentive password",
            f"Hello {user.username},\n\nAn administrator requested a password reset. "
            f"Use this link to choose a new password:\n{url}\n\n"
            "If you did not expect this, contact your administrator.",
            None, [user.email], fail_silently=False,
        )
    except Exception:
        # No reset token or sensitive mail-server configuration is sent to the browser.
        return error("Password reset email could not be sent. Check email configuration.", 503)
    record_event(action="admin.driver_password_reset_sent", actor=request.user,
                 record_type="driver", record_id=driver.pk,
                 description=f"Password reset requested for {user.username}.")
    return JsonResponse({"message": "Password reset email sent."})


@require_POST
@admin_only
def account_status(request, user_id):
    data = payload(request)
    if data is None or not isinstance(data.get("active"), bool):
        return error("active must be true or false.")
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return error("User not found.", 404)
    if user.pk == request.user.pk:
        return error("You cannot deactivate yourself.")
    user.is_active = data["active"]
    user.save(update_fields=["is_active"])
    record_event(action="admin.account_status_changed", actor=request.user,
                 record_type="user", record_id=user.pk,
                 description=f"Set {user.username} active={user.is_active}.")
    return JsonResponse({"user": user_info(user)})


@require_POST
@admin_only
def delete_account(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return error("User not found.", 404)
    if user.pk == request.user.pk:
        return error("Cannot delete your own admin account.")
    if user.user_type not in (UserType.DRIVER, UserType.SPONSOR):
        return error("Only driver and sponsor accounts may be deleted here.", 403)
    username = user.username
    try:
        with transaction.atomic():
            user.delete()
            record_event(action="admin.account_deleted", actor=request.user,
                         record_type="user", record_id=user_id,
                         description=f"Deleted {username} ({user_id}).")
    except ProtectedError:
        return error("Account has protected order history. Deactivate it instead.", 409)
    return JsonResponse({"message": f"Deleted {username}."})


@require_GET
@admin_only
def report_csv(request, kind):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="admin-{kind}.csv"'
    writer = csv.writer(response)
    if kind == "sponsors":
        writer.writerow(["Username", "Email", "Organization", "Fee percent", "Active"])
        for item in Sponsor.objects.select_related("user", "organization"):
            writer.writerow([csv_text(item.user.username), csv_text(item.user.email),
                             csv_text(item.organization.organization_name if item.organization else ""),
                             item.fee_percentage, item.user.is_active])
    elif kind == "drivers":
        writer.writerow(["Username", "Email", "Organizations", "Active"])
        for item in Driver.objects.select_related("user").prefetch_related("memberships__organization"):
            writer.writerow([csv_text(item.user.username), csv_text(item.user.email),
                             csv_text(", ".join(m.organization.organization_name for m in item.memberships.all())),
                             item.user.is_active])
    elif kind == "points":
        writer.writerow(["Driver", "Organization", "Balance"])
        for item in Points.objects.select_related("driver__user", "organization"):
            writer.writerow([csv_text(item.driver.user.username),
                             csv_text(item.organization.organization_name if item.organization else ""),
                             item.points_balance])
    elif kind == "orders":
        writer.writerow(["Order ID", "Driver", "Organization", "Status", "Points", "Created"])
        for item in Order.objects.select_related("driver__user", "organization"):
            writer.writerow([item.pk, csv_text(item.driver.user.username),
                             csv_text(item.organization.organization_name if item.organization else ""),
                             csv_text(item.order_status), item.total_points, item.created_at.isoformat()])
    else:
        return error("Report not found.", 404)
    record_event(action="admin.report_downloaded", actor=request.user,
                 record_type="report", description=f"Downloaded {kind} report.")
    return response