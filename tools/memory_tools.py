"""
Memory Tools for Kisan Mitra - Firestore Implementation

Handles creating, reading, and updating individual farmer profiles and sessions
in Google Cloud Firestore, with an in-memory fallback when credentials are absent.
"""
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# In-memory fallback
_in_memory_farmers = {}
_in_memory_sessions = {}

_db = None

def _init_firestore():
    global _db
    project = os.environ.get('GOOGLE_CLOUD_PROJECT')
    creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    database = os.environ.get('FIRESTORE_DATABASE', '(default)')
    if not project or not creds_path:
        logger.warning("⚠️ GOOGLE_CLOUD_PROJECT or GOOGLE_APPLICATION_CREDENTIALS not set. Using in-memory storage.")
        return
    try:
        from google.cloud import firestore
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_file(creds_path)
        _db = firestore.Client(project=project, credentials=creds, database=database)
        # Quick connectivity check
        _db.collection('farmers').limit(1).get()
        logger.info(f"✅ Connected to Firestore ({database}) successfully")
    except Exception as e:
        logger.warning(f"⚠️ Firestore unavailable ({e}). Using in-memory storage (data will not persist).")
        _db = None

_init_firestore()


def _farmers():
    return _db.collection('farmers') if _db else None

def _sessions():
    return _db.collection('sessions') if _db else None


def _get_default_profile(user_id):
    return {
        'user_id': user_id,
        'farmer_details': {
            'personal_info': {
                'name': 'किसान',
                'name_english': 'Farmer',
                'phone_number': user_id,
                'primary_language': 'hindi',
                'age': None
            },
            'location_details': {
                'village': None,
                'district': None,
                'state': 'Uttar Pradesh',
                'agro_climatic_zone': None,
                'coordinates': None
            },
            'farm_details': {
                'total_land_area_acres': 0,
                'irrigated_area_acres': 0,
                'soil_types': [],
                'water_sources': []
            },
            'cropping_pattern': {
                'kharif_crops': [],
                'rabi_crops_planned': [],
                'zaid_crops': []
            },
            'challenges_faced': [],
            'preferences': {
                'advisory_timing': 'Morning',
                'information_format': 'Voice',
                'language': 'hindi'
            },
            'economic_profile': {
                'investment_capacity': {
                    'annual_input_budget_inr': 0,
                    'insurance_coverage': False
                },
                'market_linkages': {
                    'primary_buyer': 'Local Mandi'
                }
            },
            'input_usage': {
                'fertilizers': {},
                'pesticides': {}
            },
            'government_schemes_enrolled': []
        },
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }


def get_farmer_profile(user_id):
    """Retrieve farmer profile by user_id from Firestore or in-memory fallback."""
    try:
        col = _farmers()
        if col is None:
            if user_id not in _in_memory_farmers:
                _in_memory_farmers[user_id] = _get_default_profile(user_id)
            return _in_memory_farmers[user_id]

        doc = col.document(user_id).get()
        if doc.exists:
            return doc.to_dict()

        logger.info(f'Creating new profile for {user_id}')
        profile = _get_default_profile(user_id)
        save_farmer_profile(user_id, profile)
        return profile
    except Exception as e:
        logger.error(f'Error loading profile for {user_id}: {e}')
        return _get_default_profile(user_id)


def save_farmer_profile(user_id, profile_data):
    """Save/update farmer profile in Firestore or in-memory fallback."""
    try:
        profile_data['updated_at'] = datetime.now().isoformat()
        profile_data['user_id'] = user_id

        col = _farmers()
        if col is None:
            _in_memory_farmers[user_id] = profile_data
            return True

        col.document(user_id).set(profile_data)
        return True
    except Exception as e:
        logger.error(f'Error saving profile for {user_id}: {e}')
        return False


def update_farmer_profile_field(user_id: str, category: str, field: str, value: str):
    """Update a specific field in the farmer profile."""
    try:
        profile = get_farmer_profile(user_id)
        details = profile['farmer_details']

        if category not in details:
            return f"Error: Invalid category '{category}'."

        if isinstance(details[category], dict):
            details[category][field] = value
            if category == 'personal_info' and field == 'language':
                details['personal_info']['primary_language'] = value
        elif isinstance(details[category], list):
            if value not in details[category]:
                details[category].append(value)

        if save_farmer_profile(user_id, profile):
            return f"Updated {category}.{field} to '{value}' for {user_id}"
        return 'Error updating profile.'
    except Exception as e:
        logger.error(f"Error updating {category}.{field}: {e}")
        return f"Error: {e}"


