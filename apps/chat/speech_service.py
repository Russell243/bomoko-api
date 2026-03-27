import os
import tempfile
import logging

import speech_recognition as sr
from pydub import AudioSegment

logger = logging.getLogger(__name__)


class SpeechService:
    @staticmethod
    def transcribe_audio_file(uploaded_file) -> str:
        suffix = os.path.splitext(uploaded_file.name or '')[1] or '.webm'
        temp_input_path = None
        temp_wav_path = None

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_input:
                for chunk in uploaded_file.chunks():
                    temp_input.write(chunk)
                temp_input_path = temp_input.name

            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_wav:
                temp_wav_path = temp_wav.name

            audio = AudioSegment.from_file(temp_input_path)
            audio = audio.set_channels(1).set_frame_rate(16000)
            audio.export(temp_wav_path, format='wav')

            recognizer = sr.Recognizer()
            with sr.AudioFile(temp_wav_path) as source:
                audio_data = recognizer.record(source)

            text = recognizer.recognize_google(audio_data, language='fr-FR')
            return text.strip() if text else ''
        except sr.UnknownValueError:
            return ''
        except Exception as exc:
            logger.error("Speech transcription failed: %s", exc)
            return ''
        finally:
            for path in (temp_input_path, temp_wav_path):
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass

