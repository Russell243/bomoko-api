from django.contrib import admin
from .models import Conversation, Message

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('is_user', 'content', 'created_at', 'urgency_level', 'sentiment_score')
    can_delete = False

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'user__username')
    readonly_fields = ('context_summary',)
    inlines = [MessageInline]
