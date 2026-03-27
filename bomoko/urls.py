from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from sos.views import PublicSOSTrackingPageView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/chat/', include('chat.urls')),
    path('api/medical/', include('medical.urls')),
    path('api/legal/', include('legal.urls')),
    path('api/forum/', include('forum.urls')),
    path('api/health/', include('health.urls')),
    path('api/sos/', include('sos.urls')),
    path('api/notifications/', include('notifications.urls')),
    # Legacy compatibility for old mobile URL
    path(
        'notifications/api/',
        include(('notifications.urls', 'notifications'), namespace='notifications_legacy'),
    ),
    path('track/<uuid:alert_id>/<uuid:token>/', PublicSOSTrackingPageView.as_view(), name='public_tracking_page_root'),
]
