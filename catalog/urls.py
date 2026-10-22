from django.urls import path
from . import views

app_name = "catalog"
urlpatterns = [
    path('', views.catalog_page, name='catalog_page'),
    path('search/', views.search, name='search'),
]