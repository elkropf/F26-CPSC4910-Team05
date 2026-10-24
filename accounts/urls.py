from django.urls import path

from . import views

from django.contrib.auth.views import PasswordResetConfirmView
from django.urls import reverse_lazy

app_name = "accounts"

urlpatterns = [
    #JSON authentication API for React
    path("api/auth/csrf/", views.api_csrf, name="api_csrf"),
    path("api/auth/register/", views.api_register, name="api_register"),
    path("api/auth/login/", views.api_login, name="api_login"),
    path("api/auth/logout/", views.api_logout, name="api_logout"),
    path("api/auth/me/", views.api_current_user, name="api_current_user"),

    #organizations
    path("api/organizations/", views.api_organizations, name="api_organizations"),

    #bulk-load organizations, drivers, and sponsor users
    path("api/users/bulk-import/",views.api_bulk_import,name="api_bulk_import",),

    #submit a driver application through the React API
    path("api/applications/submit/", views.api_submit_application, name="api_submit_application"),
    path("api/applications/mine/",views.api_my_applications,name="api_my_applications"),
    path("api/applications/pending/",views.api_sponsor_applications,name="api_sponsor_applications"),
    path("api/applications/<int:application_id>/review/",views.api_review_application,name="api_review_application"),

    #sponsor point changes
    path("api/drivers/<int:driver_id>/points/change/", views.api_change_points, name="api_change_points",),
    #sponsor point tracking
    path("api/points/sponsor/",views.api_sponsor_point_tracking,name="api_sponsor_point_tracking",),

    #driver points balance
    path("api/points/mine/", views.api_my_points, name="api_my_points",),
    path("api/points/history/", views.api_my_point_history, name="api_my_point_history",),

    #application
    path("apply/", views.app_page, name="app_page"),
    path("applying/", views.apply, name="apply"),
    path("appstatus/", views.app_status, name="app_status_page"),
    path("appstatus/check/", views.check_status, name="app_status"),

    #existing template registration and login
    path("login/", views.login_page, name="login_page"),
    path("loggingin/", views.login, name="login"),
    path("register/", views.register_page, name="register_page"),
    path("registering/", views.register, name="register"),

    #existing home pages
    path("driverhome/", views.driver_homepage, name="driver_homepage"),
    path("sponsorhome/", views.sponsor_homepage, name="sponsor_homepage"),
    path("adminhome/", views.admin_homepage, name="admin_homepage"),

    #temp pass for emailed account setup link
    path(
        "account/setup/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(
            template_name="account_setup.html",
            success_url=reverse_lazy("accounts:login_page"),
        ),
        name="account_setup",
    ),

    # Resend an imported user's account-setup email
    path("api/users/<int:user_id>/setup/resend/",views.api_resend_account_setup,name="api_resend_account_setup"),

    path("api/users/bulk-import/<int:job_id>/",views.api_bulk_import_status,name="api_bulk_import_status"),

    path("api/users/bulk-import/<int:job_id>/results/",views.api_bulk_import_results,name="api_bulk_import_results"),
]
