from django.urls import path
from . import views

app_name = "tempadmin"
urlpatterns = [
    path('listdrivers/', views.driver_list_page, name='driver_list_page'),
    path('setdriverview/<int:driver>/', views.setup_driver_view, name='setup_driver_view'),
    path('listsponsors/', views.sponsor_list_page, name='sponsor_list_page'),
    path('setsponsorview/<int:sponsor>/', views.setup_sponsor_view, name='setup_sponsor_view'),
]