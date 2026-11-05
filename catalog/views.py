from django.db.models import F
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.template import loader
from django.urls import reverse
from accounts.models import *
import http.client
import json

def driver_catalog(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            "error": "You must be logged in to view a catalog."
        }, status=401)

    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            "error": "Driver profile not found."
        }, status=404)
    
    organizations = Organization.objects.all()
    products = []
    for o in organizations:
        products.append(o.products.filter(organization_id=o))

    template = loader.get_template('driver_catalog.html')
    context = {
        'organizations': organizations,
        'products': products,
    }
    return HttpResponse(template.render(context, request))

@require_POST
def add_to_cart(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            "error": "You must be logged in to order."
        }, status=401)
    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            "error": "Driver profile not found."
        }, status=404)
        
    product = request.POST["order"]
    true_product = Product.objects.filter(product_name=product)[0]
    
    try:
        current_order = Order.objects.filter(order_status=OrderStatus.PENDING).get(driver=driver)
        OrderItem.objects.create(
            order=current_order,
            product=true_product,
            quantity=1,
            points_cost=true_product.points_value,
        )
        current_order.total_points = F("total_points") + true_product.points_value
        current_order.save()
    except Order.DoesNotExist:
        new_order = Order.objects.create(
            driver=driver,
            organization=true_product.organization,
            total_points=true_product.points_value,
        )
        OrderItem.objects.create(
            order=new_order,
            product=true_product,
            quantity=1,
            points_cost=true_product.points_value,
        )
    context = {
        "message": f"Successfully added {product} to cart."
    }
    return HttpResponseRedirect(reverse("catalog:driver_catalog", query=context))

def driver_cart(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            "error": "You must be logged in to view a cart."
        }, status=401)
    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            "error": "Driver profile not found."
        }, status=404)

    try:
        order = Order.objects.get(driver=driver, order_status=OrderStatus.PENDING)
        order_items = order.items.all()
        if len(order_items) == 0:
            order = None
    except Order.DoesNotExist:
        order = None
        order_items = None
        
    template = loader.get_template('driver_cart.html')
    context = {
        'order': order,
        'items': order_items,
    }
    print(order_items)
    return HttpResponse(template.render(context, request))

@require_POST
def place_order(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            "error": "You must be logged in to place an order."
        }, status=401)
    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            "error": "Driver profile not found."
        }, status=404)
    
    try:
        order = Order.objects.get(driver=driver)
    except Order.DoesNotExist:
        context = {
            "message": "Cannot place an order which does not exist."
        }
        return HttpResponseRedirect(reverse("catalog:driver_cart", query=context))
        
    points = Points.objects.get(driver=driver)
    if order.total_points > points.points_balance:
        context = {
            "message": "You do not have enough points to place this order."
        }
        return HttpResponseRedirect(reverse("catalog:driver_cart", query=context))
    
    order.order_status = OrderStatus.PROCESSING
    points.points_balance = F("points_balance") - order.total_points
    points.save()
    
    context = {
        "message": f"Successfully placed order #{order.id}."
    }
    return HttpResponseRedirect(reverse("catalog:driver_cart", query=context))

def remove_from_cart(request, item_id):
    if not request.user.is_authenticated:
        return JsonResponse({
            "error": "You must be logged in to remove an item."
        }, status=401)
    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            "error": "Driver profile not found."
        }, status=404)

    try:
        item = OrderItem.objects.get(pk=item_id)
        if item.order.driver != driver:
            return JsonResponse({
                "error": "You cannot remove an item from someone else's order."
            }, status=401)
    except OrderItem.DoesNotExist:
        return JsonResponse({
            "error": "Item not found."
        }, status=404)
    
    item.order.total_points = F("total_points") - item.points_cost
    item.order.save()
    item.delete()

    context = {
        'message': "Successfully removed item from your cart."
    }
    return HttpResponseRedirect(reverse("catalog:driver_cart", query=context))

