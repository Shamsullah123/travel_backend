from datetime import datetime
from mongoengine import Document, StringField, ListField, ReferenceField, DateTimeField, EmbeddedDocument, EmbeddedDocumentField, BooleanField
from .agency import Agency
from .user import User

class Comment(EmbeddedDocument):
    user = ReferenceField(User, required=True)
    text = StringField(required=True)
    createdAt = DateTimeField(default=datetime.utcnow)
    replies = ListField(EmbeddedDocumentField('self'))  # Nested replies


class Post(Document):
    agency = ReferenceField(Agency, required=True)
    content = StringField(required=True)
    mediaUrls = ListField(StringField())
    postType = StringField(default='announcement', choices=['visa', 'umrah', 'trick', 'announcement'])
    whatsappCtaNumber = StringField()
    visibility = StringField(default='agencies_only', choices=['public', 'agencies_only'])
    status = StringField(default='active', choices=['active', 'rejected', 'archived'])
    
    likes = ListField(ReferenceField(User))
    comments = ListField(EmbeddedDocumentField(Comment))
    isFeatured = BooleanField(default=False)
    createdAt = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'posts',
        'indexes': [
            '-createdAt',
            'agency',
            'isFeatured',
            'postType',
            'visibility',
            'status'
        ]
    }
