# Kisan Mitra Tools Package
# Specialized tools for Enhanced Multilingual Agronomist - Kisan Mitra
# Using built-in Gemini vision for disease detection instead of custom tools

from .weather_tool import get_agricultural_weather, get_farmer_weather
from .farming_calendar_tool import get_farming_calendar_advice, get_crop_specific_calendar
from .agriculture_schemes_tool import (
    get_relevant_schemes_for_farmer, 
    get_scheme_details, 
    list_all_available_schemes
)
from .farmer_context_tools import (
    load_farmer_profile, 
    get_farmer_context_summary, 
    get_crop_specific_context, 
    get_seasonal_recommendations
)
from .mandi_prices_tool import (
    get_farmer_mandi_prices,
    get_mandi_prices_for_date,
    get_commodity_price_info
)
# Voice Processing Tools (NEW)
from .voice_processing_tool import (
    process_voice_input,
    generate_voice_response,
    check_voice_service_status,
    process_voice_message_from_web,
    process_voice_message_from_whatsapp,
    create_voice_response_for_farmer
)

# Export all Kisan Mitra tools
__all__ = [
    # Weather Tools
    'get_farmer_weather',           # Auto weather for farmer's location
    'get_agricultural_weather',     # General weather for any location
    
    # Enhanced Farming Calendar Tools  
    'get_farming_calendar_advice',  # Comprehensive monthly farming advice
    'get_crop_specific_calendar',   # Detailed crop-specific information
    
    # Agriculture Schemes Tools
    'get_relevant_schemes_for_farmer',  # Personalized scheme recommendations
    'get_scheme_details',               # Detailed scheme information
    'list_all_available_schemes',       # List all available schemes
    
    # Farmer Context Tools
    'load_farmer_profile',
    'get_farmer_context_summary',
    'get_crop_specific_context',
    'get_seasonal_recommendations',
    
    # Mandi Prices Tools
    'get_farmer_mandi_prices',      # Today's mandi prices for farmer location
    'get_mandi_prices_for_date',    # Specific date mandi prices
    'get_commodity_price_info',     # Specific commodity price information
    
    # Voice Processing Tools (NEW)
    'process_voice_input',              # Process voice input for ADK
    'generate_voice_response',          # Generate voice responses
    'check_voice_service_status',       # Check voice service status
    'process_voice_message_from_web',   # Web voice processing
    'process_voice_message_from_whatsapp', # WhatsApp voice processing
    'create_voice_response_for_farmer', # Create voice responses
] 