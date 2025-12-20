"""
Weather Tool for Kisan Mitra
Updated for Multi-User Support via `memory_tools`

Provides real-time weather information and agricultural insights for farmers.
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any
from tools.memory_tools import get_farmer_profile

def get_farmer_weather(user_id: str = "default_user") -> Dict[str, Any]:
    """Get weather information automatically for farmer's location from profile.
    
    Args:
        user_id (str): Unique identifier for the farmer
        
    Returns:
        Dict[str, Any]: Weather data for farmer's specific location
    """
    try:
        # Load farmer profile
        profile_data = get_farmer_profile(user_id)
        
        farmer_details = profile_data.get('farmer_details', {})
        location_details = farmer_details.get('location_details', {})
        
        # Get farmer's location - try district first, then village
        farmer_location = location_details.get('district')
        farmer_name = farmer_details.get('personal_info', {}).get('name', 'Kisan')
        farmer_state = location_details.get('state', 'India')
        
        if not farmer_location:
             return {
                "status": "error",
                "error_message": "Location not found in profile. Please tell me your District/City name.",
                "user_id": user_id
            }

        # Use the existing weather function with farmer's location
        weather_result = get_agricultural_weather(farmer_location)
        
        # Add farmer context to the result
        if weather_result.get('status') == 'success':
            weather_result['farmer_context'] = {
                "farmer_name": farmer_name,
                "farmer_location": f"{farmer_location}, {farmer_state}",
                "user_id": user_id,
                "message": f"Weather information for {farmer_name} जी's location: {farmer_location}, {farmer_state}"
            }
        
        return weather_result
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error getting farmer weather: {str(e)}",
            "user_id": user_id
        }

def get_agricultural_weather(location: str, language: str = "en") -> Dict[str, Any]:
    """Get comprehensive weather information for agricultural purposes.
    
    Args:
        location (str): Location name (city, district, or coordinates)
        language (str): Response language code (en, hi, mr, etc.)
    
    Returns:
        Dict[str, Any]: Comprehensive weather data for farming decisions
    """
    api_key = "be1aacd35c28c14b6c62ad0fa78ac6ec"
    
    try:
        # First get coordinates from location name
        geocoding_url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={api_key}"
        geo_response = requests.get(geocoding_url, timeout=10)
        
        if geo_response.status_code != 200:
            return {
                "status": "error",
                "error_message": f"Could not find location: {location}. Please provide a valid city or district name."
            }
        
        geo_data = geo_response.json()
        if not geo_data:
            return {
                "status": "error", 
                "error_message": f"Location '{location}' not found. Please check spelling or try nearby major city."
            }
        
        lat = geo_data[0]['lat']
        lon = geo_data[0]['lon']
        found_location = geo_data[0]['name']
        country = geo_data[0].get('country', '')
        state = geo_data[0].get('state', '')
        
        # Get current weather
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        weather_response = requests.get(weather_url, timeout=10)
        
        if weather_response.status_code != 200:
            return {
                "status": "error",
                "error_message": "Weather service temporarily unavailable. Please try again later."
            }
        
        weather_data = weather_response.json()
        
        # Get 5-day forecast
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        forecast_response = requests.get(forecast_url, timeout=10)
        forecast_data = forecast_response.json() if forecast_response.status_code == 200 else None
        
        # Process current weather
        current = weather_data['main']
        weather_desc = weather_data['weather'][0]
        wind = weather_data['wind']
        
        # Calculate agricultural parameters
        feels_like = current['feels_like']
        humidity = current['humidity']
        pressure = current['pressure']
        visibility = weather_data.get('visibility', 0) / 1000  # Convert to km
        
        # Agricultural insights
        temp_celsius = current['temp']
        temp_fahrenheit = (temp_celsius * 9/5) + 32
        
        # Determine agricultural recommendations based on weather
        agricultural_insights = []
        spray_conditions = "Good"
        irrigation_advice = "Normal schedule"
        
        # Weather-based agricultural advice
        if humidity > 80:
            agricultural_insights.append("High humidity - Monitor for fungal diseases")
            spray_conditions = "Poor - High humidity may reduce effectiveness"
        elif humidity < 30:
            agricultural_insights.append("Low humidity - Increase irrigation frequency")
            
        if wind.get('speed', 0) > 5:  # > 18 km/h
            spray_conditions = "Poor - High wind may cause drift"
            agricultural_insights.append("High wind - Avoid spraying operations")
            
        if temp_celsius > 35:
            agricultural_insights.append("High temperature - Avoid midday field work")
            irrigation_advice = "Increase frequency, prefer early morning irrigation"
        elif temp_celsius < 10:
            agricultural_insights.append("Low temperature - Monitor for cold stress")
            
        if weather_desc['main'].lower() in ['rain', 'thunderstorm', 'drizzle']:
            spray_conditions = "Poor - Rain will wash away treatments"
            agricultural_insights.append("Rainfall expected - Postpone spraying operations")
            irrigation_advice = "Reduce or skip irrigation"
            
        # Process forecast for next 3 days
        forecast_summary = []
        if forecast_data and 'list' in forecast_data:
            for i in range(0, min(24, len(forecast_data['list'])), 8):  # Every 24 hours
                forecast_item = forecast_data['list'][i]
                date = datetime.fromtimestamp(forecast_item['dt']).strftime('%Y-%m-%d')
                temp = forecast_item['main']['temp']
                desc = forecast_item['weather'][0]['description']
                rain_chance = forecast_item.get('pop', 0) * 100  # Probability of precipitation
                
                forecast_summary.append({
                    "date": date,
                    "temperature": f"{temp:.1f}°C",
                    "description": desc,
                    "rain_probability": f"{rain_chance:.0f}%"
                })
        
        return {
            "status": "success",
            "location": {
                "name": found_location,
                "state": state,
                "country": country,
                "coordinates": f"{lat:.2f}, {lon:.2f}"
            },
            "current_weather": {
                "temperature": f"{temp_celsius:.1f}°C ({temp_fahrenheit:.1f}°F)",
                "feels_like": f"{feels_like:.1f}°C",
                "description": weather_desc['description'].title(),
                "humidity": f"{humidity}%",
                "pressure": f"{pressure} hPa",
                "wind_speed": f"{wind.get('speed', 0):.1f} m/s",
                "wind_direction": f"{wind.get('deg', 0)}°",
                "visibility": f"{visibility:.1f} km",
                "uv_index": "Data not available"
            },
            "agricultural_conditions": {
                "spray_conditions": spray_conditions,
                "irrigation_advice": irrigation_advice,
                "field_work_suitability": "Good" if temp_celsius < 35 and wind.get('speed', 0) < 5 else "Limited",
                "disease_risk": "High" if humidity > 80 else "Low" if humidity < 50 else "Medium"
            },
            "insights": agricultural_insights,
            "forecast_3_days": forecast_summary[:3],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data_source": "OpenWeatherMap"
        }
        
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error_message": "Weather service request timed out. Please check your internet connection and try again."
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "error", 
            "error_message": "Cannot connect to weather service. Please check your internet connection."
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Weather service error: {str(e)}"
        }
