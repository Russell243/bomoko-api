from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LawyerViewSet, LegalCaseViewSet

app_name = 'legal'

router = DefaultRouter()
router.register('lawyers', LawyerViewSet, basename='lawyer')
router.register('cases', LegalCaseViewSet, basename='legal-case')

urlpatterns = [
    path('', include(router.urls)),
]
