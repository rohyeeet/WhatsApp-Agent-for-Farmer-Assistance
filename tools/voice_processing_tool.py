"""
Voice Processing for Kisan Mitra WhatsApp

STT priority:  ElevenLabs Scribe v1  →  Google Cloud Speech  →  Gemini multimodal
TTS priority:  ElevenLabs Multilingual v2  →  gTTS (free fallback)
"""
import os
import io
import time
import base64
import logging
import requests

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Language maps
# ─────────────────────────────────────────────

# internal name  →  BCP-47 code (Google / Gemini)
LANGUAGE_CODES = {
    'hindi': 'hi-IN', 'english': 'en-IN', 'punjabi': 'pa-IN',
    'bengali': 'bn-IN', 'tamil': 'ta-IN', 'telugu': 'te-IN',
    'marathi': 'mr-IN', 'gujarati': 'gu-IN', 'kannada': 'kn-IN',
    'malayalam': 'ml-IN', 'odia': 'or-IN', 'assamese': 'as-IN', 'urdu': 'ur-IN',
}

# internal name  →  ISO 639-3 (ElevenLabs Scribe)
ELEVENLABS_STT_LANG = {
    'hindi': 'hin', 'english': 'eng', 'punjabi': 'pan',
    'bengali': 'ben', 'tamil': 'tam', 'telugu': 'tel',
    'marathi': 'mar', 'gujarati': 'guj', 'kannada': 'kan',
    'malayalam': 'mal', 'odia': 'ori', 'assamese': 'asm', 'urdu': 'urd',
}

# BCP-47  →  gTTS lang code
GTTS_LANG_MAP = {
    'hi-IN': 'hi', 'en-IN': 'en', 'pa-IN': 'pa', 'bn-IN': 'bn',
    'ta-IN': 'ta', 'te-IN': 'te', 'mr-IN': 'mr', 'gu-IN': 'gu',
    'kn-IN': 'kn', 'ml-IN': 'ml', 'or-IN': 'or', 'ur-IN': 'ur',
}

LANG_NAMES = {
    'hindi': 'Hindi', 'english': 'English', 'punjabi': 'Punjabi',
    'bengali': 'Bengali', 'tamil': 'Tamil', 'telugu': 'Telugu',
    'marathi': 'Marathi', 'gujarati': 'Gujarati', 'kannada': 'Kannada',
    'malayalam': 'Malayalam', 'odia': 'Odia', 'urdu': 'Urdu',
}

# ElevenLabs voice IDs — multilingual model handles all Indian languages
ELEVENLABS_VOICE_ID = 'EXAVITQu4vr4xnSDxMaL'   # Sarah — clear, neutral, works well for Hindi


def _get_language_code(farmer_language: str) -> str:
    return LANGUAGE_CODES.get(farmer_language.lower(), 'hi-IN')


# ─────────────────────────────────────────────
# Client init (runs once at module load)
# ─────────────────────────────────────────────
_elevenlabs_key = None
_genai_client   = None
_speech_client  = None


def _init_clients():
    global _elevenlabs_key, _genai_client, _speech_client

    _elevenlabs_key = os.getenv('ELEVENLABS_API_KEY')
    if _elevenlabs_key:
        logger.info('✅ ElevenLabs API key loaded (STT + TTS)')
    else:
        logger.warning('⚠️ ELEVENLABS_API_KEY not set — will use gTTS fallback for TTS and Gemini for STT')

    api_key = os.getenv('GOOGLE_API_KEY')
    if api_key:
        try:
            from google import genai as google_genai
            _genai_client = google_genai.Client(api_key=api_key)
            logger.info('✅ Gemini client ready (STT fallback)')
        except Exception as e:
            logger.error(f'❌ Gemini init failed: {e}')

    try:
        from google.cloud import speech
        _speech_client = speech.SpeechClient()
        logger.info('✅ Google Cloud Speech ready')
    except Exception as e:
        logger.warning(f'⚠️ Google Cloud Speech unavailable: {e}')


_init_clients()


# ─────────────────────────────────────────────
# STT helpers
# ─────────────────────────────────────────────

def _download_audio(media_url: str, auth_tuple: tuple) -> bytes:
    """Download voice audio from Twilio. Single attempt — media is ready immediately."""
    try:
        resp = requests.get(
            media_url, auth=auth_tuple, timeout=20,
            headers={'User-Agent': 'KisanMitra/1.0', 'Accept': 'audio/*,*/*'}
        )
        if resp.status_code == 200 and resp.content:
            logger.info(f'📥 Audio downloaded: {len(resp.content)} bytes')
            return resp.content
        logger.error(f'❌ Audio download HTTP {resp.status_code}')
    except Exception as e:
        logger.error(f'❌ Audio download error: {e}')
    return None


