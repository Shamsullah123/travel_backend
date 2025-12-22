from mongoengine import Document, StringField, ReferenceField, DateTimeField, IntField
from datetime import datetime
from .agency import Agency

class Agent(Document):
    agent_name = StringField(required=True)
    source_name = StringField(required=True)
    source_cnic_number = StringField()
    source_cnic_attachment = StringField() # Path to file
    slip_number = StringField()
    slip_attachment = StringField() # Path to file
    mobile_number = StringField(required=True)
    description = StringField()
    amount_paid = IntField()
    created_by_agency = ReferenceField(Agency)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'agents',
        'strict': False,
        'indexes': [
            {'fields': ['created_by_agency', 'mobile_number']},
            {'fields': ['created_by_agency', 'agent_name']}
        ]
    }

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super(Agent, self).save(*args, **kwargs)
