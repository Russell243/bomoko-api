import json
import logging
from typing import Iterable
from urllib import request

from django.conf import settings

from .models import UserNotification

logger = logging.getLogger(__name__)


def _normalize_expo_token(token: str) -> str:
    if token.startswith("ExponentPushToken["):
        return token
    if token.startswith("ExpoPushToken["):
        return token
    return f"ExpoPushToken[{token}]"


def send_expo_push(tokens: Iterable[str], title: str, body: str, data: dict | None = None) -> bool:
    tokens = [t for t in tokens if t]
    if not tokens:
        return False

    enabled = bool(getattr(settings, "NOTIFICATIONS_ENABLE_PUSH", True))
    if not enabled:
        return False

    push_url = getattr(settings, "EXPO_PUSH_URL", "https://exp.host/--/api/v2/push/send")
    payload = [
        {
            "to": _normalize_expo_token(token),
            "title": title,
            "body": body,
            "sound": "default",
            "priority": "high",
            "data": data or {},
        }
        for token in tokens
    ]

    req = request.Request(
        push_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=5) as response:
            _ = response.read()
        return True
    except Exception as exc:
        logger.warning("Expo push request failed: %s", exc)
        return False


def create_user_notification(
    *,
    user,
    title: str,
    body: str,
    notification_type: str = UserNotification.TYPE_INFO,
    metadata: dict | None = None,
    trigger_push: bool = True,
) -> UserNotification:
    notification = UserNotification.objects.create(
        user=user,
        title=title,
        body=body,
        notification_type=notification_type,
        metadata=metadata or {},
    )

    if trigger_push:
        try:
            from .tasks import send_push_for_notification

            send_push_for_notification.delay(str(notification.id))
        except Exception as exc:
            logger.warning("Unable to enqueue push notification task: %s", exc)

    return notification
