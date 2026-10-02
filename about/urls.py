from django.urls import path
from . import views

urlpatterns = [
    path('', views.about_information, name='about_information'),
]