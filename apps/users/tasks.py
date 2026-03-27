from celery import shared_task
from django.utils import timezone
from .models import Profile
from sos.models import SOSAlert
from chat.models import Message

@shared_task
def calculate_risk_scores_task():
    """
    Task to calculate and update the risk score for all victim profiles.
    Factors:
    - Recent SOS alerts (+0.4 each)
    - High urgency messages in chat (+0.2 each)
    """
    profiles = Profile.objects.filter(role='victim')
    
    for profile in profiles:
        user = profile.user
        score = 0.0
        
        # 1. Check SOS alerts in the last 30 days
        recent_sos_count = SOSAlert.objects.filter(
            user=user, 
            created_at__gte=timezone.now() - timezone.timedelta(days=30)
        ).count()
        score += (recent_sos_count * 0.4)
        
        # 2. Check high urgency messages in recent chat history
        recent_urgent_msgs = Message.objects.filter(
            conversation__user=user,
            is_user=True,
            created_at__gte=timezone.now() - timezone.timedelta(days=7),
            urgency_level__gte=0.7
        ).count()
        score += (recent_urgent_msgs * 0.2)
        
        # Cap score at 1.0
        final_score = min(score, 1.0)
        
        profile.risk_score = final_score
        profile.last_risk_assessment = timezone.now()
        profile.save(update_fields=['risk_score', 'last_risk_assessment'])
