"""
Farmer Context Tools for Enhanced Multilingual Agronomist - ADK Compatible
Updated for Multi-User Support via `memory_tools`

Provides farmer profile context and personalized agricultural insights.
Functions now accept `user_id` to support multiple users.
"""

from typing import Dict, Any
from datetime import datetime
from tools.memory_tools import get_farmer_profile

def load_farmer_profile(user_id: str = "default_user") -> Dict[str, Any]:
    """Load farmer profile for a specific user.
    
    Args:
        user_id (str): Unique identifier for the farmer (phone number)
        
    Returns:
        Dict[str, Any]: Farmer profile data
    """
    try:
        profile_data = get_farmer_profile(user_id)
        
        # Validate required fields
        required_fields = ['farmer_details']
        if not all(field in profile_data for field in required_fields):
            return {
                "status": "error",
                "error_message": "Invalid farmer profile format. Missing required fields.",
                "user_id": user_id
            }
            
        return {
            "status": "success",
            "farmer_profile": profile_data['farmer_details'],
            "context_instructions": profile_data.get('context_usage_instructions', {}),
            "loaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user_id
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error loading farmer profile: {str(e)}",
            "user_id": user_id
        }

def get_farmer_context_summary(user_id: str = "default_user") -> Dict[str, Any]:
    """Get a summarized farmer context for quick reference.
    
    Args:
        user_id (str): Unique identifier for the farmer
        
    Returns:
        Dict[str, Any]: Summarized farmer context with language preference
    """
    profile_result = load_farmer_profile(user_id)
    
    if profile_result["status"] == "error":
        return profile_result
    
    farmer = profile_result["farmer_profile"]
    
    # Extract location details safely
    loc = farmer.get("location_details", {})
    
    # Extract key context information
    summary = {
        "status": "success",
        "user_id": user_id,
        "farmer_summary": {
            "name": farmer["personal_info"].get("name", "Unknown"),
            "name_english": farmer["personal_info"].get("name_english", "Unknown"),
            "location": {
                "village": loc.get("village"),
                "district": loc.get("district"),
                "state": loc.get("state"),
                "agro_climatic_zone": loc.get("agro_climatic_zone")
            },
            "primary_language": farmer["personal_info"].get("primary_language", "hindi"),
            "farm_size_acres": farmer["farm_details"].get("total_land_area_acres", 0),
            "current_crops": []
        },
        "quick_context": {
            "soil_types": [soil.get("type", "Unknown") for soil in farmer["farm_details"].get("soil_types", [])],
            "major_challenges": farmer.get("challenges_faced", [])[:3],
            "preferred_communication": {
                "language": farmer["personal_info"].get("primary_language", "hindi"),
                "timing": farmer["preferences"].get("advisory_timing"),
                "format": farmer["preferences"].get("information_format")
            }
        }
    }
    
    # Add current crop information
    if "kharif_crops" in farmer.get("cropping_pattern", {}):
        for crop in farmer["cropping_pattern"]["kharif_crops"]:
            summary["farmer_summary"]["current_crops"].append({
                "crop": crop.get("crop_name"),
                "variety": crop.get("variety"),
                "growth_stage": crop.get("growth_stage")
            })
    
    return summary

def get_crop_specific_context(crop_name: str, user_id: str = "default_user") -> Dict[str, Any]:
    """Get crop-specific context from farmer profile for a given crop.
    
    Args:
        crop_name (str): Name of the crop to get context for
        user_id (str): Unique identifier for the farmer
        
    Returns:
        Dict[str, Any]: Crop-specific context and recommendations
    """
    profile_result = load_farmer_profile(user_id)
    
    if profile_result["status"] == "error":
        return profile_result
    
    farmer = profile_result["farmer_profile"]
    crop_context = None
    season = "unknown"
    
    # Search in current kharif crops
    for crop in farmer.get("cropping_pattern", {}).get("kharif_crops", []):
        if crop.get("crop_name", "").lower() == crop_name.lower():
            crop_context = crop
            season = "kharif"
            break
            
    # Search in planned rabi crops if not found
    if not crop_context:
        for crop in farmer.get("cropping_pattern", {}).get("rabi_crops_planned", []):
            if crop.get("crop_name", "").lower() == crop_name.lower():
                crop_context = crop
                season = "rabi_planned"
                break
    
    if not crop_context:
        return {
            "status": "error",
            "error_message": f"Crop '{crop_name}' not found in farmer's current or planned cropping pattern.",
            "user_id": user_id
        }
    
    return {
        "status": "success",
        "user_id": user_id,
        "crop_context": {
            "crop_details": crop_context,
            "season": season,
            "farmer_location": farmer.get("location_details", {})
        }
    }

def get_seasonal_recommendations(user_id: str = "default_user") -> Dict[str, Any]:
    """Get season-specific recommendations based on farmer profile and current date.
    
    Args:
        user_id (str): Unique identifier for the farmer
        
    Returns:
        Dict[str, Any]: Seasonal recommendations
    """
    profile_result = load_farmer_profile(user_id)
    
    if profile_result["status"] == "error":
        return profile_result
    
    farmer = profile_result["farmer_profile"]
    current_date = datetime.now()
    current_month = current_date.month
    
    # Determine current season
    if current_month in [6, 7, 8, 9, 10]:
        season = "kharif"
        season_stage = "active"
    elif current_month in [11, 12, 1, 2, 3]:
        season = "rabi"
        season_stage = "active"
    else:  # April, May
        season = "summer"
        season_stage = "preparation"
    
    recommendations = {
        "status": "success",
        "user_id": user_id,
        "seasonal_recommendations": {
            "current_season": season,
            "season_stage": season_stage,
            "month": current_month,
            "location": farmer.get("location_details", {}).get("district", "Unknown"),
            "priority_actions": []
        }
    }
    
    # Basic logic for recommendations based on season
    if season == "kharif":
        recommendations["seasonal_recommendations"]["priority_actions"] = [
            "Monitor for monsoon related pests",
            "Ensure proper drainage"
        ]
    elif season == "rabi":
        recommendations["seasonal_recommendations"]["priority_actions"] = [
            "Prepare for winter crops",
            "Irrigation planning for dry months"
        ]
        
    return recommendations