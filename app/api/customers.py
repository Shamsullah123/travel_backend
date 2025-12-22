from flask import Blueprint, request, jsonify, g
from app.middleware import token_required
from models.customer import Customer
from models.agency import Agency
from mongoengine.errors import NotUniqueError


customers_bp = Blueprint('customers', __name__)

from app.utils.serializers import mongo_to_dict

@customers_bp.route('', methods=['GET'])
@token_required
def get_customers():
    # Multi-tenancy: Filter by g.agency_id
    search = request.args.get('search')
    query = Customer.objects(agencyId=g.agency_id)
    
    if search:
        # Simple regex search on name or phone
        query = query.filter(fullName__icontains=search)
        
    customers = query.order_by('-createdAt').limit(50)
    data = mongo_to_dict(customers)
    
    # Check for bookings for each customer (MVP Approach)
    # Ideally, use aggregation lookup for performance
    from models.booking import Booking
    for customer_data in data:
        booking = Booking.objects(customerId=customer_data['_id'], agencyId=g.agency_id).first()
        customer_data['bookingStatus'] = 'Confirmed' if booking else None
        
    return jsonify(data), 200

@customers_bp.route('/<id>', methods=['GET'])
@token_required
def get_customer(id):
    customer = Customer.objects(id=id, agencyId=g.agency_id).first()
    if not customer:
        return not_found_error("Customer not found")
    return jsonify(mongo_to_dict(customer)), 200

from app.utils.error_handlers import error_response, validation_error, not_found_error

@customers_bp.route('', methods=['POST'])
@token_required
def create_customer():
    # Handle multipart/form-data
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        data = request.form.to_dict() # Convert to dict
        customer_photo = request.files.get('customer_photo')
        passport_attachment = request.files.get('passport_attachment')
    else:
        data = request.get_json()
        customer_photo = None
        passport_attachment = None


    if not data:
        return error_response("No data provided", "INVALID_REQUEST")
    
    if not data.get('fullName'):
        return validation_error({'fullName': 'Required field'})
        
    if not data.get('phone'):
        return validation_error({'phone': 'Required field'})
    
    try:
        # Save files if present
        photo_path = None
        passport_path = None
        
        if customer_photo:
            from app.utils.file_handler import save_file
            photo_path = save_file(customer_photo, 'customers/photos')
            
        if passport_attachment:
            from app.utils.file_handler import save_file
            passport_path = save_file(passport_attachment, 'customers/passports')

        customer = Customer(
            agencyId=g.agency_id,
            fullName=data.get('fullName'),
            phone=data.get('phone'),
            passportNumber=data.get('passportNumber'),
            passportIssueDate=data.get('passportIssueDate') if data.get('passportIssueDate') else None,
            passportExpiry=data.get('passportExpiry') if data.get('passportExpiry') else None, 
            gender=data.get('gender', 'Male'),
            address=data.get('address'),
            cnic=data.get('cnic'),
            finger_print=data.get('finger_print', 'No'),
            enrollment_id=data.get('enrollment_id'),
            pictureUrl=photo_path,
            passport_attachment=passport_path
        )
        customer.save()
        return jsonify(mongo_to_dict(customer)), 201
        
    except NotUniqueError as e:
        return error_response("Customer with this phone already exists.", "DUPLICATE_ENTRY", 409)
    except Exception as e:
        return error_response(str(e), "SERVER_ERROR", 500)

@customers_bp.route('/<id>', methods=['PUT'])
@token_required
def update_customer(id):
    # Handle multipart/form-data
    if request.content_type.startswith('multipart/form-data'):
        data = request.form
        customer_photo = request.files.get('customer_photo')
        passport_attachment = request.files.get('passport_attachment')
    else:
        data = request.get_json()
        customer_photo = None
        passport_attachment = None

    customer = Customer.objects(id=id, agencyId=g.agency_id).first()
    
    if not customer:
        return not_found_error("Customer not found")
        
    try:
        if 'fullName' in data: customer.fullName = data['fullName']
        if 'phone' in data: customer.phone = data['phone']
        if 'passportNumber' in data: customer.passportNumber = data['passportNumber']
        if 'passportIssueDate' in data: customer.passportIssueDate = data['passportIssueDate'] if data['passportIssueDate'] else None
        if 'passportExpiry' in data: customer.passportExpiry = data['passportExpiry'] if data['passportExpiry'] else None
        if 'gender' in data: customer.gender = data['gender']
        if 'address' in data: customer.address = data['address']
        if 'cnic' in data: customer.cnic = data['cnic']
        if 'finger_print' in data: customer.finger_print = data['finger_print']
        if 'enrollment_id' in data: customer.enrollment_id = data['enrollment_id']
        
        if customer_photo:
            from app.utils.file_handler import save_file
            customer.pictureUrl = save_file(customer_photo, 'customers/photos')
            
        if passport_attachment:
            from app.utils.file_handler import save_file
            customer.passport_attachment = save_file(passport_attachment, 'customers/passports')
        
        customer.save()
        return jsonify(mongo_to_dict(customer)), 200
    except NotUniqueError:
        return error_response("Phone number must be unique", "DUPLICATE_ENTRY", 409)
    except Exception as e:
        return error_response(str(e), "SERVER_ERROR", 500)

@customers_bp.route('/<id>', methods=['DELETE'])
@token_required
def delete_customer(id):
    customer = Customer.objects(id=id, agencyId=g.agency_id).first()
    
    if not customer:
        return not_found_error("Customer not found")
        
    try:
        customer.delete()
        return jsonify({'message': 'Customer deleted'}), 200
    except Exception as e:
        return error_response(str(e), "SERVER_ERROR", 500)
