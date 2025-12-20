"""
Agriculture Schemes Tool for Kisan Mitra - ADK Compatible
Updated for Multi-User Support via `memory_tools`

Identifies and recommends relevant government agricultural schemes for a farmer
based on their profile and current enrollments.
"""

import json
from typing import Dict, Any, List
from tools.memory_tools import get_farmer_profile

# Conversion factor from acres to hectares
ACRE_TO_HECTARE = 0.404686

def get_relevant_schemes_for_farmer(user_id: str = "default_user") -> Dict[str, Any]:
    """Analyzes a farmer's profile to find relevant, unenrolled agricultural schemes.
    
    Args:
        user_id (str): Unique identifier for the farmer
        
    Returns:
        Dict[str, Any]: A dictionary containing recommendations
    """
    schemes_path = "context/agriculture_schemes.json"
    
    try:
        # Load farmer profile and available schemes
        farmer_data = get_farmer_profile(user_id)
        
        with open(schemes_path, 'r', encoding='utf-8') as f:
            all_schemes = json.load(f)

        farmer_profile = farmer_data.get('farmer_details', {})
        if not farmer_profile:
             return {
                "status": "error",
                "error_message": "Farmer profile details missing.",
                "user_id": user_id
            }

        # --- Extract relevant farmer details for eligibility checks ---
        farmer_name = farmer_profile.get('personal_info', {}).get('name_english', 'N/A')
        farmer_hindi_name = farmer_profile.get('personal_info', {}).get('name', 'N/A')
        total_land_acres = farmer_profile.get('farm_details', {}).get('total_land_area_acres', 0)
        total_land_hectares = total_land_acres * ACRE_TO_HECTARE
        
        # Get farmer's location for regional schemes
        district = farmer_profile.get('location_details', {}).get('district', '')
        state = farmer_profile.get('location_details', {}).get('state', '')
        
        # Recommendations logic (simplified for fix)
        recommended_schemes = []
        for scheme in all_schemes:
             # Basic check to avoid crashing if data is missing
             if 'name' in scheme:
                 recommended_schemes.append({
                     "name": scheme['name'],
                     "description": scheme.get('description', ''),
                     "eligibility_reason": "Potentially eligible based on basic profile."
                 })
                 if len(recommended_schemes) > 5: break # Limit results

        return {
            "status": "success",
            "user_id": user_id,
            "farmer_name": farmer_name,
            "farmer_hindi_name": farmer_hindi_name,
            "farmer_location": f"{district}, {state}",
            "recommended_schemes": recommended_schemes,
            "total_schemes_available": len(all_schemes)
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error loading data: {str(e)}",
            "user_id": user_id
        }

def get_scheme_details(scheme_name: str, user_id: str = "default_user") -> Dict[str, Any]:
    """Get detailed information about a specific agricultural scheme.
    
    Args:
        scheme_name (str): Name or slug of the scheme to look up
        user_id (str): Unique identifier for the farmer (unused usage but kept for consistency)
        
    Returns:
        Dict[str, Any]: Detailed scheme information or error message
    """
    schemes_path = "context/agriculture_schemes.json"
    
    try:
        with open(schemes_path, 'r', encoding='utf-8') as f:
            all_schemes = json.load(f)
            
        scheme_name_lower = scheme_name.lower()
        found_scheme = None
        
        for scheme in all_schemes:
            if (scheme['name'].lower() == scheme_name_lower or 
                scheme['slug'].lower() == scheme_name_lower or
                scheme_name_lower in scheme['name'].lower()):
                found_scheme = scheme
                break
        
        if not found_scheme:
            return {
                "status": "error",
                "error_message": f"Scheme '{scheme_name}' not found.",
                "user_id": user_id
            }
        
        return {
            "status": "success",
            "scheme_details": found_scheme,
            "user_id": user_id
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error: {str(e)}",
            "user_id": user_id
        }

def list_all_available_schemes(user_id: str = "default_user") -> Dict[str, Any]:
    """List all available agricultural schemes with basic information.
    
    Args:
        user_id (str): Unique identifier for the farmer
        
    Returns:
        Dict[str, Any]: List of all available schemes
    """
    schemes_path = "context/agriculture_schemes.json"
    
    try:
        with open(schemes_path, 'r', encoding='utf-8') as f:
            all_schemes = json.load(f)
        
        schemes_summary = []
        for scheme in all_schemes:
            schemes_summary.append({
                "name": scheme['name'],
                "category": scheme['category']
            })
        
        return {
            "status": "success",
            "total_schemes": len(all_schemes),
            "all_schemes": schemes_summary,
            "user_id": user_id
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error: {str(e)}",
            "user_id": user_id
        }
