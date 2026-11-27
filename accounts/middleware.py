
from django.http import JsonResponse
from .models import User, UserType


class AdminViewAsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        target_id = request.session.get("admin_view_as_target_id")

        if target_id:
            admin = request.user

            if (
                not admin.is_authenticated
                or not admin.is_active
                or admin.user_type != UserType.ADMIN
            ):
                request.session.pop("admin_view_as_target_id", None)
                return JsonResponse({
                    "error": "Admin session is invalid."
                }, status=403)

            target = User.objects.filter(
                id=target_id,
                is_active=True,
                user_type__in=[
                    UserType.DRIVER,
                    UserType.SPONSOR
                ]
            ).first()

            if target is None:
                request.session.pop("admin_view_as_target_id", None)
                return JsonResponse({
                    "error": "Selected account is unavailable."
                }, status=403)

            request.view_as_admin = admin
            request.view_as_target = target

            # Do not let View-As modify login credentials.
            if request.path.startswith("/api/auth/"):
                if request.path != "/api/auth/me/":
                    return JsonResponse({
                        "error": "Account security changes are blocked during View-As."
                    }, status=403)

            # Temporarily prevent write operations.
            # We will enable them after adding audit safeguards.
            if request.method not in ("GET", "HEAD", "OPTIONS"):
                if request.path != "/api/admin/view-as/stop/":
                    return JsonResponse({
                        "error": "View-As write actions are not enabled yet."
                    }, status=403)

            request.user = target

        return self.get_response(request)
