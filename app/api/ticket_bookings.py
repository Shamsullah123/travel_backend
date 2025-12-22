from flask import Blueprint, request, jsonify, g
from app.middleware import token_required
from models.ticket_group import TicketGroup
from models.ticket_booking import TicketBooking, Passenger
from app.utils.serializers import mongo_to_dict
from datetime import datetime
import uuid

ticket_bookings_bp = Blueprint('ticket_bookings', __name__)

@ticket_bookings_bp.route('/', methods=['POST'])
@token_required
def create_booking():
    """
    Atomic Seat Booking API
    Prevents overbooking using atomic DB operations.
    """
    try:
        data = request.get_json()
        print(f"\n{'='*60}")
        print(f"BOOKING REQUEST RECEIVED")
        print(f"{'='*60}")
        print(f"Raw request data: {data}")
        
        group_id = data.get('ticketGroupId') or data.get('group_id')
        seats_requested = int(data.get('totalSeats') or data.get('seats_requested', 0))
        passengers_data = data.get('passengers', [])
        total_price = float(data.get('totalPrice', 0))

        print(f"Parsed values:")
        print(f"  - group_id: {group_id}")
        print(f"  - seats_requested: {seats_requested} (type: {type(seats_requested)})")
        print(f"  - total_price: {total_price}")
        print(f"  - passengers_count: {len(passengers_data)}")
        print(f"  - g.agency_id: {g.agency_id}")
        print(f"{'='*60}\n")

        if not group_id or seats_requested <= 0:
            return jsonify({'error': 'Invalid booking request'}), 400

        # ATOMIC OPERATION:
        # Find document where id=group_id AND available_seats >= seats_requested
        # AND atomically decrement available_seats by seats_requested.
        # If the query condition fails (not enough seats), it returns None.
        
        ticket_group = TicketGroup.objects(
            id=group_id, 
            available_seats__gte=seats_requested,
            status='active'
        ).modify(
            dec__available_seats=seats_requested,
            new=True # Return updated document
        )

        if not ticket_group:
            # Atomic update failed -> Overbooking prevented or Group not found/closed
            # Check if group exists to give better error
            exists = TicketGroup.objects(id=group_id).first()
            if not exists:
                return jsonify({'error': 'Ticket group not found'}), 404
            if exists.status != 'active':
                return jsonify({'error': 'Ticket group is closed'}), 400
            
            return jsonify({
                'error': 'Seats not available',
                'available_seats': exists.available_seats
            }), 409 # Conflict

        # Success - Seats secured
        # Now create booking record
        try:
            # Create Booking Reference
            ref = f"INV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
            print(f"DEBUG: Creating booking with agency_id={g.agency_id}, type={type(g.agency_id)}")
            print(f"DEBUG: seller_agency={ticket_group.agencyId}, type={type(ticket_group.agencyId)}")
            
            passengers = []
            for p_data in passengers_data:
                # Handle date parsing safely
                try:
                    dob = datetime.strptime(p_data['dob'].split('T')[0], '%Y-%m-%d')
                    expiry = datetime.strptime(p_data['expiryDate'].split('T')[0], '%Y-%m-%d')
                except:
                    dob = datetime.utcnow()
                    expiry = datetime.utcnow() # Fallback or error

                passengers.append(Passenger(
                    type=p_data['type'],
                    title=p_data.get('title', ''),
                    givenName=p_data['givenName'],
                    surName=p_data['surName'],
                    passportNumber=p_data['passportNumber'],
                    dob=dob,
                    expiryDate=expiry
                ))

            # Store Seller Agency ID for easy reporting
            seller_agency = ticket_group.agencyId
            
            # Import Agency model to get proper reference
            from models.agency import Agency
            buyer_agency = Agency.objects(id=g.agency_id).first()
            
            if not buyer_agency:
                return jsonify({'error': 'Buyer agency not found'}), 400

            booking = TicketBooking(
                agencyId=buyer_agency,
                sellerAgencyId=seller_agency,
                ticketGroupId=ticket_group,
                booking_reference=ref,
                seats_booked=seats_requested,
                total_price=total_price,
                passengers=passengers,
                status='pending'  # Changed to pending - seller must confirm
            )
            booking.save()

            return jsonify({
                'message': 'Booking confirmed',
                'booking_id': str(booking.id),
                'booking_reference': booking.booking_reference,
                'updated_available_seats': ticket_group.available_seats,
                'total_price': booking.total_price
            }), 201

        except Exception as e:
            # ROLLBACK INVENTORY IF BOOKING SAVE FAILS
            TicketGroup.objects(id=group_id).update(inc__available_seats=seats_requested)
            import traceback
            traceback.print_exc()
            if hasattr(e, 'errors'):
                print(f"Validation Errors: {e.errors}")
            raise e

    except Exception as e:
        print(f"Booking Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        error_msg = str(e)
        if hasattr(e, 'errors') and e.errors:
            error_msg = f"Validation Error: {e.errors}"
        
        return jsonify({'error': error_msg}), 500

@ticket_bookings_bp.route('/', methods=['GET'])
@token_required
def get_bookings():
    """
    Get bookings list.
    Query Params:
    - type: 'sales' (bookings OF my groups) | 'purchases' (bookings BY me)
    """
    try:
        query_type = request.args.get('type', 'purchases')
        
        if query_type == 'sales':
            # Find bookings where I am the Seller
            bookings = TicketBooking.objects(sellerAgencyId=g.agency_id).order_by('-created_at')
        else:
            # Find bookings where I am the Buyer
            bookings = TicketBooking.objects(agencyId=g.agency_id).order_by('-created_at')
            
        # Serialize
        results = []
        for booking in bookings:
            b_dict = mongo_to_dict(booking)
            
            # Enrich with Ticket Group details if available
            if booking.ticketGroupId:
                tg = booking.ticketGroupId
                b_dict['ticket_details'] = {
                    'airline': tg.airline,
                    'sector': tg.sector,
                    'date': tg.date.strftime('%Y-%m-%d') if tg.date else '',
                    'flight_no': tg.flight_no,
                    'time': tg.time,
                    'departure_time': tg.departure_time,
                    'arrival_time': tg.arrival_time
                }
            
            # Enrich with Counterparty Name and Contact
            if query_type == 'sales':
                # Show Buyer Name and Contact
                b_dict['counterparty'] = booking.agencyId.name if booking.agencyId else 'Unknown'
                if booking.agencyId:
                    from models.user import User
                    buyer_admin = User.objects(agencyId=booking.agencyId, role='AgencyAdmin').first()
                    b_dict['counterparty_phone'] = buyer_admin.phone if buyer_admin and buyer_admin.phone else ''
            else:
                # Show Seller Name and Contact
                b_dict['counterparty'] = booking.sellerAgencyId.name if booking.sellerAgencyId else 'Unknown'
                if booking.sellerAgencyId:
                    from models.user import User
                    seller_admin = User.objects(agencyId=booking.sellerAgencyId, role='AgencyAdmin').first()
                    b_dict['counterparty_phone'] = seller_admin.phone if seller_admin and seller_admin.phone else ''
                
            results.append(b_dict)
            
        return jsonify(results), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ticket_bookings_bp.route('/counts', methods=['GET'])
@token_required
def get_unread_counts():
    """Get unread counts for sales and purchases"""
    try:
        sales_count = TicketBooking.objects(sellerAgencyId=g.agency_id, is_read_by_seller=False).count()
        purchases_count = TicketBooking.objects(agencyId=g.agency_id, is_read_by_buyer=False).count()
        
        # stats - GLOBAL scope for Marketplace
        active_tickets = TicketGroup.objects(status='active').sum('available_seats')
        sold_tickets = TicketBooking.objects(status='confirmed').sum('seats_booked')

        return jsonify({
            'sales': sales_count,
            'purchases': purchases_count,
            'stats': {
                'active_tickets': active_tickets or 0,
                'sold_tickets': sold_tickets or 0
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ticket_bookings_bp.route('/mark-read', methods=['POST'])
@token_required
def mark_read():
    """Mark bookings as read for a specific type (sales/purchases)"""
    try:
        data = request.get_json()
        read_type = data.get('type') # 'sales' or 'purchases'
        
        if read_type == 'sales':
            TicketBooking.objects(sellerAgencyId=g.agency_id, is_read_by_seller=False).update(set__is_read_by_seller=True)
        elif read_type == 'purchases':
            TicketBooking.objects(agencyId=g.agency_id, is_read_by_buyer=False).update(set__is_read_by_buyer=True)
        else:
            return jsonify({'error': 'Invalid type'}), 400
            
        return jsonify({'message': 'Marked as read'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
