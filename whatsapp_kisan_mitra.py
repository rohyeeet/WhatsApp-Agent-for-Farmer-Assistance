"""
WhatsApp Kisan Mitra Server - Twilio Integration
Updated for Multi-User Memory, Bi-directional Voice & Stability
"""
import asyncio
import logging
import os
import requests
import base64
import json
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import Response
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from tools.voice_processing_tool import process_voice_message_from_whatsapp, create_voice_response_for_farmer_enhanced
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(title='WhatsApp Kisan Mitra', version='2.1.0')
ADK_API_URL = 'http://localhost:8001'
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

@app.on_event('startup')
async def startup_event():
    logger.info('📱 Starting WhatsApp Kisan Mitra Server (v2.1)...')
    logger.info(f'🔗 ADK API URL: {ADK_API_URL}')

@app.get('/')
async def root():
    return {'message': 'WhatsApp Kisan Mitra Server v2.1 Running', 'status': 'healthy'}

class ServiceBusyError(Exception):
    pass

# Retry for up to 60s (Cold Start Protection)
@retry(stop=stop_after_attempt(15), wait=wait_exponential(multiplier=1, min=2, max=5), retry=retry_if_exception_type(ServiceBusyError), reraise=True)
def _send_to_adk_with_retry(payload, app_name, session_id):
    """Sends request to ADK with auto-retry for 429/500 errors."""
    try:
        run_url = f'{ADK_API_URL}/run'
        response = requests.post(run_url, json=payload, timeout=45)
        if response.status_code == 429:
            logger.warning('⚠️ ADK Rate Limited (429). Retrying...')
            raise ServiceBusyError('ADK is at capacity (Rate Limit). Please wait 30 seconds.')
        if response.status_code >= 500:
            logger.warning(f'⚠️ ADK Server Error ({response.status_code}). Retrying...')
            try:
                err_msg = response.json().get('detail', response.text)
            except:
                err_msg = response.text
            raise ServiceBusyError(f'ADK Server Error: {err_msg}')
        return response
    except requests.exceptions.RequestException as e:
        logger.warning(f'⚠️ Connection Error: {e}. Retrying...')
        raise ServiceBusyError(f'Connection failed: {e}')
import time
from fastapi.staticfiles import StaticFiles
os.makedirs('staticv2', exist_ok=True)
app.mount('/staticv2', StaticFiles(directory='staticv2'), name='staticv2')

