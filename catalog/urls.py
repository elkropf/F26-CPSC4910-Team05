from django.urls import path
from . import views

app_name = "catalog"
urlpatterns = [
    # Driver functions
    path('driver/', views.driver_catalog, name='driver_catalog'),
    path('driver/addcart/', views.add_to_cart, name='add_to_cart'),
    path('driver/order/', views.driver_cart, name='driver_cart'),
    path('driver/removeitem/<int:item_id>', views.remove_from_cart, name='remove_from_cart'),
    path('driver/orderstatus/', views.order_status, name='order_status'),
    path('driver/placeorder/', views.place_order, name='place_order'),
    path('driver/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    # Sponsor functions
    path('sponsor/', views.sponsor_catalog, name='sponsor_catalog'),
    path('sponsor/search/', views.search_page, name='search_page'),
    path('sponsor/searching/', views.search, name='search'),
    path('sponsor/addcatalog/', views.add_to_catalog, name='add_to_catalog'),
    path('sponsor/removecatalog/<int:item_id>/', views.remove_from_catalog, name='remove_from_catalog'),
]