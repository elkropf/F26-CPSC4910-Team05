from django.urls import path
from . import api_views
from . import ebay_api
from . import order_cancel_api

urlpatterns = [
    path("products/", api_views.products, name="api_catalog_products"),
    path("points/", api_views.points, name="api_get_points"),
    path("cart/", api_views.cart, name="api_catalog_cart"),
    path("cart/add/", api_views.add_to_cart, name="api_catalog_add"),
    path("cart/remove/<int:item_id>/", api_views.remove_from_cart, name="api_catalog_remove"),
    path("cart/checkout/", api_views.checkout, name="api_catalog_checkout"),
    path("ebay/search/", ebay_api.ebay_search),
    path("ebay/add/", ebay_api.ebay_add),
    path("orders/", api_views.order_history, name="api_catalog_orders"),
    path("orders/<int:order_id>/cancel/", order_cancel_api.cancel_order, name="api_cancel_order"),
]
