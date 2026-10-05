from django.urls import path
from . import views

app_name = "accounts"
urlpatterns = [
    # Application
    path('apply/', views.app_page, name='app_page'),
    path('applying/', views.apply, name='apply'),
    path('appstatus/', views.app_status, name='app_status_page'),
    path('appstatus/check/', views.check_status, name='app_status'),
    # Register and login
    path('login/', views.login_page, name='login_page'),
    path('loggingin/', views.login, name='login'),
    path('register/', views.register_page, name='register_page'),
    path('registering/', views.register, name='register'),
    # Home pages
    # TODO: Should be replaced by a function which checks what type of user it is, then renders different stuff on the same page
    path('driverhome/', views.driver_homepage, name='driver_homepage'),
    path('sponsorhome/', views.sponsor_homepage, name='sponsor_homepage'),
    path('adminhome/', views.admin_homepage, name='admin_homepage'),
]
