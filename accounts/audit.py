from .models import auditLog
from django.core.exceptions import PermissionDenied
from .models import Sponsor, UserType
from datetime import datetime, date, time, timedelta
from django.utils import timezone

#events are recorded using consistent fields
def record_event(*, action, actor=None, organization=None, record_type="", record_id=None, description=""):

    signed_in = ( actor is not None and actor.is_authenticated)

    return auditLog.objects.create(
        user=actor if signed_in else None,
        actor_role=actor.user_type if signed_in else "",
        action=action,
        organization=organization,
        record_type=record_type,
        record_id=record_id,
        description=description
    )

#limit who can see audit logs
def can_view_audit_log(user):
    if not user.is_authenticated or not user.is_active:
        raise PermissionDenied("User must be authenticated and active to view audit logs.")

    logs = auditLog.objects.select_related('user', 'organization')

    if user.user_type == UserType.ADMIN:
        return logs
    elif user.user_type == UserType.SPONSOR:
        try:
            organization_id = user.sponsor.organization_id
        except Sponsor.DoesNotExist:
            return logs.none()

        if organization_id is None:
            return logs.none()

        return logs.filter(organization_id=organization_id)
    raise PermissionDenied("User does not have permission to view audit logs.")

#apply filters to reports and downloads for date, user, and action
def filter_audit_logs(logs, filters):
    action = filters.get("action")
    user_id = filters.get("user_id")
    start_date = filters.get("start_date")
    end_date = filters.get("end_date")

    if action:
        logs = logs.filter(action=action)
    if user_id:
            user_id = int(user_id)
            logs = logs.filter(user_id=user_id)

    if start_date:
        start_date = date.fromisoformat(start_date)

    if end_date:
        end_date = date.fromisoformat(end_date)

    if start_date and end_date:
        if start_date > end_date:
            raise ValueError("Start date cannot be after end date")

    if start_date:
        logs = logs.filter(timestamp__date__gte=start_date)
    if end_date:
        logs = logs.filter(timestamp__date__lte=end_date)

    return logs.order_by("-timestamp", "-id")

#keep exported text from being spreadsheet formula
def csv_text(value):
    if value is None:
        return ""

    text = str(value)

    if text.lstrip().startswith(("=","+","-","@")):
        text = "'" + text

    return text
