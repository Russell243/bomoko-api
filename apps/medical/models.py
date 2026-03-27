import uuid
from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class Doctor(models.Model):
    """Healthcare provider directory entry."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    specialty = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, default='Kinshasa')
    is_available = models.BooleanField(default=True)
    accepts_emergency = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dr. {self.name} ({self.specialty})"


class MedicalEntry(models.Model):
    """Injury or incident report filed by a victim."""
    SEVERITY_CHOICES = (
        ('low', 'Faible'),
        ('medium', 'Moyen'),
        ('high', 'Élevé'),
        ('critical', 'Critique'),
    )

    CARE_STAGE_INITIAL = 'initial_assessment'
    CARE_STAGE_TREATMENT = 'treatment_plan'
    CARE_STAGE_FOLLOW_UP = 'follow_up'
    CARE_STAGE_COMPLETED = 'completed'
    CARE_STAGE_CHOICES = (
        (CARE_STAGE_INITIAL, 'Evaluation initiale'),
        (CARE_STAGE_TREATMENT, 'Plan de traitement'),
        (CARE_STAGE_FOLLOW_UP, 'Suivi'),
        (CARE_STAGE_COMPLETED, 'Parcours termine'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medical_entries')
    description = models.TextField(help_text="Description de la blessure ou de l'incident")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    pain_level = models.IntegerField(default=5, help_text="Niveau de douleur (1-10)")
    body_part = models.CharField(max_length=100, blank=True)
    photo_url = models.URLField(blank=True, null=True)

    # Linked to SOS alert if applicable
    sos_alert = models.ForeignKey(
        'sos.SOSAlert', on_delete=models.SET_NULL, null=True, blank=True, related_name='medical_entries'
    )
    care_stage = models.CharField(max_length=30, choices=CARE_STAGE_CHOICES, default=CARE_STAGE_INITIAL)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Medical Entry - {self.user} ({self.severity})"


class Appointment(models.Model):
    """Medical appointment between a user and a doctor."""
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('confirmed', 'Confirmé'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    date = models.DateTimeField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"RDV {self.user} → Dr. {self.doctor.name} ({self.status})"
