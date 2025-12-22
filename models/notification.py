from mongoengine import Document, ReferenceField, StringField, DateTimeField, BooleanField, DictField
from datetime import datetime
from models.user import User

class Notification(Document):
    recipient = ReferenceField(User, required=True)
    type = StringField(required=True, choices=['featured_post', 'visa_update', 'general'])
    title = StringField(required=True)
    message = StringField(required=True)
    data = DictField()
    isRead = BooleanField(default=False)
    createdAt = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'notifications',
        'indexes': [
            'recipient',
            '-createdAt',
            'isRead'
        ]
    }
