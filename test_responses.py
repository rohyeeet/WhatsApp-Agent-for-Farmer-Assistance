#!/usr/bin/env python3
"""Test script to verify Kisan Mitra bot responses"""
import requests
import json
import time

ADK_URL = "http://localhost:8001"

def create_session(user_id="test_farmer"):
    """Create a new session"""
    resp = requests.post(f"{ADK_URL}/apps/kisan_mitra/users/{user_id}/sessions", json={})
    return resp.json()["id"]

def send_message(session_id, message, user_id="test_farmer"):
    """Send a message and get response"""
    payload = {
        "appName": "kisan_mitra",
        "userId": user_id,
        "sessionId": session_id,
        "newMessage": {
            "role": "user",
            "parts": [{"text": message}]
        }
    }
    # Correct endpoint is global /run in this ADK version
    try:
        resp = requests.post(f"{ADK_URL}/run", json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Request Error: {str(e)} (Status: {getattr(resp, 'status_code', 'N/A')})"
    
    # Handle different response formats
    
    # Handle different response formats
    def extract_text(obj):
        if isinstance(obj, dict):
            if "text" in obj and obj["text"]:
                return obj["text"]
            for v in obj.values():
                result = extract_text(v)
                if result:
                    return result
        elif isinstance(obj, list):
            for item in reversed(obj):
                result = extract_text(item)
                if result:
                    return result
        return None
    
    return extract_text(data) or f"No response found (status: {resp.status_code})"

def test_responses():
    print("=" * 60)
    print("KISAN MITRA BOT RESPONSE TESTS")
    print("=" * 60)
    
    # Test 1: English greeting
    print("\n📝 Test 1: English greeting")
    session = create_session()
    response = send_message(session, "Hello, I am a farmer from Punjab")
    print(f"Response:\n{response[:500]}...")
    time.sleep(12)  # Wait for quota
    
    # Test 2: Hindi query
    print("\n📝 Test 2: Hindi query")
    session2 = create_session("hindi_farmer")
    response2 = send_message(session2, "नमस्ते, मैं एक किसान हूं। गेहूं की बुवाई कब करनी चाहिए?", "hindi_farmer")
    print(f"Response:\n{response2[:500]}...")
    time.sleep(12)
    
    # Test 3: Weather query
    print("\n📝 Test 3: Weather query")
    session3 = create_session("weather_farmer")
    response3 = send_message(session3, "What is the weather today for farming in Ludhiana?", "weather_farmer")
    print(f"Response:\n{response3[:500]}...")
    time.sleep(12)
    
    # Test 4: Scheme query
    print("\n📝 Test 4: Government schemes query")
    session4 = create_session("scheme_farmer")
    response4 = send_message(session4, "What government schemes are available for farmers in India?", "scheme_farmer")
    print(f"Response:\n{response4[:500]}...")
    
    print("\n" + "=" * 60)
    print("TESTS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_responses()
