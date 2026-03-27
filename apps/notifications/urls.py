from django.urls import path

from .views import UserNotificationListCreateView, UserNotificationMarkReadView

app_name = 'notifications'

urlpatterns = [
    path('user-notifications/', UserNotificationListCreateView.as_view(), name='user_notifications'),
    path(
        'user-notifications/<uuid:notification_id>/mark-read/',
        UserNotificationMarkReadView.as_view(),
        name='mark_notification_read',
    ),
]

