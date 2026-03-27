from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UserNotification
from .serializers import UserNotificationSerializer
from .services import create_user_notification


class UserNotificationListCreateView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserNotificationSerializer

    def get_queryset(self):
        return UserNotification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        validated = serializer.validated_data
        serializer.instance = create_user_notification(
            user=self.request.user,
            title=validated['title'],
            body=validated['body'],
            notification_type=validated.get('notification_type', UserNotification.TYPE_INFO),
            metadata=validated.get('metadata', {}),
            trigger_push=True,
        )


class UserNotificationMarkReadView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, notification_id):
        notification = UserNotification.objects.filter(
            id=notification_id,
            user=request.user,
        ).first()
        if not notification:
            return Response({'detail': 'Notification introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        notification.is_read = True
        notification.save(update_fields=['is_read', 'updated_at'])
        return Response(UserNotificationSerializer(notification).data, status=status.HTTP_200_OK)
