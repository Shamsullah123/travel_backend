import pytest
from app import create_app
from models.agency import Agency
from models.user import User
import bcrypt
import jwt
from datetime import datetime, timedelta

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['MONGODB_SETTINGS'] = {
        'host': 'mongomock://localhost'
    }
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_header(app):
    # Setup Agency
    agency = Agency(name="Test Agency").save()
    
    # Setup User
    user = User(
        agencyId=agency,
        email="test@test.com",
        passwordHash=bcrypt.hashpw(b"password", bcrypt.gensalt()).decode('utf-8'),
        role="AgencyOwner",
        name="Test User"
    ).save()
    
    # Generate Token
    token = jwt.encode({
        'sub': str(user.id),
        'agencyId': str(agency.id),
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(days=1)
    }, app.config['SECRET_KEY'], algorithm='HS256')
    
    return {
        'Authorization': f'Bearer {token}'
    }
