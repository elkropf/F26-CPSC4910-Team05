from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


#email a password-setup link to newly imported user
def send_account_setup_email(user, base_url):
    if not user.is_active or user.has_usable_password():
        return

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    path = reverse(
        "accounts:account_setup",
        kwargs={"uidb64": uid, "token": token},
    )
    setup_url = f"{base_url.rstrip('/')}{path}"

    send_mail(
        subject="Set up your Good Driver Incentive account",
        message=(
            f"Hello {user.first_name or user.username},\n\n"
            f"Your username is: {user.username}\n\n"
            f"Choose your password using this link:\n{setup_url}\n\n"
            "If you were not expecting this account, contact your "
            "sponsor organization."
        ),
        from_email=None,
        recipient_list=[user.email],
        fail_silently=False,
    )