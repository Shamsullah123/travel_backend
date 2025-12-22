from mongoengine import Document, StringField, ListField, IntField, EmbeddedDocument, EmbeddedDocumentField, EmbeddedDocumentListField, ReferenceField, DateTimeField
from datetime import datetime
from .agency import Agency

class TransportRoute(EmbeddedDocument):
    transport_from = StringField()
    transport_to = StringField()

class Transport(EmbeddedDocument):
    status = StringField(required=True, choices=('Yes', 'No'), default='No')
    routes = EmbeddedDocumentListField(TransportRoute)

class Ticket(EmbeddedDocument):
    status = StringField(required=True, choices=('Yes', 'No'), default='No')
    ticket_type = StringField(choices=('Direct', 'Indirect'))

class Ziarat(EmbeddedDocument):
    status = StringField(required=True, choices=('Yes', 'No'), default='No')
    major_ziarat = ListField(StringField()) # Taif, Badar, Juranah
    ziarat_count = IntField()

class Moaleem(EmbeddedDocument):
    status = StringField(required=True, choices=('Yes', 'No'), default='No')
    moaleem_name = StringField()
    moaleem_contact = StringField()

class Umrahs(EmbeddedDocument):
    status = StringField(required=True, choices=('Yes', 'No'), default='No')
    umrahs_count = IntField()

class Facility(Document):
    agencyId = ReferenceField(Agency, required=True)
    
    # Simple Fields
    hotel = StringField(required=True, choices=('Yes', 'No'), default='No')
    visa = StringField(required=True, choices=('Yes', 'No'), default='No')
    food = StringField(required=True, choices=('Yes', 'No'), default='No')
    medical = StringField(required=True, choices=('Yes', 'No'), default='No')
    
    # Complex Fields
    transport = EmbeddedDocumentField(Transport, default=Transport)
    ticket = EmbeddedDocumentField(Ticket, default=Ticket)
    ziarat = EmbeddedDocumentField(Ziarat, default=Ziarat)
    moaleem = EmbeddedDocumentField(Moaleem, default=Moaleem)
    umrahs = EmbeddedDocumentField(Umrahs, default=Umrahs)
    
    createdAt = DateTimeField(default=datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'facilities',
        'indexes': [
            {'fields': ['agencyId']}
        ]
    }

    def save(self, *args, **kwargs):
        self.updatedAt = datetime.utcnow()
        return super(Facility, self).save(*args, **kwargs)
