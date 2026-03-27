from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase
from chat.models import Conversation, Message

User = get_user_model()


class ChatApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='chat-user', password='StrongPass123')
        self.client.force_authenticate(user=self.user)
        self.conversation = Conversation.objects.create(user=self.user, title='Test')

    def test_send_message_uses_full_history_not_only_user_messages(self):
        Message.objects.create(conversation=self.conversation, is_user=True, content='Message utilisateur')
        Message.objects.create(conversation=self.conversation, is_user=False, content='Reponse IA')

        with patch('chat.views.AIService.get_chat_response', return_value=('Nouvelle reponse', 0.1)) as mocked_ai:
            response = self.client.post(
                f'/api/chat/conversations/{self.conversation.id}/send_message/',
                {'content': 'Nouveau message'},
                format='json'
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('ai_response', response.data)

        history = list(mocked_ai.call_args.args[1])
        self.assertGreaterEqual(len(history), 2)
        self.assertTrue(any(not msg.is_user for msg in history))
        self.assertNotEqual(history[-1].content, 'Nouveau message')

    @patch('chat.views.SpeechService.transcribe_audio_file', return_value='Je suis en danger')
    @patch('chat.views.AIService.get_chat_response', return_value=('Restez en securite', 0.8))
    def test_voice_endpoint_transcribes_and_returns_ai_response(self, mocked_ai, mocked_speech):
        fake_audio = SimpleUploadedFile('voice.webm', b'fake-audio', content_type='audio/webm')

        response = self.client.post(
            f'/api/chat/conversations/{self.conversation.id}/voice/',
            {'audio': fake_audio},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['transcription'], 'Je suis en danger')
        self.assertTrue(response.data['danger_detected'])
        mocked_speech.assert_called_once()
        mocked_ai.assert_called_once()