async def call_adk_api(message, phone_number, image_data=None, image_mime_type=None, is_voice=False):
    """Call the ADK API server with user context injection and robust error handling."""
    try:
        app_name = 'kisan_mitra'
        user_id = phone_number
        from tools.memory_tools import get_active_session, set_active_session, get_farmer_profile, update_farmer_profile_field
        session_data = get_active_session(user_id)
        session_id = session_data.get('session_id')
        last_activity = session_data.get('last_activity')
        is_expired = False
        if last_activity:
            last_ts = datetime.fromisoformat(last_activity)
            diff = (datetime.utcnow() - last_ts).total_seconds()
            if diff > 3600:
                logger.info(f'⏳ Session {session_id} expired ({diff}s old) for {user_id}')
                is_expired = True
        if not session_id or is_expired:
            logger.info(f'🆕 Creating new session for {user_id}')
            try:
                session_response = requests.post(f'{ADK_API_URL}/apps/{app_name}/users/{user_id}/sessions', json={}, timeout=5)
                if session_response.status_code in [200, 201]:
                    session_id = session_response.json().get('id')
                    set_active_session(user_id, session_id)
                else:
                    logger.error(f'Session creation error: {session_response.text}')
                    return 'Technical Error: Server Busy. Please try again after 1 minute.'
            except Exception as e:
                logger.error(f'Session creation failed: {e}')
                return 'Technical Error: Connection failed (Session Error).'
        else:
            logger.info(f'♻️ Reusing session {session_id} for {user_id}')
            set_active_session(user_id, session_id)
        import re
        has_devanagari = bool(re.search('[\\u0900-\\u097F]', message))
        has_roman = bool(re.search('[a-zA-Z]', message))
        detected_language = 'hindi' if has_devanagari else 'english'
        current_profile = get_farmer_profile(user_id)
        saved_lang = current_profile.get('farmer_details', {}).get('preferences', {}).get('language', 'hindi')
        if detected_language != saved_lang and message.strip().lower() not in ['hi', 'hello', 'namaste']:
            logger.info(f'🌐 Updating language preference for {user_id} to {detected_language}')
            update_farmer_profile_field(user_id, 'farmer_details', 'preferences', {'language': detected_language}) # Pass dict for nested update or adjust logic
            # Actually, per memory_tools.py, it expects category, field, value
            # Let's verify memory_tools.py logic.
            # update_farmer_profile_field(user_id, category, field, value)
            # Lines 73-74: details[category][field] = value
            # So:
            update_farmer_profile_field(user_id, 'preferences', 'language', detected_language)
            update_farmer_profile_field(user_id, 'personal_info', 'primary_language', detected_language)
        script_instruction = 'RESPOND 100% IN ROMAN SCRIPT (ENGLISH/HINGLISH)' if has_roman and (not has_devanagari) else 'RESPOND 100% IN DEVANAGARI SCRIPT (HINDI)'
        system_context = f"[SYSTEM: User ID = '{user_id}'. Voice Input = {is_voice}. STRICT LANGUAGE INSTRUCTION: {script_instruction}. DO NOT TRANSLATE English to Hindi. Call 'get_farmer_context_summary'.]"
        full_message_text = f'{system_context}\n{message}'
        payload = {'appName': app_name, 'userId': user_id, 'sessionId': session_id, 'newMessage': {'role': 'user', 'parts': [{'text': full_message_text}]}}
        if image_data and image_mime_type:
            payload['newMessage']['parts'].append({'inlineData': {'mimeType': image_mime_type, 'data': image_data}})
            payload['newMessage']['parts'][0]['text'] += '\n\n[USER SENT AN IMAGE]'
        logger.info(f'🔄 Calls ADK for {user_id}: {message[:50]}...')
        response = _send_to_adk_with_retry(payload, app_name, session_id)
        if response.status_code == 404:
            logger.warning(f'⚠️ Session {session_id} not found in ADK. Recreating session...')
            from tools.memory_tools import set_active_session
            set_active_session(user_id, '')
            new_agent_response = await call_adk_api(message, phone_number, image_data, image_mime_type, is_voice)
            return new_agent_response
        if response.status_code == 200:
            result = response.json()

            def extract_text(data):
                if isinstance(data, dict):
                    if 'text' in data and data['text']:
                        return data['text']
                    for (k, v) in data.items():
                        res = extract_text(v)
                        if res:
                            return res
                elif isinstance(data, list):
                    for item in reversed(data):
                        res = extract_text(item)
                        if res:
                            return res
                return None
            agent_text = extract_text(result)
            if not agent_text:
                return 'Error: Could not extract agent response from ADK.'
            return agent_text
        elif response.status_code == 429 or response.status_code >= 500:
             logger.warning(f"⚠️ ADK Server Error ({response.status_code}): {response.text}")
             return "Server is currently busy due to high traffic. Please try again in 1 minute. 🙏"
        else:
            logger.error(f'❌ ADK Error {response.status_code}: {response.text}')
            return f'Error: ADK returned {response.status_code}'
    except Exception as e:
        logger.error(f'Call ADK Failed: {e}')
        return 'Technical Error: Unable to connect to the agent server.'

from fastapi import BackgroundTasks

# Twilio Client Initialization
from twilio.rest import Client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

