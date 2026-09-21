from django.urls import path
from . import views

urlpatterns = [
    path('accounts/', views.login_page, name='login_page'),
]