
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import base64

from django.core import signing
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from accounts.models import Product, Sponsor

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def sponsor_for(request):
    if not request.user.is_authenticated:
        return None, JsonResponse({"error": "Please log in."}, status=401)

    if request.user.user_type != "sponsor":
        return None, JsonResponse({"error": "Sponsors only."}, status=403)

    try:
        sponsor = request.user.sponsor
    except Sponsor.DoesNotExist:
        return None, JsonResponse({"error": "Sponsor profile missing."}, status=404)

    if sponsor.organization_id is None:
        return None, JsonResponse({
            "error": "Your sponsor needs an organization assigned."
        }, status=400)

    return sponsor, None

def get_ebay_token():
    client_id = os.getenv("EBAY_CLIENT_ID")
    client_secret = os.getenv("EBAY_CLIENT_SECRET")

    credentials = base64.b64encode(
        f"{client_id}:{client_secret}".encode()
    ).decode()

    data = urlencode({
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope"
    }).encode()

    req = Request(
        "https://api.ebay.com/identity/v1/oauth2/token",
        data=data,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        method="POST"
    )

    with urlopen(req, timeout=15) as response:
        return json.load(response)["access_token"]
@require_GET
def ebay_search(request):
    sponsor, error = sponsor_for(request)
    if error is not None:
        return error

    q = request.GET.get("q", "").strip()[:100]

    if not q:
        return JsonResponse({"error": "Enter a search term."}, status=400)

    access_token = get_ebay_token()

    if not access_token:
        return JsonResponse({
            "error": "CATALOG_AUTH_KEY is missing in .env."
        }, status=503)

    if access_token.lower().startswith("bearer "):
        access_token = access_token[7:].strip()

    try:
        search_url = (
            "https://api.ebay.com/buy/browse/v1/item_summary/search?"
            + urlencode({"q": q, "limit": 10})
        )

        ebay_request = Request(
            search_url,
            headers={
                "Authorization": "Bearer " + access_token,
                "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
            }
        )

        with urlopen(ebay_request, timeout=10) as response:
            data = json.load(response)

    except HTTPError as exc:
        if exc.code in (401, 403):
            return JsonResponse({
                "error": "eBay rejected catalogue_auth_key. "
                         "The token may be invalid or expired."
            }, status=502)

        return JsonResponse({
            "error": f"eBay HTTP error {exc.code}."
        }, status=502)

    except (URLError, TimeoutError, ValueError) as exc:
        return JsonResponse({
            "error": f"eBay request failed: {exc}"
        }, status=502)

    results = []

    for item in data.get("itemSummaries", []):
        price = item.get("price", {})

        if (
            price.get("currency") != "USD"
            or not price.get("value")
            or not item.get("title")
        ):
            continue

        signed = signing.dumps(
            {
                "title": item["title"],
                "price": price["value"]
            },
            salt="ebay-catalog"
        )

        results.append({
            "title": item["title"],
            "price": price["value"],
            "image": (item.get("image") or {}).get("imageUrl"),
            "token": signed,
        })

    return JsonResponse({"results": results})


@require_POST
def ebay_add(request):
    sponsor, error = sponsor_for(request)

    if error is not None:
        return error

    try:
        body = json.loads(request.body)

        item = signing.loads(
            body["token"],
            salt="ebay-catalog",
            max_age=600
        )

        price = Decimal(item["price"])

        if price < 0:
            raise ValueError("Invalid price")

        points = round(
            price * Decimal(str(sponsor.organization.points_per_dollar))
        )

        product = Product.objects.create(
            organization=sponsor.organization,
            product_name=item["title"],
            product_description="eBay reward",
            points_value=points,
        )

    except (
        KeyError,
        TypeError,
        ValueError,
        InvalidOperation,
        json.JSONDecodeError,
        signing.BadSignature,
    ):
        return JsonResponse({
            "error": "Invalid or expired selection. Search again."
        }, status=400)

    return JsonResponse({
        "message": f"Added {product.product_name} to catalog."
    }, status=201)
