"""
Enhanced Farming Calendar Tool for Kisan Mitra

Provides comprehensive seasonal farming calendar and crop guidance using extensive dataset.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

def load_farming_calendar_data(dataset_path: str = "context/farming_calendar_dataset.json") -> Dict[str, Any]:
    """Load the comprehensive farming calendar dataset.
    
    Args:
        dataset_path (str): Path to the farming calendar dataset JSON file
        
    Returns:
        Dict[str, Any]: Complete farming calendar and crop database
    """
    try:
        with open(dataset_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {
            "status": "error",
            "error_message": f"Farming calendar dataset not found: {dataset_path}"
        }
    except json.JSONDecodeError as e:
        return {
            "status": "error", 
            "error_message": f"Invalid JSON format in dataset: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error loading dataset: {str(e)}"
        }

def get_farming_calendar_advice(location: str, month: Optional[int] = None) -> Dict[str, Any]:
    """Provide comprehensive seasonal farming calendar advice using the extensive dataset.
    
    Args:
        location (str): Location name
        month (Optional[int]): Month number (1-12), defaults to current month
        
    Returns:
        Dict[str, Any]: Comprehensive seasonal farming advice
    """
    if month is None:
        month = datetime.now().month
    
    # Load the comprehensive dataset
    calendar_data = load_farming_calendar_data()
    
    if "status" in calendar_data and calendar_data["status"] == "error":
        return calendar_data
    
    try:
        # Get month-specific data from the comprehensive dataset
        month_key = f"month_{month}"
        month_data = calendar_data["farming_calendar"][month_key]
        
        # Extract comprehensive information
        season_info = {
            "month_name": month_data["month_name"],
            "hindi_name": month_data["hindi_name"],
            "season": month_data["season"],
            "temperature_range": month_data["temperature_range"],
            "rainfall_pattern": month_data["rainfall_pattern"]
        }
        
        # Extract crop information by category
        crops_by_category = {}
        for category, crops in month_data["crops"].items():
            crops_by_category[category] = []
            for crop in crops:
                crop_info = {
                    "crop_name": crop["crop_name"],
                    "varieties": crop.get("varieties", []),
                    "growth_stage": crop.get("growth_stage", ""),
                    "activities": crop.get("activities", []),
                    "fertilizer_schedule": crop.get("fertilizer_schedule", ""),
                    "expected_yield": crop.get("expected_yield_per_acre", "")
                }
                crops_by_category[category].append(crop_info)
        
        # Extract pest and disease information
        pest_disease_info = month_data.get("pest_disease_watch", {})
        
        # Extract weather considerations
        weather_considerations = month_data.get("weather_considerations", {})
        
        # Extract regional variations
        regional_variations = month_data.get("regional_variations", {})
        
        # Extract market trends
        market_trends = month_data.get("market_trends", {})
        
        return {
            "status": "success",
            "location": location,
            "month": month,
            "season_info": season_info,
            "crops_by_category": crops_by_category,
            "pest_disease_watch": pest_disease_info,
            "weather_considerations": weather_considerations,
            "regional_variations": regional_variations,
            "market_trends": market_trends,
            "general_advice": [
                "Monitor weather forecasts daily using get_farmer_weather()",
                "Follow integrated pest management (IPM) practices",
                "Maintain detailed field records for better planning",
                "Consult local KVK for region-specific guidance",
                "Use soil health card recommendations for fertilizers"
            ]
        }
        
    except KeyError as e:
        return {
            "status": "error",
            "error_message": f"Month data not found in dataset: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error processing calendar data: {str(e)}"
        }

def get_crop_specific_calendar(crop_name: str, dataset_path: str = "context/farming_calendar_dataset.json") -> Dict[str, Any]:
    """Get detailed information about a specific crop from the crop database.
    
    Args:
        crop_name (str): Name of the crop to get information for
        dataset_path (str): Path to the farming calendar dataset JSON file
        
    Returns:
        Dict[str, Any]: Detailed crop information
    """
    calendar_data = load_farming_calendar_data(dataset_path)
    
    if "status" in calendar_data and calendar_data["status"] == "error":
        return calendar_data
    
    try:
        crop_database = calendar_data["crop_database"]
        crop_key = crop_name.lower()
        
        if crop_key not in crop_database:
            # Try to find crop in any category across all months
            found_crops = []
            for month_key, month_data in calendar_data["farming_calendar"].items():
                for category, crops in month_data["crops"].items():
                    for crop in crops:
                        if crop["crop_name"].lower() == crop_key:
                            found_crops.append({
                                "month": month_data["month_name"],
                                "category": category,
                                "details": crop
                            })
            
            if found_crops:
                return {
                    "status": "success",
                    "crop_name": crop_name,
                    "monthly_calendar": found_crops,
                    "message": f"Found {crop_name} calendar across {len(found_crops)} months"
                }
            else:
                return {
                    "status": "error",
                    "error_message": f"Crop '{crop_name}' not found in database. Available crops can be found in the monthly calendar data."
                }
        
        crop_info = crop_database[crop_key]
        
        return {
            "status": "success",
            "crop_name": crop_name,
            "scientific_name": crop_info.get("scientific_name", ""),
            "hindi_name": crop_info.get("hindi_name", ""),
            "regional_names": crop_info.get("regional_names", {}),
            "category": crop_info.get("category", ""),
            "sowing_season": crop_info.get("sowing_season", ""),
            "sowing_months": crop_info.get("sowing_months", []),
            "harvest_months": crop_info.get("harvest_months", []),
            "duration_days": crop_info.get("duration_days", ""),
            "agro_climatic_zones": crop_info.get("agro_climatic_zones", []),
            "soil_requirements": crop_info.get("soil_requirements", {}),
            "water_requirements": crop_info.get("water_requirements", {}),
            "major_varieties": crop_info.get("major_varieties", []),
            "fertilizer_recommendations": crop_info.get("fertilizer_recommendations", {})
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error retrieving crop information: {str(e)}"
        }
