from flask import Blueprint, request, jsonify, g
from app.middleware import token_required
from models.system_config import SystemConfig
from app.utils.serializers import mongo_to_dict

system_config_bp = Blueprint('system_config', __name__)

@system_config_bp.route('/', methods=['GET'])
def get_config():
    """Get system configuration values by type (public endpoint)"""
    try:
        config_type = request.args.get('type')  # airline, sector, travel_type
        
        query = {'is_active': True}
        if config_type:
            if config_type not in ['airline', 'sector', 'travel_type']:
                return jsonify({'error': 'Invalid config type'}), 400
            query['config_type'] = config_type
        
        configs = SystemConfig.objects(**query).order_by('value')
        
        # Group by type
        result = {}
        for config in configs:
            config_type_key = config.config_type
            if config_type_key not in result:
                result[config_type_key] = []
            result[config_type_key].append({
                'id': str(config.id),
                'value': config.value,
                'created_at': config.created_at.isoformat() if config.created_at else None
            })
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@system_config_bp.route('/', methods=['POST'])
@token_required
def add_config():
    """Add new system configuration (SuperAdmin only)"""
    if g.role != 'SuperAdmin':
        return jsonify({'error': 'Unauthorized - SuperAdmin only'}), 403
    
    try:
        data = request.get_json()
        config_type = data.get('config_type')
        value = data.get('value', '').strip()
        
        if not config_type or not value:
            return jsonify({'error': 'config_type and value are required'}), 400
        
        if config_type not in ['airline', 'sector', 'travel_type']:
            return jsonify({'error': 'Invalid config_type'}), 400
        
        # Check if already exists
        existing = SystemConfig.objects(config_type=config_type, value=value).first()
        if existing:
            if existing.is_active:
                return jsonify({'error': 'Value already exists'}), 400
            else:
                # Reactivate
                existing.is_active = True
                existing.save()
                return jsonify({
                    'message': 'Configuration reactivated',
                    'config': mongo_to_dict(existing)
                }), 200
        
        # Create new
        config = SystemConfig(
            config_type=config_type,
            value=value
        )
        config.save()
        
        return jsonify({
            'message': 'Configuration added successfully',
            'config': mongo_to_dict(config)
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@system_config_bp.route('/<config_id>', methods=['DELETE'])
@token_required
def delete_config(config_id):
    """Soft delete system configuration (SuperAdmin only)"""
    if g.role != 'SuperAdmin':
        return jsonify({'error': 'Unauthorized - SuperAdmin only'}), 403
    
    try:
        config = SystemConfig.objects(id=config_id).first()
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        # Soft delete
        config.is_active = False
        config.save()
        
        return jsonify({'message': 'Configuration deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
