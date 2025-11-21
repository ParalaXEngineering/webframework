"""
File Handler Pages - Flask blueprint for file upload/download/delete routes.

This module provides HTTP endpoints for secure file management operations.
"""

from flask import Blueprint, request, send_file, jsonify, session, abort
from ..modules.log.logger_factory import get_logger

logger = get_logger(__name__)

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
        # No auth system = allow access (for development/testing)
        logger.warning(f"Permission check for {permission_module}.{permission_action} - auth system not available, allowing access")
        return True
    
    current_user = session.get('user')
    if not current_user:
        logger.warning(f"Permission check for {permission_module}.{permission_action} - no user in session")
        return False
    
    has_perm = auth_manager.has_permission(current_user, permission_module, permission_action)
    if not has_perm:
        logger.info(f"Permission denied: user '{current_user}' lacks '{permission_action}' permission for '{permission_module}'")
    
    return has_perm


@bp.route("/upload", methods=["POST"])
def upload():
    """Handle file upload with versioning support.
    
    Expected POST data:
        - file: The file to upload (multipart/form-data)
        - category: Top-level category (deprecated, for compatibility)
        - group_id: Group ID for versioning (optional, empty string shown in admin)
        - tags: Comma-separated tags (optional)
    
    Returns:
        JSON response with file metadata or error
    """
    if not file_manager:
        return jsonify({"error": "File manager not initialized"}), 500
    
    # Check permission
    if not _require_permission("FileManager", "upload"):
        return jsonify({
            "error": "Permission denied: You need 'upload' permission for FileManager. Contact your administrator."
        }), 403
    
    # Get file from request
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    # Get parameters
    category = request.form.get('category', 'general')
    group_id = request.form.get('group_id', '')
    tags_str = request.form.get('tags', '')
    
    # Parse tags (comma-separated)
    tag_names = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
    
    try:
        # Get current user
        current_user = session.get('user', 'GUEST')
        
        # PRE-RESOLVE GROUP: Query/create group BEFORE upload transaction
        # This prevents SQLAlchemy UNIQUE constraint failures when multiple files upload simultaneously
        group_obj = None
        if group_id:
            try:
                group_obj = file_manager.get_or_create_group(group_id, current_user)
            except Exception as e:
                logger.warning(f"Failed to resolve group '{group_id}': {e}")
                # Continue without group (will use string fallback)
        
        # PRE-RESOLVE TAGS: Query/create tags BEFORE upload transaction
        # This prevents SQLAlchemy session state conflicts when uploading multiple files
        tag_objects = []
        if tag_names:
            for tag_name in tag_names:
                try:
                    tag_obj = file_manager.get_or_create_tag(tag_name)
                    tag_objects.append(tag_obj)
                except Exception as e:
                    logger.warning(f"Failed to resolve tag '{tag_name}': {e}")
                    # Continue with other tags
        
        # Upload file with pre-resolved objects
        metadata = file_manager.upload_file(
            file, 
            category=category, 
            group_id=group_obj or group_id,  # Use object if available, fallback to string
            tags=tag_objects,  # Pass tag objects, not strings
            uploaded_by=current_user
        )
        
        logger.info(f"File uploaded by {current_user}: {metadata['name']} (group: {metadata['group_id']}, version: {metadata['version']})")
        
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
    """Serve a file for download from HashFS storage.
    
    Args:
        filepath: Storage path from database
    
    Returns:
        File download response
    """
    if not file_manager:
        abort(500, "File manager not initialized")
    
    # Check permission
    if not _require_permission("FileManager", "download"):
        abort(403, "Permission denied: You need 'download' permission for FileManager. Contact your administrator.")
    
    try:
        # Check if this is a thumbnail request
        is_thumbnail = '.thumbs' in filepath or request.args.get('inline') == 'true'
        
        if '.thumbs' in filepath:
            # Thumbnail files are stored outside HashFS in .thumbs directory
            thumb_path = file_manager.hashfs_path.parent / filepath
            if not thumb_path.exists():
                logger.warning(f"Thumbnail not found: {thumb_path}")
                abort(404, "Thumbnail not found")
            file_path = thumb_path
        else:
            # Regular files from HashFS
            file_path = file_manager.storage.get(filepath)
        
        # Get MIME type
        mime_type = file_manager.get_mime_type(filepath)
        
        logger.info(f"File download by {session.get('user', 'GUEST')}: {filepath}")
        
        # Send file - read into BytesIO to avoid Windows long path issues
        from io import BytesIO
        with open(file_path, 'rb') as f:
            file_data = BytesIO(f.read())
        
        return send_file(
            file_data,
            mimetype=mime_type,
            as_attachment=not is_thumbnail,  # Thumbnails display inline
            download_name=file_path.name if not is_thumbnail else None
        )
        
    except IOError as e:
        logger.warning(f"Invalid download path attempt: {filepath} - {e}")
        abort(404, "File not found")
        
    except Exception as e:
        logger.error(f"Unexpected download error for {filepath}: {e}", exc_info=True)
        abort(500, "Internal server error")


