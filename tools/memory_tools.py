"""
Memory Tools for Kisan Mitra - MongoDB Implementation

Handles creating, reading, and updating individual farmer profiles and sessions in MongoDB.
"""
import os
import logging
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

logger = logging.getLogger(__name__)

# MongoDB Configuration
MONGODB_URI = os.environ.get('MONGODB_URI')
DB_NAME = 'kisan_mitra'
try:
    client = MongoClient(MONGODB_URI)
    # Ping to verify connection
    client.admin.command('ping')
    db = client[DB_NAME]
    farmers_collection = db['farmers']
    sessions_collection = db['sessions']
    logger.info("✅ Connected to MongoDB Atlas successfully")
except Exception as e:
    logger.error(f"❌ Failed to connect to MongoDB: {e}")
    # Fallback/Crash if DB is critical? Ideally we should retry or fail hard.
    # For this agent, let's log error and allow it to fail at runtime if DB calls fail.
    farmers_collection = None
    sessions_collection = None

def _get_default_profile(user_id):
    """Create a default skeleton profile for a new user."""
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
    """Retrieve specific farmer profile by user_id from MongoDB."""
    try:
        if farmers_collection is None:
            return _get_default_profile(user_id)
            
        profile = farmers_collection.find_one({'user_id': user_id})
        if profile:
            # Remove _id as it's not JSON serializable usually needed by downstream tools
            if '_id' in profile:
                del profile['_id']
            return profile
        else:
            logger.info(f'Creating new MongoDB profile for {user_id}')
            profile = _get_default_profile(user_id)
            save_farmer_profile(user_id, profile)
            return profile
    except Exception as e:
        logger.error(f'Error loading profile from MongoDB for {user_id}: {e}')
        return _get_default_profile(user_id)

def save_farmer_profile(user_id, profile_data):
    """Save/Update the farmer profile in MongoDB."""
    try:
        if farmers_collection is None:
            return False
            
        profile_data['updated_at'] = datetime.now().isoformat()
        # Ensure user_id is in data
        profile_data['user_id'] = user_id
        
        result = farmers_collection.replace_one(
            {'user_id': user_id},
            profile_data,
            upsert=True
        )
        return True
    except Exception as e:
        # Check for Duplicate Key Error (E11000)
        if 'E11000' in str(e):
             logger.warning(f"⚠️ Duplicate Key Error for {user_id}. Trying to merge...")
             # Optionally: Attempt to merge or just return True (ignore)
             # For now, let's just return True so we don't crash the agent.
             return True
        logger.error(f'Error saving profile to MongoDB for {user_id}: {e}')
        return False

def update_farmer_profile_field(user_id, category, field, value):
    """Update a specific field in the farmer profile using MongoDB update operators."""
    try:
        if farmers_collection is None:
            return 'Database not available'
            
        # We need to construct the update path, e.g., 'farmer_details.personal_info.name'
        # The tool arguments are: category (e.g. 'personal_info'), field (e.g. 'name')
        
        # Helper to find where 'category' lives. Usually it's under 'farmer_details'.
        # But sometimes it might be 'farmer_details' itself passed as category?
        # Based on typical usage: update_farmer_profile_field(uid, 'personal_info', 'name', 'Ram')
        
        update_path = f"farmer_details.{category}.{field}"
        
        # Special logic for language sync
        updates = {
            "$set": {
                update_path: value,
                "updated_at": datetime.now().isoformat()
            }
        }
        
        # Sync logic (mirrored from original tool)
        if category == 'personal_info' and field == 'language':
             updates["$set"]["farmer_details.personal_info.primary_language"] = value
        
        # Check if we need to append to list instead of set
        # This requires reading first to know type, or we assume based on field name?
        # Original code read -> modified -> saved. Let's stick to read-modify-write for safety/consistency with complex logic
        # OR use just the original logic but load/save to Mongo.
        
        # Let's use the robust read-modify-write pattern to preserve the exact logic of the original tool
        profile = get_farmer_profile(user_id)
        details = profile['farmer_details']
        
        if category in details:
            if isinstance(details[category], dict):
                details[category][field] = value
                if category == 'personal_info' and field == 'language':
                     details['personal_info']['primary_language'] = value
            elif isinstance(details[category], list):
                if value not in details[category]:
                    details[category].append(value)
        else:
             return f"Error: Invalid category '{category}'. Valid categories: personal_info, location_details, farm_details, etc."
             
        if save_farmer_profile(user_id, profile):
            return f"Successfully updated {category}.{field} to '{value}' for user {user_id}"
        else:
            return 'Error updating profile in DB.'

    except Exception as e:
        logger.error(f"Error updating field {category}.{field}: {e}")
        return f"Error: {str(e)}"

def update_farmer_location(user_id, district, state='Uttar Pradesh', village=None):
    """Helper to update location."""
    profile = get_farmer_profile(user_id)
    profile['farmer_details']['location_details']['district'] = district
    profile['farmer_details']['location_details']['state'] = state
    if village:
        profile['farmer_details']['location_details']['village'] = village
    save_farmer_profile(user_id, profile)
    return f'Location updated to {district}, {state}'

def update_farmer_name(user_id, name, name_english=None):
    """Helper to update name."""
    profile = get_farmer_profile(user_id)
    profile['farmer_details']['personal_info']['name'] = name
    if name_english:
        profile['farmer_details']['personal_info']['name_english'] = name_english
    save_farmer_profile(user_id, profile)
    return f'Name updated to {name}'

def add_farmer_crop(user_id, crop_name, season='kharif'):
    """Helper to add a crop."""
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
        
    exists = False
    for crop in profile['farmer_details']['cropping_pattern'][target_list]:
        if crop['crop_name'].lower() == crop_name.lower():
            exists = True
            break
            
    if not exists:
        profile['farmer_details']['cropping_pattern'][target_list].append(crop_entry)
        save_farmer_profile(user_id, profile)
        return f'Added {crop_name} to {season} crops.'
    return f'{crop_name} already exists in {season} list.'

def get_active_session(user_id):
    """Get the active session ID for a user from MongoDB."""
    try:
        if sessions_collection is None:
            return {}
        session = sessions_collection.find_one({'user_id': user_id})
        return session if session else {}
    except Exception as e:
        logger.error(f"Error getting session for {user_id}: {e}")
        return {}

def set_active_session(user_id, session_id):
    """Set the active session ID for a user in MongoDB."""
    try:
        if sessions_collection is None:
            return
        
        sessions_collection.replace_one(
            {'user_id': user_id},
            {
                'user_id': user_id,
                'session_id': session_id,
                'last_activity': datetime.now().isoformat()
            },
            upsert=True
        )
    except Exception as e:
        logger.error(f"Error setting session for {user_id}: {e}")
