from django.contrib import admin
from .models import HealthMetric, Medication

@admin.register(HealthMetric)
class HealthMetricAdmin(admin.ModelAdmin):
    list_display = ('user', 'metric_type', 'value', 'recorded_at')
    list_filter = ('metric_type', 'recorded_at')
    search_fields = ('user__username', 'notes')

@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'dosage', 'frequency', 'is_active', 'start_date', 'end_date')
    list_filter = ('is_active', 'start_date')
    search_fields = ('name', 'user__username')
