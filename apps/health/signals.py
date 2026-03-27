from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import HealthMetric
from notifications.services import create_user_notification

@receiver(post_save, sender=HealthMetric)
def check_health_metric_thresholds(sender, instance, created, **kwargs):
    """
    Checks if a newly saved health metric exceeds dangerous thresholds 
    and sends a notification to the user if so.
    """
    if not created:
        return

    alert_needed = False
    message = ""

    # Basic business rules for vitals
    if instance.metric_type == 'blood_pressure_sys' and instance.value > 140:
        alert_needed = True
        message = "Votre pression artérielle systolique est très élevée. Veuillez consulter la section médicale ou contacter un médecin."
    elif instance.metric_type == 'heart_rate' and (instance.value > 120 or instance.value < 50):
        alert_needed = True
        message = f"Fréquence cardiaque anormale détectée ({instance.value} bpm). Un repos est conseillé."
    elif instance.metric_type == 'temperature' and instance.value > 38.5:
        alert_needed = True
        message = "Fièvre détectée. Pensez à vous hydrater et envisagez une téléconsultation médicale."

    if alert_needed:
        try:
            create_user_notification(
                user=instance.user,
                title="⚠️ Alerte de Santé",
                body=message,
                trigger_push=True
            )
        except Exception as e:
            pass
