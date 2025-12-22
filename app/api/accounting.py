from flask import Blueprint, request, jsonify, g
from app.middleware import token_required
from models.ledger import LedgerEntry
from models.booking import Booking
from datetime import datetime, timedelta
from mongoengine.queryset.visitor import Q
from mongoengine.queryset.visitor import Q
from decimal import Decimal
import csv
import io
import openpyxl
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from flask import send_file, Response

accounting_bp = Blueprint('accounting', __name__)

from app.utils.serializers import mongo_to_dict

@accounting_bp.route('/stats', methods=['GET'])
@token_required
def get_stats():
    # 1. Today's Sales (Total Booking Value)
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_bookings = Booking.objects(agencyId=g.agency_id, createdAt__gte=today_start)
    booking_sales = sum([b.totalAmount for b in today_bookings])
    
    today_credits = LedgerEntry.objects(agencyId=g.agency_id, type='Credit', date__gte=today_start)
    manual_sales = sum([e.amount for e in today_credits])
    
    today_sales = booking_sales + manual_sales
    
    # 2. Total Income/Expenses
    entries = LedgerEntry.objects(agencyId=g.agency_id)
    total_income = sum([e.amount for e in entries if e.type == 'Credit'])
    total_expenses = sum([e.amount for e in entries if e.type == 'Debit'])
    
    return jsonify({
        'todaySales': float(today_sales),
        'totalIncome': float(total_income),
        'totalExpenses': float(total_expenses),
        'netProfit': float(total_income - total_expenses)
    }), 200

@accounting_bp.route('/unpaid', methods=['GET'])
@token_required
def get_unpaid():
    bookings = Booking.objects(agencyId=g.agency_id, balanceDue__gt=0)
    return jsonify(mongo_to_dict(bookings)), 200

@accounting_bp.route('/ledger', methods=['GET'])
@token_required
def get_ledger():
    entries = LedgerEntry.objects(agencyId=g.agency_id).order_by('-date')
    
    # Manually build list to include dereferenced names
    result = []
    for entry in entries:
        item = mongo_to_dict(entry)
        
        # Populate Customer Name
        try:
            if entry.customerId:
                 item['customerName'] = entry.customerId.fullName
        except Exception:
             item['customerName'] = "Unknown (Deleted)"
            
        # Populate Booking Number if exists
        try:
            if entry.bookingId:
                item['bookingNumber'] = entry.bookingId.bookingNumber
        except Exception:
             item['bookingNumber'] = "Unknown (Deleted)"
            
        result.append(item)
        
    return jsonify(result), 200

@accounting_bp.route('/ledger', methods=['POST'])
@token_required
def create_entry():
    import os
    from werkzeug.utils import secure_filename
    from app.utils.file_handler import allowed_file, save_file
    import uuid
    import traceback
    
    # Check if multipart/form-data or json
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()

    try:
        # Handle File Upload
        slip_path = None
        if 'slip_attachment' in request.files:
            file = request.files['slip_attachment']
            # Use Cloudinary via save_file
            if file and allowed_file(file.filename):
                slip_path = save_file(file, 'ledger/slips')

        entry = LedgerEntry(
            agencyId=g.agency_id,
            type=data['type'], # Credit or Debit
            amount=Decimal(str(data['amount'])),
            description=data['description'],
            date=datetime.strptime(data['date'], '%Y-%m-%d') if data.get('date') else datetime.utcnow(),
            slip_number=data.get('slip_number'),
            slip_attachment=slip_path
        )
        
        if data.get('customerId'):
            from models.customer import Customer
            customer = Customer.objects(id=data['customerId'], agencyId=g.agency_id).first()
            if customer:
                entry.customerId = customer
                
                # Logic: Distribute payment across unpaid bookings if Credit
                if entry.type == 'Credit' and not data.get('bookingId'):
                    # Find unpaid bookings for this customer, oldest first
                    unpaid_bookings = Booking.objects(
                        agencyId=g.agency_id, 
                        customerId=customer, 
                        balanceDue__gt=0
                    ).order_by('createdAt')
                    
                    remaining_payment = entry.amount
                    
                    for booking in unpaid_bookings:
                        if remaining_payment <= 0:
                            break
                            
                        # Calculate how much we can pay on this booking
                        amount_to_pay = min(remaining_payment, booking.balanceDue)
                        
                        booking.paidAmount = (booking.paidAmount or Decimal('0.00')) + amount_to_pay
                        # Explicitly update balanceDue to ensure real-time consistency
                        booking.balanceDue = booking.totalAmount - booking.paidAmount
                        booking.save()
                        
                        remaining_payment -= amount_to_pay
                        
                    # Note: Any remaining payment stays as Credit on the Ledger Entry 
                    # but doesn't attach to a booking if all are paid.

        if data.get('bookingId'):
             booking = Booking.objects(id=data['bookingId'], agencyId=g.agency_id).first()
             if booking:
                 entry.bookingId = booking
                 if entry.type == 'Credit':
                     booking.paidAmount = (booking.paidAmount or Decimal('0.00')) + Decimal(str(data['amount']))
                     # Explicitly update balanceDue
                     booking.balanceDue = booking.totalAmount - booking.paidAmount
                     booking.save() 
        
        entry.save()
        return jsonify(mongo_to_dict(entry)), 201
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400

