from mongoengine import Document, StringField, DecimalField, DateTimeField, ReferenceField
from datetime import datetime
from decimal import Decimal
from .agency import Agency
from .customer import Customer
from .quotation import Quotation

from .package import Package

class Booking(Document):
    agencyId = ReferenceField(Agency, required=True)
    quotationId = ReferenceField(Quotation, required=False) # Changed to optional
    packageId = ReferenceField(Package, required=False) # Added for direct booking
    customerId = ReferenceField(Customer, required=True)
    
    bookingNumber = StringField(required=True)
    
    # Pricing Breakdown
    category = StringField(choices=('Sharing', '4 Bed', '3 Bed', '2 Bed')) # Category selected
    baseAmount = DecimalField(precision=2, default=Decimal('0.00')) # Price from package
    discount = DecimalField(precision=2, default=Decimal('0.00'))   # Discount given
    totalAmount = DecimalField(precision=2, required=True) # Final amount after discount
    
    paidAmount = DecimalField(precision=2, default=Decimal('0.00'))
    balanceDue = DecimalField(precision=2) 
    
    status = StringField(choices=('Confirmed', 'Ticketed', 'Completed', 'Cancelled'), default='Confirmed')
    
    pnr = StringField()
    supplierRef = StringField()
    
    createdAt = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'bookings',
        'indexes': [
            {'fields': ['agencyId', 'bookingNumber'], 'unique': True}
        ]
    }
    
    def clean(self):
        if self.totalAmount is not None:
            # Ensure paidAmount is Decimal before subtraction
            paid = self.paidAmount if self.paidAmount is not None else Decimal('0.00')
            if not isinstance(paid, Decimal):
                paid = Decimal(str(paid))
                
            total = self.totalAmount
            if not isinstance(total, Decimal):
                total = Decimal(str(total))
                
            self.balanceDue = total - paid
