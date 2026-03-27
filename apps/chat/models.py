import uuid
from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255, default="Nouvelle Conversation")
    
    # V2 enhancements
    context_summary = models.TextField(blank=True, help_text="AI generated summary for long-term memory")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title

class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    
    is_user = models.BooleanField(default=True)
    content = models.TextField()
    
    # AI analysis metadata
    sentiment_score = models.FloatField(null=True, blank=True)
    urgency_level = models.FloatField(default=0.0)
    keywords = models.JSONField(default=list, blank=True)
    
    # V2 enhancements
    audio_url = models.URLField(blank=True, null=True)
    is_offline = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']

    def __str__(self):
        role = "User" if self.is_user else "AI"
        return f"{role}: {self.content[:50]}"
