from mongoengine import Document, StringField, DecimalField, DateTimeField, ReferenceField
from datetime import datetime
from .agency import Agency
from .facility import Facility

class Package(Document):
    agencyId = ReferenceField(Agency, required=True)
    facilityId = ReferenceField(Facility)  # Reference to Facility for Moaleem data
    name = StringField(required=True)
    description = StringField()
    
    # Dates & Duration
    startDate = DateTimeField()
    endDate = DateTimeField()
    duration = StringField() # Number of days e.g. "14 Days" or IntField
    
    # Pricing
    sharingPrice = DecimalField(precision=2)
    fourBedPrice = DecimalField(precision=2)
    threeBedPrice = DecimalField(precision=2)
    twoBedPrice = DecimalField(precision=2)
    
    createdAt = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'packages',
        'indexes': [
            {'fields': ['agencyId', 'name']}
        ]
    }
