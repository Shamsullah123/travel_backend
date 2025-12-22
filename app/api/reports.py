from flask import Blueprint, jsonify, request, g
from app.middleware import token_required
from models.ledger import LedgerEntry
from models.booking import Booking
from models.ticket_booking import TicketBooking
from models.visa_booking import VisaBooking
from models.miscellaneous_expense import MiscellaneousExpense
from models.agency import Agency
from mongoengine.queryset.visitor import Q
from datetime import datetime, timedelta
from bson import ObjectId
import calendar

reports_bp = Blueprint('reports', __name__)

def get_date_range(filter_type):
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if filter_type == 'today':
        return today_start, now
    elif filter_type == 'this_month':
        start = today_start.replace(day=1)
        # End of month is tricky, just use now or future
        next_month = start.replace(day=28) + timedelta(days=4)
        end = next_month - timedelta(days=next_month.day)
        return start, end.replace(hour=23, minute=59, second=59)
    elif filter_type == 'last_30_days':
        return now - timedelta(days=30), now
    elif filter_type == 'custom':
        # Expect query params start_date, end_date
        return None, None 
    else:
        # Default to all time or this month? Let's default to this month
        start = today_start.replace(day=1)
        return start, now

@reports_bp.route('/summary', methods=['GET'])
@token_required
def get_summary():
    """
    KPI Cards: Total Credit, Total Debit, Net Balance, Pending Amount
    """
    try:
        print("DEBUG: Inside get_summary route handler")
        agency_id = ObjectId(g.agency_id)
        filter_type = request.args.get('filter', 'this_month')
        start_date_str = request.args.get('startDate')
        end_date_str = request.args.get('endDate')
        
        start_date = None
        end_date = None

        if filter_type == 'custom' and start_date_str and end_date_str:
             start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00')).replace(tzinfo=None) # naive UTC
             end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00')).replace(tzinfo=None)
        else:
             start_date, end_date = get_date_range(filter_type)

        # 1. Total Credit & Debit (from Ledger)
        pipeline = [
            {
                '$match': {
                    'agencyId': agency_id,
                    'date': {'$gte': start_date, '$lte': end_date}
                }
            },
            {
                '$group': {
                    '_id': '$type', # 'Credit' or 'Debit'
                    'total': {'$sum': '$amount'}
                }
            }
        ]
        
        
        ledger_stats = list(LedgerEntry.objects.aggregate(*pipeline))
        total_credit = next((item['total'] for item in ledger_stats if item['_id'] == 'Credit'), 0)
        
        # Use shared financial service for debit calculation
        from app.services.financial_service import FinancialService
        debit_breakdown = FinancialService.calculate_total_debit(agency_id, start_date, end_date)
        total_debit = debit_breakdown['total_debit']
        
        # 2. Pending Amount (Bookings with balanceDue > 0)
        # Calculate from active Bookings created in this period
        pending_pipeline = [
            {
                '$match': {
                    'agencyId': agency_id,
                    'createdAt': {'$gte': start_date, '$lte': end_date},
                    'balanceDue': {'$gt': 0},
                    'status': {'$ne': 'Cancelled'}
                }
            },
            {
                '$group': {
                    '_id': None,
                    'totalPending': {'$sum': '$balanceDue'}
                }
            }
        ]
        pending_res = list(Booking.objects.aggregate(*pending_pipeline))
        pending_amount = pending_res[0]['totalPending'] if pending_res else 0

        return jsonify({
            'totalCredit': total_credit,
            'totalDebit': total_debit,
            'netBalance': total_credit - total_debit,
            'pendingAmount': pending_amount
        })

    except Exception as e:
        print(f"Error in reports/summary: {e}")
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/cash-flow', methods=['GET'])
@token_required
def get_cash_flow():
    """
    Line Chart: Credit vs Debit over time
    """
    try:
        agency_id = ObjectId(g.agency_id)
        filter_type = request.args.get('filter', 'this_month')
        start_date_str = request.args.get('startDate')
        end_date_str = request.args.get('endDate')
        
        if filter_type == 'custom' and start_date_str and end_date_str:
             start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00')).replace(tzinfo=None)
             end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00')).replace(tzinfo=None)
        else:
             start_date, end_date = get_date_range(filter_type)

        pipeline = [
            {
                '$match': {
                    'agencyId': agency_id,
                    'date': {'$gte': start_date, '$lte': end_date}
                }
            },
            {
                '$project': {
                    'dateStr': { '$dateToString': { 'format': '%Y-%m-%d', 'date': '$date' } },
                    'amount': 1,
                    'type': 1
                }
            },
            {
                '$group': {
                    '_id': { 'date': '$dateStr', 'type': '$type' },
                    'total': { '$sum': '$amount' }
                }
            },
            {
                '$sort': { '_id.date': 1 }
            }
        ]
        
        results = list(LedgerEntry.objects.aggregate(*pipeline))
        
        # Reformating for chart
        chart_data = {}
        for r in results:
            d = r['_id']['date']
            t = r['_id']['type'] # Credit or Debit
            amt = r['total']
            
            if d not in chart_data:
                chart_data[d] = {'date': d, 'Credit': 0, 'Debit': 0}
            chart_data[d][t] = amt
            
        return jsonify(list(chart_data.values()))

    except Exception as e:
        print(f"Error in reports/cash-flow: {e}")
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/revenue-by-service', methods=['GET'])
@token_required
def get_revenue_by_service():
    """
    Bar Chart: Revenue by Service Type
    Services: Visa, Ticket, Umrah, Ziarat, Transport (General Booking Categories)
    """
    try:
        agency_id = ObjectId(g.agency_id)
        # ... date logic ... (simplified)
        start_date, end_date = get_date_range(request.args.get('filter', 'this_month'))

        revenue = {
            'Visa': 0,
            'Ticket': 0,
            'Umrah': 0,
            'Ziarat': 0,
            'Other': 0
        }
        
        # 1. Booking Model (General Packages: Umrah, Ziarat, Other)
        booking_pipeline = [
            {
                '$match': {
                    'agencyId': agency_id,
                    'createdAt': {'$gte': start_date, '$lte': end_date},
                    'status': {'$ne': 'Cancelled'}
                }
            },
            {
                '$lookup': {
                    'from': 'packages',
                    'localField': 'packageId',
                    'foreignField': '_id',
                    'as': 'package'
                }
            },
            {
                '$group': {
                    # Try to group by Package Type if available, else derive from name or fallback
                    '_id': '$category', # 'Sharing', etc., not useful for service type. 
                    # We need access to Package.type
                    'total': {'$sum': '$totalAmount'},
                    'packages': { '$push': '$package' } # Inefficient for large data, but okay for report
                }
            }
        ]
        
        # OPTIMIZED APPROACH: separate queries for cleaner logic
        
        # VISAS (from VisaBooking) - Sales
        visa_pipeline = [
            {
                '$match': {
                    'seller_agency_id': agency_id,
                    'created_at': {'$gte': start_date, '$lte': end_date},
                    'status': {'$ne': 'rejected'}
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total': {'$sum': '$final_amount'}
                }
            }
        ]
        visa_res = list(VisaBooking.objects.aggregate(*visa_pipeline))
        revenue['Visa'] += visa_res[0]['total'] if visa_res else 0
        
        # TICKETS (from TicketBooking) - Sales
        ticket_pipeline = [
            {
                '$match': {
                    'sellerAgencyId': agency_id,
                    'created_at': {'$gte': start_date, '$lte': end_date},
                    'status': {'$in': ['confirmed', 'ticketed']}
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total': {'$sum': '$total_price'}
                }
            }
        ]
        ticket_res = list(TicketBooking.objects.aggregate(*ticket_pipeline))
        revenue['Ticket'] += ticket_res[0]['total'] if ticket_res else 0

        # General Bookings - Use aggregation to avoid N+1 query
        booking_pipeline = [
            {
                '$match': {
                    'agencyId': agency_id,
                    'createdAt': {'$gte': start_date, '$lte': end_date},
                    'status': {'$ne': 'Cancelled'}
                }
            },
            {
                '$lookup': {
                    'from': 'packages',
                    'localField': 'packageId',
                    'foreignField': '_id',
                    'as': 'package'
                }
            },
            {
                '$unwind': {
                    'path': '$package',
                    'preserveNullAndEmptyArrays': True
                }
            },
            {
                '$project': {
                    'totalAmount': 1,
                    'packageName': {'$toLower': {'$ifNull': ['$package.name', '']}}
                }
            }
        ]
        
        booking_results = list(Booking.objects.aggregate(*booking_pipeline))
        for b in booking_results:
            pkg_name = b.get('packageName', '')
            amount = float(b.get('totalAmount', 0))
            
            if 'umrah' in pkg_name:
                revenue['Umrah'] += amount
            elif 'ziarat' in pkg_name:
                revenue['Ziarat'] += amount
            else:
                revenue['Other'] += amount

        data = [{'name': k, 'value': v} for k, v in revenue.items()]
        return jsonify(data)

    except Exception as e:
        print(f"Error in revenue: {e}")
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/outstanding-payments', methods=['GET'])
@token_required
def get_outstanding_payments():
    try:
        # Use string ID for consistency with other routes, MongoEngine handles conversion for ReferenceField
        agency_id = g.agency_id
        
        bookings = Booking.objects(agencyId=agency_id, balanceDue__gt=0, status__ne='Cancelled').limit(50)
        
        data = []
        for b in bookings:
            try:
                # Safely access customer, catch DoesNotExist if customer was deleted
                customer = b.customerId
                cust_name = customer.fullName if customer else "Unknown"
            except Exception:
                cust_name = "Unknown (Deleted)"
            
            # Calculate days overdue
            days_overdue = (datetime.utcnow() - b.createdAt).days if b.createdAt else 0
            
            data.append({
                'id': str(b.id),
                'customerName': cust_name,
                'bookingType': b.category, 
                'totalAmount': float(b.totalAmount),
                'paidAmount': float(b.paidAmount),
                'remainingAmount': float(b.balanceDue),
                'daysOverdue': days_overdue
            })
            
        return jsonify(data)
    except Exception as e:
        print(f"Outstanding Payments Error: {e}")
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/top-customers', methods=['GET'])
@token_required
def get_top_customers():
    try:
        agency_id = ObjectId(g.agency_id)
        pipeline = [
            {
                '$match': {
                    'agencyId': agency_id,
                    'status': {'$ne': 'Cancelled'}
                }
            },
            {
                '$group': {
                    '_id': '$customerId',
                    'totalSpend': {'$sum': '$totalAmount'},
                    'bookingCount': {'$sum': 1},
                    'totalBalance': {'$sum': '$balanceDue'}
                }
            },
            { '$sort': { 'totalSpend': -1 } },
            { '$limit': 5 },
            {
                '$lookup': {
                    'from': 'customers',
                    'localField': '_id',
                    'foreignField': '_id',
                    'as': 'customer'
                }
            },
            { '$unwind': '$customer' }
        ]
        
        results = list(Booking.objects.aggregate(*pipeline))
        data = [{
            'name': r['customer']['fullName'],
            'totalSpend': r['totalSpend'],
            'bookingCount': r['bookingCount'],
            'outstandingBalance': r['totalBalance']
        } for r in results]
        
        return jsonify(data)
    except Exception as e:
        print(f"Top Customers Error: {e}")
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/expenses-breakdown', methods=['GET'])
@token_required
def get_expenses_breakdown():
    try:
        agency_id = ObjectId(g.agency_id)
        start_date, end_date = get_date_range(request.args.get('filter', 'this_month'))
        
        # 1. Misc Expenses
        misc_pipeline = [
             { '$match': { 'agencyId': agency_id, 'expense_date': {'$gte': start_date, '$lte': end_date} } },
             { '$group': { '_id': '$title', 'total': { '$sum': '$amount' } } } # Group by Title as pseudo-category
        ]
        misc_res = list(MiscellaneousExpense.objects.aggregate(*misc_pipeline))
        
        # 2. Agent Commissions (Ledger Debits that are commissions?)
        # Ideally we'd have a specific type. For now, let's just use Misc Expenses + Ledger general Debits logic if needed.
        # But per requirements: Agent Commission, Office, Misc, Marketing.
        # We'll map MiscExpense titles to these categories if possible, or just return MiscExpense titles.
        
        data = [{'name': r['_id'], 'value': r['total']} for r in misc_res]
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
