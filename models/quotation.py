from mongoengine import Document, EmbeddedDocument, StringField, DecimalField, IntField, DateTimeField, ReferenceField, ListField, EmbeddedDocumentField
from datetime import datetime
from .agency import Agency
from .customer import Customer
from .visa_case import VisaCase

class LineItem(EmbeddedDocument):
    description = StringField(required=True)
    type = StringField(choices=('Visa', 'Ticket', 'Hotel', 'Insurance', 'Other'))
    costPrice = DecimalField(precision=2)
    sellPrice = DecimalField(precision=2, required=True)
    quantity = IntField(default=1)
    
class Quotation(Document):
    agencyId = ReferenceField(Agency, required=True)
    customerId = ReferenceField(Customer, required=True)
    visaCaseId = ReferenceField(VisaCase)
    
    quoteNumber = StringField(required=True)
    
    lineItems = ListField(EmbeddedDocumentField(LineItem))
    
    totalAmount = DecimalField(precision=2)
    validUntil = DateTimeField()
    
    status = StringField(choices=('Draft', 'Sent', 'Converted', 'Expired'), default='Draft')
    
    createdAt = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'quotations',
        'indexes': [
            {'fields': ['agencyId', 'quoteNumber'], 'unique': True}
        ]
    }
