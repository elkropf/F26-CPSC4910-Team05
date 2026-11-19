

import json

from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from accounts.models import (
    Product,
    Order,
    OrderItem,
    OrderStatus,
    Points,
    Driver,
    DriverOrganization,
    Sponsor,
)


def _driver(request):
    if not request.user.is_authenticated:
        return None, JsonResponse(
            {"error": "Please log in."}, status=401
        )

    if request.user.user_type != "driver":
        return None, JsonResponse(
            {"error": "Driver account required."}, status=403
        )

    try:
        return request.user.driver, None
    except Driver.DoesNotExist:
        return None, JsonResponse(
            {"error": "Driver profile not found."}, status=404
        )


def _driver_organization_id(driver):
    # Use the driver's assigned organization.
    # The project expects one sponsor per driver.
    return (
        DriverOrganization.objects.filter(driver=driver)
        .order_by("id")
        .values_list("organization_id", flat=True)
        .first()
    )


def _product_dict(product):
    return {
        "id": product.pk,
        "name": product.product_name,
        "description": product.product_description,
        "points": product.points_value,
        "organization_id": product.organization_id,
    }


@require_GET
def products(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Please log in."}, status=401
        )

    if request.user.user_type == "sponsor":
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

        queryset = Product.objects.filter(
            organization_id=sponsor.organization_id
        )

    elif request.user.user_type == "driver":
        driver, error = _driver(request)

        if error is not None:
            return error

        organization_id = _driver_organization_id(driver)

        if organization_id is None:
            return JsonResponse({"products": []})

        queryset = Product.objects.filter(
            organization_id=organization_id
        )

    else:
        return JsonResponse(
            {"error": "Catalog unavailable for this role."},
            status=403,
        )

    return JsonResponse({
        "products": [
            _product_dict(product)
            for product in queryset.order_by("id")
        ]
    })


def _cart_dict(driver):
    order = (
        Order.objects.filter(
            driver=driver,
            order_status=OrderStatus.PENDING,
        )
        .first()
    )

    if order is None:
        return {"items": [], "total_points": 0}

    return {
        "items": [
            {
                "id": item.pk,
                "name": item.product.product_name,
                "quantity": item.quantity,
                "points": item.points_cost,
            }
            for item in order.items.select_related("product")
        ],
        "total_points": order.total_points,
    }


@require_GET
def cart(request):
    driver, error = _driver(request)

    if error is not None:
        return error

    return JsonResponse({"cart": _cart_dict(driver)})


@require_POST
@transaction.atomic
def add_to_cart(request):
    driver, error = _driver(request)

    if error is not None:
        return error

    try:
        payload = json.loads(request.body)
        product_id = int(payload["product_id"])
    except (
        KeyError,
        ValueError,
        TypeError,
        json.JSONDecodeError,
    ):
        return JsonResponse(
            {"error": "Valid product_id required."},
            status=400,
        )

    organization_id = _driver_organization_id(driver)

    if organization_id is None:
        return JsonResponse(
            {"error": "You must belong to a sponsor first."},
            status=403,
        )

    product = Product.objects.filter(
        pk=product_id,
        organization_id=organization_id,
    ).first()

    if product is None:
        return JsonResponse(
            {"error": "Product not found in your sponsor's store."},
            status=404,
        )

    order = (
        Order.objects.select_for_update()
        .filter(
            driver=driver,
            order_status=OrderStatus.PENDING,
        )
        .first()
    )

    if order is None:
        order = Order.objects.create(
            driver=driver,
            organization=product.organization,
            total_points=0,
            order_status=OrderStatus.PENDING,
        )

    elif order.organization_id != organization_id:
        return JsonResponse(
            {
                "error": (
                    "Your pending cart belongs to another "
                    "organization. Clear it before continuing."
                )
            },
            status=400,
        )

    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=1,
        points_cost=product.points_value,
    )

    order.total_points = (
        F("total_points") + product.points_value
    )

    order.save(update_fields=["total_points"])

    return JsonResponse({"message": "Added to cart."})


@require_POST
@transaction.atomic
def remove_from_cart(request, item_id):
    driver, error = _driver(request)

    if error is not None:
        return error

    item = (
        OrderItem.objects.select_related("order")
        .filter(
            pk=item_id,
            order__driver=driver,
            order__order_status=OrderStatus.PENDING,
        )
        .first()
    )

    if item is None:
        return JsonResponse(
            {"error": "Cart item not found."},
            status=404,
        )

    order = item.order

    order.total_points = (
        F("total_points") - item.points_cost
    )

    order.save(update_fields=["total_points"])
    item.delete()

    return JsonResponse({"message": "Removed from cart."})


@require_POST
@transaction.atomic
def checkout(request):
    driver, error = _driver(request)

    if error is not None:
        return error

    order = (
        Order.objects.select_for_update()
        .filter(
            driver=driver,
            order_status=OrderStatus.PENDING,
        )
        .first()
    )

    if order is None or not order.items.exists():
        return JsonResponse(
            {"error": "Cart is empty."},
            status=400,
        )

    organization_id = _driver_organization_id(driver)

    if organization_id != order.organization_id:
        return JsonResponse(
            {"error": "This cart is not for your assigned sponsor."},
            status=403,
        )

    points = (
        Points.objects.select_for_update()
        .filter(
            driver=driver,
            organization_id=order.organization_id,
        )
        .first()
    )

    if points is None:
        return JsonResponse(
            {"error": "Points account not found."},
            status=404,
        )

    if points.points_balance < order.total_points:
        return JsonResponse(
            {"error": "Not enough points."},
            status=400,
        )

    points.points_balance = (
        F("points_balance") - order.total_points
    )
    points.save(update_fields=["points_balance"])

    order.order_status = OrderStatus.PROCESSING
    order.save(update_fields=["order_status"])

    return JsonResponse({
        "message": f"Order #{order.pk} placed successfully."
    })