def order_status(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            "error": "You must be logged in to place an order."
        }, status=401)
    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            "error": "Driver profile not found."
        }, status=404)

    orders = Order.objects.filter(driver=driver)
    if len(orders) == 0:
        orders = None
        order_items = None
    else:
        order_items = []
        for o in orders:
            items = o.items.all()
            for i in items:
                order_items.append(i)

    template = loader.get_template('driver_orderstatus.html')
    context = {
        'order': orders,
        'order_item': order_items,
    }
    return HttpResponse(template.render(context, request))

def cancel_order(request, order_id):
    if not request.user.is_authenticated:
        return JsonResponse({
            "error": "You must be logged in to cancel an order."
        }, status=401)
    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            "error": "Driver profile not found."
        }, status=404)
    
    try:
        order = Order.objects.get(pk=order_id)
        if order.driver != driver:
            return JsonResponse({
                "error": "You cannot cancel someone else's order."
            }, status=401)
    except Order.DoesNotExist:
        return JsonResponse({
            "error": "Order not found."
        }, status=404)
    
    # HTML already checks if the current status is one that can be cancelled
    order.order_status = OrderStatus.CANCELLED
    order.save()
    return HttpResponseRedirect(reverse("catalog:order_status"))

###################################################
def sponsor_catalog(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            "error": "You must be logged in to view the catalog."
        }, status=401)

    if request.user.user_type != UserType.SPONSOR:
        return JsonResponse({
            "error": "Only sponsors can change an organization's catalog."
        }, status=403)

    try:
        sponsor = request.user.sponsor
    except Sponsor.DoesNotExist:
        return JsonResponse({
            "error": "Sponsor profile not found."
        }, status=404)

    organization = sponsor.organization
    catalog = organization.products.all()
    if len(catalog) == 0:
        catalog = None

    template = loader.get_template('sponsor_view.html')
    context = {
        'products': catalog
    }
    return HttpResponse(template.render(context, request))

def search_page(request):
    template = loader.get_template('sponsor_catalog.html')
    return HttpResponse(template.render())

