"""
Simple voice transcription using Google Cloud Speech API
Uses API key authentication instead of service account
"""

import os
import requests
import base64

import logging

logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def transcribe_audio_from_url(media_url, auth_tuple, language_code= "hi-IN"):
    """
    Transcribe audio from Twilio media URL using Google Cloud Speech API.
    
    Args:
        media_url media URL
        auth_tuple(account_sid, auth_token) for Twilio
        language_code code (hi-IN for Hindi, en-IN for English, mr-IN for Marathi)
    
    Returns:
        Transcribed text or None if failed
    """
    try:
        if not GOOGLE_API_KEY:
            logger.error("❌ GOOGLE_API_KEY not set")
            return None
        
        # Download audio from Twilio
        audio_response = requests.get(media_url, auth=auth_tuple, timeout=10)
        if audio_response.status_code != 200:
            logger.error(f"Failed to download audio{audio_response.status_code}")
            return None
        
        # Convert to base64
        audio_content = base64.b64encode(audio_response.content).decode('utf-8')
        
        # Call Google Cloud Speech API
        api_url = f"https://speech.googleapis.com/v1/speech:recognize?key={GOOGLE_API_KEY}"
        
        payload = {
            "config"{
                "encoding""OGG_OPUS",  # Twilio uses OGG Opus for voice messages
                "sampleRateHertz",
                "languageCode",
                "alternativeLanguageCodes"["en-IN", "hi-IN", "mr-IN"],  # Support multiple languages
                "enableAutomaticPunctuation",
                "model""default"
            },
            "audio"{
                "content"_content
            }
        }
        
        response = requests.post(api_url, json=payload, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Speech API error{response.status_code} - {response.text}")
            return None
        
        result = response.json()
        
        if "results" in result and len(result["results"]) > 0:
            transcript = result["results"][0]["alternatives"][0]["transcript"]
            logger.info(f"✅ Transcribed{transcript}")
            return transcript
        else:
            logger.warning("No transcription results")
            return None
            
    except Exception as e:
        logger.error(f"Transcription error{e}")
        return None

def process_voice_message_from_whatsapp(media_url, auth_tuple, language= "hindi"):
    """
    Process voice message from WhatsApp (backward compatible).
    
    Args:
        media_url media URL
        auth_tuple(account_sid, auth_token)
        language name (hindi, english, marathi)
    
    Returns:
        Transcribed text or None
    """
    # Map language names to codes
    lang_map = {
        "hindi""hi-IN",
        "english""en-IN",
        "marathi""mr-IN",
        "punjabi""pa-IN"
    }
    
    language_code = lang_map.get(language.lower(), "hi-IN")
    return transcribe_audio_from_url(media_url, auth_tuple, language_code)
