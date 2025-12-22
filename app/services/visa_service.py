from datetime import datetime
from models.visa_case import VisaCase, VisaStatusHistory

class VisaService:
    VALID_TRANSITIONS = {
        'New': ['DocsReceived', 'Cancelled'],
        'DocsReceived': ['Submitted', 'Cancelled'],
        'Submitted': ['Approved', 'Rejected'],
        'Approved': ['Completed'],
        'Rejected': ['Completed'], # Loop back or close
        'Completed': [],
        'Cancelled': []
    }

    @staticmethod
    def change_status(case: VisaCase, new_status: str, user_id: str, notes: str = None):
        current_status = case.status
        
        # Validation Logic
        if new_status not in VisaService.VALID_TRANSITIONS.get(current_status, []):
            # Allow super override or force? For MVP, strict enforcement.
            # Except if same status (update info)
            if new_status != current_status:
                return False, f"Invalid transition from {current_status} to {new_status}"
        
        # Update Case
        case.status = new_status
        case.updatedAt = datetime.utcnow()
        
        # Add History
        history_entry = VisaStatusHistory(
            status=new_status,
            date=datetime.utcnow(),
            updatedBy=user_id,
            notes=notes
        )
        case.history.append(history_entry)
        case.save()
        
        return True, case
