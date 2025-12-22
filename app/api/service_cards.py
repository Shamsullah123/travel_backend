from flask import Blueprint, request, jsonify, g
from app.middleware import token_required
from models.booking import Booking
from models.customer import Customer
from models.package import Package
from models.facility import Facility
from models.agency import Agency
from app.utils.serializers import mongo_to_dict

service_cards_bp = Blueprint('service_cards', __name__)

@service_cards_bp.route('/<booking_id>', methods=['GET'])
@token_required
def get_service_card(booking_id):
    """
    Fetch aggregated data for service card display
    Returns: Customer, Booking, Facility (with Moaleem), Agency data
    """
    try:
        # Fetch booking
        booking = Booking.objects(id=booking_id, agencyId=g.agency_id).first()
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Prepare response data
        card_data = {
            'booking': {
                'bookingNumber': booking.bookingNumber,
                'category': booking.category,
                'status': booking.status
            },
            'customer': {
                'name': 'N/A',
                'gender': 'N/A',
                'cnic': 'N/A',
                'passportNumber': 'N/A',
                'pictureUrl': None
            },
            'moaleem': {
                'name': 'N/A',
                'contact': 'N/A'
            },
            'agency': {
                'name': 'N/A'
            }
        }
        
        # Fetch Customer data
        try:
            if booking.customerId:
                customer = booking.customerId
                card_data['customer'] = {
                    'name': customer.fullName or 'N/A',
                    'gender': customer.gender or 'N/A',
                    'cnic': customer.cnic or 'N/A',
                    'passportNumber': customer.passportNumber or 'N/A',
                    'pictureUrl': getattr(customer, 'pictureUrl', None) or getattr(customer, 'customer_photo', None)
                }
        except Exception as e:
            print(f"Error fetching customer: {e}")
        
        # Fetch Package to get facilityId, then fetch Facility for Moaleem
        try:
            if booking.packageId:
                package = booking.packageId
                # Check if package has facilityId reference
                if hasattr(package, 'facilityId') and package.facilityId:
                    facility = package.facilityId
                    # Extract Moaleem from Facility
                    if hasattr(facility, 'moaleem') and facility.moaleem:
                        moaleem = facility.moaleem
                        if hasattr(moaleem, 'moaleem_name') and moaleem.moaleem_name:
                            card_data['moaleem']['name'] = moaleem.moaleem_name
                        if hasattr(moaleem, 'moaleem_contact') and moaleem.moaleem_contact:
                            card_data['moaleem']['contact'] = moaleem.moaleem_contact
        except Exception as e:
            print(f"Error fetching facility/moaleem: {e}")
        
        # Fetch Agency data
        try:
            if booking.agencyId:
                agency = booking.agencyId
                card_data['agency']['name'] = agency.name or 'N/A'
        except Exception as e:
            print(f"Error fetching agency: {e}")
        
        return jsonify(card_data), 200
        
    except Exception as e:
        print(f"Error in get_service_card: {e}")
        return jsonify({'error': str(e)}), 500
