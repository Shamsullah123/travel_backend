from mongoengine import Document, StringField, DictField, DateTimeField
from datetime import datetime

class SystemSetting(Document):
    key = StringField(required=True, unique=True)
    value = DictField(default={})
    description = StringField()
    updatedAt = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'system_settings',
        'strict': False
    }
