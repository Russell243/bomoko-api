import logging
import os
import base64
import hashlib
from django.conf import settings
from django.utils import timezone
from django.http import HttpResponse
from django.shortcuts import render
from django.core.files.base import ContentFile
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from .models import EmergencyContact, SOSAlert, LocationUpdate, DiscreetAppSettings
from .serializers import (
    EmergencyContactSerializer, 
    SOSAlertSerializer, 
    LocationUpdateSerializer,
    DiscreetAppSettingsSerializer
)
from .services import SMSService
from .tasks import retry_sos_sms_fallback
from notifications.models import UserNotification
from notifications.services import create_user_notification
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


def _get_audio_fernet():
    raw_key = getattr(settings, 'SOS_AUDIO_ENCRYPTION_KEY', '') or ''
    if raw_key:
        try:
            return Fernet(raw_key.encode('utf-8'))
        except Exception:
            logger.warning("Invalid SOS_AUDIO_ENCRYPTION_KEY format. Falling back to derived key.")

    secret = (getattr(settings, 'SECRET_KEY', '') or 'bomoko-default-key').encode('utf-8')
    digest = hashlib.sha256(secret).digest()
    derived_key = base64.urlsafe_b64encode(digest)
    return Fernet(derived_key)


class EmergencyContactViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EmergencyContactSerializer
    
    def get_queryset(self):
        return EmergencyContact.objects.filter(user=self.request.user)
        
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SOSAlertViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SOSAlertSerializer
    
    def get_queryset(self):
        return SOSAlert.objects.filter(user=self.request.user)
        
    def perform_create(self, serializer):
        min_contacts = int(getattr(settings, 'SOS_MIN_CONTACTS_REQUIRED', 3))
        contacts_count = self.request.user.emergency_contacts.count()
        if contacts_count < min_contacts:
            raise ValidationError(
                {
                    'detail': (
                        f'Vous devez enregistrer au moins {min_contacts} contacts de confiance '
                        "avant d'activer le SOS."
                    ),
                    'required_contacts': min_contacts,
                    'current_contacts': contacts_count,
                }
            )

        alert = serializer.save(user=self.request.user, status='active')
        # We defer SMS until a real position is available.
        logger.info("SOS Alert %s created. Waiting for first location before SMS.", alert.id)

        create_user_notification(
            user=alert.user,
            title='Alerte SOS declenchee',
            body='Votre alerte SOS est active. Partagez votre position pour notifier vos contacts.',
            notification_type=UserNotification.TYPE_ALERT,
            metadata={'alert_id': str(alert.id), 'status': alert.status},
            trigger_push=True,
        )

        counselors = (
            alert.user.__class__.objects.filter(profile__role='counselor', is_active=True)
            .exclude(id=alert.user_id)
            .select_related('profile')
        )
        for counselor in counselors[:20]:
            create_user_notification(
                user=counselor,
                title='Nouvelle alerte SOS',
                body="Une victime a declenche une alerte SOS. Verifiez le tableau d'assistance.",
                notification_type=UserNotification.TYPE_ALERT,
                metadata={'alert_id': str(alert.id), 'victim_id': str(alert.user_id)},
                trigger_push=True,
            )

    @action(detail=True, methods=['post'])
    def location(self, request, pk=None):
        alert = self.get_object()
        if alert.status != 'active':
            return Response({"detail": "Alert is not active."}, status=status.HTTP_400_BAD_REQUEST)
            
        serializer = LocationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(alert=alert)

        # Re-send SMS with updated position on first location update
        if alert.locations.count() == 1 and not alert.sms_fallback_sent:
            try:
                sent = SMSService.send_sos_sms(
                    alert,
                    require_location=True,
                    allow_mock=bool(getattr(settings, 'DEBUG', False)),
                )
                logger.info("SOS Alert %s: %s SMS sent after first location.", alert.id, sent)
                if sent <= 0:
                    retry_sos_sms_fallback.delay(str(alert.id))
            except Exception as e:
                logger.error(f"SMS on first location update failed: {e}")
                retry_sos_sms_fallback.delay(str(alert.id))

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        alert = self.get_object()
        alert.status = 'resolved'
        alert.resolved_at = timezone.now()
        alert.save(update_fields=['status', 'resolved_at'])

        create_user_notification(
            user=alert.user,
            title='Alerte SOS resolue',
            body='Votre alerte SOS a ete marquee comme resolue.',
            notification_type=UserNotification.TYPE_INFO,
            metadata={'alert_id': str(alert.id), 'status': alert.status},
            trigger_push=True,
        )

        # Notify contacts that the alert is resolved
        try:
            SMSService.send_resolved_sms(alert)
        except Exception as e:
            logger.error(f"Resolved SMS failed: {e}")
        return Response({'status': 'resolved'})

    @action(detail=True, methods=['post'])
    def tracking_link(self, request, pk=None):
        alert = self.get_object()
        token = alert.ensure_tracking_token()
        tracking_base_url = getattr(settings, 'PUBLIC_TRACKING_BASE_URL', '').rstrip('/')
        tracking_url = f"{tracking_base_url}/track/{alert.id}/{token}/"
        return Response(
            {
                'alert_id': str(alert.id),
                'tracking_token': str(token),
                'tracking_url': tracking_url,
                'expires_at': alert.tracking_token_expires_at,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'])
    def revoke_tracking_link(self, request, pk=None):
        alert = self.get_object()
        alert.revoke_tracking_token()
        return Response(
            {
                'alert_id': str(alert.id),
                'tracking_revoked': True,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post', 'delete'])
    def audio(self, request, pk=None):
        alert = self.get_object()

        if request.method.upper() == 'DELETE':
            if not alert.audio_evidence:
                return Response({'detail': 'Aucun audio a supprimer.'}, status=status.HTTP_404_NOT_FOUND)

            try:
                alert.audio_evidence.close()
            except Exception:
                pass
            alert.audio_evidence.delete(save=False)
            alert.audio_evidence = None
            alert.audio_mime_type = ''
            alert.audio_original_name = ''
            alert.audio_encrypted = False
            alert.save(update_fields=['audio_evidence', 'audio_mime_type', 'audio_original_name', 'audio_encrypted'])
            return Response({'audio_deleted': True, 'alert_id': str(alert.id)}, status=status.HTTP_200_OK)

        audio_file = request.FILES.get('audio')
        if not audio_file:
            return Response({'detail': 'Le fichier audio est requis.'}, status=status.HTTP_400_BAD_REQUEST)

        max_upload_size = int(getattr(settings, 'SOS_AUDIO_MAX_UPLOAD_BYTES', 5 * 1024 * 1024))
        if getattr(audio_file, 'size', 0) > max_upload_size:
            return Response(
                {'detail': 'Le fichier audio depasse la taille maximale autorisee.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_bytes = audio_file.read()
        mime_type = getattr(audio_file, 'content_type', '') or 'application/octet-stream'
        original_name = getattr(audio_file, 'name', '') or 'audio-record'
        if not mime_type.startswith('audio/'):
            return Response({'detail': 'Le fichier doit etre un audio valide.'}, status=status.HTTP_400_BAD_REQUEST)

        should_encrypt = bool(getattr(settings, 'SOS_AUDIO_ENCRYPTION_ENABLED', True))
        saved_file = audio_file
        encrypted = False
        if should_encrypt:
            fernet = _get_audio_fernet()
            encrypted_bytes = fernet.encrypt(raw_bytes)
            _, ext = os.path.splitext(original_name)
            encrypted_name = f"{os.path.splitext(original_name)[0]}{ext}.enc"
            saved_file = ContentFile(encrypted_bytes, name=encrypted_name)
            encrypted = True

        alert.audio_evidence = saved_file
        alert.audio_mime_type = mime_type
        alert.audio_original_name = original_name
        alert.audio_encrypted = encrypted
        alert.save(update_fields=['audio_evidence', 'audio_mime_type', 'audio_original_name', 'audio_encrypted'])
        return Response(
            {
                'audio_uploaded': True,
                'audio_encrypted': encrypted,
                'alert_id': str(alert.id),
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['get'], url_path='audio-history')
    def audio_history(self, request):
        alerts = self.get_queryset().exclude(audio_evidence='').exclude(audio_evidence__isnull=True)
        data = [
            {
                'alert_id': str(alert.id),
                'created_at': alert.created_at,
                'resolved_at': alert.resolved_at,
                'audio_original_name': alert.audio_original_name or 'audio-record',
                'audio_mime_type': alert.audio_mime_type or 'application/octet-stream',
                'audio_encrypted': alert.audio_encrypted,
            }
            for alert in alerts
        ]
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='audio-stream')
    def audio_stream(self, request, pk=None):
        alert = self.get_object()
        if not alert.audio_evidence:
            return Response({'detail': 'Aucun audio enregistre pour cette alerte.'}, status=status.HTTP_404_NOT_FOUND)

        file_bytes = alert.audio_evidence.read()
        try:
            alert.audio_evidence.close()
        except Exception:
            pass
        content = file_bytes
        if alert.audio_encrypted:
            try:
                fernet = _get_audio_fernet()
                content = fernet.decrypt(file_bytes)
            except Exception:
                return Response({'detail': "Impossible de dechiffrer l'audio."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response = HttpResponse(content, content_type=alert.audio_mime_type or 'application/octet-stream')
        filename = alert.audio_original_name or f"audio-{alert.id}.bin"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        response['Cache-Control'] = 'no-store, no-cache, max-age=0, private'
        response['Pragma'] = 'no-cache'
        return response


class DiscreetSettingsViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DiscreetAppSettingsSerializer
    
    def get_queryset(self):
        return DiscreetAppSettings.objects.filter(user=self.request.user)
        
    def get_object(self):
        obj, created = DiscreetAppSettings.objects.get_or_create(user=self.request.user)
        return obj
        
    def list(self, request, *args, **kwargs):
        return Response(self.get_serializer(self.get_object()).data)


class PublicSOSTrackingView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'public_tracking'

    def get(self, request, alert_id, token):
        alert = SOSAlert.objects.filter(id=alert_id).first()
        if not alert or not alert.is_tracking_token_valid(token):
            return Response({'detail': 'Tracking link invalid or expired.'}, status=status.HTTP_404_NOT_FOUND)

        latest_location = alert.locations.order_by('-timestamp').first()
        location_data = None
        if latest_location:
            location_data = {
                'latitude': round(float(latest_location.latitude), 4) if latest_location.latitude is not None else None,
                'longitude': round(float(latest_location.longitude), 4) if latest_location.longitude is not None else None,
                'is_indoor': latest_location.is_indoor,
                'timestamp': latest_location.timestamp,
            }

        base_url = getattr(settings, 'PUBLIC_TRACKING_BASE_URL', '')
        response = Response(
            {
                'alert_id': str(alert.id),
                'status': alert.status,
                'created_at': alert.created_at,
                'resolved_at': alert.resolved_at,
                'tracking_expires_at': alert.tracking_token_expires_at,
                'latest_location': location_data,
                'public_tracking_base_url': base_url,
            },
            status=status.HTTP_200_OK,
        )
        response['Cache-Control'] = 'no-store, no-cache, max-age=0, private'
        response['Pragma'] = 'no-cache'
        return response


class PublicSOSTrackingPageView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'public_tracking'

    def get(self, request, alert_id, token):
        alert = SOSAlert.objects.filter(id=alert_id).first()
        if not alert or not alert.is_tracking_token_valid(token):
            return HttpResponse('Lien de suivi invalide ou expire.', status=404)

        response = render(
            request,
            'sos/public_tracking.html',
            {
                'alert_id': str(alert_id),
                'token': str(token),
            },
        )
        response['Cache-Control'] = 'no-store, no-cache, max-age=0, private'
        response['Pragma'] = 'no-cache'
        return response
