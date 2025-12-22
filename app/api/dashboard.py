from flask import Blueprint, jsonify, g
from app.middleware import token_required
from models.visa_case import VisaCase
from models.booking import Booking
from models.customer import Customer
from datetime import datetime, timedelta
from app.utils.serializers import mongo_to_dict

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/tasks', methods=['GET'])
@token_required
def get_dashboard_tasks():
    today = datetime.utcnow()
    six_months_later = today + timedelta(days=180)

    # 1. Pending Visa Follow-ups (Active cases)
    # Statuses that imply pending work: 'New', 'Submitted', 'Processing'
    # We exclude 'Approved', 'Rejected', 'Completed'
    active_visas = VisaCase.objects(
        agencyId=g.agency_id,
        status__nin=['Approved', 'Rejected', 'Completed']
    ).order_by('expectedIssueDate')  # Prioritize by due date
    
    # 2. Due Payments (Booking balance > 0)
    due_bookings = Booking.objects(
        agencyId=g.agency_id,
        balanceDue__gt=0,
        status__ne='Cancelled'
    ).order_by('-createdAt')

    # 3. Expiring Passports (Next 6 months)
    expiring_passports = Customer.objects(
        agencyId=g.agency_id,
        passportExpiry__gte=today,
        passportExpiry__lte=six_months_later
    ).order_by('passportExpiry')

    # Serialize
    # We only need summary data, but full object is fine for now
    return jsonify({
        'visaFollowUps': mongo_to_dict(active_visas)[:5], # Top 5
        'duePayments': mongo_to_dict(due_bookings)[:5],
        'expiringPassports': mongo_to_dict(expiring_passports)[:5]
    }), 200
