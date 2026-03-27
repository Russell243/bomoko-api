from celery import shared_task

from .models import UserNotification
from .services import send_expo_push


@shared_task
def send_push_for_notification(notification_id: str):
    notification = (
        UserNotification.objects.select_related("user", "user__profile")
        .filter(id=notification_id)
        .first()
    )
    if not notification:
        return {"status": "missing", "notification_id": notification_id}

    token = getattr(getattr(notification.user, "profile", None), "firebase_token", None)
    if not token:
        return {"status": "skipped", "reason": "no_token", "notification_id": notification_id}

    ok = send_expo_push(
        [token],
        title=notification.title,
        body=notification.body,
        data={"notification_id": str(notification.id), **(notification.metadata or {})},
    )
    return {"status": "sent" if ok else "failed", "notification_id": notification_id}
