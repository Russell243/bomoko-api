from django.db import connection
from django.conf import settings
import redis
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from .models import HealthMetric, Medication
from .serializers import HealthMetricSerializer, MedicationSerializer


class HealthMetricViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = HealthMetricSerializer

    def get_queryset(self):
        queryset = HealthMetric.objects.filter(user=self.request.user)
        metric_type = self.request.query_params.get('type')
        if metric_type:
            queryset = queryset.filter(metric_type=metric_type)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MedicationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MedicationSerializer

    def get_queryset(self):
        return Medication.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SystemHealthView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'system_health'

    def get(self, request):
        db_ok = False
        redis_ok = False
        db_error = None
        redis_error = None

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            db_ok = True
        except Exception as exc:
            db_error = str(exc)

        try:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            redis_client = redis.Redis.from_url(redis_url, socket_connect_timeout=1, socket_timeout=1)
            redis_ok = bool(redis_client.ping())
        except Exception as exc:
            redis_error = str(exc)

        status_code = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE
        can_view_details = bool(getattr(request.user, 'is_authenticated', False) and request.user.is_staff)
        payload = {
            'status': 'ok' if db_ok else 'degraded',
            'database': {'ok': db_ok},
            'redis': {'ok': redis_ok},
        }
        if can_view_details:
            payload['database']['error'] = db_error
            payload['redis']['error'] = redis_error

        return Response(
            payload,
            status=status_code,
        )
