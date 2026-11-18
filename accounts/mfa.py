import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.utils import timezone

from .models import MfaChallenge

#generate a random 6-digit code and send via email
def send_mfa_code(user):
    code = f"{secrets.randbelow(1_000_000):06d}"

    challenge = MfaChallenge.objects.create(
        user=user,
        code_hash=make_password(code),
        expires_at=timezone.now() + timedelta(minutes=5),
    )

    try:
        send_mail(
            subject="Your One Time Sign-in Code",
            message=f"Your sign-in code is: {code}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )

    except Exception:
        challenge.delete()
        raise

    return challenge