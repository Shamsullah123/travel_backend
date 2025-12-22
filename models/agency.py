from mongoengine import Document, EmbeddedDocument, StringField, DateTimeField, EmbeddedDocumentField
from datetime import datetime

class Branding(EmbeddedDocument):
    logoUrl = StringField()
    primaryColor = StringField()

class ContactInfo(EmbeddedDocument):
    phone = StringField()
    email = StringField()
    address = StringField()

class Agency(Document):
    name = StringField(required=True)
    status = StringField(choices=('Active', 'Suspended', 'Pending', 'Rejected'), default='Pending')
    subscriptionPlan = StringField(choices=('Basic', 'Premium'), default='Basic')
    contactInfo = EmbeddedDocumentField(ContactInfo)
    branding = EmbeddedDocumentField(Branding)
    createdAt = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'agencies',
        'strict': False
    }
