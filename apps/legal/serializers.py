from rest_framework import serializers
from .models import Lawyer, LegalCase, LegalCaseEvent


class LawyerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lawyer
        fields = '__all__'


class LegalCaseSerializer(serializers.ModelSerializer):
    lawyer_name = serializers.CharField(source='assigned_lawyer.name', read_only=True, default=None)
    events = serializers.SerializerMethodField()

    class Meta:
        model = LegalCase
        fields = '__all__'
        read_only_fields = ('user', 'assigned_lawyer', 'created_at', 'updated_at', 'status_changed_at', 'events')

    def get_events(self, obj):
        return LegalCaseEventSerializer(obj.events.all()[:20], many=True).data


class LegalCaseEventSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source='actor.username', read_only=True)

    class Meta:
        model = LegalCaseEvent
        fields = '__all__'
        read_only_fields = ('id', 'legal_case', 'actor', 'created_at')
