import logging
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    logger.warning("google-genai package is not installed. AI features will be mocked.")

# Initialize Client inside the method or globally. 
# We'll use a global client if possible, but it requires the API key.
_client = None

def get_client():
    global _client
    if _client is None and HAS_GENAI and getattr(settings, 'GEMINI_API_KEY', None):
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client

class AIService:
    """Service to interact with Google Gemini AI for Bomoko"""
    
    SYSTEM_PROMPT = """Tu es Bomoko, un assistant IA virtuel bienveillant et expert en RDC. 
Ton rôle est d'aider les victimes de violences basées sur le genre (VBG), de fournir des conseils juridiques, médicaux et de santé, tout en restant empathique.

CONSIGNES IMPORTANTES :
1. Réponds toujours de manière structurée au format JSON.
2. Évalue l'urgence de la situation sur une échelle de 0.0 à 1.0.
3. Si l'urgence est supérieure à 0.7, recommande explicitement d'utiliser le bouton SOS.
4. Utilise le résumé de contexte fourni pour personnaliser tes réponses.

FORMAT DE RÉPONSE ATTENDU (JSON) :
{
  "text": "Ta réponse à l'utilisateur ici...",
  "urgency_score": 0.0 a 1.0,
  "sentiment": "positif/neutre/negatif",
  "recommended_action": "none/sos/medical/legal"
}
"""

    @classmethod
    def get_chat_response(cls, conversation, history_messages, new_message):
        """
        Takes the conversation object, history messages and the new user message,
        returns the text response from Gemini and a calculated urgency level.
        """
        if not HAS_GENAI:
            return "Mode hors-ligne ou bibliothèque IA non installée. Message reçu : " + new_message, 0.0
            
        if not getattr(settings, 'GEMINI_API_KEY', None):
            return "Configuration IA manquante. Veuillez renseigner GEMINI_API_KEY dans le backend.", 0.0
            
        try:
            client = get_client()
            if not client:
                return "Erreur d'initialisation de l'IA.", 0.0

            # Include context summary if available
            context_instruction = ""
            if conversation.context_summary:
                context_instruction = f"\n\nRÉSUMÉ DU CONTEXTE PRÉCÉDENT : {conversation.context_summary}"

            # Format history for the new SDK
            history = []
            for msg in history_messages[-20:]:  # Last 20 messages
                role = "user" if msg.is_user else "model"
                history.append(types.Content(role=role, parts=[types.Part(text=msg.content)]))
            
            # Request response with JSON constraint
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=history + [types.Content(role="user", parts=[types.Part(text=new_message)])],
                config=types.GenerateContentConfig(
                    system_instruction=cls.SYSTEM_PROMPT + context_instruction,
                    temperature=0.7,
                    response_mime_type="application/json",
                )
            )

            # Trigger summary update in background if it's been a while (e.g. every 5 messages)
            if len(history_messages) % 5 == 0:
                # In a real production app, use Celery: update_summary_task.delay(conversation.id)
                # For now, we'll provide the method and let the dev decide on the trigger.
                pass
            
            import json
            try:
                data = json.loads(response.text)
                response_text = data.get('text', "Désolé, j'ai eu un problème pour formater ma réponse.")
                urgency = data.get('urgency_score', 0.0)
            except json.JSONDecodeError:
                # Fallback if AI doesn't return valid JSON
                response_text = response.text
                urgency = 0.5 if "sos" in response_text.lower() else 0.0
                
            return response_text, urgency
            
        except Exception as e:
            logger.error(f"Gemini API Error: {str(e)}")
            return "Désolé, je rencontre une erreur de connexion avec le service IA. Si vous êtes en danger, utilisez le bouton SOS.", 0.9

    @classmethod
    def generate_summary(cls, history_messages):
        """Generates a concise summary of the conversation history"""
        if not HAS_GENAI or not get_client():
            return ""
            
        try:
            prompt = "Résume cette conversation de manière très concise (maximum 3 phrases) en soulignant les points clés (problème rencontré, état émotionnel, conseils déjà donnés) :"
            
            history = []
            for msg in history_messages:
                role = "user" if msg.is_user else "model"
                history.append(types.Content(role=role, parts=[types.Part(text=msg.content)]))
                
            response = get_client().models.generate_content(
                model='gemini-1.5-flash',
                contents=history + [types.Content(role="user", parts=[types.Part(text=prompt)])],
                config=types.GenerateContentConfig(temperature=0.3)
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return ""
