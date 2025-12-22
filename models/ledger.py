from mongoengine import Document, StringField, DecimalField, DateTimeField, ReferenceField
from datetime import datetime
from .agency import Agency
from .booking import Booking
from .customer import Customer

class LedgerEntry(Document):
    agencyId = ReferenceField(Agency, required=True)
    bookingId = ReferenceField(Booking)
    customerId = ReferenceField(Customer)
    
    type = StringField(choices=('Credit', 'Debit'), required=True)
    
    amount = DecimalField(precision=2, required=True)
    date = DateTimeField(default=datetime.utcnow)
    description = StringField(required=True)
    
    slip_number = StringField()
    slip_attachment = StringField() # Path to file
    
    meta = {
        'collection': 'ledger_entries',
        'indexes': [
            {'fields': ['agencyId', 'date']}
        ]
    }
