from mongoengine import Document, EmbeddedDocument, StringField, DateTimeField, ReferenceField, ListField, EmbeddedDocumentField
from datetime import datetime
from .agency import Agency
from .customer import Customer

class VisaStatusHistory(EmbeddedDocument):
    status = StringField(required=True)
    date = DateTimeField(default=datetime.utcnow)
    updatedBy = StringField()
    notes = StringField()

class VisaCase(Document):
    agencyId = ReferenceField(Agency, required=True)
    customerId = ReferenceField(Customer, required=True)
    
    country = StringField(required=True)
    visaType = StringField(required=True)
    
    status = StringField(default='New', required=True)
    
    submissionDate = DateTimeField()
    expectedIssueDate = DateTimeField()
    
    history = ListField(EmbeddedDocumentField(VisaStatusHistory))
    
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'visa_cases',
        'indexes': [
            {'fields': ['agencyId', 'status']},
            {'fields': ['agencyId', 'customerId']}
        ]
    }
