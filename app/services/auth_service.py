import jwt
import datetime
import bcrypt
from flask import current_app
from models.user import User

class AuthService:
    @staticmethod
    def login(email, password):
        print(f"DEBUG: Attempting login for {email}")
        user = User.objects(email=email).first()
        if not user:
            print(f"DEBUG: User not found: {email}")
            return None, "User not found"
        
        print(f"DEBUG: User found: {user.id}, Role: {user.role}")
        print(f"DEBUG: Stored Hash: {user.passwordHash}")
        print(f"DEBUG: Attempting with: {password}")
        
        if not bcrypt.checkpw(password.encode('utf-8'), user.passwordHash.encode('utf-8')):
            print(f"DEBUG: Password mismatch for {email}")
            return None, "Invalid password"
            
        if not user.isActive:
            print(f"DEBUG: User inactive: {email}")
            return None, "Account disabled"

        # Check Agency Status for non-SuperAdmins
        if user.role != 'SuperAdmin':
            # Ensure agency is loaded
            if not user.agencyId:
                 print(f"DEBUG: User {email} has no agency assigned")
                 return None, "System error: No agency assigned"
            
            agency = user.agencyId
            print(f"DEBUG: Agency Status: {agency.status}")
            
            if agency.status != 'Active':
                if agency.status == 'Pending':
                     return None, "Your agency registration is pending approval. Please wait for admin approval."
                elif agency.status == 'Suspended':
                     return None, "Your agency has been suspended. Please contact support."
                elif agency.status == 'Rejected':
                     return None, "Your agency registration has been rejected. Please contact support."
                else:
                     return None, f"Agency status is {agency.status}. Login denied."

        print(f"DEBUG: Login successful for {email}")
        # Generate Tokens
        access_token = AuthService.create_access_token(user)
        refresh_token = AuthService.create_refresh_token(user)
        
        return {
            'accessToken': access_token,
            'refreshToken': refresh_token,
            'user': {
                'id': str(user.id),
                'email': user.email,
                'name': user.name,
                'role': user.role,
                'agencyId': str(user.agencyId.id),
                'agencyName': user.agencyId.name
            }
        }, None

    @staticmethod
    def create_access_token(user):
        payload = {
            'sub': str(user.id),
            'agencyId': str(user.agencyId.id),
            'role': user.role,
            'type': 'access',
            'iat': datetime.datetime.utcnow(),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)
        }
        return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def create_refresh_token(user):
        payload = {
            'sub': str(user.id),
            'type': 'refresh',
            'iat': datetime.datetime.utcnow(),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def refresh_token(token):
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            if payload.get('type') != 'refresh':
                return None, "Invalid token type"
            
            user = User.objects(id=payload['sub']).first()
            if not user or not user.isActive:
                return None, "User not found or inactive"
                
            new_access_token = AuthService.create_access_token(user)
            return {'accessToken': new_access_token}, None
        except jwt.ExpiredSignatureError:
            return None, "Token has expired"
        except jwt.InvalidTokenError:
            return None, "Invalid token"
        except Exception as e:
            return None, f"Token processing error: {str(e)}"
            
    @staticmethod
    def register_agency(data):
        from models.agency import Agency
        
        # Check existing user
        if User.objects(email=data.get('email')).first():
            return None, "Email already exists"
            
        try:
            # 1. Create Agency (Pending)
            agency = Agency(
                name=data.get('agencyName'),
                status='Pending',
                contactInfo={'phone': data.get('mobileNumber')}
            )
            agency.save()
            
            # 2. Create Agency Admin User
            salt = bcrypt.gensalt()
            hashed_pw = bcrypt.hashpw(data.get('password').encode('utf-8'), salt).decode('utf-8')
            
            user = User(
                agencyId=agency,
                email=data.get('email'),
                passwordHash=hashed_pw,
                name=data.get('adminName'),
                phone=data.get('mobileNumber'),
                role='AgencyAdmin',
                isActive=True
            )
            user.save()
            
            # Generate Tokens
            access_token = AuthService.create_access_token(user)
            refresh_token = AuthService.create_refresh_token(user)
            
            return {
                'message': 'Registration successful',
                'accessToken': access_token,
                'refreshToken': refresh_token,
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'name': user.name,
                    'role': user.role,
                    'agencyId': str(agency.id),
                    'agencyName': agency.name
                }
            }, None
        except Exception as e:
            return None, f"Registration failed: {str(e)}"
