import os
import sys
from mongoengine import disconnect
import bcrypt

# Ensure app is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.agency import Agency
from models.user import User

app = create_app()

def seed_super_admin():
    with app.app_context():
        print("Seeding Super Admin...")
        
        # Helper: Ensure we have at least one agency
        agency = Agency.objects.first()
        if not agency:
            print("Creating dummy agency...")
            agency = Agency(name="System Agency", status="Active").save()
            
        email = "superadmin@bannu.com"
        existing = User.objects(email=email).first()
        if existing:
            existing.delete()
            
        hashed = bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode('utf-8')
        
        super_admin = User(
            agencyId=agency,
            email=email,
            passwordHash=hashed,
            role="SuperAdmin",
            name="System Admin",
            permissions=["ALL"]
        ).save()
        
        print(f"Super Admin Created: {email} / admin")

if __name__ == "__main__":
    seed_super_admin()
