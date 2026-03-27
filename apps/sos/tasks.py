import logging
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from .models import SOSAlert
from .services import SMSService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def retry_sos_sms_fallback(self, alert_id: str):
    """
    Retry sending SMS fallback for a single alert.
    This task avoids mock sending to keep real delivery semantics.
    """
    alert = SOSAlert.objects.filter(id=alert_id).first()
    if not alert:
        logger.warning("retry_sos_sms_fallback: alert %s not found.", alert_id)
        return {"status": "missing", "alert_id": alert_id}

    if alert.status != "active":
        return {"status": "ignored", "reason": "not_active", "alert_id": alert_id}

    if alert.sms_fallback_sent:
        return {"status": "ignored", "reason": "already_sent", "alert_id": alert_id}

    sent = SMSService.send_sos_sms(alert, require_location=True, allow_mock=False)
    if sent <= 0:
        raise self.retry()

    return {"status": "sent", "sent_count": sent, "alert_id": alert_id}


@shared_task
def retry_pending_sos_sms():
    """
    Periodic task: retry pending SMS fallback for active alerts.
    """
    cutoff = timezone.now() - timedelta(hours=24)
    pending_alerts = (
        SOSAlert.objects.filter(
            status="active",
            sms_fallback_sent=False,
            created_at__gte=cutoff,
        )
        .order_by("-created_at")
    )

    retried = 0
    for alert in pending_alerts:
        if not alert.locations.exists():
            continue
        retry_sos_sms_fallback.delay(str(alert.id))
        retried += 1

    return {"retried": retried}


@shared_task
def purge_expired_sos_audio_evidence():
    """
    Periodic task: remove audio evidence files older than configured retention.
    """
    if not getattr(settings, 'SOS_AUDIO_RETENTION_ENABLED', True):
        return {"deleted": 0, "skipped": True, "reason": "retention_disabled"}

    retention_days = int(getattr(settings, 'SOS_AUDIO_RETENTION_DAYS', 90))
    cutoff = timezone.now() - timedelta(days=retention_days)
    expired_alerts = (
        SOSAlert.objects.filter(created_at__lt=cutoff)
        .exclude(audio_evidence='')
        .exclude(audio_evidence__isnull=True)
    )

    deleted = 0
    for alert in expired_alerts.iterator():
        try:
            alert.audio_evidence.close()
        except Exception:
            pass
        alert.audio_evidence.delete(save=False)
        alert.audio_evidence = None
        alert.audio_mime_type = ''
        alert.audio_original_name = ''
        alert.audio_encrypted = False
        alert.save(update_fields=['audio_evidence', 'audio_mime_type', 'audio_original_name', 'audio_encrypted'])
        deleted += 1

    return {"deleted": deleted, "retention_days": retention_days}
