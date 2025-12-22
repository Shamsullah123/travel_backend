from mongoengine import Document, StringField, DateTimeField, BooleanField
from datetime import datetime

class ContactMessage(Document):
    name = StringField(required=True)
    email = StringField(required=True)
    subject = StringField(required=True)
    message = StringField(required=True)
    read = BooleanField(default=False)
    createdAt = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'contact_messages',
        'ordering': ['-createdAt'],
        'strict': False
    }
