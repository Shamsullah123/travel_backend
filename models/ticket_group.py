from mongoengine import Document, StringField, ReferenceField, IntField, FloatField, BooleanField, DateTimeField
from datetime import datetime
from .agency import Agency

class TicketGroup(Document):
    agencyId = ReferenceField(Agency, required=True)
    airline = StringField(required=True)
    sector = StringField(required=True)
    travel_type = StringField(required=True) # Umrah, KSA One Way, etc.
    date = DateTimeField(required=True)
    flight_no = StringField(required=True)
    departure_time = StringField() # New field
    arrival_time = StringField() # New field
    time = StringField() # Keeping for backward compatibility, now optional
    
    # Return Ticket Details (Optional, for Umrah/Return trips)
    return_flight_no = StringField()
    return_date = DateTimeField()
    return_departure_time = StringField()
    return_arrival_time = StringField()

    baggage = StringField()
    meal = BooleanField(default=False)
    price_per_seat = FloatField(required=True)
    total_seats = IntField(required=True, min_value=1)
    available_seats = IntField(required=True)  # No min_value to allow atomic decrement
    status = StringField(choices=('active', 'closed'), default='active')
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'ticket_groups',
        'indexes': [
            'agencyId',
            'status',
            ('travel_type', 'sector'),
            'date'
        ]
    }

    def clean(self):
        # Ensure available_seats doesn't exceed total_seats
        if self.available_seats > self.total_seats:
            self.available_seats = self.total_seats
        if self.available_seats < 0:
            self.available_seats = 0
