"""
File Handler Pages - Flask blueprint for file upload/download/delete routes.

This module provides HTTP endpoints for secure file management operations.
"""

from flask import Blueprint, request, send_file, jsonify, session, abort
from werkzeug.exceptions import RequestEntityTooLarge
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

bp = Blueprint("file_handler", __name__, url_prefix="/files")

# File manager instance will be injected by main.py
file_manager = None


def _get_auth_manager():
    """Get auth_manager dynamically to avoid initialization issues."""
    try:
        from ..modules.auth.auth_manager import auth_manager
        return auth_manager
    except ImportError:
        return None


def _require_permission(permission_module: str, permission_action: str = "upload"):
    """Check if current user has permission.
    
    Args:
        permission_module: Module name (e.g., "FileManager")
        permission_action: Action name (e.g., "upload", "download", "delete")
        
    Returns:
        bool: True if permitted, False otherwise
    """
    auth_manager = _get_auth_manager()
    if not auth_manager:
        # No auth system = allow access
        return True
    
    current_user = session.get('user')
    if not current_user:
        return False
    
    return auth_manager.check_permission(current_user, permission_module, permission_action)


@bp.route("/upload", methods=["POST"])
def upload():
    """Handle file upload.
    
    Expected POST data:
        - file: The file to upload (multipart/form-data)
        - category: Top-level category (e.g., "documents")
        - subcategory: Optional subcategory (e.g., user ID)
    
    Returns:
        JSON response with file metadata or error
    """
    if not file_manager:
        return jsonify({"error": "File manager not initialized"}), 500
    
    # Check permission
    if not _require_permission("FileManager", "upload"):
        return jsonify({"error": "Permission denied"}), 403
    
    # Get file from request
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    # Get category/subcategory
    category = request.form.get('category', 'general')
    subcategory = request.form.get('subcategory', '')
    
    try:
        # Upload file
        metadata = file_manager.upload_file(file, category, subcategory)
        
        logger.info(f"File uploaded by {session.get('user', 'GUEST')}: {metadata['path']}")
        
        return jsonify({
            "success": True,
            "file": metadata
        }), 200
        
    except ValueError as e:
        # Validation error (file type, size, etc.)
        logger.warning(f"File upload validation failed: {e}")
        return jsonify({"error": str(e)}), 400
        
    except IOError as e:
        # File system error
        logger.error(f"File upload I/O error: {e}")
        return jsonify({"error": "Failed to save file"}), 500
        
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected file upload error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/download/<path:filepath>", methods=["GET"])
def download(filepath):
    """Serve a file for download.
    
    Args:
        filepath: Relative path to file (from base storage directory)
    
    Returns:
        File download response
    """
    if not file_manager:
        abort(500, "File manager not initialized")
    
    # Check permission
    if not _require_permission("FileManager", "download"):
        abort(403, "Permission denied")
    
    try:
        # Get absolute file path with security checks
        file_path = file_manager.get_file_path(filepath)
        
        # Get MIME type
        mime_type = file_manager.get_mime_type(filepath)
        
        # Check if this is a thumbnail request (in-browser display)
        is_thumbnail = '.thumbs' in filepath or request.args.get('inline') == 'true'
        
        logger.info(f"File download by {session.get('user', 'GUEST')}: {filepath}")
        
        # Send file
        return send_file(
            file_path,
            mimetype=mime_type,
            as_attachment=not is_thumbnail,  # Thumbnails display inline
            download_name=file_path.name if not is_thumbnail else None
        )
        
    except ValueError as e:
        # Path traversal or invalid path
        logger.warning(f"Invalid download path attempt: {filepath} - {e}")
        abort(400, str(e))
        
    except FileNotFoundError:
        logger.warning(f"Download requested for non-existent file: {filepath}")
        abort(404, "File not found")
        
    except Exception as e:
        logger.error(f"Unexpected download error for {filepath}: {e}", exc_info=True)
        abort(500, "Internal server error")


@bp.route("/delete/<path:filepath>", methods=["DELETE", "POST"])
def delete(filepath):
    """Delete a file.
    
    Args:
        filepath: Relative path to file
    
    Query params:
        permanent: If 'true', permanently delete instead of soft-delete
    
    Returns:
        JSON response with success/error status
    """
    if not file_manager:
        return jsonify({"error": "File manager not initialized"}), 500
    
    # Check permission (higher permission level for delete)
    if not _require_permission("FileManager", "delete"):
        return jsonify({"error": "Permission denied"}), 403
    
    # Get delete mode
    permanent = request.args.get('permanent', 'false').lower() == 'true'
    soft_delete = not permanent
    
    try:
        # Delete file
        success = file_manager.delete_file(filepath, soft_delete=soft_delete)
        
        if success:
            logger.info(f"File {'permanently ' if permanent else ''}deleted by {session.get('user', 'GUEST')}: {filepath}")
            return jsonify({
                "success": True,
                "message": f"File {'permanently deleted' if permanent else 'moved to trash'}"
            }), 200
        else:
            return jsonify({"error": "Failed to delete file"}), 500
            
    except ValueError as e:
        logger.warning(f"Invalid delete path attempt: {filepath} - {e}")
        return jsonify({"error": str(e)}), 400
        
    except Exception as e:
        logger.error(f"Unexpected delete error for {filepath}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/list", methods=["GET"])
def list_files():
    """List files in a category/subcategory.
    
    Query params:
        category: Category to list (optional, default = all)
        subcategory: Subcategory to list (optional, default = all in category)
    
    Returns:
        JSON response with file list
    """
    if not file_manager:
        return jsonify({"error": "File manager not initialized"}), 500
    
    # Check permission
    if not _require_permission("FileManager", "list"):
        return jsonify({"error": "Permission denied"}), 403
    
    category = request.args.get('category', '')
    subcategory = request.args.get('subcategory', '')
    
    try:
        files = file_manager.list_files(category, subcategory)
        
        return jsonify({
            "success": True,
            "files": files,
            "count": len(files)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to list files: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@bp.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    """Handle file size exceeded error."""
    return jsonify({"error": "File too large"}), 413
