from celery import shared_task
from .models import Conversation
from .ai_service import AIService

@shared_task
def update_conversation_summary_task(conversation_id):
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        messages = conversation.messages.order_by('created_at')
        if messages.count() > 5:
            new_summary = AIService.generate_summary(list(messages))
            if new_summary:
                conversation.context_summary = new_summary
                conversation.save(update_fields=['context_summary'])
    except Exception as e:
        print(f"Error in summary task: {e}")
