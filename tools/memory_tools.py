"""
Memory Tools for Kisan Mitra - Multi-User Support

Handles creating, reading, and updating individual farmer profiles based on user_id (phone number).
Stores profiles in `context/profiles/{user_id}.json`.
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

PROFILE_DIR = "context/profiles"

# Ensure profile directory exists
os.makedirs(PROFILE_DIR, exist_ok=True)

def _get_profile_path(user_id: str) -> str:
    """Get the file path for a specific user's profile."""
    # Sanitize user_id to be safe for filenames
    safe_id = "".join(c for c in user_id if c.isalnum() or c in ('+', '-', '_'))
    return os.path.join(PROFILE_DIR, f"{safe_id}.json")

def _get_default_profile(user_id: str) -> Dict[str, Any]:
    """Create a default skeleton profile for a new user."""
    return {
        "farmer_details": {
            "personal_info": {
                "name": "किसान",  # Default name
                "name_english": "Farmer",
                "phone_number": user_id,
                "primary_language": "hindi", # Default language
                "age": None
            },
            "location_details": {
                "village": None,
                "district": None,
                "state": "Uttar Pradesh", # Default state for context
                "agro_climatic_zone": None,
                "coordinates": None
            },
            "farm_details": {
                "total_land_area_acres": 0,
                "irrigated_area_acres": 0,
                "soil_types": [],
                "water_sources": []
            },
            "cropping_pattern": {
                "kharif_crops": [],
                "rabi_crops_planned": [],
                "zaid_crops": []
            },
            "challenges_faced": [],
            "preferences": {
                "advisory_timing": "Morning",
                "information_format": "Voice"
            },
            "economic_profile": {
                 "investment_capacity": {
                    "annual_input_budget_inr": 0,
                    "insurance_coverage": False
                },
                "market_linkages": {
                    "primary_buyer": "Local Mandi"
                }
            },
            "input_usage": {
                "fertilizers": {},
                "pesticides": {}
            },
             "government_schemes_enrolled": []
        },
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

def get_farmer_profile(user_id: str) -> Dict[str, Any]:
    """
    Retrieve specific farmer profile by user_id (phone number).
    Creates a new default profile if one doesn't exist.
    """
    path = _get_profile_path(user_id)
    
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Create new profile
            logger.info(f"Creating new profile for {user_id}")
            profile = _get_default_profile(user_id)
            save_farmer_profile(user_id, profile)
            return profile
            
    except Exception as e:
        logger.error(f"Error loading profile for {user_id}: {e}")
        # Return a temporary default profile in case of error, to prevent crash
        return _get_default_profile(user_id)

def save_farmer_profile(user_id: str, profile_data: Dict[str, Any]) -> bool:
    """Save the farmer profile to disk."""
    path = _get_profile_path(user_id)
    try:
        profile_data["updated_at"] = datetime.now().isoformat()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving profile for {user_id}: {e}")
        return False

def update_farmer_profile_field(user_id: str, category: str, field: str, value: Any) -> str:
    """
    Update a specific field in the farmer profile.
    
    Args:
        user_id: Phone number
        category: Top level key in 'farmer_details' (e.g., 'personal_info', 'location_details')
        field: Specific field to update (e.g., 'name', 'district')
        value: New value
        
    Returns:
        Status message
    """
    profile = get_farmer_profile(user_id)
    
    if "farmer_details" not in profile:
        profile = _get_default_profile(user_id) # Should not happen usually
        
    details = profile["farmer_details"]
    
    # Handle direct fields vs nested fields
    if category in details:
        if isinstance(details[category], dict):
            details[category][field] = value
            # Auto-update related fields if necessary (e.g., english name)
            if category == 'personal_info' and field == 'language':
                 details['personal_info']['primary_language'] = value
        
        elif isinstance(details[category], list):
            # For lists, we might just append if it's a simple item, 
            # or replace if it's a specific implementation.
            # For simplicity in this tool, let's assume 'value' is the item to add
            if value not in details[category]:
                details[category].append(value)
    else:
        # If category doesn't strictly exist as a dict (rare), try to be flexible? 
        # Better to return error for structure safety.
        return f"Error: Invalid category '{category}'. Valid categories: personal_info, location_details, farm_details, etc."

    if save_farmer_profile(user_id, profile):
        return f"Successfully updated {category}.{field} to '{value}' for user {user_id}"
    else:
        return "Error updating profile."

def update_farmer_location(user_id: str, district: str, state: str = "Uttar Pradesh") -> str:
    """Helper to update location specifically."""
    profile = get_farmer_profile(user_id)
    profile["farmer_details"]["location_details"]["district"] = district
    profile["farmer_details"]["location_details"]["state"] = state
    save_farmer_profile(user_id, profile)
    return f"Location updated to {district}, {state}"

def update_farmer_name(user_id: str, name: str) -> str:
    """Helper to update name."""
    profile = get_farmer_profile(user_id)
    profile["farmer_details"]["personal_info"]["name"] = name
    save_farmer_profile(user_id, profile)
    return f"Name updated to {name}"

def add_farmer_crop(user_id: str, crop_name: str, season: str = "kharif") -> str:
    """Helper to add a crop."""
    profile = get_farmer_profile(user_id)
    
    crop_entry = {
       "crop_name": crop_name,
       "variety": "Unknown",
       "area_acres": 1.0,  # Default
       "sowing_date": datetime.now().strftime("%Y-%m-%d"),
       "growth_stage": "Sowing" 
    }
    
    target_list = "kharif_crops"
    if season.lower() == "rabi": target_list = "rabi_crops_planned"
    elif season.lower() == "zaid": target_list = "zaid_crops"
    
    # Check if already exists
    exists = False
    for crop in profile["farmer_details"]["cropping_pattern"][target_list]:
        if crop["crop_name"].lower() == crop_name.lower():
            exists = True
            break
            
    if not exists:
        profile["farmer_details"]["cropping_pattern"][target_list].append(crop_entry)
        save_farmer_profile(user_id, profile)
        return f"Added {crop_name} to {season} crops."
    return f"{crop_name} already exists in {season} list."
