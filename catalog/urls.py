from django.urls import path
from . import views

app_name = "catalog"
urlpatterns = [
    path('driver/', views.driver_catalog, name='driver_catalog'),
    path('driver/addcart/', views.add_to_cart, name='add_to_cart'),
    path('driver/order/', views.driver_cart, name='driver_cart'),
    path('sponsor/', views.sponsor_catalog, name='sponsor_catalog'),
    path('search/', views.search, name='search'),
    path('addcatalog/', views.add_to_catalog, name='add_to_catalog'),
]