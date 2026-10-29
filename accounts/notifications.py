from .models import notification

#unless disables, create in app notifiation
def create_notification(*, user, message, notification_type="general", organization=None):

    if notification_type == "points":
        if not user.order_notifications:
            return None

    if notification_type == "order":
        if not user.order_notifications:
            return None

    return notification.objects.create(
        user=user,
        message=message,
        notification_type=notification_type,
        organization=organization,
    )