def update_farmer_location(user_id: str, district: str, state: str = 'Uttar Pradesh', village: str = ''):
    """Update farmer location."""
    profile = get_farmer_profile(user_id)
    profile['farmer_details']['location_details']['district'] = district
    profile['farmer_details']['location_details']['state'] = state
    if village:
        profile['farmer_details']['location_details']['village'] = village
    save_farmer_profile(user_id, profile)
    return f'Location updated to {district}, {state}'


def update_farmer_name(user_id: str, name: str, name_english: str = ''):
    """Update farmer name."""
    profile = get_farmer_profile(user_id)
    profile['farmer_details']['personal_info']['name'] = name
    if name_english:
        profile['farmer_details']['personal_info']['name_english'] = name_english
    save_farmer_profile(user_id, profile)
    return f'Name updated to {name}'


def add_farmer_crop(user_id: str, crop_name: str, season: str = 'kharif'):
    """Add a crop to the farmer's cropping pattern."""
    profile = get_farmer_profile(user_id)
    crop_entry = {
        'crop_name': crop_name,
        'variety': 'Unknown',
        'area_acres': 1.0,
        'sowing_date': datetime.now().strftime('%Y-%m-%d'),
        'growth_stage': 'Sowing'
    }
    target_list = 'kharif_crops'
    if season.lower() == 'rabi':
        target_list = 'rabi_crops_planned'
    elif season.lower() == 'zaid':
        target_list = 'zaid_crops'

    crops = profile['farmer_details']['cropping_pattern'][target_list]
    if any(c['crop_name'].lower() == crop_name.lower() for c in crops):
        return f'{crop_name} already in {season} list.'

    crops.append(crop_entry)
    save_farmer_profile(user_id, profile)
    return f'Added {crop_name} to {season} crops.'


def save_farmer_insight(user_id: str, insight: str) -> str:
    """Save a compact insight or learning about the farmer to Firestore.

    Call this whenever you learn something meaningful about the farmer during a conversation:
    a problem they mentioned, advice you gave, a crop issue, a scheme they're interested in,
    a preference, or anything that would help you serve them better next time.
    Keep the insight under 200 characters — concise, factual, actionable.

    Args:
        user_id: Farmer's phone number (e.g. +919876543210)
        insight: A short note, e.g. "Has 2ac wheat near Varanasi, aphid issue Jun-26, advised neem spray"
    """
    try:
        profile = get_farmer_profile(user_id)
        insights = profile.get('conversation_insights', [])
        insights.append({
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M'),
            'note': insight[:300]
        })
        # Keep only the most recent 50 insights
        profile['conversation_insights'] = insights[-50:]
        save_farmer_profile(user_id, profile)
        return f"Insight saved for {user_id}."
    except Exception as e:
        logger.error(f"Error saving insight for {user_id}: {e}")
        return f"Error saving insight: {e}"


def get_farmer_insights(user_id: str, last_n: int = 15) -> list:
    """Return the most recent N insights for a farmer."""
    try:
        profile = get_farmer_profile(user_id)
        return profile.get('conversation_insights', [])[-last_n:]
    except Exception as e:
        logger.error(f"Error getting insights for {user_id}: {e}")
        return []


def get_active_session(user_id):
    """Get active session for a user."""
    try:
        col = _sessions()
        if col is None:
            return _in_memory_sessions.get(user_id, {})
        doc = col.document(user_id).get()
        return doc.to_dict() if doc.exists else {}
    except Exception as e:
        logger.error(f"Error getting session for {user_id}: {e}")
        return {}


def set_active_session(user_id, session_id):
    """Set active session for a user."""
    try:
        data = {
            'user_id': user_id,
            'session_id': session_id,
            'last_activity': datetime.now().isoformat()
        }
        col = _sessions()
        if col is None:
            _in_memory_sessions[user_id] = data
            return
        col.document(user_id).set(data)
    except Exception as e:
        logger.error(f"Error setting session for {user_id}: {e}")
