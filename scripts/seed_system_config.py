"""
Seed script to populate system configuration with Airlines, Sectors, and Travel Types
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models.system_config import SystemConfig
from mongoengine import connect

app = create_app()

# Airlines
airlines = [
    "Air Arabia",
    "Airblue",
    "AirSial",
    "Emirates",
    "Fly Jinnah",
    "Flyadeal",
    "Flydubai",
    "Flynas",
    "PIA (Pakistan International Airlines)",
    "Qatar Airways",
    "SalamAir",
    "Saudia (Saudi Airlines)"
]

# Sectors
sectors = [
    "Faisalabad - Dubai - Jeddah - Dubai - Faisalabad",
    "Faisalabad - Dubai - Riyadh",
    "Faisalabad - Jeddah - Faisalabad",
    "Faisalabad - Sharjah - Jeddah - Sharjah - Faisalabad",
    "Islamabad - Abu Dhabi",
    "Islamabad - Bahrain",
    "Islamabad - Dammam",
    "Islamabad - Dubai",
    "Islamabad - Jeddah",
    "Islamabad - Jeddah - Islamabad",
    "Islamabad - Jeddah (Verbatim)",
    "Islamabad - Muscat - Jeddah",
    "Islamabad - Muscat - Riyadh",
    "Islamabad - Riyadh",
    "Islamabad - Riyadh - Jeddah - Islamabad",
    "Islamabad - Sharjah",
    "Islamabad - Sharjah - Riyadh",
    "Lahore - Abu Dhabi",
    "Lahore - Dammam",
    "Lahore - Dubai",
    "Lahore - Jeddah - Lahore",
    "Lahore - Muscat - Jeddah",
    "Lahore - Muscat - Jeddah - Muscat - Lahore",
    "Lahore - Riyadh",
    "Multan - Dubai - Riyadh",
    "Multan - Jeddah - Multan",
    "Peshawar - Doha - Jeddah - Doha - Peshawar",
    "Peshawar - Doha - Riyadh",
    "Peshawar - Dubai - Jeddah - Dubai - Peshawar",
    "Peshawar - Dubai - Riyadh",
    "Peshawar - Jeddah",
    "Peshawar - Jeddah - Peshawar",
    "Peshawar - Muscat - Jeddah - Muscat - Peshawar",
    "Peshawar - Muscat - Riyadh",
    "Peshawar - Riyadh",
    "Peshawar - Sharjah",
    "Sialkot - Dubai",
    "Sialkot - Riyadh"
]

# Travel Types
travel_types = [
    "Umrah",
    "UAE One Way",
    "KSA One Way",
    "Qatar Groups",
    "Oman One Way",
    "Bahrain One Way",
    "UK One Way"
]

def seed_config():
    """Seed system configuration"""
    print("Starting system configuration seeding...")
    
    # Clear existing configs (optional - comment out if you want to keep existing)
    # SystemConfig.objects.delete()
    # print("Cleared existing configurations")
    
    # Add Airlines
    print("\nAdding Airlines...")
    for airline in airlines:
        existing = SystemConfig.objects(config_type='airline', value=airline).first()
        if not existing:
            config = SystemConfig(config_type='airline', value=airline)
            config.save()
            print(f"  ✓ Added: {airline}")
        else:
            print(f"  - Skipped (exists): {airline}")
    
    # Add Sectors
    print("\nAdding Sectors...")
    for sector in sectors:
        existing = SystemConfig.objects(config_type='sector', value=sector).first()
        if not existing:
            config = SystemConfig(config_type='sector', value=sector)
            config.save()
            print(f"  ✓ Added: {sector}")
        else:
            print(f"  - Skipped (exists): {sector}")
    
    # Add Travel Types
    print("\nAdding Travel Types...")
    for travel_type in travel_types:
        existing = SystemConfig.objects(config_type='travel_type', value=travel_type).first()
        if not existing:
            config = SystemConfig(config_type='travel_type', value=travel_type)
            config.save()
            print(f"  ✓ Added: {travel_type}")
        else:
            print(f"  - Skipped (exists): {travel_type}")
    
    # Summary
    print("\n" + "="*60)
    print("SEEDING COMPLETE!")
    print("="*60)
    print(f"Airlines: {SystemConfig.objects(config_type='airline', is_active=True).count()}")
    print(f"Sectors: {SystemConfig.objects(config_type='sector', is_active=True).count()}")
    print(f"Travel Types: {SystemConfig.objects(config_type='travel_type', is_active=True).count()}")
    print("="*60)

if __name__ == '__main__':
    with app.app_context():
        seed_config()
