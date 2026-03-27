import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

User = settings.AUTH_USER_MODEL

class EmergencyContact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    relationship = models.CharField(max_length=50, blank=True)
    
    # V2 enhancements
    sms_template = models.TextField(blank=True, help_text="Custom SOS message")
    auto_call_enabled = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.relationship}) - {self.user}"

class SOSAlert(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('resolved', 'Resolved'),
        ('false_alarm', 'False Alarm'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sos_alerts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # V2 metadata
    battery_level = models.IntegerField(null=True, blank=True)
    network_type = models.CharField(max_length=20, blank=True)
    sms_fallback_sent = models.BooleanField(default=False)
    audio_evidence = models.FileField(upload_to='sos/audio/', null=True, blank=True)
    audio_mime_type = models.CharField(max_length=120, blank=True, default='')
    audio_original_name = models.CharField(max_length=255, blank=True, default='')
    audio_encrypted = models.BooleanField(default=False)
    public_tracking_token = models.UUIDField(unique=True, null=True, blank=True)
    tracking_token_expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"SOS {self.id} from {self.user} - {self.status}"

    def ensure_tracking_token(self):
        if self.public_tracking_token and self.tracking_token_expires_at and self.tracking_token_expires_at > timezone.now():
            return self.public_tracking_token

        ttl_hours = getattr(settings, 'SOS_TRACKING_TOKEN_TTL_HOURS', 72)
        self.public_tracking_token = uuid.uuid4()
        self.tracking_token_expires_at = timezone.now() + timedelta(hours=ttl_hours)
        self.save(update_fields=['public_tracking_token', 'tracking_token_expires_at'])
        return self.public_tracking_token

    def is_tracking_token_valid(self, token):
        if not self.public_tracking_token or not self.tracking_token_expires_at:
            return False
        if self.tracking_token_expires_at <= timezone.now():
            return False
        return str(self.public_tracking_token) == str(token)

    def revoke_tracking_token(self):
        self.public_tracking_token = None
        self.tracking_token_expires_at = None
        self.save(update_fields=['public_tracking_token', 'tracking_token_expires_at'])

class LocationUpdate(models.Model):
    id = models.BigAutoField(primary_key=True)
    alert = models.ForeignKey(SOSAlert, on_delete=models.CASCADE, related_name='locations')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # V2 enhancements where GPS is not available
    cell_tower_id = models.CharField(max_length=100, blank=True, null=True)
    is_indoor = models.BooleanField(default=False)
    
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Location for {self.alert.id} at {self.timestamp}"

class DiscreetAppSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='discreet_settings')
    
    # V2 Discreet Mode
    app_icon_type = models.CharField(max_length=50, default='default', help_text="e.g. calculator, weather")
    fake_app_name = models.CharField(max_length=50, default='Bomoko')
    widget_enabled = models.BooleanField(default=False)
    power_button_trigger = models.BooleanField(default=True)
    shake_to_trigger = models.BooleanField(default=False)
    
    audio_recording_enabled = models.BooleanField(default=True)
    pin_code = models.CharField(max_length=128, blank=True)
    
    def __str__(self):
        return f"Discreet Config - {self.user}"
