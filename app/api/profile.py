from flask import Blueprint, request, jsonify, g
from app.middleware import token_required
from models.user import User
from models.agency import Agency
from app.utils.serializers import mongo_to_dict
import bcrypt

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/me', methods=['GET'])
@token_required
def get_profile():
    """Get current user's profile"""
    try:
        user = User.objects(id=g.user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        profile_data = {
            'id': str(user.id),
            'name': user.name,
            'email': user.email,
            'phone': user.phone or '',
            'role': user.role,
            'agencyId': str(user.agencyId.id) if user.agencyId else None,
            'agencyName': user.agencyId.name if user.agencyId else None,
            'isActive': user.isActive,
            'createdAt': user.createdAt.isoformat() if user.createdAt else None
        }
        
        return jsonify(profile_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/me', methods=['PUT'])
@token_required
def update_profile():
    """Update current user's profile (name, email)"""
    try:
        user = User.objects(id=g.user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone', '')
        
        # Validate inputs
        if not name or not email:
            return jsonify({'error': 'Name and email are required'}), 400
        
        # Check if email is being changed and if it's already taken
        if email != user.email:
            existing_user = User.objects(email=email).first()
            if existing_user:
                return jsonify({'error': 'Email already in use'}), 400
        
        # Update user
        user.name = name
        user.email = email
        user.phone = phone
        user.save()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': {
                'id': str(user.id),
                'name': user.name,
                'email': user.email,
                'phone': user.phone
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/change-password', methods=['POST'])
@token_required
def change_password():
    """Change user's password"""
    try:
        user = User.objects(id=g.user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        current_password = data.get('currentPassword')
        new_password = data.get('newPassword')
        
        # Validate inputs
        if not current_password or not new_password:
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        # Validate password strength
        if len(new_password) < 6:
            return jsonify({'error': 'New password must be at least 6 characters long'}), 400
        
        # Verify current password
        if not bcrypt.checkpw(current_password.encode('utf-8'), user.passwordHash.encode('utf-8')):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Hash new password
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        user.passwordHash = hashed_password.decode('utf-8')
        user.save()
        
        return jsonify({'message': 'Password changed successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