def _stt_elevenlabs(audio_data: bytes, farmer_language: str) -> str:
    """
    ElevenLabs Scribe v1 — primary STT.
    Accepts OGG/MP3/WAV, excellent Indian language accuracy.
    """
    if not _elevenlabs_key:
        return None
    lang_code = ELEVENLABS_STT_LANG.get(farmer_language.lower(), 'hin')
    try:
        resp = requests.post(
            'https://api.elevenlabs.io/v1/speech-to-text',
            headers={'xi-api-key': _elevenlabs_key},
            files={'file': ('voice.ogg', audio_data, 'audio/ogg; codecs=opus')},
            data={'model_id': 'scribe_v1', 'language_code': lang_code},
            timeout=15
        )
        if resp.status_code == 200:
            result = resp.json()
            transcript = result.get('text', '').strip()
            if transcript:
                lang_prob = result.get('language_probability', 0)
                logger.info(f'✅ ElevenLabs STT: "{transcript[:80]}" (lang_prob={lang_prob:.2f})')
                return transcript
            logger.warning('ElevenLabs STT returned empty transcript')
        else:
            logger.error(f'❌ ElevenLabs STT error {resp.status_code}: {resp.text[:200]}')
    except Exception as e:
        logger.error(f'❌ ElevenLabs STT exception: {e}')
    return None


def _stt_google_cloud(audio_data: bytes, language_code: str) -> str:
    """Google Cloud Speech — secondary STT (requires ADC credentials)."""
    if not _speech_client:
        return None
    from google.cloud import speech
    configs = [
        (speech.RecognitionConfig.AudioEncoding.OGG_OPUS, 16000),
        (speech.RecognitionConfig.AudioEncoding.WEBM_OPUS, 48000),
    ]
    audio = speech.RecognitionAudio(content=audio_data)
    for encoding, rate in configs:
        try:
            config = speech.RecognitionConfig(
                encoding=encoding, sample_rate_hertz=rate,
                language_code=language_code,
                enable_automatic_punctuation=True,
                model='latest_short', use_enhanced=True,
                alternative_language_codes=(
                    ['en-IN', 'hi-IN'] if language_code not in ['en-IN', 'hi-IN'] else []
                )
            )
            result = _speech_client.recognize(config=config, audio=audio)
            if result.results:
                alt = result.results[0].alternatives[0]
                if alt.confidence > 0.3:
                    logger.info(f'✅ Google Speech: "{alt.transcript[:60]}" (conf={alt.confidence:.2f})')
                    return alt.transcript
        except Exception as e:
            logger.warning(f'Google Speech config failed: {e}')
    return None


def _stt_gemini(audio_data: bytes, farmer_language: str) -> str:
    """Gemini multimodal — tertiary STT fallback (no extra credentials needed)."""
    if not _genai_client:
        return None
    lang_name = LANG_NAMES.get(farmer_language.lower(), 'Hindi')
    audio_b64 = base64.b64encode(audio_data).decode('utf-8')
    contents = [{
        'parts': [
            {'inline_data': {'mime_type': 'audio/ogg; codecs=opus', 'data': audio_b64}},
            {'text': (
                f'Transcribe this WhatsApp voice message exactly as spoken. '
                f'The farmer likely speaks {lang_name} or Hinglish. '
                f'Return ONLY the transcribed words — no explanation, no prefix.'
            )}
        ]
    }]
    for attempt in range(3):
        try:
            resp = _genai_client.models.generate_content(
                model='gemini-2.0-flash', contents=contents
            )
            transcript = resp.text.strip()
            logger.info(f'✅ Gemini STT: "{transcript[:80]}"')
            return transcript
        except Exception as e:
            if '503' in str(e) and attempt < 2:
                logger.warning(f'Gemini 503, retry {attempt+1}/3...')
                time.sleep(2)
            else:
                logger.error(f'❌ Gemini STT failed: {e}')
                return None
    return None


def transcribe_whatsapp_voice(media_url: str, auth_tuple: tuple, farmer_language: str = 'hindi') -> str:
    """
    Download and transcribe a WhatsApp OGG voice message.
    Priority: ElevenLabs Scribe → Google Cloud Speech → Gemini
    """
    audio_data = _download_audio(media_url, auth_tuple)
    if not audio_data:
        return None

    # 1. ElevenLabs Scribe (best quality, supports all Indian languages)
    transcript = _stt_elevenlabs(audio_data, farmer_language)
    if transcript:
        return transcript

    # 2. Google Cloud Speech
    language_code = _get_language_code(farmer_language)
    transcript = _stt_google_cloud(audio_data, language_code)
    if transcript:
        return transcript

    # 3. Gemini multimodal (always available with GOOGLE_API_KEY)
    logger.info('🤖 Using Gemini STT fallback...')
    return _stt_gemini(audio_data, farmer_language)


# ─────────────────────────────────────────────
# TTS helpers
# ─────────────────────────────────────────────

