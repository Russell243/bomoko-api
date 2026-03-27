from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HealthMetricViewSet, MedicationViewSet, SystemHealthView

app_name = 'health'

router = DefaultRouter()
router.register('vitals', HealthMetricViewSet, basename='health-metric')
router.register('medications', MedicationViewSet, basename='medication')

urlpatterns = [
    path('', include(router.urls)),
    path('system/', SystemHealthView.as_view(), name='system-health'),
]
