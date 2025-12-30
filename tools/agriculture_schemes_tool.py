"""
Agriculture Schemes Tool for Kisan Mitra - ADK Compatible
Updated for Multi-User Support via `memory_tools`
"""
import json
from tools.memory_tools import get_farmer_profile
ACRE_TO_HECTARE = 0.404686

def get_relevant_schemes_for_farmer(user_id='default_user'):
    """Analyzes a farmer's profile to find relevant agricultural schemes.
    
    Args:
        user_id (str): Unique identifier for the farmer
        
    Returns:
        dict: A dictionary containing recommendations
    """
    schemes_path = 'context/agriculture_schemes.json'
    try:
        farmer_data = get_farmer_profile(user_id)
        with open(schemes_path, 'r', encoding='utf-8') as f:
            all_schemes = json.load(f)
        farmer_profile = farmer_data.get('farmer_details', {})
        if not farmer_profile:
            return {'status': 'error', 'error_message': 'Farmer profile details missing.'}
        recommended_schemes = []
        for scheme in all_schemes:
            if 'name' in scheme:
                recommended_schemes.append({'name': scheme['name'], 'description': scheme.get('description', ''), 'eligibility_reason': 'Potentially eligible based on profile.'})
                if len(recommended_schemes) > 5:
                    break
        return {'status': 'success', 'recommended_schemes': recommended_schemes, 'total_schemes_available': len(all_schemes)}
    except Exception as e:
        return {'status': 'error', 'error_message': str(e)}

def search_government_schemes(query='latest agricultural schemes for farmers in India'):
    """Search for latest government schemes using dynamic web search.
    
    Args:
        query (str): The search query for schemes
        
    Returns:
        dict: Search results with scheme names and URLs
    """
    try:
        from googlesearch import search
        results = []
        for url in search(query, num_results=5):
            results.append({'title': 'Scheme Information', 'url': url})
            if len(results) >= 5:
                break
        return {'status': 'success', 'query': query, 'schemes_found': results, 'note': 'These are dynamic results from the web. Please verify details on official portals.'}
    except Exception as e:
        return {'status': 'error', 'error_message': f'Search failed: {str(e)}'}

def get_scheme_details(scheme_name, user_id='default_user'):
    """Get detailed information about a specific agricultural scheme."""
    schemes_path = 'context/agriculture_schemes.json'
    try:
        with open(schemes_path, 'r', encoding='utf-8') as f:
            all_schemes = json.load(f)
        scheme_name_lower = scheme_name.lower()
        for scheme in all_schemes:
            if scheme['name'].lower() == scheme_name_lower or scheme['slug'].lower() == scheme_name_lower:
                return {'status': 'success', 'scheme_details': scheme}
        return {'status': 'error', 'error_message': f"Scheme '{scheme_name}' not found."}
    except Exception as e:
        return {'status': 'error', 'error_message': str(e)}

def list_all_available_schemes(user_id='default_user'):
    """List all available agricultural schemes."""
    schemes_path = 'context/agriculture_schemes.json'
    try:
        with open(schemes_path, 'r', encoding='utf-8') as f:
            all_schemes = json.load(f)
        schemes_summary = [{'name': s['name'], 'category': s['category']} for s in all_schemes]
        return {'status': 'success', 'total_schemes': len(all_schemes), 'all_schemes': schemes_summary}
    except Exception as e:
        return {'status': 'error', 'error_message': str(e)}