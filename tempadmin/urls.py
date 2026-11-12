from django.urls import path
from . import views

app_name = "tempadmin"
urlpatterns = [
    path('listdrivers/', views.driver_list_page, name='driver_list_page'),
    path('listsponsors/', views.sponsor_list_page, name='sponsor_list_page'),
]