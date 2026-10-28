from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
from django.urls import reverse
from accounts.models import *
import http.client
import json

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

    organizations = DriverOrganization.objects.filter(driver=driver)
    products = []
    for o in organizations:
        products.append(Product.objects.filter(organization=o))
    print(organizations)
    print(products)

    template = loader.get_template('driver_catalog.html')
    context = {
        'organizations': organizations,
        'products': products,
    }
    return HttpResponse(template.render(context, request))

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

    #order_items = OrderItem.objects.filter(driver)
    try:
        orders = Order.objects.get(driver=driver)
        order_items = orders.items.all()
    except Order.DoesNotExist:
        order_items = None

    template = loader.get_template('driver_cart.html')
    context = {
        'orders': order_items
    }
    print(order_items)
    return HttpResponse(template.render(context, request))

def sponsor_catalog(request):
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
    for x in items2:
        print(x['title'])
        
    context = {
        'error_message': "",
        'response': items,
    }
    return render(
        request,
        "sponsor_catalog.html",
        {
            'error_message': "",
            'response': items,
        }
    )

def add_to_catalog(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            "error": "You must be logged in to apply."
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

    selections = request.POST["chosen"]
    for x in selections:
        Product.objects.create(
            organization=organization_id,
            product_name=selections['title'],
            product_description="",
            points_value=selections['price']['value']
        )

    template = loader.get_template(reverse("catalog:sponsor_catalog"))
    context = {
        'error_message': "Successfully added items.",
        'response': None
    }
    return HttpResponseRedirect(template.render(context, request))