from flask import Blueprint, request, jsonify, g
from app.middleware import token_required
from models.ticket_group import TicketGroup
from app.utils.serializers import mongo_to_dict
from datetime import datetime, timedelta
from mongoengine.queryset.visitor import Q

ticket_inventory_bp = Blueprint('ticket_inventory', __name__)

@ticket_inventory_bp.route('/', methods=['GET'])
def get_ticket_groups():
    """Get all ticket groups with filters (Public/Private)"""
    # Optional Auth Logic
    token = None
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        if auth_header.startswith('Bearer '):
            token = auth_header.split(" ")[1]
            
    if token:
        try:
            import jwt
            from flask import current_app
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            g.user_id = data['sub']
            g.agency_id = data.get('agencyId')
            g.role = data.get('role')
        except:
            # Invalid token -> Treat as Public
            g.role = 'Public'
            g.agency_id = None
    else:
        g.role = 'Public'
        g.agency_id = None

    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        skip = (page - 1) * limit
        
        # Filters
        sector = request.args.get('sector')
        travel_type = request.args.get('travel_type')
        airline = request.args.get('airline')
        date = request.args.get('date')
        status = request.args.get('status')
        owned_only = request.args.get('owned_only') == 'true'
        
        # Sorting
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        query = {}
        if sector:
            query['sector__icontains'] = sector
        if airline:
            query['airline__icontains'] = airline
        if travel_type:
            query['travel_type'] = travel_type
        if date and date.strip():
            try:
                target_date = datetime.strptime(date.strip(), '%Y-%m-%d')
                query['date__gte'] = target_date
                query['date__lt'] = target_date + timedelta(days=1)
            except ValueError:
                pass 
        
        if status:
            query['status'] = status
        
        # Access Control:
        if owned_only or g.role == 'AgencyAdmin': 
             pass

        final_query = TicketGroup.objects(**query)
        
        if g.role != 'SuperAdmin':
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # If date filter is applied, we trust the user's filter but ensure it's not in past?
            # Actually, standard logic:
            filter_q = Q(status='active', date__gte=today, available_seats__gt=0) | Q(agencyId=g.agency_id)
            final_query = final_query.filter(filter_q)

        total = final_query.count()
        
        # Sorting definition
        sort_field = sort_by
        if sort_order == 'desc':
            sort_field = f'-{sort_by}'
        
        # Validate sort field to prevent injection or errors
        valid_sort_fields = ['created_at', 'price_per_seat', 'date', 'airline', 'sector']
        if sort_by not in valid_sort_fields:
            sort_field = '-created_at'

        groups = final_query.order_by(sort_field).skip(skip).limit(limit)
        
        # Enrich with agency contact information
        enriched_groups = []
        for group in groups:
            group_dict = mongo_to_dict(group)
            if group.agencyId:
                # Get agency admin user for contact info
                from models.user import User
                admin_user = User.objects(agencyId=group.agencyId, role='AgencyAdmin').first()
                group_dict['agency_contact'] = {
                    'name': group.agencyId.name,
                    'phone': admin_user.phone if admin_user and admin_user.phone else ''
                }
            enriched_groups.append(group_dict)
        
        return jsonify({
            'ticket_groups': enriched_groups,
            'total': total,
            'page': page,
            'limit': limit
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ticket_inventory_bp.route('/', methods=['POST'])
@token_required
def create_ticket_group():
    """Create a new ticket group (AgencyAdmin only)"""
    # Requirement: "POST /api/ticket-groups (agency_admin only)"
    # Though usually we check permission list, assuming Role check for now based on request.
    if g.role not in ['AgencyAdmin', 'SuperAdmin']:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        data = request.get_json()
        
        # Date parsing
        date_str = data.get('date')
        if date_str:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        else:
            return jsonify({'error': 'Date is required'}), 400

        # Return Date parsing
        return_date_str = data.get('return_date')
        return_date_obj = None
        if return_date_str:
            return_date_obj = datetime.strptime(return_date_str, '%Y-%m-%d')

        group = TicketGroup(
            agencyId=g.agency_id,
            airline=data.get('airline'),
            sector=data.get('sector'),
            travel_type=data.get('travel_type'),
            date=date_obj,
            flight_no=data.get('flight_no'),
            departure_time=data.get('departure_time'),
            arrival_time=data.get('arrival_time'),
            # Return details
            return_flight_no=data.get('return_flight_no'),
            return_date=return_date_obj,
            return_departure_time=data.get('return_departure_time'),
            return_arrival_time=data.get('return_arrival_time'),
            
            time=data.get('departure_time') or data.get('time'), # Auto-fill time with departure if available
            baggage=data.get('baggage'),
            meal=data.get('meal', False),
            price_per_seat=data.get('price_per_seat'),
            total_seats=data.get('total_seats'),
            available_seats=data.get('total_seats'), # Default to total
            status='active'
        )
        group.save()
        
        return jsonify(mongo_to_dict(group)), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@ticket_inventory_bp.route('/<id>', methods=['PUT'])
@token_required
def update_ticket_group(id):
    """Update ticket group (Only creator agency)"""
    try:
        group = TicketGroup.objects(id=id).first()
        if not group:
            return jsonify({'error': 'Ticket group not found'}), 404
            
        # Check ownership
        # Convert both to string for comparison to be safe
        if str(group.agencyId.id) != str(g.agency_id) and g.role != 'SuperAdmin':
            return jsonify({'error': 'Unauthorized'}), 403

        data = request.get_json()
        
        if 'airline' in data: group.airline = data['airline']
        if 'sector' in data: group.sector = data['sector']
        if 'travel_type' in data: group.travel_type = data['travel_type']
        if 'flight_no' in data: group.flight_no = data['flight_no']
        if 'time' in data: group.time = data['time']
        if 'departure_time' in data: 
            group.departure_time = data['departure_time']
            group.time = data['departure_time'] # Sync legacy field
        if 'arrival_time' in data: group.arrival_time = data['arrival_time']
        if 'baggage' in data: group.baggage = data['baggage']
        if 'meal' in data: group.meal = data['meal']
        if 'price_per_seat' in data: group.price_per_seat = data['price_per_seat']
        if 'total_seats' in data: group.total_seats = int(data['total_seats'])
        
        # Handle available seats logic? 
        # Usually if total updates, available might need update if no bookings yet. 
        # But for now sticking to explicit updates or manual management.
        if 'available_seats' in data:
            group.available_seats = int(data['available_seats'])
            
        if 'date' in data:
             group.date = datetime.strptime(data['date'], '%Y-%m-%d')

        # Update Return Details
        if 'return_flight_no' in data: group.return_flight_no = data['return_flight_no']
        if 'return_departure_time' in data: group.return_departure_time = data['return_departure_time']
        if 'return_arrival_time' in data: group.return_arrival_time = data['return_arrival_time']
        if 'return_date' in data:
            if data['return_date']:
                group.return_date = datetime.strptime(data['return_date'], '%Y-%m-%d')
            else:
                group.return_date = None

        group.save()
        return jsonify(mongo_to_dict(group)), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@ticket_inventory_bp.route('/<id>/status', methods=['PATCH'])
@token_required
def update_status(id):
    """Update status (active/closed)"""
    try:
        group = TicketGroup.objects(id=id).first()
        if not group:
            return jsonify({'error': 'Ticket group not found'}), 404
            
        if str(group.agencyId.id) != str(g.agency_id) and g.role != 'SuperAdmin':
            return jsonify({'error': 'Unauthorized'}), 403

        data = request.get_json()
        status = data.get('status')
        if status not in ['active', 'closed']:
            return jsonify({'error': 'Invalid status'}), 400
            
        group.status = status
        group.save()
        return jsonify(mongo_to_dict(group)), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@ticket_inventory_bp.route('/<id>', methods=['DELETE'])
@token_required
def delete_ticket_group(id):
    """Delete ticket group (Only creator agency)"""
    try:
        group = TicketGroup.objects(id=id).first()
        if not group:
            return jsonify({'error': 'Ticket group not found'}), 404
            
        # Check ownership
        if str(group.agencyId.id) != str(g.agency_id) and g.role != 'SuperAdmin':
            return jsonify({'error': 'Unauthorized'}), 403

        group.delete()
        
        return jsonify({'message': 'Ticket group deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400
