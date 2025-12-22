from flask import Blueprint, request, jsonify, g
from app.middleware import token_required
from models.facility import Facility, Transport, TransportRoute, Ticket, Ziarat, Moaleem, Umrahs
from app.utils.serializers import mongo_to_dict
from app.utils.error_handlers import error_response, validation_error, not_found_error
from datetime import datetime

facilities_bp = Blueprint('facilities', __name__)

def validate_facility_data(data):
    errors = {}
    
    # Transport Validation
    if data.get('transport', {}).get('status') == 'Yes':
        transport = data.get('transport', {})
        routes = transport.get('routes', [])
        
        if not routes or len(routes) == 0:
             errors['transport_routes'] = 'At least one route is required when Transport is Yes'
        else:
            for i, route in enumerate(routes):
                if not route.get('transport_from'):
                    errors[f'transport_routes_{i}_from'] = f'Route {i+1}: From location is required'
                if not route.get('transport_to'):
                    errors[f'transport_routes_{i}_to'] = f'Route {i+1}: To location is required'
            
    # Ticket Validation
    if data.get('ticket', {}).get('status') == 'Yes':
        if not data.get('ticket', {}).get('ticket_type'):
            errors['ticket_type'] = 'Ticket Type is required when Ticket is Yes'
            
    # Ziarat Validation
    if data.get('ziarat', {}).get('status') == 'Yes':
        ziarat = data.get('ziarat', {})
        if not ziarat.get('major_ziarat') or len(ziarat.get('major_ziarat')) == 0:
            errors['major_ziarat'] = 'At least one Major Ziarat must be selected'
        if not ziarat.get('ziarat_count'):
            errors['ziarat_count'] = 'Ziarat Count is required'
            
    # Moaleem Validation
    if data.get('moaleem', {}).get('status') == 'Yes':
        moaleem = data.get('moaleem', {})
        if not moaleem.get('moaleem_name'):
            errors['moaleem_name'] = 'Moaleem Name is required'
        if not moaleem.get('moaleem_contact'):
            errors['moaleem_contact'] = 'Moaleem Contact is required'
            
    # Umrahs Validation
    if data.get('umrahs', {}).get('status') == 'Yes':
        if not data.get('umrahs', {}).get('umrahs_count'):
            errors['umrahs_count'] = 'Umrahs Count is required'
            
    return errors

@facilities_bp.route('', methods=['GET'])
@token_required
def get_facilities():
    facilities = Facility.objects(agencyId=g.agency_id).order_by('-createdAt')
    return jsonify(mongo_to_dict(facilities)), 200

@facilities_bp.route('', methods=['POST'])
@token_required
def create_facility():
    data = request.get_json()
    print(f"DEBUG: create_facility received data: {data}") # Debug log
    if not data:
        return error_response("No data provided", "INVALID_REQUEST")
        
    validation_errors = validate_facility_data(data)
    if validation_errors:
        return validation_error(validation_errors)
        
    try:
        # transport processing
        transport_data = data.get('transport', {'status': 'No'})
        transport_routes = []
        if transport_data.get('status') == 'Yes':
            for route in transport_data.get('routes', []):
                transport_routes.append(TransportRoute(
                    transport_from=route.get('transport_from'),
                    transport_to=route.get('transport_to')
                ))
        
        facility = Facility(
            agencyId=g.agency_id,
            hotel=data.get('hotel', 'No'),
            visa=data.get('visa', 'No'),
            food=data.get('food', 'No'),
            medical=data.get('medical', 'No'),
            transport=Transport(status=transport_data.get('status'), routes=transport_routes),
            ticket=Ticket(**data.get('ticket', {'status': 'No'})),
            ziarat=Ziarat(**data.get('ziarat', {'status': 'No'})),
            moaleem=Moaleem(**data.get('moaleem', {'status': 'No'})),
            umrahs=Umrahs(**data.get('umrahs', {'status': 'No'}))
        )
        facility.save()
        return jsonify(mongo_to_dict(facility)), 201
    except Exception as e:
        return error_response(str(e), "SERVER_ERROR", 500)

@facilities_bp.route('/<id>', methods=['GET'])
@token_required
def get_facility(id):
    facility = Facility.objects(id=id, agencyId=g.agency_id).first()
    if not facility:
        return not_found_error("Facility not found")
    return jsonify(mongo_to_dict(facility)), 200

@facilities_bp.route('/<id>', methods=['PUT'])
@token_required
def update_facility(id):
    facility = Facility.objects(id=id, agencyId=g.agency_id).first()
    if not facility:
        return not_found_error("Facility not found")
        
    data = request.get_json()
    validation_errors = validate_facility_data(data)
    if validation_errors:
        return validation_error(validation_errors)
        
    try:
        if 'hotel' in data: facility.hotel = data['hotel']
        if 'visa' in data: facility.visa = data['visa']
        if 'food' in data: facility.food = data['food']
        if 'medical' in data: facility.medical = data['medical']
        
        if 'transport' in data:
            transport_data = data['transport']
            transport_routes = []
            if transport_data.get('status') == 'Yes':
                for route in transport_data.get('routes', []):
                    transport_routes.append(TransportRoute(
                        transport_from=route.get('transport_from'),
                        transport_to=route.get('transport_to')
                    ))
            facility.transport = Transport(status=transport_data.get('status'), routes=transport_routes)
            
        if 'ticket' in data:
            facility.ticket = Ticket(**data['ticket'])
        if 'ziarat' in data:
            facility.ziarat = Ziarat(**data['ziarat'])
        if 'moaleem' in data:
            facility.moaleem = Moaleem(**data['moaleem'])
        if 'umrahs' in data:
            facility.umrahs = Umrahs(**data['umrahs'])
            
        facility.save()
        return jsonify(mongo_to_dict(facility)), 200
    except Exception as e:
        return error_response(str(e), "SERVER_ERROR", 500)

@facilities_bp.route('/<id>', methods=['DELETE'])
@token_required
def delete_facility(id):
    facility = Facility.objects(id=id, agencyId=g.agency_id).first()
    if not facility:
        return not_found_error("Facility not found")
        
    try:
        facility.delete()
        return jsonify({'message': 'Facility deleted successfully'}), 200
    except Exception as e:
        return error_response(str(e), "SERVER_ERROR", 500)