async def process_and_send_response(phone_number, message_body, num_media, media_url, media_type, is_voice, host, proto):
    """Async task to process message and send response via Twilio API."""
    try:
        # 0. Get Farmer Context for Language
        from tools.memory_tools import get_farmer_profile
        farmer_profile = get_farmer_profile(phone_number)
        farmer_lang = farmer_profile.get('preferences', {}).get('language', 'hindi')
        if not farmer_lang:
            farmer_lang = farmer_profile.get('farmer_details', {}).get('preferences', {}).get('language', 'hindi')
        
        # 1. Handle Voice Transcription
        if is_voice and media_url:
            auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            transcript = process_voice_message_from_whatsapp(media_url, auth, farmer_language=farmer_lang)
            if transcript:
                message_body = transcript
                logger.info(f'📝 Transcript ({farmer_lang}): {message_body}')
            else:
                message_body = f'[SYSTEM: Voice transcription failed for {farmer_lang} audio. Please inform the user politely that you couldn\'t hear them clearly.]'
        
        # 2. Handle Image
        image_data = None
        if int(num_media) > 0 and media_type and ('image' in media_type) and media_url:
            try:
                auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
                img_resp = requests.get(media_url, auth=auth)
                if img_resp.status_code == 200:
                    image_data = base64.b64encode(img_resp.content).decode('utf-8')
            except Exception as e:
                logger.error(f'Image download failed: {e}')

        # 3. Call Agent
        agent_response = await call_adk_api(
            message=message_body or 'Image sent', 
            phone_number=phone_number, 
            image_data=image_data, 
            image_mime_type=media_type, 
            is_voice=is_voice
        )

        # 4. Generate Voice Response (if applicable)
        media_url_to_send = None
        if is_voice:
            try:
                from tools.voice_processing_tool import create_voice_response_for_farmer_enhanced
                audio_base64 = create_voice_response_for_farmer_enhanced(
                    agent_response, 
                    farmer_language=farmer_lang,
                    farmer_context=farmer_profile
                )
                if audio_base64:
                    filename = f'resp_{int(time.time())}.mp3'
                    filepath = os.path.join('staticv2', filename)
                    with open(filepath, 'wb') as f:
                        f.write(base64.b64decode(audio_base64))
                    
                    # Construct Public URL
                    # Use provided host/proto from the webhook request context
                    media_url_to_send = f'{proto}://{host}/staticv2/{filename}'
                    logger.info(f'🔊 Generated voice response: {media_url_to_send}')
            except Exception as e:
                logger.error(f'Voice generation failed via Async: {e}')

        # 5. Send Message via Twilio API
        # Note: WhatsApp requires 'whatsapp:' prefix
        from_number = f'whatsapp:{TWILIO_PHONE_NUMBER}' if not TWILIO_PHONE_NUMBER.startswith('whatsapp:') else TWILIO_PHONE_NUMBER
        to_number = f'whatsapp:{phone_number}'
        
        # Split logic: If media exists, send media message. Else send text.
        # Twilio API handles both body and media_url in one go.
        
        # Formatting Text
        import html
        # Twilio API Body doesn't need XML escaping typically, but let's keep it clean plain text
        # Actually API expects plain text, not TwiML escaped. 
        # So we use agent_response raw.
        
        msg_args = {
            'body': agent_response,
            'from_': from_number,
            'to': to_number
        }
        if media_url_to_send:
            msg_args['media_url'] = [media_url_to_send]
            
        # Truncate message if too long (Twilio limit ~1600-4000 depending on account/media)
        # We aim for 3000 for safety and readability.
        if len(agent_response) > 3000:
            logger.warning(f"⚠️ Message too long ({len(agent_response)} chars). Truncating.")
            agent_response = agent_response[:3000] + "... (truncated)"
            msg_args['body'] = agent_response

        logger.info(f"🚀 Sending Async Message to {phone_number} (Media: {bool(media_url_to_send)})")
        twilio_client.messages.create(**msg_args)
        logger.info("✅ Message sent successfully via Twilio API")

    except Exception as e:
        logger.error(f"❌ Async Processing Failed: {e}")
        # Optional: Send error message to user?
        try:
             twilio_client.messages.create(
                body="Technical Error: Unable to process your request at the moment.",
                from_=f'whatsapp:{TWILIO_PHONE_NUMBER}' if not TWILIO_PHONE_NUMBER.startswith('whatsapp:') else TWILIO_PHONE_NUMBER,
                to=f'whatsapp:{phone_number}'
             )
        except:
            pass

@app.post('/webhook/whatsapp')
async def whatsapp_webhook(
    background_tasks: BackgroundTasks,
    request: Request, 
    From=Form(...), 
    Body=Form(None), 
    NumMedia=Form('0'), 
    MediaUrl0=Form(None), 
    MediaContentType0=Form(None)
):
    """Handle incoming WhatsApp messages with Async Background Processing"""
    phone_number = From.replace('whatsapp:', '')
    logger.info(f'📨 Msg from {phone_number} (Async Scheduled)')
    
    # Check for Voice vs Text immediately to define 'is_voice'
    is_voice = False
    if int(NumMedia) > 0 and MediaContentType0:
        if 'audio' in MediaContentType0 or 'voice' in MediaContentType0:
            logger.info('🎤 Voice message detected')
            is_voice = True
    
    # We need host/proto for URL generation, but request object is not available in background task
    # So we extract them now
    host = request.headers.get('host')
    proto = request.headers.get('x-forwarded-proto', 'http')
    
    if not Body and int(NumMedia) == 0:
        # Empty heartbeat?
        return Response(content="<?xml version='1.0' encoding='UTF-8'?><Response></Response>", media_type='application/xml')

    # Schedule the heavy lifting
    background_tasks.add_task(
        process_and_send_response,
        phone_number=phone_number,
        message_body=Body,
        num_media=NumMedia,
        media_url=MediaUrl0,
        media_type=MediaContentType0,
        is_voice=is_voice,
        host=host,
        proto=proto
    )

    # Return immediate success to Twilio to avoid timeout
    return Response(content="<?xml version='1.0' encoding='UTF-8'?><Response></Response>", media_type='application/xml')

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)