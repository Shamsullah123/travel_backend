from mongoengine import Document, StringField, ReferenceField, IntField, FloatField, DateTimeField, ListField, EmbeddedDocument, EmbeddedDocumentField, BooleanField
from datetime import datetime
from .agency import Agency
from .ticket_group import TicketGroup

class Passenger(EmbeddedDocument):
    type = StringField(choices=('Adult', 'Child', 'Infant'), required=True)
    title = StringField()
    givenName = StringField(required=True)
    surName = StringField(required=True)
    passportNumber = StringField(required=True)
    dob = DateTimeField(required=True)
    expiryDate = DateTimeField(required=True)

class TicketBooking(Document):
    agencyId = ReferenceField(Agency, required=True) # The Buyer
    sellerAgencyId = ReferenceField(Agency, required=True) # The Seller (Owner of Group)
    ticketGroupId = ReferenceField(TicketGroup, required=True)
    booking_reference = StringField(required=True, unique=True)
    
    seats_booked = IntField(required=True, min_value=0) # Relaxed from 1 for debugging
    total_price = FloatField(required=True)
    passengers = ListField(EmbeddedDocumentField(Passenger))
    
    status = StringField(choices=('pending', 'confirmed', 'rejected', 'cancelled'), default='pending')
    
    # Notification Flags
    is_read_by_buyer = BooleanField(default=False)
    is_read_by_seller = BooleanField(default=False)
    
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'ticket_bookings',
        'indexes': [
            'agencyId',
            'ticketGroupId',
            'booking_reference'
        ]
    }
