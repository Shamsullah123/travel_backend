from flask import Blueprint, request, jsonify, g
from app.middleware import token_required
from models.quotation import Quotation, LineItem
from app.services.booking_service import BookingService
from decimal import Decimal

quotations_bp = Blueprint('quotations', __name__)

@quotations_bp.route('', methods=['POST'])
@token_required
def create_quote():
    data = request.get_json()
    items = []
    total = Decimal(0)
    
    for item in data.get('lineItems', []):
        li = LineItem(
            description=item['description'],
            type=item['type'],
            costPrice=item.get('costPrice', 0),
            sellPrice=item['sellPrice'],
            quantity=item.get('quantity', 1)
        )
        items.append(li)
        total += Decimal(li.sellPrice) * li.quantity
        
    quote = Quotation(
        agencyId=g.agency_id,
        customerId=data['customerId'],
        visaCaseId=data.get('visaCaseId'),
        quoteNumber=BookingService.generate_number("QT"),
        lineItems=items,
        totalAmount=total,
        status='Draft'
    )
    quote.save()
    return jsonify(quote), 201

@quotations_bp.route('/<id>/convert', methods=['POST'])
@token_required
def convert_to_booking(id):
    booking, error = BookingService.create_booking_from_quote(id, g.agency_id)
    if error:
        return jsonify({'error': error}), 400
    return jsonify(booking), 201
