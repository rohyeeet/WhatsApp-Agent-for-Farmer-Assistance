"""
Quick script to view MongoDB farmer data
"""
import os
from pymongo import MongoClient
import json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://kisan:kisan123@cluster0.mongodb.net/kisan_mitra')

def view_all_farmers():
    """View all farmers in the database."""
    try:
        client = MongoClient(MONGODB_URI)
        db = client['kisan_mitra']
        farmers = db['farmers']
        print('🌾 KISAN MITRA - FARMER DATABASE')
        print('=' * 60)
        count = farmers.count_documents({})
        print(f'\n📊 Total Farmers: {count}\n')
        for farmer in farmers.find():
            phone = farmer.get('phone_number', 'Unknown')
            details = farmer.get('farmer_details', {})
            personal = details.get('personal_info', {})
            location = details.get('location_details', {})
            farm = details.get('farm_details', {})
            print(f'📱 Phone: {phone}')
            print(f"👤 Name: {personal.get('name', 'N/A')}")
            print(f"📍 Location: {location.get('district', 'N/A')}, {location.get('state', 'N/A')}")
            print(f"🌾 Crops: {', '.join([c.get('name', '') for c in farm.get('crops', [])])}")
            print(f"🕐 Last Updated: {farmer.get('last_updated', 'N/A')}")
            print('-' * 60)
        client.close()
    except Exception as e:
        print(f'❌ Error: {e}')

def export_to_json():
    """Export all data to JSON file."""
    try:
        client = MongoClient(MONGODB_URI)
        db = client['kisan_mitra']
        farmers = db['farmers']
        data = list(farmers.find())
        for doc in data:
            doc.pop('_id', None)
        filename = f"farmers_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f'✅ Exported {len(data)} farmers to {filename}')
        client.close()
    except Exception as e:
        print(f'❌ Error: {e}')
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'export':
        export_to_json()
    else:
        view_all_farmers()
        print("\n💡 Tip: Run 'python view_mongodb_data.py export' to export to JSON")