from django.contrib import admin
from django.utils.html import format_html
from .models import SOSAlert, EmergencyContact, LocationUpdate

class LocationUpdateInline(admin.TabularInline):
    model = LocationUpdate
    extra = 0
    readonly_fields = ['timestamp', 'latitude', 'longitude', 'is_indoor', 'cell_tower_id']
    can_delete = False

@admin.register(SOSAlert)
class SOSAlertAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'created_at', 'resolved_at', 'public_tracking_link')
    list_filter = ('status', 'sms_fallback_sent', 'created_at')
    search_fields = ('user__username', 'user__phone_number', 'id')
    readonly_fields = ('id', 'public_tracking_link', 'audio_evidence_player')
    inlines = [LocationUpdateInline]
    
    def public_tracking_link(self, obj):
        if obj.public_tracking_token:
            url = f"/track/{obj.id}/{obj.public_tracking_token}/"
            return format_html('<a href="{}" target="_blank">Lien de Suivi</a>', url)
        return "Non généré"
    public_tracking_link.short_description = "Suivi Public"
    
    def audio_evidence_player(self, obj):
        if obj.audio_evidence:
            return format_html('<audio controls><source src="{}" type="{}"></audio>', obj.audio_evidence.url, obj.audio_mime_type or "audio/mpeg")
        return "Aucun audio"
    audio_evidence_player.short_description = "Preuve Audio"

@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'phone_number', 'relationship', 'auto_call_enabled')
    list_filter = ('auto_call_enabled',)
    search_fields = ('name', 'user__username', 'phone_number')
