import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

from .models import Conversation, Message
from .ai_service import AIService

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if not user or user.is_anonymous:
            await self.close(code=4401)
            return

        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        self.user = user

        self.conversation = await self.get_user_conversation()
        if not self.conversation:
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"WebSocket Connected: {self.room_group_name}")

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({'detail': 'Invalid JSON payload.'}))
            return

        message_content = text_data_json.get('message', '')
        
        if not message_content:
            return

        # 1. Save User Message
        user_msg = await self.save_message(is_user=True, content=message_content)

        # Broadcast user message to group (in case of multiple device sync or counselor is present)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_content,
                'is_user': True,
                'danger_detected': False
            }
        )

        # 2. Get AI Response
        ai_response_text, urgency = await self.get_ai_response(
            new_message=message_content,
            exclude_message_id=str(user_msg.id)
        )
        danger = urgency > 0.7

        # 3. Save AI Message
        ai_msg = await self.save_message(is_user=False, content=ai_response_text, urgency_level=urgency)

        # Broadcast AI message to group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': ai_response_text,
                'is_user': False,
                'danger_detected': danger
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        is_user = event['is_user']
        danger_detected = event.get('danger_detected', False)

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'is_user': is_user,
            'danger_detected': danger_detected
        }))

    @sync_to_async
    def save_message(self, is_user, content, urgency_level=0.0):
        return Message.objects.create(
            conversation=self.conversation,
            is_user=is_user,
            content=content,
            urgency_level=urgency_level
        )
        
    @sync_to_async
    def get_ai_response(self, new_message, exclude_message_id=None):
        # Retrieve a bounded conversation context with both user and AI turns.
        history_qs = self.conversation.messages.order_by('created_at')
        if exclude_message_id:
            history_qs = history_qs.exclude(id=exclude_message_id)
        history = list(history_qs[:20])
        return AIService.get_chat_response(self.conversation, history, new_message)

    @sync_to_async
    def get_user_conversation(self):
        try:
            return Conversation.objects.get(id=self.conversation_id, user=self.user)
        except Conversation.DoesNotExist:
            return None
