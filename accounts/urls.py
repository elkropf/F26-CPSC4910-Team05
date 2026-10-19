from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    # JSON authentication API for React
    path("api/auth/csrf/", views.api_csrf, name="api_csrf"),
    path("api/auth/register/", views.api_register, name="api_register"),
    path("api/auth/login/", views.api_login, name="api_login"),
    path("api/auth/logout/", views.api_logout, name="api_logout"),
    path("api/auth/me/", views.api_current_user, name="api_current_user"),

    # Organizations
    path(
        "api/organizations/",
        views.api_organizations,
        name="api_organizations"
    ),

    # Submit a driver application through the React API
    path(
        "api/applications/submit/",
        views.api_submit_application,
        name="api_submit_application"
    ),
    path(
    "api/applications/mine/",
    views.api_my_applications,
    name="api_my_applications"
    ),

    # Application
    path("apply/", views.app_page, name="app_page"),
    path("applying/", views.apply, name="apply"),
    path("appstatus/", views.app_status, name="app_status_page"),
    path("appstatus/check/", views.check_status, name="app_status"),

    # Existing template registration and login
    path("login/", views.login_page, name="login_page"),
    path("loggingin/", views.login, name="login"),
    path("register/", views.register_page, name="register_page"),
    path("registering/", views.register, name="register"),

    # Existing home pages
    path("driverhome/", views.driver_homepage, name="driver_homepage"),
    path("sponsorhome/", views.sponsor_homepage, name="sponsor_homepage"),
    path("adminhome/", views.admin_homepage, name="admin_homepage"),
]
