import uuid
from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class Lawyer(models.Model):
    """Legal professional directory entry."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    specialty = models.CharField(max_length=100, help_text="Ex: droit familial, droit penal")
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    bar_association = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, default='Kinshasa')
    is_available = models.BooleanField(default=True)
    accepts_pro_bono = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Me. {self.name} ({self.specialty})"


class LegalCase(models.Model):
    """Legal support request filed by a victim."""
    TYPE_CHOICES = (
        ('complaint', 'Plainte'),
        ('consultation', 'Consultation'),
        ('protection_order', 'Ordonnance de protection'),
        ('divorce', 'Divorce'),
        ('custody', "Garde d'enfants"),
        ('other', 'Autre'),
    )
    STATUS_CHOICES = (
        ('submitted', 'Soumis'),
        ('in_review', "En cours d'examen"),
        ('assigned', 'Assigne a un avocat'),
        ('in_progress', 'En cours'),
        ('resolved', 'Resolu'),
        ('closed', 'Ferme'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='legal_cases')
    case_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    assigned_lawyer = models.ForeignKey(
        Lawyer, on_delete=models.SET_NULL, null=True, blank=True, related_name='cases'
    )
    is_anonymous = models.BooleanField(default=True, help_text="Garder l'identite confidentielle")
    is_urgent = models.BooleanField(default=False)
    status_changed_at = models.DateTimeField(auto_now_add=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Case {self.title} ({self.status})"


class LegalCaseEvent(models.Model):
    EVENT_STATUS_CHANGE = 'status_change'
    EVENT_NOTE = 'note'
    EVENT_CHOICES = (
        (EVENT_STATUS_CHANGE, 'Status change'),
        (EVENT_NOTE, 'Note'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    legal_case = models.ForeignKey(LegalCase, on_delete=models.CASCADE, related_name='events')
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='legal_case_events')
    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES, default=EVENT_STATUS_CHANGE)
    from_status = models.CharField(max_length=20, blank=True, default='')
    to_status = models.CharField(max_length=20, blank=True, default='')
    note = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.legal_case_id} {self.event_type} {self.from_status}->{self.to_status}"