@bp.route("/delete/<int:file_id>", methods=["DELETE", "POST"])
def delete(file_id):
    """Delete a file by database ID.
    
    Args:
        file_id: Database ID of file version
    
    Returns:
        JSON response with success/error status
    """
    if not file_manager:
        return jsonify({"error": "File manager not initialized"}), 500
    
    # Check permission (higher permission level for delete)
    if not _require_permission("FileManager", "delete"):
        return jsonify({
            "error": "Permission denied: You need 'delete' permission for FileManager. Contact your administrator."
        }), 403
    
    try:
        # Delete file (reference-counted in HashFS)
        success = file_manager.delete_file(file_id)
        
        if success:
            logger.info(f"File deleted by {session.get('user', 'GUEST')}: ID {file_id}")
            return jsonify({
                "success": True,
                "message": "File deleted successfully"
            }), 200
        else:
            return jsonify({"error": "Failed to delete file"}), 500
            
    except Exception as e:
        logger.error(f"Unexpected delete error for file ID {file_id}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/list", methods=["GET"])
def list_files():
    """List files from database.
    
    Query params:
        group_id: Filter by group_id (optional)
        tag: Filter by tag (optional)
        limit: Maximum number of results (optional)
    
    Returns:
        JSON response with file list
    """
    if not file_manager:
        return jsonify({"error": "File manager not initialized"}), 500
    
    # Check permission (list is covered by view)
    if not _require_permission("FileManager", "view"):
        return jsonify({
            "error": "Permission denied: You need 'view' permission for FileManager. Contact your administrator."
        }), 403
    
    try:
        # Get query parameters
        group_id = request.args.get('group_id')
        tag = request.args.get('tag')
        limit = request.args.get('limit', type=int)
        
        files = file_manager.list_files_from_db(group_id=group_id, tag=tag, limit=limit)
        
        return jsonify({
            "success": True,
            "files": files,
            "count": len(files)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to list files: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/download/by_id/<int:file_id>", methods=["GET"])
def download_by_id(file_id):
    """Download file by database ID from HashFS.
    
    Args:
        file_id: Database ID of file version
    
    Returns:
        File download response
    """
    if not file_manager:
        abort(500, "File manager not initialized")
    
    # Check permission
    if not _require_permission("FileManager", "download"):
        abort(403, "Permission denied: You need 'download' permission for FileManager. Contact your administrator.")
    
    # Get file from database
    file_version = file_manager.get_file_by_id(file_id)
    
    if not file_version:
        abort(404, "File not found")
    
    try:
        # Get file from HashFS
        file_path = file_manager.storage.get(file_version.storage_path)
        
        # Check if file exists
        if not file_path.exists():
            logger.error(f"File not found in HashFS: {file_version.storage_path} (orphaned DB record)")
            abort(404, f"File '{file_version.filename}' not found on disk")
        
        logger.info(f"File download by {session.get('user', 'GUEST')}: {file_version.filename} (ID: {file_id})")
        
        # Send file - read into BytesIO to avoid Windows long path issues with send_file
        from io import BytesIO
        with open(file_path, 'rb') as f:
            file_data = BytesIO(f.read())
        
        return send_file(
            file_data,
            mimetype=file_version.mime_type,
            as_attachment=True,
            download_name=file_version.filename
        )
        
    except Exception as e:
        logger.error(f"Download by ID error for {file_id}: {e}", exc_info=True)
        abort(500, "Internal server error")


@bp.route("/versions/<group_id>/<filename>", methods=["GET"])
def get_versions(group_id: str, filename: str):
    """Get all versions of a file.
    
    Args:
        group_id: Group identifier
        filename: Filename
        
    Returns:
        JSON list of file versions
    """
    if not file_manager:
        abort(500, "File manager not initialized")
    
    # Check permission
    if not _require_permission("FileManager", "view"):
        abort(403, "Permission denied")
    
    try:
        versions = file_manager.get_file_versions(group_id, filename)
        return jsonify(versions), 200
    except Exception as e:
        logger.error(f"Error getting file versions: {e}")
        abort(500, "Internal server error")


@bp.route("/restore", methods=["POST"])
def handle_file_too_large(e):
    """Handle file size exceeded error."""
    return jsonify({"error": "File too large"}), 413

