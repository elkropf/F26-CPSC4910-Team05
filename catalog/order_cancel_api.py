from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from accounts.audit import record_event
from accounts.models import Order, OrderStatus, Points
from accounts.notifications import create_notification
from .api_views import _driver


@require_POST
@transaction.atomic
def cancel_order(request, order_id):
    driver, error = _driver(request)
    if error is not None:
        return error

    order = (
        Order.objects.select_for_update()
        .filter(id=order_id, driver=driver)
        .first()
    )
    if order is None:
        return JsonResponse({"error": "Order not found."}, status=404)

    if order.order_status not in (OrderStatus.APPROVED, OrderStatus.PROCESSING):
        return JsonResponse(
            {"error": "This order cannot be cancelled."}, status=400
        )

    balance = (
        Points.objects.select_for_update()
        .filter(driver=driver, organization_id=order.organization_id)
        .first()
    )
    if balance is None:
        return JsonResponse({"error": "Points account not found."}, status=404)

    balance.points_balance = F("points_balance") + order.total_points
    balance.save(update_fields=["points_balance"])

    order.order_status = OrderStatus.CANCELLED
    order.save(update_fields=["order_status", "updated_at"])

    record_event(
        action="driver.order_cancelled",
        actor=request.user,
        organization=order.organization,
        record_type="order",
        record_id=order.id,
        description=f"Cancelled order #{order.id} and refunded {order.total_points} points.",
    )
    create_notification(
        user=request.user,
        notification_type="order",
        organization=order.organization,
        message=f"Order #{order.id} cancelled. {order.total_points} points refunded.",
    )

    return JsonResponse({"message": f"Order #{order.id} cancelled and points refunded."})
