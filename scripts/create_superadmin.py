from app import create_app
from models.agency import Agency
from models.user import User
import mongoengine
from werkzeug.security import generate_password_hash

app = create_app()

def create_superadmin():
    # Find or create main agency
    agency = Agency.objects.first()
    if not agency:
        print("No agency found, creating one...")
        agency = Agency(
            name="Bannu Pilot Super Admin",
            email="superadmin@example.com",
            phone="0000000000",
            address="System",
            city="System"
        )
        agency.save()
        print("Created agency")
    else:
        print(f"Using existing agency: {agency.name}")

    # Create SuperAdmin user
    user = User(
        email='superadmin@example.com',
        passwordHash=generate_password_hash('admin123'),
        name='Super Admin',
        role='SuperAdmin',
        agencyId=agency
    )
    user.save()
    print("SuperAdmin user created successfully!")
    print("Email: superadmin@example.com")
    print("Password: admin123")

if __name__ == '__main__':
    with app.app_context():
        create_superadmin()
