from mongoengine import Document, StringField, DateTimeField, ReferenceField
from datetime import datetime
from .agency import Agency

class AgentProfile(Document):
    name = StringField(required=True)
    source_name = StringField()
    mobile_number = StringField(required=True)
    cnic = StringField()
    
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    # Link to Agency (Tenant)
    agencyId = ReferenceField(Agency, required=True)

    meta = {
        'collection': 'agent_profiles',
        'indexes': [
            {'fields': ['agencyId', 'mobile_number'], 'unique': True},  # Enforce unique mobile per agency
            {'fields': ['agencyId', 'name']}
        ]
    }

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super(AgentProfile, self).save(*args, **kwargs)