def _tts_elevenlabs(text: str, language_code: str) -> bytes:
    """ElevenLabs Multilingual v2 TTS — primary, high quality for Indian languages."""
    if not _elevenlabs_key:
        return None
    # Trim to 500 chars for speed (Twilio WhatsApp voice notes are short)
    text = text[:500]
    try:
        resp = requests.post(
            f'https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}',
            headers={
                'xi-api-key': _elevenlabs_key,
                'Accept': 'audio/mpeg',
                'Content-Type': 'application/json'
            },
            json={
                'text': text,
                'model_id': 'eleven_multilingual_v2',
                'voice_settings': {
                    'stability': 0.4,
                    'similarity_boost': 0.8,
                    'style': 0.2,
                    'use_speaker_boost': True
                }
            },
            timeout=25
        )
        if resp.status_code == 200:
            logger.info(f'✅ ElevenLabs TTS: {len(resp.content)} bytes')
            return resp.content
        logger.error(f'❌ ElevenLabs TTS error {resp.status_code}: {resp.text[:200]}')
    except Exception as e:
        logger.error(f'❌ ElevenLabs TTS exception: {e}')
    return None


def _tts_gtts(text: str, language_code: str) -> bytes:
    """gTTS — free fallback TTS."""
    try:
        from gtts import gTTS
        lang = GTTS_LANG_MAP.get(language_code, 'hi')
        tts = gTTS(text=text[:500], lang=lang, slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        audio = buf.read()
        logger.info(f'✅ gTTS: {len(audio)} bytes (lang={lang})')
        return audio
    except Exception as e:
        logger.error(f'❌ gTTS error: {e}')
        return None


def generate_voice_audio(text: str, farmer_language: str = 'hindi') -> bytes:
    """
    Main TTS entry point. Returns raw MP3 bytes.
    Priority: ElevenLabs Multilingual v2 → gTTS
    """
    language_code = _get_language_code(farmer_language)

    audio = _tts_elevenlabs(text, language_code)
    if audio:
        return audio

    logger.info('🔊 ElevenLabs unavailable, using gTTS fallback...')
    return _tts_gtts(text, language_code)


# ─────────────────────────────────────────────
# Backward-compatible wrappers
# ─────────────────────────────────────────────

def process_voice_message_from_whatsapp(media_url, auth_tuple, farmer_language='hindi'):
    return transcribe_whatsapp_voice(media_url, auth_tuple, farmer_language)

def process_voice_message_from_whatsapp_enhanced(media_url, auth_tuple, farmer_language='hindi'):
    return transcribe_whatsapp_voice(media_url, auth_tuple, farmer_language)

def create_voice_response_for_farmer_enhanced(text, farmer_language='hindi', farmer_context=None):
    audio_bytes = generate_voice_audio(text, farmer_language)
    if audio_bytes:
        return base64.b64encode(audio_bytes).decode('utf-8')
    return None

def create_voice_response_for_farmer(text, farmer_language='hindi', farmer_context=None):
    return create_voice_response_for_farmer_enhanced(text, farmer_language, farmer_context)

def process_voice_message_from_web(audio_base64, farmer_language='hindi'):
    if not _speech_client:
        return None
    try:
        from google.cloud import speech
        audio_data = base64.b64decode(audio_base64)
        language_code = _get_language_code(farmer_language)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            sample_rate_hertz=48000, language_code=language_code,
            enable_automatic_punctuation=True, model='latest_short', use_enhanced=True
        )
        result = _speech_client.recognize(
            config=config, audio=speech.RecognitionAudio(content=audio_data)
        )
        if result.results:
            return result.results[0].alternatives[0].transcript
    except Exception as e:
        logger.error(f'❌ Web speech recognition: {e}')
    return None

def check_voice_service_status():
    return {
        'stt': {
            'elevenlabs_scribe': 'active ✅' if _elevenlabs_key else 'not configured',
            'google_cloud_speech': 'active ✅' if _speech_client else 'unavailable (no ADC credentials)',
            'gemini_fallback': 'active ✅' if _genai_client else 'unavailable',
        },
        'tts': {
            'elevenlabs_multilingual_v2': 'active ✅' if _elevenlabs_key else 'not configured',
            'gtts_fallback': 'active ✅',
        }
    }

def process_voice_input(audio_data: str, source: str = 'web', farmer_language: str = 'hindi'):
    return {'success': False, 'error': 'Handled by WhatsApp gateway', 'transcript': None}

def generate_voice_response(text: str, farmer_language: str = 'hindi'):
    audio_b64 = create_voice_response_for_farmer_enhanced(text, farmer_language)
    if audio_b64:
        return {'success': True, 'audio_data': audio_b64, 'format': 'mp3', 'encoding': 'base64'}
    return {'success': False, 'error': 'TTS failed', 'audio_data': None}


# Shim for old code that references enhanced_voice_processor directly
class _Shim:
    def detect_language_from_context(self, farmer_language='hindi'):
        return _get_language_code(farmer_language)
    def text_to_speech_elevenlabs(self, text, language_code='hi-IN'):
        return _tts_elevenlabs(text, language_code)
    def transcribe_with_gemini(self, audio_data, farmer_language='hindi'):
        return _stt_gemini(audio_data, farmer_language)
    @property
    def speech_client(self): return _speech_client
    @property
    def elevenlabs_api_key(self): return _elevenlabs_key
    @property
    def _genai_client(self): return _genai_client

enhanced_voice_processor = _Shim()
