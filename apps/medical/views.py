from datetime import timedelta
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Doctor, MedicalEntry, Appointment
from .serializers import DoctorSerializer, MedicalEntrySerializer, AppointmentSerializer
from .tasks import send_due_appointment_reminders
from notifications.models import UserNotification
from notifications.services import create_user_notification


def _can_manage_reminders(user):
    role = getattr(getattr(user, 'profile', None), 'role', '')
    return bool(user.is_staff or role in {'admin', 'doctor'})


class DoctorViewSet(viewsets.ReadOnlyModelViewSet):
    """Public read-only list of doctors for the directory."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DoctorSerializer
    queryset = Doctor.objects.filter(is_available=True)
    filterset_fields = ['specialty', 'city', 'accepts_emergency']


class MedicalEntryViewSet(viewsets.ModelViewSet):
    """CRUD for a user's medical injury entries."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MedicalEntrySerializer

    def get_queryset(self):
        return MedicalEntry.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='advance-care-stage')
    def advance_care_stage(self, request, pk=None):
        entry = self.get_object()
        transition_map = {
            MedicalEntry.CARE_STAGE_INITIAL: MedicalEntry.CARE_STAGE_TREATMENT,
            MedicalEntry.CARE_STAGE_TREATMENT: MedicalEntry.CARE_STAGE_FOLLOW_UP,
            MedicalEntry.CARE_STAGE_FOLLOW_UP: MedicalEntry.CARE_STAGE_COMPLETED,
            MedicalEntry.CARE_STAGE_COMPLETED: MedicalEntry.CARE_STAGE_COMPLETED,
        }
        next_stage = transition_map[entry.care_stage]
        if next_stage == entry.care_stage:
            return Response({'detail': 'Parcours deja termine.'}, status=status.HTTP_400_BAD_REQUEST)

        entry.care_stage = next_stage
        entry.save(update_fields=['care_stage', 'updated_at'])
        return Response(self.get_serializer(entry).data, status=status.HTTP_200_OK)


class AppointmentViewSet(viewsets.ModelViewSet):
    """CRUD for a user's medical appointments."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        return Appointment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        appointment = serializer.save(user=self.request.user)
        create_user_notification(
            user=self.request.user,
            title='Rendez-vous medical cree',
            body=f"Votre RDV avec Dr. {appointment.doctor.name} est enregistre.",
            notification_type=UserNotification.TYPE_INFO,
            metadata={'appointment_id': str(appointment.id), 'module': 'medical'},
            trigger_push=True,
        )

    @action(detail=False, methods=['get'], url_path='due-reminders')
    def due_reminders(self, request):
        now = timezone.now()
        horizon = now + timedelta(hours=24)
        qs = self.get_queryset().filter(
            status__in=['pending', 'confirmed'],
            reminder_sent_at__isnull=True,
            date__gte=now,
            date__lte=horizon,
        )
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='send-reminders')
    def send_reminders(self, request):
        if not _can_manage_reminders(request.user):
            return Response({'detail': 'Action reservee au personnel medical autorise.'}, status=status.HTTP_403_FORBIDDEN)
        result = send_due_appointment_reminders.delay()
        return Response({'queued': True, 'task_id': result.id}, status=status.HTTP_202_ACCEPTED)
