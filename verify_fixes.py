
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

print("🧪 Starting Fix Verification...")

# 1. Hindi Query
print("\n--- Test 1: Hindi Query (Expect Hindi Response) ---")
send_message("Mausam kaisa hai aaj?")
time.sleep(15)

# 2. English Switch
print("\n--- Test 2: English Switch (Expect English Response - Strict Rule) ---")
send_message("What is the price of Wheat today?")
time.sleep(15)

# 3. Marathi Switch
print("\n--- Test 3: Marathi Switch (Expect Marathi Response) ---")
send_message("Aaj cha havaman kasa aahe?")
time.sleep(15)

print("\n✅ Verification Complete.")
