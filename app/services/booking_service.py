from datetime import datetime
import random
from models.booking import Booking
from models.quotation import Quotation

class BookingService:
    @staticmethod
    def generate_number(prefix="BK"):
        """
        Generates a readable ID like BK-20231024-1234
        In production, rely on a sequence counter in DB to avoid collisions.
        For MVP, timestamp + random is sufficient.
        """
        date_str = datetime.utcnow().strftime("%Y%m%d")
        rand_suffix = random.randint(1000, 9999)
        return f"{prefix}-{date_str}-{rand_suffix}"

    @staticmethod
    def create_booking_from_quote(quote_id, agency_id):
        quote = Quotation.objects(id=quote_id, agencyId=agency_id).first()
        if not quote:
            return None, "Quotation not found"
            
        if quote.status == 'Converted':
            return None, "Quotation already converted"
            
        # Create Booking
        booking = Booking(
            agencyId=quote.agencyId,
            quotationId=quote,
            customerId=quote.customerId,
            bookingNumber=BookingService.generate_number("BK"),
            totalAmount=quote.totalAmount,
            paidAmount=0,
            status='Confirmed'
        )
        booking.save()
        
        # Update Quote Status
        quote.status = 'Converted'
        quote.save()
        
        return booking, None
