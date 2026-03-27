from rest_framework import serializers
from .models import HealthMetric, Medication


class HealthMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthMetric
        fields = '__all__'
        read_only_fields = ('user', 'recorded_at')


class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = '__all__'
        read_only_fields = ('user', 'created_at')
