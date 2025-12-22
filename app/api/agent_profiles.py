from flask import Blueprint, request, jsonify, g
from app.middleware import token_required
from models.agent_profile import AgentProfile
from app.utils.serializers import mongo_to_dict
from app.utils.error_handlers import error_response, validation_error, not_found_error

agent_profiles_bp = Blueprint('agent_profiles', __name__)

@agent_profiles_bp.route('', methods=['POST'])
@token_required
def create_profile():
    data = request.get_json()
    if not data:
        return error_response("No data provided", "INVALID_REQUEST")
    
    if 'name' not in data or 'mobile_number' not in data:
        return validation_error({'name': 'Required', 'mobile_number': 'Required'})

    try:
        # Check uniqueness
        existing = AgentProfile.objects(agencyId=g.agency_id, mobile_number=data['mobile_number']).first()
        if existing:
            return validation_error({'mobile_number': 'Agent with this mobile number already exists'})

        profile = AgentProfile(
            name=data['name'],
            source_name=data.get('source_name', ''),
            mobile_number=data['mobile_number'],
            cnic=data.get('cnic', ''),
            agencyId=g.agency_id
        )
        profile.save()
        
        return jsonify(mongo_to_dict(profile)), 201

    except Exception as e:
        return error_response(str(e), "SERVER_ERROR", 500)

@agent_profiles_bp.route('', methods=['GET'])
@token_required
def get_profiles():
    profiles = AgentProfile.objects(agencyId=g.agency_id).order_by('name')
    return jsonify(mongo_to_dict(profiles)), 200

@agent_profiles_bp.route('/<id>', methods=['PUT'])
@token_required
def update_profile(id):
    data = request.get_json()
    profile = AgentProfile.objects(id=id, agencyId=g.agency_id).first()
    
    if not profile:
        return not_found_error("Agent Profile not found")
        
    try:
        if 'name' in data: profile.name = data['name']
        if 'source_name' in data: profile.source_name = data['source_name']
        if 'mobile_number' in data:
            # Check for conflict
            existing = AgentProfile.objects(agencyId=g.agency_id, mobile_number=data['mobile_number'], id__ne=id).first()
            if existing:
                return validation_error({'mobile_number': 'Another agent has this mobile number'})
            profile.mobile_number = data['mobile_number']
        if 'cnic' in data: profile.cnic = data['cnic']
        
        profile.save()
        return jsonify(mongo_to_dict(profile)), 200
        
    except Exception as e:
        return error_response(str(e), "SERVER_ERROR", 500)

@agent_profiles_bp.route('/<id>', methods=['DELETE'])
@token_required
def delete_profile(id):
    profile = AgentProfile.objects(id=id, agencyId=g.agency_id).first()
    if not profile:
        return not_found_error("Agent Profile not found")
    
    try:
        profile.delete()
        return jsonify({"message": "Profile deleted"}), 200
    except Exception as e:
        return error_response(str(e), "SERVER_ERROR", 500)
