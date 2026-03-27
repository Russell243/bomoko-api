from rest_framework import serializers

from .models import UserNotification


class UserNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotification
        fields = (
            'id',
            'title',
            'body',
            'notification_type',
            'is_read',
            'metadata',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

