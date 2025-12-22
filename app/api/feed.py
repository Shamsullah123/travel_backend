from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService
from models.post import Post, Comment
from models.user import User

feed_bp = Blueprint('feed', __name__)

# Middleware helper (simplified for now, ideally strictly token based)
def get_current_user(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    token = auth_header.split(" ")[1]
    # In a real scenario, verify token via AuthService. 
    # For now, we trust the ID sent or implement token logic if needed.
    # Actually, let's use the AuthService to verify if possible, or just extract ID if we trusted the gateway.
    # But since we have AuthService.refresh_token, let's try to decode if we can.
    # Simplification: We will assume the frontend sends the user ID in a header or we trust the implementation for this MVP step.
    # BETTER: Use a decorator. But for speed, let's just get the user from the body or simplified auth.
    # WAIT, we have AuthService. We should use it. 
    # For this MVP, let's assume the client sends 'X-User-ID' for write ops if we don't have full middleware setup yet.
    # ACTUALLY, I should implement a simple token verify here or use the existing structure.
    # I will assume the request contains a valid token and I will decode it.
    try:
        import jwt
        from flask import current_app
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return User.objects(id=payload['sub']).first()
    except:
        return None

@feed_bp.route('/', methods=['GET'])
def get_feed():
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        skip = (page - 1) * limit

        posts = Post.objects(status='active').order_by('-isFeatured', '-createdAt').skip(skip).limit(limit)
        
        # Helper function to serialize comments recursively
        def serialize_comment(comment):
            return {
                'user': comment.user.name if comment.user else 'Unknown',
                'text': comment.text,
                'createdAt': comment.createdAt.isoformat(),
                'replies': [serialize_comment(reply) for reply in (comment.replies or [])]
            }
        
        # Serialize
        feed_data = []
        for post in posts:
            feed_data.append({
                'id': str(post.id),
                'agencyName': post.agency.name,
                'agencyLogo': post.agency.logoUrl if hasattr(post.agency, 'logoUrl') else None,
                'content': post.content,
                'mediaUrls': post.mediaUrls,
                'postType': post.postType,
                'whatsappCtaNumber': post.whatsappCtaNumber,
                'visibility': post.visibility,
                'createdAt': post.createdAt.isoformat(),
                'likesCount': len(post.likes),
                'commentsCount': len(post.comments),
                'isFeatured': post.isFeatured,
                'comments': [serialize_comment(comment) for comment in post.comments]
            })
            
        return jsonify(feed_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@feed_bp.route('/', methods=['POST'])
def create_post():
    user = get_current_user(request)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if user.agencyId.status != 'Active':
        return jsonify({'error': 'Agency not active'}), 403

    data = request.get_json()
    if not data.get('content'):
        return jsonify({'error': 'Content required'}), 400

    try:
        # Sanitize WhatsApp Number
        raw_number = data.get('whatsappCtaNumber')
        if not raw_number and user.agencyId and user.agencyId.contactInfo:
            raw_number = user.agencyId.contactInfo.phone

        clean_number = None
        if raw_number:
            import re
            # Keep only digits
            clean_number = "".join(re.findall(r'\d+', raw_number))

        post = Post(
            agency=user.agencyId,
            content=data.get('content'),
            mediaUrls=data.get('mediaUrls', []),
            postType=data.get('postType', 'announcement'),
            whatsappCtaNumber=clean_number,
            visibility=data.get('visibility', 'agencies_only'),
            status='active'
        )
        post.save()

        # Trigger Notifications
        from app.services.notification_service import NotificationService
        
        if post.isFeatured:
            NotificationService.broadcast_to_agencies(
                type='featured_post',
                title='New Featured Opportunity!',
                message=f"Check out this featured post from {post.agency.name}: {post.content[:50]}...",
                data={'postId': str(post.id), 'postType': post.postType},
                exclude_user_id=user.id
            )
        elif post.postType == 'visa':
            NotificationService.broadcast_to_agencies(
                type='visa_update',
                title='New Visa Update',
                message=f"New Visa opportunity available: {post.content[:50]}...",
                data={'postId': str(post.id), 'postType': 'visa'},
                exclude_user_id=user.id
            )
        else:
             NotificationService.broadcast_to_agencies(
                type='new_post',
                title=f'New Post from {post.agency.name}',
                message=f"{post.content[:50]}...",
                data={'postId': str(post.id), 'postType': post.postType},
                exclude_user_id=user.id
            )

        return jsonify({'message': 'Post created', 'id': str(post.id)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@feed_bp.route('/<id>/like', methods=['POST'])
def like_post(id):
    user = get_current_user(request)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        post = Post.objects.get(id=id)
        if user in post.likes:
            post.likes.remove(user)
            action = 'unliked'
        else:
            post.likes.append(user)
            action = 'liked'
        post.save()
        return jsonify({'message': f'Post {action}', 'likesCount': len(post.likes)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@feed_bp.route('/<id>/comment', methods=['POST'])
def comment_post(id):
    user = get_current_user(request)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    if not data or not data.get('text'):
        return jsonify({'error': 'Comment text required'}), 400

    try:
        post = Post.objects.get(id=id)
        comment_index = data.get('commentIndex')  # Optional: index of parent comment for replies
        
        new_comment = Comment(user=user, text=data['text'])
        
        if comment_index is not None:
            # This is a reply to an existing comment
            if 0 <= comment_index < len(post.comments):
                if not post.comments[comment_index].replies:
                    post.comments[comment_index].replies = []
                post.comments[comment_index].replies.append(new_comment)
            else:
                return jsonify({'error': 'Invalid comment index'}), 400
        else:
            # This is a top-level comment
            post.comments.append(new_comment)
            
        post.save()
        return jsonify({'message': 'Comment added', 'commentsCount': len(post.comments)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
