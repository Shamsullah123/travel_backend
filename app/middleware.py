from functools import wraps
from flask import request, jsonify, current_app, g
import jwt

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        print(f"DEBUG Headers for {request.path}: {request.headers}", flush=True)
        
        auth_header = request.headers.get('Authorization') or request.headers.get('X-Auth-Token')
        
        if auth_header:
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
            else:
                token = auth_header # Allow direct token in X-Auth-Token
        
        if not token:
            return jsonify({'message': 'Token is missing!', 'code': 'TOKEN_MISSING'}), 401
            
        try:
            print(f"Middleware Debug: Decoding token for {request.path}")
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            # print(f"Decoded Data: {data}")
            g.user_id = data['sub']
            g.agency_id = data.get('agencyId')
            g.role = data.get('role')
        except jwt.ExpiredSignatureError:
            print(f"Token Expired: {token[:10]}...")
            return jsonify({'message': 'Token has expired!', 'code': 'TOKEN_EXPIRED'}), 401
        except jwt.InvalidTokenError as e:
            print(f"Token Invalid: {e} - Token: {token[:20]}... key: {current_app.config['SECRET_KEY']}")
            return jsonify({'message': 'Token is invalid!', 'code': 'TOKEN_INVALID'}), 401
        except Exception as e:
            return jsonify({'message': 'Token processing error', 'code': 'TOKEN_ERROR'}), 401
            
        return f(*args, **kwargs)
    
    return decorated

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Ensure g.role exists (token_required should have set it)
            if not hasattr(g, 'role'):
                return jsonify({'message': 'Authentication required', 'code': 'AUTH_REQUIRED'}), 401
                
            if isinstance(roles, list):
                if g.role not in roles:
                    return jsonify({'message': 'Permission denied', 'code': 'FORBIDDEN'}), 403
            elif g.role != roles:
                return jsonify({'message': 'Permission denied', 'code': 'FORBIDDEN'}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator
