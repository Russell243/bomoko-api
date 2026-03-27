from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid

class User(AbstractUser):
    """Custom User model for Bomoko Mobile V2"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    
    # We use username for login, but it could be set to phone_number
    # in a real world mobile-first app. For now we keep AbstractUser defaults.
    
    def __str__(self):
        return self.username or self.phone_number or str(self.id)

class Profile(models.Model):
    """Extended user profile with V2 additions like biometric and app_pin"""
    ROLE_CHOICES = (
        ('victim', _('Victime')),
        ('counselor', _('Conseiller')),
        ('doctor', _('Médecin')),
        ('lawyer', _('Avocat')),
        ('admin', _('Administrateur')),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='victim')
    
    # V2 features
    firebase_token = models.CharField(max_length=255, blank=True, null=True)
    biometric_enabled = models.BooleanField(default=False)
    app_pin_hash = models.CharField(max_length=128, blank=True, null=True)
    preferred_language = models.CharField(max_length=10, default='fr-fr')
    
    # Analytics / Risk Scoring
    risk_score = models.FloatField(default=0.0, help_text="Calculated vulnerability score (0.0 - 1.0)")
    last_risk_assessment = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.username} ({self.role})"
