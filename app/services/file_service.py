import os
import shutil
import uuid
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Define base upload directory
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")

def ensure_upload_dir(file_type: str) -> str:
    """Ensure the upload directory exists for the given file type."""
    target_dir = os.path.join(UPLOAD_DIR, file_type.lower())
    os.makedirs(target_dir, exist_ok=True)
    return target_dir

def upload_local_file(file_path: str, filename: str, file_type: str) -> str:
    """
    Save a file locally.
    
    Args:
        file_path: Temporary local path to the file
        filename: Original filename
        file_type: Type of file (e.g. 'images', 'documents')
        
    Returns:
        str: The local URL path for the saved file (e.g., /uploads/images/uuid-filename.jpg)
    """
    target_dir = ensure_upload_dir(file_type)
    
    # Generate unique filename to avoid collisions
    ext = os.path.splitext(filename)[1]
    unique_filename = f"{uuid.uuid4()}{ext}"
    destination = os.path.join(target_dir, unique_filename)
    
    # Copy from temp path to destination
    shutil.copy2(file_path, destination)
    logger.info(f"Saved file to {destination}")
    
    return f"/uploads/{file_type.lower()}/{unique_filename}"

def delete_local_file(file_url: str) -> bool:
    """
    Delete a locally stored file given its URL path.
    """
    if not file_url.startswith("/uploads/"):
        return False
    
    # Extract relative path from URL (e.g. "images/uuid-filename.jpg")
    rel_path = file_url[len("/uploads/"):]
    full_path = os.path.join(UPLOAD_DIR, rel_path)
    
    try:
        if os.path.exists(full_path):
            os.remove(full_path)
            logger.info(f"Deleted file {full_path}")
            return True
        else:
            logger.warning(f"File not found for deletion: {full_path}")
            return True # Consider it successfully "deleted" if it doesn't exist
    except Exception as e:
        logger.error(f"Error deleting file {full_path}: {e}")
        raise Exception(f"Failed to delete file: {str(e)}")

# Keep these names for compatibility with some existing code if needed, 
# but route them to the local functions or raise errors.
def upload_file_to_supabase(file_path: str, filename: str, file_type: str, bucket_name: str = None) -> str:
    return upload_local_file(file_path, filename, file_type)

def delete_file_from_supabase(file_name: str, file_type: str, bucket_name: str = None) -> bool:
    # Notice that we used to pass just the filename and type. 
    # With local files, it's easier to just pass the full URL path to delete_local_file.
    # We will update product_service.py to just use delete_local_file directly.
    return True
