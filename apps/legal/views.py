from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Lawyer, LegalCase, LegalCaseEvent
from .serializers import LawyerSerializer, LegalCaseSerializer, LegalCaseEventSerializer
from notifications.models import UserNotification
from notifications.services import create_user_notification


class LawyerViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LawyerSerializer
    queryset = Lawyer.objects.filter(is_available=True)
    filterset_fields = ['specialty', 'city', 'accepts_pro_bono']


class LegalCaseViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LegalCaseSerializer

    def get_queryset(self):
        return LegalCase.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        legal_case = serializer.save(user=self.request.user)
        LegalCaseEvent.objects.create(
            legal_case=legal_case,
            actor=self.request.user,
            event_type=LegalCaseEvent.EVENT_STATUS_CHANGE,
            from_status='',
            to_status=legal_case.status,
            note='Creation du dossier',
        )
        create_user_notification(
            user=self.request.user,
            title='Dossier juridique cree',
            body=f"Votre dossier \"{legal_case.title}\" est enregistre.",
            notification_type=UserNotification.TYPE_INFO,
            metadata={'legal_case_id': str(legal_case.id), 'module': 'legal'},
            trigger_push=True,
        )

    @action(detail=True, methods=['post'], url_path='transition')
    def transition(self, request, pk=None):
        legal_case = self.get_object()
        target_status = request.data.get('to_status')
        note = request.data.get('note', '')

        allowed_transitions = {
            'submitted': ['in_review', 'closed'],
            'in_review': ['assigned', 'closed'],
            'assigned': ['in_progress', 'closed'],
            'in_progress': ['resolved', 'closed'],
            'resolved': ['closed'],
            'closed': [],
        }

        if target_status not in dict(LegalCase.STATUS_CHOICES):
            return Response({'detail': 'Statut cible invalide.'}, status=status.HTTP_400_BAD_REQUEST)
        if target_status not in allowed_transitions.get(legal_case.status, []):
            return Response(
                {'detail': f"Transition interdite: {legal_case.status} -> {target_status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        previous_status = legal_case.status
        legal_case.status = target_status
        legal_case.status_changed_at = timezone.now()
        legal_case.save(update_fields=['status', 'status_changed_at', 'updated_at'])

        LegalCaseEvent.objects.create(
            legal_case=legal_case,
            actor=request.user,
            event_type=LegalCaseEvent.EVENT_STATUS_CHANGE,
            from_status=previous_status,
            to_status=target_status,
            note=note,
        )

        create_user_notification(
            user=legal_case.user,
            title='Mise a jour dossier juridique',
            body=f"Dossier \"{legal_case.title}\": {previous_status} -> {target_status}.",
            notification_type=UserNotification.TYPE_WARNING,
            metadata={'legal_case_id': str(legal_case.id), 'module': 'legal'},
            trigger_push=True,
        )

        return Response(self.get_serializer(legal_case).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='add-note')
    def add_note(self, request, pk=None):
        legal_case = self.get_object()
        note = (request.data.get('note') or '').strip()
        if not note:
            return Response({'detail': 'La note est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        event = LegalCaseEvent.objects.create(
            legal_case=legal_case,
            actor=request.user,
            event_type=LegalCaseEvent.EVENT_NOTE,
            note=note,
            from_status=legal_case.status,
            to_status=legal_case.status,
        )
        return Response(LegalCaseEventSerializer(event).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='history')
    def history(self, request, pk=None):
        legal_case = self.get_object()
        events = legal_case.events.all()
        return Response(LegalCaseEventSerializer(events, many=True).data, status=status.HTTP_200_OK)
