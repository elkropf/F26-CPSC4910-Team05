"""Downloadable and on-screen reports for GDIP.

Report queries are limited by the signed-in role. Never trust a requested
organization or driver id as an authorization check.
"""
import csv
from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET

from .audit import csv_text
from .models import (
    Driver, DriverOrganization, Order, OrderStatus, Organization,
    Points, Sponsor, UserType, auditLog, pointLog,
)

CENTS = Decimal("0.01")


def money(value):
    return str(Decimal(value).quantize(CENTS, rounding=ROUND_HALF_UP))


def parse_filter(request):
    try:
        start = date.fromisoformat(request.GET["start_date"]) if request.GET.get("start_date") else None
        end = date.fromisoformat(request.GET["end_date"]) if request.GET.get("end_date") else None
        organization_id = int(request.GET["organization_id"]) if request.GET.get("organization_id") else None
        driver_id = int(request.GET["driver_id"]) if request.GET.get("driver_id") else None
        if start and end and start > end:
            raise ValueError("Start date must be before end date.")
        if organization_id is not None and organization_id <= 0:
            raise ValueError("Invalid organization selection.")
        if driver_id is not None and driver_id <= 0:
            raise ValueError("Invalid driver selection.")
        view = request.GET.get("view", "detail")
        if view not in ("detail", "summary"):
            raise ValueError("Invalid report view.")
        return {"start": start, "end": end, "organization_id": organization_id,
                "driver_id": driver_id, "view": view}, None
    except (ValueError, TypeError) as exc:
        return None, JsonResponse({"error": str(exc)}, status=400)


def limit_dates(queryset, field, filters):
    if filters["start"]:
        queryset = queryset.filter(**{field + "__date__gte": filters["start"]})
    if filters["end"]:
        queryset = queryset.filter(**{field + "__date__lte": filters["end"]})
    return queryset


def authorized_org(request):
    if not request.user.is_authenticated:
        return None, JsonResponse({"error": "Log in first."}, status=401)
    if request.user.user_type != UserType.SPONSOR:
        return None, JsonResponse({"error": "Sponsor access required."}, status=403)
    sponsor = Sponsor.objects.filter(user=request.user).first()
    if not sponsor or sponsor.organization_id is None:
        return None, JsonResponse({"error": "Sponsor organization not found."}, status=403)
    return sponsor.organization_id, None


def result(title, columns, rows, totals=None):
    return {"title": title, "columns": columns, "rows": rows, "totals": totals or {}}


