"""
Kisan Mitra — WhatsApp Gateway (Twilio)
Receives messages → calls ADK agent → sends reply (text + optional voice)
"""
import os
import time
import base64
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Form, Request, BackgroundTasks
from fastapi.responses import Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from twilio.rest import Client as TwilioClient

# Voice tools
from tools.voice_processing_tool import (
    process_voice_message_from_whatsapp,
    generate_voice_audio,
    _get_language_code,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
ADK_API_URL = 'http://localhost:8001'
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN  = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '+14155238886')

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR  = os.path.join(PROJECT_DIR, 'staticv2')
os.makedirs(STATIC_DIR, exist_ok=True)

twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def _detect_public_url() -> str:
    """Auto-detect public tunnel URL from ngrok or serveo at startup."""
    # Try ngrok API first (most reliable)
    try:
        resp = requests.get('http://localhost:4040/api/tunnels', timeout=3)
        for t in resp.json().get('tunnels', []):
            if t.get('proto') == 'https':
                url = t['public_url'].rstrip('/')
                logger.info(f'🌐 Public URL (ngrok): {url}')
                return url
    except Exception:
        pass
    logger.warning('⚠️ Could not detect public URL — audio media delivery will be text-only fallback')
    return ''


PUBLIC_BASE_URL = _detect_public_url()

app = FastAPI(title='Kisan Mitra WhatsApp', version='3.0.0')
app.mount('/staticv2', StaticFiles(directory=STATIC_DIR), name='staticv2')


# ─────────────────────────────────────────────
# Health endpoints
# ─────────────────────────────────────────────
@app.get('/')
@app.get('/health')
async def health():
    return {'status': 'healthy', 'service': 'Kisan Mitra WhatsApp', 'version': '3.0.0'}


# ─────────────────────────────────────────────
# ADK session + message
# ─────────────────────────────────────────────
class ServiceBusyError(Exception):
    pass

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    retry=retry_if_exception_type(ServiceBusyError),
    reraise=True
)
def _call_adk(payload: dict) -> requests.Response:
    try:
        resp = requests.post(f'{ADK_API_URL}/run', json=payload, timeout=45)
        if resp.status_code == 429:
            raise ServiceBusyError('ADK rate limited')
        if resp.status_code >= 500:
            raise ServiceBusyError(f'ADK server error {resp.status_code}')
        return resp
    except requests.exceptions.RequestException as e:
        raise ServiceBusyError(f'Connection error: {e}')


def _get_or_create_session(user_id: str) -> str:
    """Return a valid ADK session ID for this user, creating one if needed."""
    from tools.memory_tools import get_active_session, set_active_session
    session_data = get_active_session(user_id)
    session_id = session_data.get('session_id')
    last_activity = session_data.get('last_activity')

    # Expire sessions older than 1 hour
    if session_id and last_activity:
        age = (datetime.utcnow() - datetime.fromisoformat(last_activity)).total_seconds()
        if age > 3600:
            logger.info(f'Session expired ({age:.0f}s) for {user_id}')
            session_id = None

    if not session_id:
        try:
            r = requests.post(
                f'{ADK_API_URL}/apps/kisan_mitra/users/{user_id}/sessions',
                json={}, timeout=10
            )
            if r.status_code in (200, 201):
                session_id = r.json().get('id')
                set_active_session(user_id, session_id)
                logger.info(f'New session {session_id} for {user_id}')
            else:
                logger.error(f'Session creation failed: {r.status_code} {r.text}')
        except Exception as e:
            logger.error(f'Session creation error: {e}')
    else:
        set_active_session(user_id, session_id)

    return session_id


def _extract_text(data) -> str:
    """Recursively pull the last text value from the ADK response JSON."""
    if isinstance(data, dict):
        if data.get('text'):
            return data['text']
        for v in data.values():
            r = _extract_text(v)
            if r:
                return r
    elif isinstance(data, list):
        for item in reversed(data):
            r = _extract_text(item)
            if r:
                return r
    return ''


def _save_exchange_insight(user_id: str, farmer_msg: str, agent_reply: str):
    """Persist a compact record of each exchange to Firestore so future sessions have context."""
    try:
        from tools.memory_tools import save_farmer_insight
        # Skip trivial/very-short exchanges
        if len(farmer_msg.strip()) < 10:
            return
        insight = f"Q: {farmer_msg[:120].strip()} | A: {agent_reply[:120].strip()}"
        save_farmer_insight(user_id, insight)
    except Exception as e:
        logger.warning(f'Could not save insight for {user_id}: {e}')


