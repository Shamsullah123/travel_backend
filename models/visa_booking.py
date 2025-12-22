from mongoengine import Document, StringField, FloatField, IntField, DateTimeField, ReferenceField, ListField, EmbeddedDocument, EmbeddedDocumentField, BooleanField
from datetime import datetime
from .agency import Agency
from .visa_case import VisaCase # Optional if needed, but likely independent
from .customer import Customer

class Applicant(EmbeddedDocument):
    fullName = StringField(required=True)
    gender = StringField(choices=('Male', 'Female'), required=True)
    dob = DateTimeField(required=True)
    passportNumber = StringField(required=True)
    passportExpiry = DateTimeField(required=True)
    nationality = StringField(required=True)
    
    # File paths
    passportScan = StringField()
    cnicScan = StringField()
    photo = StringField()
    medical = StringField()
    police = StringField()
    vaccine = StringField()

class VisaBooking(Document):
    buyer_agency_id = ReferenceField(Agency, required=True)
    seller_agency_id = ReferenceField(Agency, required=True)
    visa_group_id = ReferenceField('VisaGroup', required=True) # Lazy ref to avoid circular if VisaGroup model exists or using generic ObjectId
    
    booking_reference = StringField(required=True, unique=True)
    quantity = IntField(required=True)
    
    applicants = ListField(EmbeddedDocumentField(Applicant))
    
    total_amount = FloatField(required=True)
    discount = FloatField(default=0.0)
    final_amount = FloatField(required=True)
    
    payment_method = StringField(choices=('Cash', 'Bank Transfer'), required=True)
    receipt_url = StringField()
    
    status = StringField(choices=('pending_documents', 'submitted', 'processing', 'approved', 'rejected', 'delivered'), default='submitted')
    
    is_read_by_seller = BooleanField(default=False)
    is_read_by_buyer = BooleanField(default=False)
    
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'visabookings',
        'indexes': [
            'buyer_agency_id',
            'seller_agency_id',
            'visa_group_id',
            'status',
            'created_at'
        ]
    }
