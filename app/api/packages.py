from flask import Blueprint, request, jsonify, g
from app.middleware import token_required
from models.package import Package
from app.utils.serializers import mongo_to_dict
from app.utils.error_handlers import error_response, validation_error, not_found_error
from bson import ObjectId
import traceback

packages_bp = Blueprint('packages', __name__)

@packages_bp.route('', methods=['GET'])
@token_required
def get_packages():
    search = request.args.get('search')
    query = Package.objects(agencyId=g.agency_id)
    
    if search:
        query = query.filter(name__icontains=search)
        
    packages = query.order_by('-createdAt')
    return jsonify(mongo_to_dict(packages)), 200

@packages_bp.route('', methods=['POST'])
@token_required
def create_package():
    data = request.get_json()
    
    if not data:
        return error_response("No data provided", "INVALID_REQUEST")
    
    if not data.get('name'):
        return validation_error({'name': 'Package name is required'})

    try:
        facility_id = data.get('facilityId')
        facility_id = ObjectId(facility_id) if (facility_id and ObjectId.is_valid(facility_id)) else None
        
        def clean_decimal(val):
            if val is None: return None
            s = str(val).strip()
            return s if s else None

        package = Package(
            agencyId=g.agency_id,
            facilityId=facility_id,
            name=data.get('name'),
            description=data.get('description'),
            startDate=data.get('startDate') or None,
            endDate=data.get('endDate') or None,
            duration=data.get('duration'),
            sharingPrice=clean_decimal(data.get('sharingPrice')),
            fourBedPrice=clean_decimal(data.get('fourBedPrice')),
            threeBedPrice=clean_decimal(data.get('threeBedPrice')),
            twoBedPrice=clean_decimal(data.get('twoBedPrice'))
        )
        package.save()
        return jsonify(mongo_to_dict(package)), 201
    except Exception as e:
        return error_response(str(e), "SERVER_ERROR", 500)

@packages_bp.route('/<id>', methods=['GET'])
@token_required
def get_package(id):
    package = Package.objects(id=id, agencyId=g.agency_id).first()
    if not package:
        return not_found_error("Package not found")
    return jsonify(mongo_to_dict(package)), 200

@packages_bp.route('/<id>', methods=['PUT'])
@token_required
def update_package(id):
    package = Package.objects(id=id, agencyId=g.agency_id).first()
    if not package:
        return not_found_error("Package not found")
        
    data = request.get_json()
    
    try:
        def clean_decimal(val):
            if val is None: return None
            if isinstance(val, (list, dict)): return None # Prevent structured data
            s = str(val).strip()
            return s if s else None

        if 'name' in data: package.name = data['name']
        if 'facilityId' in data: 
            fid = data['facilityId']
            package.facilityId = ObjectId(fid) if (fid and ObjectId.is_valid(fid)) else None
            
        if 'description' in data: package.description = data['description']
        if 'startDate' in data: package.startDate = data['startDate'] or None
        if 'endDate' in data: package.endDate = data['endDate'] or None
        if 'duration' in data: package.duration = data['duration']
        if 'sharingPrice' in data: package.sharingPrice = clean_decimal(data['sharingPrice'])
        if 'fourBedPrice' in data: package.fourBedPrice = clean_decimal(data['fourBedPrice'])
        if 'threeBedPrice' in data: package.threeBedPrice = clean_decimal(data['threeBedPrice'])
        if 'twoBedPrice' in data: package.twoBedPrice = clean_decimal(data['twoBedPrice'])
        
        package.save()
        return jsonify(mongo_to_dict(package)), 200
    except Exception as e:
        traceback.print_exc()
        return error_response(str(e), "SERVER_ERROR", 500)

@packages_bp.route('/<id>', methods=['DELETE'])
@token_required
def delete_package(id):
    package = Package.objects(id=id, agencyId=g.agency_id).first()
    if not package:
        return not_found_error("Package not found")
        
    try:
        package.delete()
        return jsonify({'message': 'Package deleted successfully'}), 200
    except Exception as e:
        return error_response(str(e), "SERVER_ERROR", 500)
