import re

from django.http import JsonResponse

from .audit import record_event, view_as_context
from .models import User, UserType


class AdminViewAsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        target_id = request.session.get("admin_view_as_target_id")

        if not target_id:
            return self.get_response(request)

        admin = request.user
        if (
            not admin.is_authenticated
            or not admin.is_active
            or admin.user_type != UserType.ADMIN
        ):
            request.session.pop("admin_view_as_target_id", None)
            return JsonResponse({"error": "Admin session is invalid."}, status=403)

        target = User.objects.filter(
            id=target_id,
            is_active=True,
            user_type__in=[UserType.DRIVER, UserType.SPONSOR],
        ).first()

        if target is None:
            request.session.pop("admin_view_as_target_id", None)
            return JsonResponse({"error": "Selected account is unavailable."}, status=403)

        request.view_as_admin = admin
        request.view_as_target = target

        path = request.path_info
        method = request.method
        stop_path = "/api/admin/view-as/stop/"

        # Returning to Admin must run with the actual authenticated Admin user.
        if path == stop_path:
            if method != "POST":
                return JsonResponse({"error": "POST required."}, status=405)
            return self.get_response(request)

        # An acting Driver/Sponsor must never enter Admin-only endpoints.
        if path.startswith("/api/admin/"):
            return JsonResponse({"error": "Return to Admin first."}, status=403)

        # Allow viewing current session details and fetching the CSRF cookie,
        # but do not allow login/logout or account credential/profile changes.
        if path.startswith("/api/auth/") and path not in (
            "/api/auth/me/",
            "/api/auth/csrf/",
            "/api/auth/profile/",
        ):
            return JsonResponse({"error": "Authentication changes are blocked."}, status=403)

        # Do not mix the older server-rendered View-As mechanism into this one.
        if path.startswith(("/sponsor/setdriverview/", "/sponsor/removeview/")):
            return JsonResponse({"error": "Legacy View-As is unavailable."}, status=403)

        allowed_actions = [
            r"/api/notifications/\d+/read/",
            r"/api/notifications/preferences/update/",
        ]

        if target.user_type == UserType.DRIVER:
            allowed_actions += [
                r"/api/applications/submit/",
                r"/api/catalog/cart/add/",
                r"/api/catalog/cart/remove/\d+/",
                r"/api/catalog/cart/checkout/",
            ]
        elif target.user_type == UserType.SPONSOR:
            allowed_actions += [
                r"/api/applications/\d+/review/",
                r"/api/drivers/\d+/points/change/",
                r"/api/catalog/ebay/add/",
            ]

        is_write = method not in ("GET", "HEAD", "OPTIONS")

        if is_write and not (
            method == "POST" and any(re.fullmatch(pattern, path) for pattern in allowed_actions)
        ):
            return JsonResponse({
                "error": "This action is not permitted during Admin View-As."
            }, status=403)

        request.user = target
        token = view_as_context.set((admin, target))

        try:
            response = self.get_response(request)
            if is_write and response.status_code < 400:
                record_event(
                    action="admin.view_as_action",
                    actor=admin,
                    record_type="user",
                    record_id=target.id,
                    description=(
                        f"Admin {admin.username} performed {method} {path} "
                        f"as {target.username}."
                    ),
                )
            return response
        finally:
            view_as_context.reset(token)
