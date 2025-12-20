
import requests
import time
import os
import json

BASE_URL = "http://localhost:8000"
PHONE_NUMBER = "+919876543210"

def send_message(body):
    print(f"\n📤 Sending: '{body}'")
    try:
        response = requests.post(
            f"{BASE_URL}/webhook/whatsapp",
            data={
                "From": f"whatsapp:{PHONE_NUMBER}",
                "Body": body,
                "NumMedia": "0"
            },
            timeout=60
        )
        print(f"📥 Response: {response.text}")
        return response.text
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def check_profile():
    profile_path = f"context/profiles/{PHONE_NUMBER}.json"
    if os.path.exists(profile_path):
        with open(profile_path, 'r') as f:
            data = json.load(f)
            print(f"📄 Profile Data: Name={data['farmer_details']['personal_info'].get('name')}, Location={data['farmer_details']['location_details'].get('district')}")
            return data
    else:
        print("❌ Profile file not found.")
        return None

print("🧪 Starting Verification Tests...")

# 1. New Conversation
print("\n--- Test 1: Greeting (Expect Name/Location Request) ---")
send_message("Namaste")
time.sleep(15)

# 2. Provide Info
print("\n--- Test 2: Providing Info (Expect Memory Save) ---")
send_message("Mera naam Suresh hai aur main Nashik se hoon. Main Pyaaz (Onion) ugata hoon.")
time.sleep(2)

# 3. Verify Memory
print("\n--- Test 3: Verifying Memory persistence ---")
data = check_profile()
if data and data['farmer_details']['location_details']['district'] == 'Nashik':
    print("✅ Memory Verified: Location saved as Nashik")
else:
    print("❌ Memory Verification Failed")

# 4. Contextual Query
print("\n--- Test 4: Contextual Query (Weather) ---")
send_message("Mausam kaisa hai?")
time.sleep(2)

print("\n✅ Verification Complete.")