async def call_adk(message: str, phone_number: str, image_data: str = None, image_mime: str = None) -> str:
    """Send a message to the ADK agent and return the text response."""
    user_id = phone_number
    session_id = _get_or_create_session(user_id)
    if not session_id:
        return 'सर्वर व्यस्त है, कृपया 1 मिनट बाद फिर से कोशिश करें।'

    payload = {
        'appName': 'kisan_mitra',
        'userId': user_id,
        'sessionId': session_id,
        'newMessage': {
            'role': 'user',
            'parts': [{'text': message}]
        }
    }
    if image_data and image_mime:
        payload['newMessage']['parts'].append(
            {'inlineData': {'mimeType': image_mime, 'data': image_data}}
        )
        payload['newMessage']['parts'][0]['text'] += '\n[Image attached]'

    logger.info(f'→ ADK [{user_id}]: {message[:80]}')
    try:
        resp = _call_adk(payload)
    except ServiceBusyError as e:
        logger.error(f'ADK busy: {e}')
        return 'सर्वर अभी व्यस्त है। थोड़ी देर बाद कोशिश करें। 🙏'

    if resp.status_code == 404:
        # Session disappeared — clear and retry once
        from tools.memory_tools import set_active_session
        set_active_session(user_id, '')
        return await call_adk(message, phone_number, image_data, image_mime)

    if resp.status_code == 200:
        text = _extract_text(resp.json())
        if text:
            logger.info(f'← ADK reply [{user_id}]: {text[:80]}')
            _save_exchange_insight(user_id, message, text)
            return text
        return 'कुछ समझ नहीं आया। कृपया फिर से पूछें।'

    logger.error(f'ADK error {resp.status_code}: {resp.text[:200]}')
    return 'तकनीकी समस्या हो गई। थोड़ी देर बाद कोशिश करें।'


# ─────────────────────────────────────────────
# Voice helpers
# ─────────────────────────────────────────────

def _farmer_language(phone_number: str) -> str:
    """Get saved language preference for this farmer."""
    try:
        from tools.memory_tools import get_farmer_profile
        profile = get_farmer_profile(phone_number)
        lang = (
            profile.get('preferences', {}).get('language')
            or profile.get('farmer_details', {}).get('preferences', {}).get('language')
        )
        return lang or 'hindi'
    except Exception:
        return 'hindi'


def _save_audio_file(audio_bytes: bytes) -> str:
    """Save MP3 bytes to staticv2/ and return the filename."""
    filename = f'resp_{int(time.time() * 1000)}.mp3'
    filepath = os.path.join(STATIC_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(audio_bytes)
    return filename


def _split_message(text: str, limit: int = 1500):
    """Split long text at sentence boundaries to stay under Twilio's limit."""
    if len(text) <= limit:
        return [text]
    chunks, current = [], ''
    # Split on newlines first, then sentences
    for line in text.split('\n'):
        if len(current) + len(line) + 1 <= limit:
            current += ('\n' if current else '') + line
        else:
            if current:
                chunks.append(current)
            # Line itself too long — split at last space before limit
            while len(line) > limit:
                cut = line.rfind(' ', 0, limit)
                if cut == -1:
                    cut = limit
                chunks.append(line[:cut])
                line = line[cut:].lstrip()
            current = line
    if current:
        chunks.append(current)
    return chunks


def _send_whatsapp(to: str, body: str, media_url: str = None):
    """Send a WhatsApp message via Twilio. Splits long replies; attaches audio on first chunk."""
    from_num = TWILIO_PHONE_NUMBER
    if not from_num.startswith('whatsapp:'):
        from_num = f'whatsapp:{from_num}'
    to_num = f'whatsapp:{to}' if not to.startswith('whatsapp:') else to

    chunks = _split_message(body)
    for i, chunk in enumerate(chunks):
        kwargs = {'body': chunk, 'from_': from_num, 'to': to_num}
        if i == 0 and media_url:
            kwargs['media_url'] = [media_url]
        try:
            msg = twilio_client.messages.create(**kwargs)
            logger.info(f'✅ Sent chunk {i+1}/{len(chunks)} to {to} (SID={msg.sid})')
        except Exception as e:
            if 'media_url' in kwargs and ('media' in str(e).lower() or '400' in str(e)):
                # Audio URL not accessible — send text only
                logger.warning(f'⚠️ Audio URL failed ({e}), retrying text-only')
                kwargs.pop('media_url')
                msg = twilio_client.messages.create(**kwargs)
                logger.info(f'✅ Sent text-only chunk {i+1}/{len(chunks)} to {to} (SID={msg.sid})')
            else:
                raise


# ─────────────────────────────────────────────
# Background processing
# ─────────────────────────────────────────────

async def _process_and_reply(
    phone_number: str,
    message_body: str,
    num_media: str,
    media_url: str,
    media_type: str,
    is_voice: bool,
    public_base_url: str,   # e.g. https://xxx.serveousercontent.com
):
    try:
        farmer_lang = _farmer_language(phone_number)
        logger.info(f'Processing from {phone_number} | voice={is_voice} | lang={farmer_lang}')

        # 1. Transcribe voice if needed
        if is_voice and media_url:
            auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            logger.info(f'🎤 Transcribing voice message...')
            transcript = process_voice_message_from_whatsapp(media_url, auth, farmer_language=farmer_lang)
            if transcript:
                logger.info(f'📝 Transcript: {transcript}')
                message_body = transcript
            else:
                logger.warning('⚠️ Transcription failed — asking agent to acknowledge')
                message_body = (
                    f'[The farmer sent a voice message but transcription failed. '
                    f'Reply in {farmer_lang} saying you could not hear them clearly and ask them to repeat or type.]'
                )

        # 2. Handle image attachment
        image_data = None
        if num_media and int(num_media) > 0 and media_type and 'image' in media_type and media_url:
            try:
                r = requests.get(media_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN), timeout=15)
                if r.status_code == 200:
                    image_data = base64.b64encode(r.content).decode('utf-8')
            except Exception as e:
                logger.error(f'Image download failed: {e}')

        # 3. Get agent response
        agent_reply = await call_adk(
            message=message_body or 'Hello',
            phone_number=phone_number,
            image_data=image_data,
            image_mime=media_type
        )

        # 4. Generate voice response (if farmer sent voice)
        audio_media_url = None
        if is_voice:
            logger.info(f'🔊 Generating voice reply in {farmer_lang}...')
            try:
                audio_bytes = generate_voice_audio(agent_reply, farmer_lang)
                if audio_bytes and public_base_url:
                    filename = _save_audio_file(audio_bytes)
                    audio_media_url = f'{public_base_url}/staticv2/{filename}'
                    logger.info(f'🔊 Voice file ready: {audio_media_url}')
            except Exception as e:
                logger.warning(f'⚠️ TTS failed: {e} — will send text only')

        # 5. Send reply — try with audio, fall back to text-only if media URL rejected
        try:
            _send_whatsapp(phone_number, agent_reply, audio_media_url)
        except Exception as e:
            if audio_media_url and ('media' in str(e).lower() or '400' in str(e)):
                logger.warning(f'⚠️ Media URL rejected by Twilio, sending text only: {e}')
                _send_whatsapp(phone_number, agent_reply, None)
            else:
                raise

    except Exception as e:
        logger.error(f'❌ Background processing error: {e}', exc_info=True)
        # Last-resort: send the actual agent reply as text rather than a generic error
        try:
            if 'agent_reply' in dir() and agent_reply:
                _send_whatsapp(phone_number, agent_reply, None)
            else:
                _send_whatsapp(phone_number, 'माफ करें, कुछ तकनीकी समस्या हो गई। थोड़ी देर बाद कोशिश करें। 🙏')
        except Exception:
            pass


