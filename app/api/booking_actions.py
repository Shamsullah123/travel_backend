from flask import Blueprint, request, jsonify, g
from app.middleware import token_required
from models.ticket_booking import TicketBooking
from models.ticket_group import TicketGroup

booking_actions_bp = Blueprint('booking_actions', __name__)

@booking_actions_bp.route('/<booking_id>/confirm', methods=['POST'])
@token_required
def confirm_booking(booking_id):
    """Confirm a pending booking (seller only)"""
    try:
        booking = TicketBooking.objects(id=booking_id).first()
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Only seller can confirm
        if str(booking.sellerAgencyId.id) != str(g.agency_id):
            return jsonify({'error': 'Unauthorized - only seller can confirm'}), 403
        
        if booking.status != 'pending':
            return jsonify({'error': f'Booking is already {booking.status}'}), 400
        
        # Update status to confirmed
        booking.status = 'confirmed'
        booking.save()
        
        return jsonify({
            'message': 'Booking confirmed successfully',
            'booking_id': str(booking.id),
            'status': booking.status
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@booking_actions_bp.route('/<booking_id>/reject', methods=['POST'])
@token_required
def reject_booking(booking_id):
    """Reject a pending booking and restore seats (seller only)"""
    try:
        booking = TicketBooking.objects(id=booking_id).first()
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Only seller can reject
        if str(booking.sellerAgencyId.id) != str(g.agency_id):
            return jsonify({'error': 'Unauthorized - only seller can reject'}), 403
        
        if booking.status != 'pending':
            return jsonify({'error': f'Booking is already {booking.status}'}), 400
        
        # Restore seats to ticket group
        TicketGroup.objects(id=booking.ticketGroupId.id).update(
            inc__available_seats=booking.seats_booked
        )
        
        # Update status to rejected
        booking.status = 'rejected'
        booking.save()
        
        return jsonify({
            'message': 'Booking rejected and seats restored',
            'booking_id': str(booking.id),
            'status': booking.status,
            'seats_restored': booking.seats_booked
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@booking_actions_bp.route('/<booking_id>/cancel', methods=['POST'])
@token_required
def cancel_booking(booking_id):
    """Cancel a confirmed booking and restore seats (buyer or seller)"""
    try:
        booking = TicketBooking.objects(id=booking_id).first()
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Both buyer and seller can cancel
        if str(booking.agencyId.id) != str(g.agency_id) and str(booking.sellerAgencyId.id) != str(g.agency_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        if booking.status not in ['pending', 'confirmed']:
            return jsonify({'error': f'Cannot cancel - booking is {booking.status}'}), 400
        
        # Restore seats to ticket group
        TicketGroup.objects(id=booking.ticketGroupId.id).update(
            inc__available_seats=booking.seats_booked
        )
        
        # Update status to cancelled
        booking.status = 'cancelled'
        booking.save()
        
        return jsonify({
            'message': 'Booking cancelled and seats restored',
            'booking_id': str(booking.id),
            'status': booking.status,
            'seats_restored': booking.seats_booked
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