@accounting_bp.route('/ledger/<id>', methods=['PUT'])
@token_required
def update_entry(id):
    print(f"DEBUG: update_entry called for {id}")
    data = request.get_json()
    print(f"DEBUG: Payload: {data}")
    entry = LedgerEntry.objects(id=id, agencyId=g.agency_id).first()
    if not entry:
        return jsonify({'error': 'Entry not found'}), 404
        
    try:
        # Revert previous booking effect if any
        if entry.bookingId and entry.type == 'Credit':
            entry.bookingId.paidAmount = (entry.bookingId.paidAmount or 0) - entry.amount
            entry.bookingId.save()
            
        # Update fields
        entry.type = data['type']
        entry.amount = Decimal(data['amount'])
        entry.description = data['description']
        
        if data.get('customerId'):
             from models.customer import Customer
             customer = Customer.objects(id=data['customerId'], agencyId=g.agency_id).first()
             entry.customerId = customer
        else:
             entry.customerId = None

        # Apply new booking effect if any (Assuming booking link doesn't change for MVP, or we need to handle it)
        # For simplicity, if bookingId was present, we re-apply to the SAME booking.
        # If user wants to change Booking ID, that's complex logic. Let's assume booking link stays same for now unless explicitly handled.
        
        if entry.bookingId and entry.type == 'Credit':
             entry.bookingId.paidAmount = (entry.bookingId.paidAmount or 0) + entry.amount
             entry.bookingId.save()
             
        entry.save()
        return jsonify(mongo_to_dict(entry)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@accounting_bp.route('/ledger/<id>', methods=['DELETE'])
@token_required
def delete_entry(id):
    print(f"DEBUG: delete_entry called for {id}")
    entry = LedgerEntry.objects(id=id, agencyId=g.agency_id).first()
    if not entry:
        return jsonify({'error': 'Entry not found'}), 404
        
    try:
        # Revert booking effect
        if entry.bookingId and entry.type == 'Credit':
            entry.bookingId.paidAmount = (entry.bookingId.paidAmount or 0) - entry.amount
            entry.bookingId.save()
            
        entry.delete()
        return jsonify({'message': 'Deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@accounting_bp.route('/export', methods=['GET'])
@token_required
def export_ledger():
    fmt = request.args.get('format', 'csv')
    entries = LedgerEntry.objects(agencyId=g.agency_id).order_by('-date')
    
    # Prepare data
    data = []
    for entry in entries:
        row = {
            'Date': entry.date.strftime('%Y-%m-%d'),
            'Type': entry.type,
            'Description': entry.description,
            'Amount': float(entry.amount),
            'Customer': entry.customerId.fullName if entry.customerId else '-',
            'Booking': entry.bookingId.bookingNumber if entry.bookingId else '-'
        }
        data.append(row)
    
    if fmt == 'csv':
        si = io.StringIO()
        cw = csv.DictWriter(si, fieldnames=['Date', 'Type', 'Description', 'Amount', 'Customer', 'Booking'])
        cw.writeheader()
        cw.writerows(data)
        return Response(si.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=ledger.csv'})
        
    elif fmt == 'excel':
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(['Date', 'Type', 'Description', 'Amount', 'Customer', 'Booking'])
        for row in data:
            ws.append([row['Date'], row['Type'], row['Description'], row['Amount'], row['Customer'], row['Booking']])
        
        out = io.BytesIO()
        wb.save(out)
        out.seek(0)
        return send_file(out, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='ledger.xlsx')
        
    elif fmt == 'pdf':
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # Data for Table
        table_data = [['Date', 'Type', 'Description', 'Amount', 'Customer (Book#)']]
        for row in data:
            desc = row['Description'][:25] + '...' if len(row['Description']) > 25 else row['Description']
            cust = row['Customer']
            if row['Booking'] != '-':
                cust += f" ({row['Booking']})"
            table_data.append([row['Date'], row['Type'], desc, str(row['Amount']), cust])
            
        t = Table(table_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t)
        doc.build(elements)
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name='ledger.pdf')
        
    return jsonify({'error': 'Invalid format'}), 400
# Add these lines at the end of accounting.py after line 299


# Miscellaneous Expenses Endpoints
@accounting_bp.route('/misc-expenses', methods=['GET'])
@token_required
def get_misc_expenses():
    """Get all miscellaneous expenses for the agency"""
    from models.miscellaneous_expense import MiscellaneousExpense
    
    expenses = MiscellaneousExpense.objects(agencyId=g.agency_id).order_by('-expense_date')
    return jsonify(mongo_to_dict(expenses)), 200

@accounting_bp.route('/misc-expenses', methods=['POST'])
@token_required
def create_misc_expense():
    """Create a new miscellaneous expense"""
    from models.miscellaneous_expense import MiscellaneousExpense
    from decimal import Decimal
    
    data = request.get_json()
    
    try:
        expense = MiscellaneousExpense(
            agencyId=g.agency_id,
            title=data['title'],
            amount=Decimal(str(data['amount'])),
            expense_date=datetime.strptime(data['expense_date'], '%Y-%m-%d') if data.get('expense_date') else datetime.utcnow(),
            description=data.get('description', '')
        )
        expense.save()
        
        return jsonify(mongo_to_dict(expense)), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@accounting_bp.route('/misc-expenses/<id>', methods=['PUT'])
@token_required
def update_misc_expense(id):
    """Update a miscellaneous expense"""
    from models.miscellaneous_expense import MiscellaneousExpense
    from decimal import Decimal
    
    try:
        expense = MiscellaneousExpense.objects(id=id, agencyId=g.agency_id).first()
        if not expense:
            return jsonify({'error': 'Expense not found'}), 404
        
        data = request.get_json()
        
        if 'title' in data:
            expense.title = data['title']
        if 'amount' in data:
            expense.amount = Decimal(str(data['amount']))
        if 'expense_date' in data:
            expense.expense_date = datetime.strptime(data['expense_date'], '%Y-%m-%d')
        if 'description' in data:
            expense.description = data['description']
        
        expense.save()
        return jsonify(mongo_to_dict(expense)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@accounting_bp.route('/misc-expenses/<id>', methods=['DELETE'])
@token_required
def delete_misc_expense(id):
    """Delete a miscellaneous expense"""
    from models.miscellaneous_expense import MiscellaneousExpense
    
    try:
        expense = MiscellaneousExpense.objects(id=id, agencyId=g.agency_id).first()
        if not expense:
            return jsonify({'error': 'Expense not found'}), 404
        
        expense.delete()
        return jsonify({'message': 'Expense deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
