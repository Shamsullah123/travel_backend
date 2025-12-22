from flask import Blueprint, request, jsonify, current_app
from models.ledger import LedgerEntry
from models.user import User
from datetime import datetime
import jwt

financial_summary_bp = Blueprint('financial_summary', __name__)

def get_current_user(request):
    """Extract user from JWT token in Authorization header"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return User.objects(id=payload['sub']).first()
    except:
        return None


@financial_summary_bp.route('/financial-summary', methods=['GET'])
def get_financial_summary():
    """
    Get financial summary for the current agency.
    
    Query Parameters:
    - start_date (optional): ISO format date string
    - end_date (optional): ISO format date string
    
    Returns:
    {
        "total_credit": float,
        "total_debit": float,
        "net_balance": float,
        "status": "positive" | "negative"
    }
    """
    user = get_current_user(request)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    agency_id = user.agencyId
    if not agency_id:
        return jsonify({'error': 'User not associated with an agency'}), 400
    
    try:
        # Build query filters
        filters = {'agencyId': agency_id}
        
        # Optional date filtering
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date or end_date:
            if start_date:
                # Parse ISO string and make timezone-aware
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                filters['date__gte'] = start_dt
            if end_date:
                # Parse ISO string and make timezone-aware
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                filters['date__lte'] = end_dt
        
        
        # Calculate total credit
        credit_entries = LedgerEntry.objects(**filters, type='Credit')
        total_credit = sum(float(entry.amount) for entry in credit_entries)
        
        # Use shared financial service for debit calculation
        from app.services.financial_service import FinancialService
        debit_breakdown = FinancialService.calculate_total_debit(
            agency_id, 
            filters.get('date__gte'), 
            filters.get('date__lte')
        )
        total_debit = debit_breakdown['total_debit']
        
        # Calculate net balance
        net_balance = total_credit - total_debit
        
        # Determine status
        status = 'positive' if net_balance >= 0 else 'negative'
        
        response = {
            'total_credit': round(total_credit, 2),
            'total_debit': round(total_debit, 2),
            'net_balance': round(net_balance, 2),
            'status': status
        }
        
        # Include period info if date filters were applied
        if start_date or end_date:
            response['period'] = {
                'start_date': start_date,
                'end_date': end_date
            }
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
