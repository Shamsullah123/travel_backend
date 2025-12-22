import os
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
import uuid

media_bp = Blueprint('media', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mp3'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@media_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Unique name
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # CUSTOM LOCAL PATH (User Request)
        # Using a fixed path on C: drive for persistence "on personal computer"
        BASE_UPLOAD_DIR = r"C:\Users\PC\TravAgency_Uploads"
        os.makedirs(BASE_UPLOAD_DIR, exist_ok=True)
        
        file.save(os.path.join(BASE_UPLOAD_DIR, unique_filename))
        
        # URL construction
        # We return the filename so it works with ServiceCard's relative logic,
        # OR we returns the full URL. ServiceCard checks for http.
        # Let's return the full URL matching our new route.
        url = f"http://localhost:5000/uploads/{unique_filename}"
        
        return jsonify({'url': url, 'type': 'image' if filename.rsplit('.', 1)[1].lower() in ['png', 'jpg', 'jpeg', 'gif'] else 'video'}), 200
        
    return jsonify({'error': 'File type not allowed'}), 400

# SERVE FILES FROM LOCAL DIR
@media_bp.route('/uploads/<filename>')
def serve_upload(filename):
    BASE_UPLOAD_DIR = r"C:\Users\PC\TravAgency_Uploads"
    return send_from_directory(BASE_UPLOAD_DIR, filename)

# Legacy route support (if needed)
@media_bp.route('/static/uploads/<filename>')
def serve_static_upload(filename):
    BASE_UPLOAD_DIR = r"C:\Users\PC\TravAgency_Uploads"
    return send_from_directory(BASE_UPLOAD_DIR, filename)
