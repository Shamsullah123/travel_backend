from mongoengine import Document, StringField, DecimalField, DateTimeField, ReferenceField
from datetime import datetime
from .agency import Agency

class MiscellaneousExpense(Document):
    agencyId = ReferenceField(Agency, required=True)
    title = StringField(required=True, max_length=200)
    amount = DecimalField(precision=2, required=True)
    expense_date = DateTimeField(default=datetime.utcnow)
    description = StringField()  # Optional additional details
    
    meta = {
        'collection': 'miscellaneous_expenses',
        'indexes': [
            {'fields': ['agencyId', 'expense_date']}
        ]
    }
