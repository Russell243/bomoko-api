import uuid

from django.conf import settings
from django.db import models


class UserNotification(models.Model):
    TYPE_INFO = 'info'
    TYPE_WARNING = 'warning'
    TYPE_ALERT = 'alert'

    TYPE_CHOICES = (
        (TYPE_INFO, 'Info'),
        (TYPE_WARNING, 'Warning'),
        (TYPE_ALERT, 'Alert'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    title = models.CharField(max_length=120)
    body = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_INFO)
    is_read = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user_id} - {self.title}'

