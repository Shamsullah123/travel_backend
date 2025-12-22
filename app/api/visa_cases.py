from flask import Blueprint, request, jsonify, g
from app.middleware import token_required
from models.visa_case import VisaCase
from app.services.visa_service import VisaService

visa_cases_bp = Blueprint('visa_cases', __name__)

from app.utils.serializers import mongo_to_dict

@visa_cases_bp.route('', methods=['GET'])
@token_required
def get_cases():
    query = VisaCase.objects(agencyId=g.agency_id)
    # Filter by status
    status = request.args.get('status')
    if status:
        query = query.filter(status=status)
        
    cases = query.order_by('-updatedAt')
    
    # Manually populate customer names
    results = []
    for case in cases:
        c_dict = mongo_to_dict(case)
        try:
            if case.customerId:
                # Dereference the customer
                customer = case.customerId
                c_dict['customerName'] = customer.fullName if hasattr(customer, 'fullName') else 'Unknown'
                c_dict['customerPhone'] = customer.phone if hasattr(customer, 'phone') else ''
            else:
                c_dict['customerName'] = 'Unknown'
                c_dict['customerPhone'] = ''
        except Exception as e:
            print(f"Error dereferencing customer for case {case.id}: {e}")
            c_dict['customerName'] = 'Unknown'
            c_dict['customerPhone'] = ''
        results.append(c_dict)
        
    return jsonify(results), 200

@visa_cases_bp.route('', methods=['POST'])
@token_required
def create_case():
    data = request.get_json()
    try:
        case = VisaCase(
            agencyId=g.agency_id,
            customerId=data['customerId'],
            country=data['country'],
            visaType=data['visaType'],
            status='New'
        )
        case.save()
        return jsonify(mongo_to_dict(case)), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@visa_cases_bp.route('/<id>/status', methods=['POST'])
@token_required
def update_status(id):
    data = request.get_json()
    new_status = data.get('status')
    notes = data.get('notes')
    
    case = VisaCase.objects(id=id, agencyId=g.agency_id).first()
    if not case:
        return jsonify({'error': 'Case not found'}), 404
        
    success, result = VisaService.change_status(case, new_status, g.user_id, notes)
    
    if not success:
        return jsonify({'error': result}), 400
        
    return jsonify(mongo_to_dict(result)), 200
