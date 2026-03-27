from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmergencyContactViewSet,
    SOSAlertViewSet,
    DiscreetSettingsViewSet,
    PublicSOSTrackingView,
    PublicSOSTrackingPageView,
)

app_name = 'sos'

router = DefaultRouter()
router.register(r'contacts', EmergencyContactViewSet, basename='contact')
router.register(r'alerts', SOSAlertViewSet, basename='alert')

urlpatterns = [
    path('', include(router.urls)),
    path('settings/discreet/', DiscreetSettingsViewSet.as_view({'get': 'list', 'put': 'update', 'patch': 'partial_update'}), name='discreet_settings'),
    path('track/<uuid:alert_id>/<uuid:token>/', PublicSOSTrackingView.as_view(), name='public_tracking'),
    path('track-page/<uuid:alert_id>/<uuid:token>/', PublicSOSTrackingPageView.as_view(), name='public_tracking_page'),
]
