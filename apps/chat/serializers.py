from rest_framework import serializers
from .models import Conversation, Message

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'is_user', 'content', 'sentiment_score', 'urgency_level', 'audio_url', 'is_offline', 'created_at']
        read_only_fields = ['id', 'sentiment_score', 'urgency_level', 'created_at']

class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Conversation
        fields = ['id', 'title', 'is_active', 'created_at', 'updated_at', 'messages']
        read_only_fields = ['id', 'created_at', 'updated_at']
        
class ConversationListSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'title', 'is_active', 'updated_at', 'last_message']
        
    def get_last_message(self, obj):
        msg = obj.messages.order_by('-created_at').first()
        return MessageSerializer(msg).data if msg else None