@require_GET
def report_options(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Log in first."}, status=401)
    role = request.user.user_type
    if role == UserType.SPONSOR:
        org, error = authorized_org(request)
        if error is not None:
            return error
        organizations = Organization.objects.filter(pk=org)
        drivers = Driver.objects.filter(memberships__organization_id=org).distinct()
    elif role == UserType.ADMIN:
        organizations = Organization.objects.all()
        drivers = Driver.objects.all()
    else:
        return JsonResponse({"error": "Reports unavailable."}, status=403)

    return JsonResponse({
        "organizations": [{"id": o.pk, "name": o.organization_name} for o in organizations.order_by("organization_name")],
        "drivers": [{"id": d.pk, "name": d.user.get_full_name() or d.user.username,
                     "username": d.user.username,
                     "organization_ids": list(d.memberships.values_list("organization_id", flat=True))}
                    for d in drivers.select_related("user").prefetch_related("memberships")],
    })


def sponsor_points(request, filters, org):
    logs = pointLog.objects.filter(organization_id=org,
        driver__memberships__organization_id=org).select_related(
        "driver__user", "changed_by_user", "organization").distinct()
    logs = limit_dates(logs, "timestamp", filters)
    if filters["driver_id"]:
        logs = logs.filter(driver_id=filters["driver_id"])
    balances = dict(Points.objects.filter(organization_id=org).values_list("driver_id", "points_balance"))
    rows = []
    for change in logs.order_by("-timestamp", "-pk"):
        rows.append({
            "Date": change.timestamp.date().isoformat(),
            "Driver": change.driver.user.username,
            "Current points": balances.get(change.driver_id, 0),
            "Change": change.points_changed,
            "Sponsor": change.organization.organization_name,
            "Changed by": change.changed_by_user.username if change.changed_by_user else "System",
            "Reason": change.action,
        })
    return result("Sponsor — Driver Point Tracking",
        ["Date", "Driver", "Current points", "Change", "Sponsor", "Changed by", "Reason"],
        rows, {"Point changes in period": sum(int(row["Change"]) for row in rows)})


def audit_rows(request, filters, org=None):
    logs = auditLog.objects.select_related("user", "organization").all()
    if org is not None:
        logs = logs.filter(organization_id=org)
    elif filters["organization_id"]:
        logs = logs.filter(organization_id=filters["organization_id"])
    if request.GET.get("action"):
        logs = logs.filter(action__icontains=request.GET["action"][:100])
    logs = limit_dates(logs, "timestamp", filters)
    rows = [{
        "Date": e.timestamp.strftime("%Y-%m-%d %H:%M"),
        "Category": e.action,
        "User": e.user.username if e.user else "System",
        "Sponsor": e.organization.organization_name if e.organization else "",
        "Details": e.description,
    } for e in logs.order_by("-timestamp", "-pk")[:5000]]
    return result("Sponsor Audit Log" if org else "Admin Audit Log",
        ["Date", "Category", "User", "Sponsor", "Details"], rows,
        {"Events shown": len(rows)})


def sales_orders(filters):
    orders = Order.objects.select_related("driver__user", "organization")\
        .exclude(order_status__in=[OrderStatus.PENDING, OrderStatus.CANCELLED])
    if filters["organization_id"]:
        orders = orders.filter(organization_id=filters["organization_id"])
    if filters["driver_id"]:
        orders = orders.filter(driver_id=filters["driver_id"])
    return limit_dates(orders, "created_at", filters).order_by("created_at", "pk")


def sales_report(request, filters, kind):
    rate_map = {}
    for sponsor in Sponsor.objects.filter(organization__isnull=False, user__is_active=True)\
            .select_related("organization").order_by("pk"):
        rate_map.setdefault(sponsor.organization_id, sponsor.fee_percentage)

    transactions = []
    for order in sales_orders(filters):
        org = order.organization
        points_per_dollar = org.points_per_dollar if org else Decimal("100")
        if points_per_dollar <= 0:
            continue
        dollars = Decimal(order.total_points) / points_per_dollar
        percentage = Decimal(rate_map.get(order.organization_id, Decimal("1")))
        fee = dollars * percentage / 100
        transactions.append({
            "Order": order.pk,
            "Date": order.created_at.date().isoformat(),
            "Sponsor": org.organization_name if org else "Unassigned",
            "Driver": order.driver.user.username,
            "Status": order.order_status,
            "Points": order.total_points,
            "Sales ($)": dollars,
            "Fee rate (%)": percentage,
            "Fee ($)": fee,
        })

    if kind == "admin_sales_sponsor":
        title, group_by = "Sales by Sponsor", "Sponsor"
    elif kind == "admin_sales_driver":
        title, group_by = "Sales by Driver", "Driver"
    else:
        title, group_by = "Sponsor Invoices", "Sponsor"

    total_sales = sum((r["Sales ($)"] for r in transactions), Decimal(0))
    total_fees = sum((r["Fee ($)"] for r in transactions), Decimal(0))
    totals = {"Orders": len(transactions), "Sales ($)": money(total_sales), "Fees due ($)": money(total_fees)}

    if filters["view"] == "summary" or kind == "admin_invoices":
        groups = defaultdict(lambda: {"orders": 0, "points": 0, "sales": Decimal(0), "fee": Decimal(0)})
        for r in transactions:
            key = (r["Sponsor"], r["Driver"]) if kind == "admin_invoices" else r[group_by]
            group = groups[key]
            group["orders"] += 1
            group["points"] += r["Points"]
            group["sales"] += r["Sales ($)"]
            group["fee"] += r["Fee ($)"]
        if kind == "admin_invoices":
            columns = ["Sponsor", "Driver", "Orders", "Points", "Sales ($)", "Fee due ($)"]
            rows = [{"Sponsor": key[0], "Driver": key[1], "Orders": g["orders"],
                     "Points": g["points"], "Sales ($)": money(g["sales"]),
                     "Fee due ($)": money(g["fee"])} for key,g in sorted(groups.items())]
        else:
            columns = [group_by, "Orders", "Points", "Sales ($)", "Fees ($)"]
            rows = [{group_by: key, "Orders": g["orders"], "Points": g["points"],
                     "Sales ($)": money(g["sales"]), "Fees ($)": money(g["fee"])}
                    for key,g in sorted(groups.items())]
    else:
        columns = ["Order", "Date", "Sponsor", "Driver", "Status", "Points", "Sales ($)", "Fee rate (%)", "Fee ($)"]
        rows = [{**r, "Sales ($)": money(r["Sales ($)"]),
                 "Fee rate (%)": str(r["Fee rate (%)"]), "Fee ($)": money(r["Fee ($)"])}
                for r in transactions]

    return result(title, columns, rows, totals)


@require_GET
def final_report(request, kind):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Log in first."}, status=401)

    filters, error = parse_filter(request)
    if error is not None:
        return error

    if kind in ("sponsor_points", "sponsor_audit"):
        org, error = authorized_org(request)
        if error is not None:
            return error
        if filters["driver_id"] and not DriverOrganization.objects.filter(
                driver_id=filters["driver_id"], organization_id=org).exists():
            return JsonResponse({"error": "Driver not in your organization."}, status=403)
        data = sponsor_points(request, filters, org) if kind == "sponsor_points" else audit_rows(request, filters, org)
    elif kind in ("admin_sales_sponsor", "admin_sales_driver", "admin_invoices", "admin_audit"):
        if request.user.user_type != UserType.ADMIN:
            return JsonResponse({"error": "Administrator access required."}, status=403)
        data = audit_rows(request, filters) if kind == "admin_audit" else sales_report(request, filters, kind)
    else:
        return JsonResponse({"error": "Unknown report."}, status=404)

    if request.GET.get("format") == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{kind}.csv"'
        writer = csv.writer(response)
        writer.writerow(data["columns"])
        for row in data["rows"]:
            writer.writerow([csv_text(row.get(column, "")) for column in data["columns"]])
        return response

    return JsonResponse(data)
