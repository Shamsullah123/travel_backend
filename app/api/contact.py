from flask import Blueprint, request, jsonify
from app.utils.error_handlers import error_response, validation_error

contact_bp = Blueprint('contact', __name__)

@contact_bp.route('', methods=['POST'])
def submit_contact_form():
    data = request.get_json()
    
    if not data:
        return error_response("No data provided", "INVALID_REQUEST")
    
    required_fields = ['name', 'email', 'subject', 'message']
    for field in required_fields:
        if not data.get(field):
            return validation_error({field: 'This field is required'})
            
    from models.contact_message import ContactMessage
    
    # Save to Database
    msg = ContactMessage(
        name=data['name'],
        email=data['email'],
        subject=data['subject'],
        message=data['message']
    )
    msg.save()
    
    return jsonify({'message': 'Message received successfully'}), 200