# ─────────────────────────────────────────────
# Webhook
# ─────────────────────────────────────────────

@app.post('/webhook/whatsapp')
async def whatsapp_webhook(
    background_tasks: BackgroundTasks,
    request: Request,
    From: str = Form(...),
    Body: str = Form(None),
    NumMedia: str = Form('0'),
    MediaUrl0: str = Form(None),
    MediaContentType0: str = Form(None),
):
    phone_number = From.replace('whatsapp:', '')
    media_count = int(NumMedia or '0')

    is_voice = (
        media_count > 0 and MediaContentType0 and
        ('audio' in MediaContentType0 or 'voice' in MediaContentType0 or 'ogg' in MediaContentType0)
    )

    logger.info(f'📨 Webhook: from={phone_number} body={repr(Body)} media={media_count} voice={is_voice} type={MediaContentType0}')

    # Empty heartbeat
    if not Body and media_count == 0:
        return Response(
            content="<?xml version='1.0' encoding='UTF-8'?><Response></Response>",
            media_type='application/xml'
        )

    background_tasks.add_task(
        _process_and_reply,
        phone_number=phone_number,
        message_body=Body,
        num_media=NumMedia,
        media_url=MediaUrl0,
        media_type=MediaContentType0,
        is_voice=is_voice,
        public_base_url=PUBLIC_BASE_URL,
    )

    return Response(
        content="<?xml version='1.0' encoding='UTF-8'?><Response></Response>",
        media_type='application/xml'
    )


# ─────────────────────────────────────────────
# Test endpoint (no Twilio needed)
# ─────────────────────────────────────────────

@app.post('/test/message')
async def test_message(
    background_tasks: BackgroundTasks,
    request: Request,
    message: str = 'नमस्ते, मेरी फसल के बारे में बताओ',
    phone: str = '+919999999999',
    voice: bool = False,
):
    """Simulate a WhatsApp text message for testing without Twilio."""
    logger.info(f'🧪 TEST: phone={phone} message={message} voice={voice}')
    agent_reply = await call_adk(message=message, phone_number=phone)
    return JSONResponse({'status': 'ok', 'agent_reply': agent_reply, 'phone': phone})


@app.get('/test/voice-status')
async def test_voice_status():
    """Check which voice services are available."""
    from tools.voice_processing_tool import check_voice_service_status
    return JSONResponse(check_voice_service_status())


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
