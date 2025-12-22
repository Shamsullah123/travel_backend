from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)

from app.utils.serializers import mongo_to_dict

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing credentials'}), 400
        
    result, error = AuthService.login(data['email'], data['password'])
    
    if error:
        return jsonify({'error': error}), 401
    
    # result contains 'user' dict which is already serializable, so no change needed here actually.
    # But let's verify AuthService implementation. 
    # AuthService.login returns dict built from user fields via string access.
    # So Auth is fine. I will skip patching Auth for now if it's returning dicts.
    return jsonify(result), 200

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    data = request.get_json()
    if not data or not data.get('refreshToken'):
        return jsonify({'error': 'Refresh token is required'}), 400
        
    result, error = AuthService.refresh_token(data['refreshToken'])
    
    if error:
        return jsonify({'error': error}), 401
        
    return jsonify(result), 200

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    required_fields = ['agencyName', 'adminName', 'email', 'password', 'mobileNumber']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400
            
    result, error = AuthService.register_agency(data)
    
    if error:
        return jsonify({'error': error}), 400
        
    return jsonify(result), 201
