from flask import Blueprint, request, jsonify
from app.middleware import token_required, role_required
from models.agency import Agency
from models.user import User
from models.contact_message import ContactMessage
from models.system_setting import SystemSetting
from models.booking import Booking
from app.utils.serializers import mongo_to_dict
from app.services.auth_service import AuthService
from mongoengine.queryset.visitor import Q
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/stats', methods=['GET'])
@token_required
@role_required('SuperAdmin')
def get_dashboard_stats():
    # 1. Agency Stats
    total_agencies = Agency.objects.count()
    active_agencies = Agency.objects(status='Active').count()
    pending_agencies = Agency.objects(status='Pending').count()
    
    # 2. Revenue/Booking Stats (Aggregate from all bookings)
    # This might be heavy if many bookings, but fine for MVP
    total_bookings = Booking.objects.count()
    recent_bookings = Booking.objects(createdAt__gte=datetime.utcnow() - timedelta(days=30)).count()
    
    return jsonify({
        'agencies': {
            'total': total_agencies,
            'active': active_agencies,
            'pending': pending_agencies
        },
        'bookings': {
            'total': total_bookings,
            'recent_30_days': recent_bookings
        }
    }), 200

@admin_bp.route('/agencies', methods=['GET'])
@token_required
@role_required('SuperAdmin')
def list_agencies():
    status_filter = request.args.get('status')
    search = request.args.get('search')
    
    query = Q()
    if status_filter:
        query &= Q(status=status_filter)
    
    if search:
        query &= Q(name__icontains=search)
        
    agencies = Agency.objects(query).order_by('-createdAt')
    
    # Enrich with Admin Email
    agency_list = []
    for agency in agencies:
        data = mongo_to_dict(agency)
        # Find the SuperAdmin/AgencyAdmin for this agency
        admin_user = User.objects(agencyId=agency.id, role__in=['AgencyAdmin', 'SuperAdmin']).first()
        data['adminEmail'] = admin_user.email if admin_user else 'N/A'
        agency_list.append(data)
        
    return jsonify(agency_list), 200

@admin_bp.route('/agencies/<id>/status', methods=['PUT'])
@token_required
@role_required('SuperAdmin')
def update_agency_status(id):
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in ['Active', 'Suspended', 'Pending', 'Rejected']:
        return jsonify({'error': 'Invalid status'}), 400
        
    agency = Agency.objects(id=id).first()
    if not agency:
        return jsonify({'error': 'Agency not found'}), 404
        
    agency.status = new_status
    agency.save()
    
    # If suspended/rejected, maybe we want to deactivate users?
    # For now keeping it simple.
    
    return jsonify(mongo_to_dict(agency)), 200

@admin_bp.route('/agencies/<id>/reset-password', methods=['POST'])
@token_required
@role_required('SuperAdmin')
def reset_agency_password(id):
    from bson import ObjectId
    
    data = request.get_json()
    new_password = data.get('password')
    
    if not new_password:
        return jsonify({'error': 'New password is required'}), 400
    
    # Convert string ID to ObjectId for querying
    try:
        agency_obj_id = ObjectId(id)
    except:
        return jsonify({'error': 'Invalid agency ID'}), 400
        
    # Find the main admin user for this agency
    # Assumption: The user created during registration is the 'AgencyAdmin'
    admin_user = User.objects(agencyId=agency_obj_id, role='AgencyAdmin').first()
    
    if not admin_user:
        return jsonify({'error': 'Agency admin user not found'}), 404
        
    # Use AuthService helper or direct update
    hashed = AuthService.hash_password(new_password)
    admin_user.passwordHash = hashed
    admin_user.save()
    
    return jsonify({'message': 'Password reset successfully'}), 200

@admin_bp.route('/messages', methods=['GET'])
@token_required
@role_required('SuperAdmin')
def get_messages():
    messages = ContactMessage.objects.all()
    return jsonify([mongo_to_dict(m) for m in messages]), 200

@admin_bp.route('/settings', methods=['GET', 'PUT'])
@token_required
@role_required('SuperAdmin')
def manage_settings():
    if request.method == 'GET':
        settings = SystemSetting.objects.all()
        # Convert list to a key-value dict for easier frontend consumption
        result = {s.key: s.value for s in settings}
        return jsonify(result), 200
        
    elif request.method == 'PUT':
        data = request.get_json()
        updated = {}
        for key, value in data.items():
            setting = SystemSetting.objects(key=key).first()
            if not setting:
                setting = SystemSetting(key=key)
            setting.value = value
            setting.updatedAt = datetime.utcnow()
            setting.save()
            updated[key] = value
            
        return jsonify(updated), 200
