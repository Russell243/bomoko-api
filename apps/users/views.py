import logging
import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView

from .serializers import UserSerializer, RegisterSerializer, ProfileSerializer

User = get_user_model()
logger = logging.getLogger(__name__)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'auth_register'
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.warning("Registration validation failed: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = serializer.save()
            logger.info("User created successfully: %s", user.username)
            refresh = RefreshToken.for_user(user)

            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        except Exception:
            logger.exception("Registration failed.")
            return Response(
                {"detail": "Impossible de creer le compte pour le moment."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LoginView(TokenObtainPairView):
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'auth_login'


class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user_serializer = self.get_serializer(self.get_object(), data=request.data, partial=True)
        user_serializer.is_valid(raise_exception=True)
        self.perform_update(user_serializer)

        profile_data = request.data.get('profile', None)
        if profile_data:
            profile = self.get_object().profile
            profile_serializer = ProfileSerializer(profile, data=profile_data, partial=True)
            profile_serializer.is_valid(raise_exception=True)
            profile_serializer.save()

        return Response(self.get_serializer(self.get_object()).data)

class VerifyOTPView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'auth_verify_otp'

    def post(self, request):
        code = request.data.get('code')
        expected_code = getattr(settings, 'OTP_BYPASS_CODE', '')

        if settings.DEBUG and expected_code and code == expected_code:
            user = request.user
            user.is_verified = True
            user.save()
            return Response({"detail": "Phone verified successfully."}, status=status.HTTP_200_OK)

        return Response(
            {"detail": "Invalid OTP code or OTP service not configured."},
            status=status.HTTP_400_BAD_REQUEST
        )


class ChangePasswordView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        current_password = request.data.get('current_password', '')
        new_password = request.data.get('new_password', '')
        user = request.user

        if not user.check_password(current_password):
            return Response({"detail": "Mot de passe actuel incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password, user=user)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save(update_fields=['password'])
        return Response({"detail": "Mot de passe mis a jour."}, status=status.HTTP_200_OK)


class DeactivateAccountView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = request.user
        user.is_active = False
        user.save(update_fields=['is_active'])
        return Response({"detail": "Compte suspendu."}, status=status.HTTP_200_OK)


class DeleteAccountView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = request.user
        anonymized_username = f"deleted-{uuid.uuid4().hex[:24]}"

        user.username = anonymized_username
        user.email = ''
        user.first_name = ''
        user.last_name = ''
        user.phone_number = None
        user.is_active = False
        user.is_verified = False
        user.set_unusable_password()
        user.save(
            update_fields=[
                'username',
                'email',
                'first_name',
                'last_name',
                'phone_number',
                'is_active',
                'is_verified',
                'password',
            ]
        )

        profile = getattr(user, 'profile', None)
        if profile:
            profile.firebase_token = None
            profile.biometric_enabled = False
            profile.app_pin_hash = None
            profile.save(update_fields=['firebase_token', 'biometric_enabled', 'app_pin_hash', 'updated_at'])

        return Response({"detail": "Compte anonymise et desactive."}, status=status.HTTP_200_OK)
