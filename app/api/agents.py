from flask import Blueprint, request, jsonify, current_app, g
from models.agent import Agent
from models.agency import Agency
from app.middleware import token_required
from app.utils.serializers import mongo_to_dict
from app.utils.error_handlers import error_response, validation_error, not_found_error
from mongoengine.errors import ValidationError, DoesNotExist
from mongoengine.errors import ValidationError, DoesNotExist


agents_bp = Blueprint('agents', __name__)

from app.utils.file_handler import save_file, allowed_file

@agents_bp.route('/', methods=['GET'])
@token_required
def get_agents():
    try:
        # Filter by current agency
        agency_id = g.agency_id
        
        # Search filters
        query = request.args.get('search')
        
        agents_query = Agent.objects(created_by_agency=agency_id)
        
        if query:
            # Simple case-insensitive search on name, mobile, source name
            from mongoengine.queryset.visitor import Q
            agents_query = agents_query.filter(
                Q(agent_name__icontains=query) | 
                Q(mobile_number__icontains=query) | 
                Q(source_name__icontains=query) |
                Q(source_cnic_number__icontains=query) |
                Q(slip_number__icontains=query)
            )
            
        agents_query = agents_query.order_by('-created_at')
        return jsonify(mongo_to_dict(agents_query)), 200
        
    except Exception as e:
        return error_response(str(e), "SERVER_ERROR", 500)

@agents_bp.route('/', methods=['POST'])
@token_required
def create_agent():
    try:
        data = request.form.to_dict()
        cnic_file = request.files.get('source_cnic_attachment')
        slip_file = request.files.get('slip_attachment')
        
        # Validation
        required_fields = ['agent_name', 'source_name', 'mobile_number']
        for field in required_fields:
            if not data.get(field):
                return validation_error({field: 'Required field'})
                
        # File Upload handling
        cnic_path = save_file(cnic_file, 'agents/cnic')
        slip_path = save_file(slip_file, 'agents/slips')
        
        agent = Agent(
            agent_name=data.get('agent_name'),
            source_name=data.get('source_name'),
            source_cnic_number=data.get('source_cnic_number'),
            source_cnic_attachment=cnic_path,
            slip_number=data.get('slip_number'),
            slip_attachment=slip_path,
            mobile_number=data.get('mobile_number'),
            description=data.get('description'),
            amount_paid=int(data.get('amount_paid')) if data.get('amount_paid') else 0,
            created_by_agency=g.agency_id
        )
        
        agent.save()
        
        return jsonify(mongo_to_dict(agent)), 201
        
    except ValidationError as e:
        return validation_error(e.to_dict())
    except Exception as e:
        return error_response(str(e), "SERVER_ERROR", 500)

@agents_bp.route('/<id>', methods=['GET'])
@token_required
def get_agent(id):
    try:
        agent = Agent.objects.get(id=id, created_by_agency=g.agency_id)
        return jsonify(mongo_to_dict(agent)), 200
        
    except DoesNotExist:
        return not_found_error("Agent not found")
    except Exception as e:
        return error_response(str(e), "SERVER_ERROR", 500)

@agents_bp.route('/<id>', methods=['PUT'])
@token_required
def update_agent(id):
    try:
        agent = Agent.objects.get(id=id, created_by_agency=g.agency_id)
        data = request.form.to_dict()
        cnic_file = request.files.get('source_cnic_attachment')
        slip_file = request.files.get('slip_attachment')
        
        if 'agent_name' in data: agent.agent_name = data['agent_name']
        if 'source_name' in data: agent.source_name = data['source_name']
        if 'source_cnic_number' in data: agent.source_cnic_number = data['source_cnic_number']
        if 'slip_number' in data: agent.slip_number = data['slip_number']
        if 'mobile_number' in data: agent.mobile_number = data['mobile_number']
        if 'mobile_number' in data: agent.mobile_number = data['mobile_number']
        if 'description' in data: agent.description = data['description']
        if 'amount_paid' in data: agent.amount_paid = int(data['amount_paid']) if data['amount_paid'] else 0
        
        cnic_path = save_file(cnic_file, 'agents/cnic')
        if cnic_path:
            agent.source_cnic_attachment = cnic_path
            
        slip_path = save_file(slip_file, 'agents/slips')
        if slip_path:
            agent.slip_attachment = slip_path
            
        agent.save()
        
        return jsonify(mongo_to_dict(agent)), 200
        
    except DoesNotExist:
        return not_found_error("Agent not found")
    except Exception as e:
        return error_response(str(e), "SERVER_ERROR", 500)

@agents_bp.route('/<id>', methods=['DELETE'])
@token_required
def delete_agent(id):
    try:
        agent = Agent.objects.get(id=id, created_by_agency=g.agency_id)
        agent.delete()
        return jsonify({'message': 'Agent deleted successfully'}), 200
    except DoesNotExist:
        return not_found_error("Agent not found")
    except Exception as e:
        return error_response(str(e), "SERVER_ERROR", 500)
