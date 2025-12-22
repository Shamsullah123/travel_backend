from mongoengine import Document, StringField, BooleanField, DateTimeField
from datetime import datetime

class SystemConfig(Document):
    config_type = StringField(choices=('airline', 'sector', 'travel_type'), required=True)
    value = StringField(required=True)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'system_config',
        'indexes': [
            'config_type',
            'is_active',
            {'fields': ['config_type', 'value'], 'unique': True}
        ]
    }
