import uuid
from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class HealthMetric(models.Model):
    """Daily health vitals tracking."""
    METRIC_TYPES = (
        ('weight', 'Poids (kg)'),
        ('blood_pressure_sys', 'Pression artérielle (sys)'),
        ('blood_pressure_dia', 'Pression artérielle (dia)'),
        ('heart_rate', 'Fréquence cardiaque'),
        ('temperature', 'Température (°C)'),
        ('sleep_hours', 'Heures de sommeil'),
        ('pain_level', 'Niveau de douleur'),
        ('mood', 'Humeur (1-10)'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='health_metrics')
    metric_type = models.CharField(max_length=30, choices=METRIC_TYPES)
    value = models.DecimalField(max_digits=8, decimal_places=2)
    notes = models.TextField(blank=True)

    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.user} - {self.metric_type}: {self.value}"


class Medication(models.Model):
    """Medication tracking for the user."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medications')
    name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100, help_text="Ex: 2x par jour")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.dosage}) - {self.user}"
