"""
SMS fallback service for SOS alerts.
Uses Twilio when configured; otherwise logs mock sends.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from twilio.rest import Client as TwilioClient
    HAS_TWILIO = True
except ImportError:
    HAS_TWILIO = False

try:
    import africastalking
    HAS_AT = True
except ImportError:
    HAS_AT = False


class SMSService:
    """Service to send SMS notifications for SOS alerts."""

    SMS_TEMPLATE = (
        "ALERTE URGENCE - BOMOKO\n"
        "{name} a besoin d'aide immediate !\n"
        "Position: https://maps.google.com/?q={lat},{lng}\n"
        "Suivi: {tracking_url}\n"
        "{time}"
    )

    SMS_RESOLVED_TEMPLATE = (
        "ALERTE TERMINEE - BOMOKO\n"
        "{name} a indique que la situation est securisee.\n"
        "Alerte resolue a {time}."
    )

    @staticmethod
    def _mask_phone_number(phone_number):
        if not phone_number:
            return 'unknown'
        digits = str(phone_number)
        if len(digits) <= 4:
            return digits
        return f"{digits[:2]}***{digits[-2:]}"

    @classmethod
    def _send_at_sms(cls, to, message):
        """Send SMS via Africa's Talking."""
        username = getattr(settings, 'AFRICASTALKING_USERNAME', 'sandbox')
        api_key = getattr(settings, 'AFRICASTALKING_API_KEY', '')
        if not api_key:
            return False, "Africa's Talking API key not configured."
        
        try:
            africastalking.initialize(username, api_key)
            sms = africastalking.SMS
            response = sms.send(message, [to])
            # AT success response format contains recipient status
            recipients = response.get('SMSMessageData', {}).get('Recipients', [])
            if recipients and recipients[0].get('status') in ['Success', 'Sent']:
                return True, response
            return False, response
        except Exception as e:
            return False, str(e)

    @classmethod
    def _send_twilio_sms(cls, to, message):
        """Send SMS via Twilio."""
        sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', '')
        if not sid or not token or not from_number:
            return False, "Twilio credentials not configured."
        
        try:
            client = TwilioClient(sid, token)
            msg = client.messages.create(body=message, from_=from_number, to=to)
            return True, msg.sid
        except Exception as e:
            return False, str(e)

    @classmethod
    def send_sos_sms(cls, alert, require_location=False, allow_mock=True):
        """
        Send SOS SMS to all emergency contacts.
        If require_location is True, send only when coordinates exist.
        Returns number of SMS successfully sent.
        """
        user = alert.user
        contacts = user.emergency_contacts.all()

        if not contacts.exists():
            logger.info("No emergency contacts for user %s. SMS not sent.", user.id)
            return 0

        latest_location = alert.locations.order_by('-timestamp').first()
        lat = float(latest_location.latitude) if latest_location and latest_location.latitude is not None else None
        lng = float(latest_location.longitude) if latest_location and latest_location.longitude is not None else None

        if require_location and (lat is None or lng is None):
            logger.info("SOS Alert %s: location unavailable, SMS deferred.", alert.id)
            return 0

        from django.utils import timezone
        now = timezone.now().strftime("%d/%m/%Y %H:%M")
        username = user.get_full_name() or user.username or user.phone_number or 'Utilisateur'
        token = alert.ensure_tracking_token()
        tracking_base_url = getattr(settings, 'PUBLIC_TRACKING_BASE_URL', 'http://localhost:8000').rstrip('/')
        tracking_url = f"{tracking_base_url}/track/{alert.id}/{token}/"

        message_body = cls.SMS_TEMPLATE.format(
            name=username,
            lat=lat if lat is not None else 0,
            lng=lng if lng is not None else 0,
            tracking_url=tracking_url,
            time=now,
        )

        sent_count = 0
        at_api_key = getattr(settings, 'AFRICASTALKING_API_KEY', '')

        for contact in contacts:
            body = contact.sms_template or message_body
            success = False
            
            if HAS_AT and at_api_key:
                success, info = cls._send_at_sms(contact.phone_number, body)
                if success:
                    logger.info("SMS [Africa's Talking] sent to %s", cls._mask_phone_number(contact.phone_number))
                    sent_count += 1
                else:
                    logger.error("Failed [Africa's Talking] to %s: %s", cls._mask_phone_number(contact.phone_number), info)
            elif HAS_TWILIO:
                success, info = cls._send_twilio_sms(contact.phone_number, body)
                if success:
                    logger.info("SMS [Twilio] sent to %s: SID=%s", cls._mask_phone_number(contact.phone_number), info)
                    sent_count += 1
                else:
                    logger.error("Failed [Twilio] to %s: %s", cls._mask_phone_number(contact.phone_number), info)
            
            if not success and allow_mock:
                logger.info("[MOCK SMS] alert=%s contact=%s", alert.id, cls._mask_phone_number(contact.phone_number))
                sent_count += 1

        if sent_count > 0:
            alert.sms_fallback_sent = True
            alert.save(update_fields=['sms_fallback_sent'])

        return sent_count

    @classmethod
    def send_resolved_sms(cls, alert):
        user = alert.user
        contacts = user.emergency_contacts.all()

        from django.utils import timezone
        now = timezone.now().strftime("%d/%m/%Y %H:%M")
        username = user.get_full_name() or user.username or user.phone_number or 'Utilisateur'
        body = cls.SMS_RESOLVED_TEMPLATE.format(name=username, time=now)

        at_api_key = getattr(settings, 'AFRICASTALKING_API_KEY', '')

        for contact in contacts:
            success = False
            if HAS_AT and at_api_key:
                success, _ = cls._send_at_sms(contact.phone_number, body)
            elif HAS_TWILIO:
                success, _ = cls._send_twilio_sms(contact.phone_number, body)
            
            if not success:
                logger.info("[MOCK SMS RESOLVED] alert=%s contact=%s", alert.id, cls._mask_phone_number(contact.phone_number))
