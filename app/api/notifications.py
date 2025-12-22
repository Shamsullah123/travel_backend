from flask import Blueprint, request, jsonify, current_app
from models.notification import Notification
from models.user import User
import jwt

notifications_bp = Blueprint('notifications', __name__)

def get_current_user(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return User.objects(id=payload['sub']).first()
    except:
        return None

@notifications_bp.route('/', methods=['GET'])
def get_notifications():
    user = get_current_user(request)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Get unread first, then recent read
        notifications = Notification.objects(recipient=user).order_by('isRead', '-createdAt').limit(50)
        
        results = []
        for n in notifications:
            results.append({
                'id': str(n.id),
                'type': n.type,
                'title': n.title,
                'message': n.message,
                'data': n.data,
                'isRead': n.isRead,
                'createdAt': n.createdAt.isoformat()
            })
            
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/unread-count', methods=['GET'])
def get_unread_count():
    user = get_current_user(request)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        count = Notification.objects(recipient=user, isRead=False).count()
        return jsonify({'count': count}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/<id>/read', methods=['POST'])
def mark_as_read(id):
    user = get_current_user(request)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        n = Notification.objects(id=id, recipient=user).first()
        if n:
            n.isRead = True
            n.save()
            return jsonify({'message': 'Marked as read'}), 200
        return jsonify({'error': 'Notification not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/read-all', methods=['POST'])
def mark_all_read():
    user = get_current_user(request)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        Notification.objects(recipient=user, isRead=False).update(set__isRead=True)
        return jsonify({'message': 'All marked as read'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
