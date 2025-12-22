from mongoengine import Document, StringField, ReferenceField, DateTimeField
from datetime import datetime
from .agency import Agency

class Customer(Document):
    agencyId = ReferenceField(Agency, required=True)
    fullName = StringField(required=True)
    phone = StringField(required=True)
    cnic = StringField()
    passportNumber = StringField()
    passportIssueDate = DateTimeField()
    passportExpiry = DateTimeField()
    dob = DateTimeField()
    address = StringField()
    gender = StringField(choices=('Male', 'Female', 'Other'), default='Male')
    notes = StringField()
    finger_print = StringField(choices=('Yes', 'No'), default='No')
    enrollment_id = StringField()
    pictureUrl = StringField()  # Customer photo URL
    customer_photo = StringField() # Legacy/Alternate photo field
    passport_attachment = StringField()
    createdAt = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'customers',
        'strict': False,
        'indexes': [
            {'fields': ['agencyId', 'phone'], 'unique': True},
            {'fields': ['agencyId', 'passportNumber']}
        ]
    }
