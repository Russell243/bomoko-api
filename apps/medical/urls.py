from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DoctorViewSet, MedicalEntryViewSet, AppointmentViewSet

app_name = 'medical'

router = DefaultRouter()
router.register('doctors', DoctorViewSet, basename='doctor')
router.register('entries', MedicalEntryViewSet, basename='medical-entry')
router.register('appointments', AppointmentViewSet, basename='appointment')

urlpatterns = [
    path('', include(router.urls)),
]
