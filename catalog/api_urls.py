from django.urls import path
from . import api_views
from . import ebay_api

urlpatterns = [
    path("products/", api_views.products, name="api_catalog_products"),
    path("cart/", api_views.cart, name="api_catalog_cart"),
    path("cart/add/", api_views.add_to_cart, name="api_catalog_add"),
    path("cart/remove/<int:item_id>/", api_views.remove_from_cart, name="api_catalog_remove"),
    path("cart/checkout/", api_views.checkout, name="api_catalog_checkout"),
    path("ebay/search/", ebay_api.ebay_search),
    path("ebay/add/", ebay_api.ebay_add),
]
