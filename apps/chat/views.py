from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Conversation, Message
from .serializers import ConversationSerializer, ConversationListSerializer, MessageSerializer
from .ai_service import AIService
from .speech_service import SpeechService

class ConversationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ConversationListSerializer
        return ConversationSerializer
        
    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user).order_by('-updated_at')
        
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        conversation = self.get_object()
        user_content = request.data.get('content')
        is_offline = request.data.get('is_offline', False)
        
        if not user_content:
            return Response({"detail": "Le contenu du message est requis."}, status=status.HTTP_400_BAD_REQUEST)
            
        # 1. Save user message
        user_msg = Message.objects.create(
            conversation=conversation,
            is_user=True,
            content=user_content,
            is_offline=is_offline
        )
        
        # If offline, we just acknowledge receipt, no AI response yet
        if is_offline:
            return Response(MessageSerializer(user_msg).data, status=status.HTTP_201_CREATED)
            
        # 2. Get bounded history (both user + AI messages) for better context.
        history = list(
            conversation.messages.exclude(id=user_msg.id).order_by('created_at')[:20]
        )
        
        # 3. Request AI response
        ai_response_text, urgency = AIService.get_chat_response(conversation, history, user_content)
        
        # 4. Save AI response
        ai_msg = Message.objects.create(
            conversation=conversation,
            is_user=False,
            content=ai_response_text,
            urgency_level=urgency
        )
        
        # 5. Trigger summary update (async)
        from .tasks import update_conversation_summary_task
        update_conversation_summary_task.delay(conversation.id)
        
        # 6. Return both the user message (to confirm save) and AI message
        return Response({
            "user_message": MessageSerializer(user_msg).data,
            "ai_response": MessageSerializer(ai_msg).data,
            "danger_detected": urgency > 0.7
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def voice(self, request, pk=None):
        conversation = self.get_object()
        audio_file = request.FILES.get('audio')
        
        if not audio_file:
            return Response({"detail": "Le fichier audio est requis."}, status=status.HTTP_400_BAD_REQUEST)

        transcription = SpeechService.transcribe_audio_file(audio_file)
        if not transcription:
            return Response(
                {"detail": "Impossible de transcrire l'audio. Veuillez reessayer avec un enregistrement plus clair."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_msg = Message.objects.create(
            conversation=conversation,
            is_user=True,
            content=f"[Vocal] {transcription}"
        )
        
        history = list(conversation.messages.exclude(id=user_msg.id).order_by('created_at')[:20])
        ai_response_text, urgency = AIService.get_chat_response(conversation, history, transcription)
        
        ai_msg = Message.objects.create(
            conversation=conversation,
            is_user=False,
            content=ai_response_text,
            urgency_level=urgency
        )
        
        from .tasks import update_conversation_summary_task
        update_conversation_summary_task.delay(conversation.id)
        
        return Response({
            "transcription": transcription,
            "ai_response": MessageSerializer(ai_msg).data,
            "danger_detected": urgency > 0.7
        }, status=status.HTTP_201_CREATED)
