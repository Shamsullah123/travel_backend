import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
import cloudinary
import cloudinary.uploader
import cloudinary.api

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file, subfolder):
    """
    Uploads a file to Cloudinary.
    Returns the secure URL of the uploaded file.
    """
    if file and allowed_file(file.filename):
        try:
            # Upload to Cloudinary
            # Use subfolder as 'folder' in Cloudinary to organize
            upload_result = cloudinary.uploader.upload(
                file, 
                folder=subfolder,
                resource_type="auto" # Auto-detect image vs raw (pdf)
            )
            return upload_result.get('secure_url')
        except Exception as e:
            print(f"Cloudinary upload failed: {e}")
            return None
    return None

