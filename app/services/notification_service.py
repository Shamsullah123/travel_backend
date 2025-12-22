import os
import requests
from models.notification import Notification
from models.user import User

class NotificationService:
    @staticmethod
    def create_notification(user, type, title, message, data=None):
        """Creates a single notification for a user."""
        try:
            notification = Notification(
                recipient=user,
                type=type,
                title=title,
                message=message,
                data=data or {}
            )
            notification.save()
            return notification
        except Exception as e:
            print(f"Error creating notification: {e}")
            return None

    @staticmethod
    def broadcast_to_agencies(type, title, message, data=None, exclude_user_id=None):
        """Creates notifications for all Agency users (Owner/Agent)."""
        try:
            # Find all relevant users (all agency staff)
            # In a real app we might batch this or use a queue
            query = {'role__in': ['AgencyOwner', 'AgencyAdmin', 'Agent']}
            if exclude_user_id:
                query['id__ne'] = exclude_user_id

            users = User.objects(**query)
            
            notifications = []
            for user in users:
                # We save individually for now to trigger signals if needed, 
                # but bulk_insert is better for scale.
                # MongoDB creates are fast enough for N < 1000
                n = Notification(
                    recipient=user,
                    type=type,
                    title=title,
                    message=message,
                    data=data or {}
                )
                notifications.append(n)
            
            if notifications:
                Notification.objects.insert(notifications)
                
            # Trigger N8N
            NotificationService.trigger_n8n_webhook(type, data)
            
            return len(notifications)
        except Exception as e:
            print(f"Error broadcasting notifications: {e}")
            return 0

    @staticmethod
    def trigger_n8n_webhook(type, data):
        """Sends an event to n8n webhook."""
        webhook_url = os.environ.get('N8N_WEBHOOK_URL')
        if not webhook_url:
            # print("N8N_WEBHOOK_URL not set, skipping webhook.")
            return

        try:
            payload = {
                "event": "broadcast_notification",
                "type": type,
                "data": data,
                "timestamp": str(datetime.utcnow())
            }
            # Fire and forget (timeout short)
            requests.post(webhook_url, json=payload, timeout=2)
        except Exception as e:
            print(f"Failed to trigger n8n webhook: {e}")
