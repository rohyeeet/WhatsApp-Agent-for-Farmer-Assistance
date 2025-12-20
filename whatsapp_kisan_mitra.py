"""
WhatsApp Kisan Mitra Server - Twilio Integration
Updated for Multi-User Memory, Bi-directional Voice & Stability
"""

import asyncio
import logging
import os
import requests
import base64
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import Response
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Voice processing imports
from tools.voice_processing_tool import (
    process_voice_message_from_whatsapp,
    create_voice_response_for_farmer,
    process_voice_message_smart
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="WhatsApp Kisan Mitra", version="2.1.0")

# Configuration
ADK_API_URL = "http://localhost:8001"
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

@app.on_event("startup")
async def startup_event():
    logger.info("📱 Starting WhatsApp Kisan Mitra Server (v2.1)...")
    logger.info(f"🔗 ADK API URL: {ADK_API_URL}")

@app.get("/")
async def root():
    return {"message": "WhatsApp Kisan Mitra Server v2.1 Running", "status": "healthy"}

class ServiceBusyError(Exception):
    pass

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(ServiceBusyError),
    reraise=True
)
def _send_to_adk_with_retry(payload):
    """Semds request to ADK with auto-retry for 429/500 errors."""
    try:
        response = requests.post(f"{ADK_API_URL}/run", json=payload, timeout=45)
        
        # Check for 429 specifically (Resource Exhausted)
        if response.status_code == 429:
             logger.warning("⚠️ ADK Rate Limited (429). Retrying...")
             raise ServiceBusyError("Rate limit exceeded")
             
        # Check for 500s that might be transient
        if response.status_code >= 500:
            logger.warning(f"⚠️ ADK Server Error ({response.status_code}). Retrying...")
            raise ServiceBusyError(f"Server error: {response.text}")
            
        return response
    except requests.exceptions.RequestException as e:
        # Network errors should also retry
        logger.warning(f"⚠️ Connection Error: {e}. Retrying...")
        raise ServiceBusyError(f"Connection failed: {e}")

async def call_adk_api(message: str, phone_number: str, image_data: str = None, image_mime_type: str = None, is_voice: bool = False):
    """Call the ADK API server with user context injection and robust error handling."""
    try:
        app_name = "kisan_mitra"
        user_id = phone_number  # Phone number IS the user_id
        
        # Create user session (this is fast, usually doesn't need heavy retry)
        try:
            session_response = requests.post(
                f"{ADK_API_URL}/apps/{app_name}/users/{user_id}/sessions",
                json={}, timeout=5
            )
        except Exception as e:
            logger.error(f"Session creation failed: {e}")
            return "तकनीकी समस्या: संपर्क स्थापित नहीं हो सका (Session Error)।"
        
        if session_response.status_code not in [200, 201]:
            # Usually means app not found or server down
            logger.error(f"Session creation error: {session_response.text}")
            return "तकनीकी समस्या: सर्वर व्यस्त है। कृपया 1 मिनट बाद प्रयास करें।"
        
        session_id = session_response.json().get("id")
        
        # INJECT SYSTEM CONTEXT into the message so the model knows the user_id
        system_context = f"[SYSTEM: Current User ID is '{user_id}'. Voice Input: {is_voice}.]"
        full_message_text = f"{system_context}\n{message}"
        
        payload = {
            "appName": app_name,
            "userId": user_id,
            "sessionId": session_id,
            "newMessage": {
                "role": "user",
                "parts": [{"text": full_message_text}]
            }
        }
        
        if image_data and image_mime_type:
            payload["newMessage"]["parts"].append({
                "inlineData": {
                    "mimeType": image_mime_type,
                    "data": image_data
                }
            })
            payload["newMessage"]["parts"][0]["text"] += "\n\n[USER SENT AN IMAGE]"

        logger.info(f"🔄 Calls ADK for {user_id}: {message[:50]}...")
        
        # Execute run with RETRY logic
        try:
            response = _send_to_adk_with_retry(payload)
        except ServiceBusyError:
            return "सेवा अभी अत्यधिक व्यस्त है (High Traffic). कृपया 30 सेकंड बाद पुनः प्रयास करें। (Error: 429/503)"
        
        if response.status_code == 200:
            result = response.json()
            # Simple recursive search for text
            def extract_text(data):
                if isinstance(data, dict):
                    if "text" in data and data["text"]: return data["text"]
                    for k, v in data.items():
                        res = extract_text(v)
                        if res: return res
                elif isinstance(data, list):
                    for item in reversed(data): # Reverse to get latest
                        res = extract_text(item)
                        if res: return res
                return None

            found_text = extract_text(result)
            if found_text:
                return found_text
            
            return "सर्वर ने उत्तर भेजा, लेकिन वह स्पष्ट नहीं है।"
        else:
            logger.error(f"ADK Error (Non-Retryable): {response.text}")
            return "तकनीकी समस्या: सर्वर से सही जवाब नहीं मिला।"

    except Exception as e:
        logger.error(f"Call ADK Failed (Fatal): {e}")
        return "तकनीकी समस्या के कारण संपर्क नहीं हो पा रहा है।"

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(None),
    NumMedia: str = Form("0"),
    MediaUrl0: str = Form(None),
    MediaContentType0: str = Form(None)
):
    """Handle incoming WhatsApp messages"""
    phone_number = From.replace("whatsapp:", "")
    logger.info(f"📨 Msg from {phone_number}")
    
    response_text = ""
    is_voice = False
    
    # 1. Handle Voice/Media
    if int(NumMedia) > 0 and MediaContentType0:
        if "audio" in MediaContentType0 or "voice" in MediaContentType0:
            logger.info("🎤 Voice message detected")
            is_voice = True
            auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            # Transcribe
            transcript = process_voice_message_from_whatsapp(MediaUrl0, auth)
            if transcript:
                Body = transcript 
                logger.info(f"📝 Transcript: {Body}")
            else:
                Body = "Voice message received but transcription failed."
        elif "image" in MediaContentType0:
            logger.info("📸 Image message detected")
            pass

    if not Body and int(NumMedia) == 0:
        logger.warning("Empty message received")
        return Response(content="<?xml version='1.0' encoding='UTF-8'?><Response></Response>", media_type="application/xml")

    # 2. Get Response from Agent
    image_data = None
    if int(NumMedia) > 0 and "image" in MediaContentType0 and MediaUrl0:
         try:
            auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            img_resp = requests.get(MediaUrl0, auth=auth)
            if img_resp.status_code == 200:
                image_data = base64.b64encode(img_resp.content).decode('utf-8')
         except Exception as e:
             logger.error(f"Image download failed: {e}")

    agent_response = await call_adk_api(
        message=Body or "Image sent", 
        phone_number=phone_number,
        image_data=image_data,
        image_mime_type=MediaContentType0,
        is_voice=is_voice
    )
    
    # 3. Handle Voice Response (if input was voice)
    final_twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{agent_response}</Message>
</Response>"""

    return Response(content=final_twiml, media_type="application/xml")