def search(request):
    term = request.GET["search"]
    num = request.GET["limit"]
    off = request.GET["offset"]

    if len(term) <= 0 or len(num) <= 0 or len(off) <= 0:
        return render(
            request,
            "sponsor_catalog.html",
            {
                "error_message": "Please enter a valid search, limit, and offset."
            }
        )
    if int(num) <= 0 or int(off) < 0:
        return render(
            request,
            "sponsor_catalog.html",
            {
                "error_message": "limit must be at least 1, and offset must not be negative."
            }
        )

    conn = http.client.HTTPSConnection("api.ebay.com")
    payload = 'grant_type=client_credentials&scope=https%3A%2F%2Fapi.ebay.com%2Foauth%2Fapi_scope'
    headers = {
        'Authorization': '',
        'Cookie': 'ak_bmsc=5D333C71CD70594DB40EC2E02C3AB134~000000000000000000000000000000~YAAQhkA2F3eeFzyhAQAA22guWwHwF8863CEcEw1sukIiwh2s8w0E4Z/5osWopnsx0ViGVI1t1ZNhBXaeDHn+xRP8dHYCi6DlaO2uLjLVermcHSBbePpheyiYIh2RMpyu6O0u0oo/IQGs9UtI8bX4ErnAPP8a7Pkd4uObpCD8t3JYBBN0a4qNF2P7hxeIXqSIeWRXIA+STJuT/Hs2iIZvKb2GHjPwaGmFyUiVFOipzdyPHFE7ZJQGuVle1SIw2w/D9Ixseut8HTMLAE6OrIOSA+Q3jSYAKyBRycmvC4W3zQXu5tVBzNA/e79TBxeBPxYRhNmEarYoZaP1d8/JBNGcgrHXg32B6YI4yB4=',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    conn.request("POST", "/identity/v1/oauth2/token", payload, headers)
    res = conn.getresponse()
    data = res.read()
    decoded = data.decode("utf-8")
    decoded = decoded.removeprefix('{"access_token":"')
    i = decoded.index('"')
    j = len(decoded)
    decoded = decoded.removesuffix(decoded[i:j])
    
    conn = http.client.HTTPSConnection("api.ebay.com")
    payload = ''
    headers = {
      'Cookie': 'ak_bmsc=5D333C71CD70594DB40EC2E02C3AB134~000000000000000000000000000000~YAAQhkA2F3eeFzyhAQAA22guWwHwF8863CEcEw1sukIiwh2s8w0E4Z/5osWopnsx0ViGVI1t1ZNhBXaeDHn+xRP8dHYCi6DlaO2uLjLVermcHSBbePpheyiYIh2RMpyu6O0u0oo/IQGs9UtI8bX4ErnAPP8a7Pkd4uObpCD8t3JYBBN0a4qNF2P7hxeIXqSIeWRXIA+STJuT/Hs2iIZvKb2GHjPwaGmFyUiVFOipzdyPHFE7ZJQGuVle1SIw2w/D9Ixseut8HTMLAE6OrIOSA+Q3jSYAKyBRycmvC4W3zQXu5tVBzNA/e79TBxeBPxYRhNmEarYoZaP1d8/JBNGcgrHXg32B6YI4yB4=',
      'Authorization': ' '.join(['Bearer', decoded])
    }
    conn.request("GET", f"/buy/browse/v1/item_summary/search?q={term}&limit={num}&offset={off}", payload, headers)
    res = conn.getresponse()
    data = res.read()
    decoded = data.decode("utf-8")
    items = json.loads(decoded)
    items2 = items['itemSummaries']
        
    context = {
        'error_message': "",
        'response': items,
    }
    
    return render(
        request,
        'sponsor_catalog.html',
        {
            'error_message': "",
            'response': items,
        }
    )

@require_POST
def add_to_catalog(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            "error": "You must be logged in to change the catalog."
        }, status=401)

    if request.user.user_type != UserType.SPONSOR:
        return JsonResponse({
            "error": "Only sponsors can change an organization's catalog."
        }, status=403)

    try:
        sponsor = request.user.sponsor
    except Sponsor.DoesNotExist:
        return JsonResponse({
            "error": "Sponsor profile not found."
        }, status=404)
    
    try:
        organization_id = sponsor.organization
    except (TypeError, ValueError):
        return JsonResponse({
            "error": "A valid organization ID is required."
        }, status=400)

    selections = request.POST["chosen"]
    adjusted = selections.replace("'", '"').replace('False', 'false').replace('True', 'true')
    selection_items = json.loads(adjusted)
    Product.objects.create(
        organization=organization_id,
        product_name=selection_items['title'],
        product_description="",
        points_value=round(float(selection_items['price']['value']) * (int)(organization_id.points_per_dollar))
    )

    context = {
        'error_message': "Successfully added items.",
        'response': None
    }
    return HttpResponseRedirect(reverse("catalog:search_page", query=context))

def remove_from_catalog(request, item_id):
    if not request.user.is_authenticated:
        return JsonResponse({
            "error": "You must be logged in to change the catalog."
        }, status=401)

    if request.user.user_type != UserType.SPONSOR:
        return JsonResponse({
            "error": "Only sponsors can change an organization's catalog."
        }, status=403)

    try:
        sponsor = request.user.sponsor
    except Sponsor.DoesNotExist:
        return JsonResponse({
            "error": "Sponsor profile not found."
        }, status=404)
    
    try:
        organization_id = sponsor.organization
    except (TypeError, ValueError):
        return JsonResponse({
            "error": "A valid organization ID is required."
        }, status=400)

    try:
        product = Product.objects.get(pk=item_id)
    except Product.DoesNotExist:
        return JsonResponse({
            "error": "Item not found."
        }, status=404)

    # Ensure there aren't any phantom items left in driver carts
    items = OrderItem.objects.filter(product=product)
    for i in items:
        i.order.total_points = F("total_points") - i.points_cost
        i.order.save()
        i.delete()
    # Now delete the actual product
    product.delete()

    return HttpResponseRedirect(reverse("catalog:sponsor_catalog"))
