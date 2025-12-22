import os
import pymongo
from bson import ObjectId
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv('.env.local')

def seed_external_visas():
    mongodb_uri = os.getenv('MONGODB_URI')
    if not mongodb_uri:
        print("MONGODB_URI not found")
        return
    
    client = pymongo.MongoClient(mongodb_uri)
    db = client.get_default_database()
    
    # Murad Agency ID
    murad_agency_id = ObjectId("693fe20678fbdc3a52e25008")
    
    visas = [
        {
            "agency_id": murad_agency_id,
            "visa_title": "Saudi Work Visa (seeded)",
            "visa_type": "Work",
            "country": "Saudi Arabia",
            "entry_type": "Single",
            "processing_time_days": 15,
            "visa_validity_days": 90,
            "stay_duration_days": 90,
            "total_visas": 20,
            "available_visas": 20,
            "price_per_visa": 150000,
            "passport_required": True,
            "cnic_required": True,
            "photo_required": True,
            "medical_required": True,
            "police_certificate_required": True,
            "vaccine_required": True,
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "agency_id": murad_agency_id,
            "visa_title": "UK Visit Visa (seeded)",
            "visa_type": "Visit",
            "country": "United Kingdom",
            "entry_type": "Multiple",
            "processing_time_days": 21,
            "visa_validity_days": 180,
            "stay_duration_days": 30,
            "total_visas": 10,
            "available_visas": 10,
            "price_per_visa": 45000,
            "passport_required": True,
            "cnic_required": True,
            "photo_required": True,
            "medical_required": False,
            "police_certificate_required": False,
            "vaccine_required": False,
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    result = db.visagroups.insert_many(visas)
    print(f"Successfully seeded {len(result.inserted_ids)} visas for Murad Agency.")

if __name__ == "__main__":
    seed_external_visas()
