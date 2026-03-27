from rest_framework import serializers
from .models import Doctor, MedicalEntry, Appointment


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = '__all__'


class MedicalEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalEntry
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')


class AppointmentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    doctor_specialty = serializers.CharField(source='doctor.specialty', read_only=True)

    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'reminder_sent_at')
