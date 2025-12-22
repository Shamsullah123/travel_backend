from mongoengine import Document, StringField, ReferenceField, ListField, BooleanField, DateTimeField
from datetime import datetime
from .agency import Agency

class User(Document):
    agencyId = ReferenceField(Agency, required=True)
    email = StringField(required=True, unique=True)
    passwordHash = StringField(required=True)
    role = StringField(choices=('SuperAdmin', 'AgencyAdmin', 'Agent'), default='Agent', required=True)
    name = StringField(required=True)
    phone = StringField()  # Mobile number
    permissions = ListField(StringField())
    isActive = BooleanField(default=True)
    createdAt = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'users',
        'strict': False,
        'indexes': [
            {'fields': ['agencyId', 'email'], 'unique': True}, 
            'email'
        ]
    }
