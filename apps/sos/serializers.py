from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import EmergencyContact, SOSAlert, LocationUpdate, DiscreetAppSettings

class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = ['id', 'name', 'phone_number', 'email', 'relationship', 'sms_template', 'auto_call_enabled', 'created_at']
        read_only_fields = ['id', 'created_at']

class LocationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationUpdate
        fields = ['latitude', 'longitude', 'cell_tower_id', 'is_indoor', 'timestamp']
        read_only_fields = ['timestamp']

class SOSAlertSerializer(serializers.ModelSerializer):
    locations = LocationUpdateSerializer(many=True, read_only=True)
    
    class Meta:
        model = SOSAlert
        fields = [
            'id',
            'status',
            'battery_level',
            'network_type',
            'sms_fallback_sent',
            'audio_evidence',
            'audio_mime_type',
            'audio_original_name',
            'audio_encrypted',
            'public_tracking_token',
            'tracking_token_expires_at',
            'created_at',
            'resolved_at',
            'locations',
        ]
        read_only_fields = ['id', 'created_at', 'resolved_at', 'public_tracking_token', 'tracking_token_expires_at']

class DiscreetAppSettingsSerializer(serializers.ModelSerializer):
    pin_code = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        max_length=10
    )
    has_pin = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DiscreetAppSettings
        fields = [
            'app_icon_type', 'fake_app_name', 'widget_enabled', 
            'power_button_trigger', 'shake_to_trigger', 
            'audio_recording_enabled', 'pin_code', 'has_pin'
        ]

    def get_has_pin(self, obj):
        return bool(obj.pin_code)

    def validate_pin_code(self, value):
        if not value:
            return value
        if not value.isdigit():
            raise serializers.ValidationError("PIN must contain only digits.")
        if len(value) < 4:
            raise serializers.ValidationError("PIN must be at least 4 digits.")
        return value

    def create(self, validated_data):
        pin_code = validated_data.pop('pin_code', '')
        if pin_code:
            validated_data['pin_code'] = make_password(pin_code)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        pin_code = validated_data.pop('pin_code', None)
        if pin_code is not None:
            instance.pin_code = make_password(pin_code) if pin_code else ''
        return super().update(instance, validated_data)
