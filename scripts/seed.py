import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from mongoengine import disconnect

# Ensure app is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.agency import Agency, ContactInfo, Branding
from models.user import User
from models.customer import Customer
from models.visa_case import VisaCase, VisaStatusHistory
from models.quotation import Quotation, LineItem
from models.booking import Booking
from models.package import Package
from models.ledger import LedgerEntry
import bcrypt

app = create_app()

def seed_data():
    with app.app_context():
        print("Clearing Database...")
        # Get DB name from URI
        uri = app.config['MONGODB_SETTINGS']['host'] if 'MONGODB_SETTINGS' in app.config else os.getenv('MONGODB_URI')
        db_name = uri.split('/')[-1].split('?')[0]
        
        from mongoengine.connection import get_connection
        try:
            conn = get_connection()
            conn.drop_database(db_name)
        except Exception:
            # Maybe not connected yet or connection alias issue
            pass

        print("Seeding Agency...")
        agency = Agency(
            name="Bannu Pilot Travels",
            status="Active",
            subscriptionPlan="Premium",
            contactInfo=ContactInfo(
                phone="+923001234567",
                email="info@bannupilot.com",
                address="Bannu, KPK"
            ),
            branding=Branding(logoUrl="https://example.com/logo.png")
        ).save()

        print("Seeding Users...")
        # Create Owner
        hashed = bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode('utf-8')
        owner = User(
            agencyId=agency,
            email="admin@bannupilot.com",
            passwordHash=hashed,
            role="AgencyOwner",
            name="Shamsullah Khan",
            permissions=["ALL"]
        ).save()

        # Create Super Admin
        super_admin = User(
            email="superadmin@bannu.com",
            passwordHash=bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode('utf-8'),
            role="SuperAdmin",
            name="Super Admin",
            permissions=["ALL"]
        ).save()

        # ... (Rest is same logic, just objects)
        print("Seeding Customers...")
        c1 = Customer(
            agencyId=agency,
            fullName="Tariq Jamil",
            phone="+923335555555",
            passportNumber="A1234567",
            passportExpiry=datetime.utcnow() + timedelta(days=365*2),
            gender="Male",
            address="Lahore"
        ).save()
        
        print("Done! Database seeded.")
        print("Login with: admin@bannupilot.com / admin")

if __name__ == "__main__":
    seed_data()
