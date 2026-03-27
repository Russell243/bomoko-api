from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Profile

User = get_user_model()

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['role', 'firebase_token', 'biometric_enabled', 'preferred_language', 'risk_score', 'last_risk_assessment', 'created_at', 'updated_at']
        read_only_fields = ['role', 'risk_score', 'last_risk_assessment', 'created_at', 'updated_at']

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'phone_number', 'email', 'first_name', 'last_name', 'is_verified', 'profile']
        read_only_fields = ['id', 'is_verified']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=Profile.ROLE_CHOICES, required=False, default='victim')
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)

    class Meta:
        model = User
        fields = ['username', 'phone_number', 'password', 'role', 'first_name', 'last_name']

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        validated_data.pop('role', None)
        user = User.objects.create_user(
            username=validated_data['username'],
            phone_number=validated_data.get('phone_number', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', '').strip(),
            last_name=validated_data.get('last_name', '').strip(),
        )
        user.profile.role = 'victim'
        user.profile.save(update_fields=['role'])
        return user
