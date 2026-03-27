from datetime import timedelta
from celery import shared_task
from django.utils import timezone

from notifications.models import UserNotification
from notifications.services import create_user_notification
from .models import Appointment


def _get_due_appointments():
    now = timezone.now()
    horizon = now + timedelta(hours=24)
    return Appointment.objects.select_related('doctor', 'user').filter(
        status__in=['pending', 'confirmed'],
        reminder_sent_at__isnull=True,
        date__gte=now,
        date__lte=horizon,
    )


@shared_task
def send_due_appointment_reminders():
    due = _get_due_appointments()
    sent = 0
    for appointment in due:
        create_user_notification(
            user=appointment.user,
            title='Rappel rendez-vous medical',
            body=f"Vous avez un RDV avec Dr. {appointment.doctor.name} le {appointment.date.strftime('%d/%m/%Y %H:%M')}.",
            notification_type=UserNotification.TYPE_WARNING,
            metadata={'appointment_id': str(appointment.id), 'module': 'medical'},
            trigger_push=True,
        )
        appointment.reminder_sent_at = timezone.now()
        appointment.save(update_fields=['reminder_sent_at'])
        sent += 1
    return {'sent': sent}
