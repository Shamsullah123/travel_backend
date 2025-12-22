from flask import Blueprint, request, jsonify
from models.post import Post
from models.user import User
import jwt
from flask import current_app

admin_moderation_bp = Blueprint('admin_moderation', __name__)

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

def is_super_admin(user):
    return user and user.role == 'SuperAdmin'

@admin_moderation_bp.route('/posts', methods=['GET'])
def get_posts():
    user = get_current_user(request)
    if not is_super_admin(user):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        skip = (page - 1) * limit
        status_filter = request.args.get('status')

        query = {}
        if status_filter:
            query['status'] = status_filter

        posts = Post.objects(**query).order_by('-createdAt').skip(skip).limit(limit)
        
        results = []
        for post in posts:
            results.append({
                'id': str(post.id),
                'agencyName': post.agency.name,
                'content': post.content,
                'mediaUrls': post.mediaUrls,
                'postType': post.postType,
                'status': post.status,
                'isFeatured': post.isFeatured,
                'likesCount': len(post.likes),
                'createdAt': post.createdAt.isoformat()
            })
            
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_moderation_bp.route('/posts/<id>', methods=['PATCH'])
def update_post_status(id):
    user = get_current_user(request)
    if not is_super_admin(user):
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    try:
        post = Post.objects.get(id=id)
        
        if 'status' in data:
            post.status = data['status']
        if 'isFeatured' in data:
            post.isFeatured = data['isFeatured']
            
        post.save()
        return jsonify({'message': 'Post updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
