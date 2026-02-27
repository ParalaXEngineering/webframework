"""
File Handler Pages - Flask blueprint for file upload/download/delete routes.

This module provides HTTP endpoints for secure file management operations.
"""

# Standard library
from io import BytesIO

# Third-party
from flask import Blueprint, request, send_file, jsonify, session, abort, url_for

# Framework modules - constants and i18n
from ..modules.constants import (
    IMAGE_MAX_SIZE,
    USER_GUEST_NAME,
)
from ..modules.i18n.messages import (
    ERROR_FILE_HANDLER_NOT_INIT,
    ERROR_NO_FILE_PROVIDED,
    ERROR_NO_FILE_SELECTED,
    ERROR_INVALID_UPLOAD_PATH,
    ERROR_FAILED_SAVE_FILE,
    ERROR_PERMISSION_DENIED_UPLOAD,
    ERROR_PERMISSION_DENIED_DOWNLOAD,
    ERROR_PERMISSION_DENIED_DELETE,
    ERROR_PERMISSION_DENIED_VIEW,
    ERROR_FILE_NOT_FOUND_HANDLER,
    ERROR_THUMBNAIL_NOT_FOUND,
    ERROR_ORPHANED_FILE,
    ERROR_INTERNAL_SERVER,
    MSG_FILE_DELETED_SUCCESS,
    MSG_FILE_TOO_LARGE,
)

# Local modules
from ..modules.log.logger_factory import get_logger
from ..modules.app_context import app_context

logger = get_logger(__name__)

# Constants - Blueprint and URL routing
BLUEPRINT_NAME = "file_handler"
BLUEPRINT_PREFIX = "/files"

# Constants - Permission and module names
PERMISSION_MODULE = "FileManager"
PERMISSION_UPLOAD = "upload"
PERMISSION_DOWNLOAD = "download"
PERMISSION_DELETE = "delete"
PERMISSION_VIEW = "view"

# Constants - File handling
FILE_CATEGORY_DEFAULT = "general"
FILE_EXTENSIONS_IMAGE = ('jpg', 'jpeg', 'png', 'gif', 'webp')
PARAM_RENAME_PLACEHOLDER_USER = '{username}'
PARAM_RENAME_PLACEHOLDER_ALT = '{user}'
FORM_FIELD_FILE = 'file'
FORM_FIELD_CATEGORY = 'category'
FORM_FIELD_GROUP_ID = 'group_id'
FORM_FIELD_TAGS = 'tags'
FORM_FIELD_UPLOAD_PATH = 'upload_path'
FORM_FIELD_RENAME_TO = 'rename_to'

# Constants - Query parameters and request
QUERY_PARAM_ALL_VERSIONS = 'all_versions'
QUERY_PARAM_INLINE = 'inline'
QUERY_PARAM_GROUP_ID = 'group_id'
QUERY_PARAM_TAG = 'tag'
QUERY_PARAM_LIMIT = 'limit'
PARAM_VALUE_TRUE = 'true'

# Constants - Path and file handling
PATH_ASSET_DIRECTORY = 'website'
PATH_ASSET_SUBDIRECTORY = 'assets'
PATH_DEFAULT_UPLOAD = 'uploads'
PATH_SEPARATOR = '/'
FILENAME_SAFE_PATTERN = r'[^\w\-.]'
FILENAME_SAFE_REPLACEMENT = '_'

# Constants - User session
SESSION_USER_ANON = 'anonymous'

# Constants - Response keys
RESPONSE_SUCCESS = "success"
RESPONSE_FILE = "file"
RESPONSE_PATH = "path"
RESPONSE_FILENAME = "filename"
RESPONSE_URL = "url"
RESPONSE_MESSAGE = "message"
RESPONSE_ERROR = "error"
RESPONSE_FILES = "files"
RESPONSE_COUNT = "count"

bp = Blueprint(BLUEPRINT_NAME, __name__, url_prefix=BLUEPRINT_PREFIX)

# File manager instance will be injected by main.py
file_manager = None


def _require_permission(permission_module: str, permission_action: str = PERMISSION_UPLOAD):
    """Check if current user has permission.
    
    Args:
        permission_module: Module name (e.g., "FileManager")
        permission_action: Action name (e.g., "upload", "download", "delete")
        
    Returns:
        bool: True if permitted, False otherwise
    """
    if not app_context.auth_manager:
        # No auth system = allow access (for development/testing)
        logger.warning(f"Permission check for {permission_module}.{permission_action} - auth system not available, allowing access")
        return True
    
    current_user = session.get('user')
    if not current_user:
        logger.warning(f"Permission check for {permission_module}.{permission_action} - no user in session")
        return False
    
    has_perm = app_context.auth_manager.has_permission(current_user, permission_module, permission_action)
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
        return jsonify({RESPONSE_ERROR: ERROR_FILE_HANDLER_NOT_INIT}), 500
    
    # Check permission
    if not _require_permission(PERMISSION_MODULE, PERMISSION_UPLOAD):
        return jsonify({RESPONSE_ERROR: ERROR_PERMISSION_DENIED_UPLOAD}), 403
    
    # Get file from request
    if FORM_FIELD_FILE not in request.files:
        return jsonify({RESPONSE_ERROR: ERROR_NO_FILE_PROVIDED}), 400
    
    file = request.files[FORM_FIELD_FILE]
    
    # Get parameters
    category = request.form.get(FORM_FIELD_CATEGORY, FILE_CATEGORY_DEFAULT)
    group_id = request.form.get(FORM_FIELD_GROUP_ID, '')
    tags_str = request.form.get(FORM_FIELD_TAGS, '')
    
    # Parse tags (comma-separated)
    tag_names = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
    
    try:
        # Get current user
        current_user = session.get('user', USER_GUEST_NAME)
        
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
            RESPONSE_SUCCESS: True,
            RESPONSE_FILE: metadata
        }), 200
        
    except ValueError as e:
        # Validation error (file type, size, etc.)
        logger.warning(f"File upload validation failed: {e}")
        return jsonify({RESPONSE_ERROR: str(e)}), 400
        
    except IOError as e:
        # File system error
        logger.error(f"File upload I/O error: {e}")
        return jsonify({RESPONSE_ERROR: ERROR_FAILED_SAVE_FILE}), 500
        
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected file upload error: {e}", exc_info=True)
        return jsonify({RESPONSE_ERROR: ERROR_INTERNAL_SERVER}), 500


@bp.route("/simple-upload", methods=["POST"])
def simple_upload():
    """Simple filesystem upload - no FileManager, no permissions required.
    
    This endpoint is for simple file uploads that don't need versioning,
    metadata, or permission checks. Files are saved directly to filesystem.
    
    Expected POST data:
        - file: The file to upload (multipart/form-data)
        - upload_path: Relative path under website/assets/ (e.g., "images/users")
        - rename_to: Optional rename pattern (e.g., "{username}" uses session user)
    
    Returns:
        JSON response with file path or error
    """
    import os
    import re
    from PIL import Image
    
    # Get file from request
    if FORM_FIELD_FILE not in request.files:
        return jsonify({RESPONSE_ERROR: ERROR_NO_FILE_PROVIDED}), 400
    
    file = request.files[FORM_FIELD_FILE]
    if not file or not file.filename:
        return jsonify({RESPONSE_ERROR: ERROR_NO_FILE_SELECTED}), 400
    
    # Get parameters
    upload_path = request.form.get(FORM_FIELD_UPLOAD_PATH, PATH_DEFAULT_UPLOAD)
    rename_to = request.form.get(FORM_FIELD_RENAME_TO, '')
    
    # Security: validate upload_path (no directory traversal)
    # Only block ".." for directory traversal - allow forward and backslashes for subdirectories
    if '..' in upload_path:
        logger.warning(f"Simple upload rejected - directory traversal attempt: {upload_path}")
        return jsonify({RESPONSE_ERROR: ERROR_INVALID_UPLOAD_PATH}), 400
    
    # Normalize path separators
    upload_path = upload_path.replace('\\', PATH_SEPARATOR)
    
    # Get file extension from original filename
    original_filename = file.filename
    file_ext = ''
    if '.' in original_filename:
        file_ext = original_filename.rsplit('.', 1)[1].lower()
    
    # Determine final filename
    if rename_to:
        # Replace patterns in rename_to
        current_user = session.get('user', SESSION_USER_ANON)
        final_name = rename_to.replace(PARAM_RENAME_PLACEHOLDER_USER, current_user)
        final_name = final_name.replace(PARAM_RENAME_PLACEHOLDER_ALT, current_user)
        # Add extension if not present
        if file_ext and not final_name.endswith(f'.{file_ext}'):
            final_name = f"{final_name}.{file_ext}"
        # Sanitize filename
        final_name = re.sub(FILENAME_SAFE_PATTERN, FILENAME_SAFE_REPLACEMENT, final_name)
    else:
        # Use original filename (sanitized)
        final_name = re.sub(FILENAME_SAFE_PATTERN, FILENAME_SAFE_REPLACEMENT, original_filename)
    
    # Build destination path
    app_path = app_context.app_path or os.getcwd()
    dest_dir = os.path.join(app_path, PATH_ASSET_DIRECTORY, PATH_ASSET_SUBDIRECTORY, upload_path)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, final_name)
    
    try:
        # Save file
        file.save(dest_path)
        
        # For images, optionally resize (max 1024x1024)
        if file_ext in FILE_EXTENSIONS_IMAGE:
            try:
                with Image.open(dest_path) as img:
                    # Only resize if larger than 1024x1024
                    if img.width > IMAGE_MAX_SIZE[0] or img.height > IMAGE_MAX_SIZE[1]:
                        img.thumbnail(IMAGE_MAX_SIZE, Image.Resampling.LANCZOS)
                        # Convert to RGB for JPEG (removes alpha channel)
                        if file_ext in ('jpg', 'jpeg') and img.mode in ('RGBA', 'P'):
                            img = img.convert('RGB')
                        img.save(dest_path)
                        logger.info(f"Resized image to fit {IMAGE_MAX_SIZE[0]}x{IMAGE_MAX_SIZE[1]}: {final_name}")
            except Exception as e:
                logger.warning(f"Could not process image {final_name}: {e}")
        
        # Build relative path and URL
        relative_path = f"{upload_path}/{final_name}"
        # URL for serving the file
        if PATH_SEPARATOR in upload_path:
            url = url_for('common.assets', asset_type=upload_path.split(PATH_SEPARATOR)[0], filename=f"{PATH_SEPARATOR.join(upload_path.split(PATH_SEPARATOR)[1:])}/{final_name}")
        else:
            url = url_for('common.assets', asset_type=upload_path, filename=final_name)
        
        current_user = session.get('user', USER_GUEST_NAME)
        logger.info(f"Simple file upload by {current_user}: {relative_path}")
        
        return jsonify({
            RESPONSE_SUCCESS: True,
            RESPONSE_PATH: relative_path,
            RESPONSE_FILENAME: final_name,
            RESPONSE_URL: url
        }), 200
        
    except Exception as e:
        logger.error(f"Simple upload error: {e}", exc_info=True)
        # Clean up on error
        if os.path.exists(dest_path):
            try:
                os.remove(dest_path)
            except:
                pass
        return jsonify({RESPONSE_ERROR: f"{ERROR_FAILED_SAVE_FILE}: {str(e)}"}), 500


@bp.route("/download/<path:filepath>", methods=["GET"])
def download(filepath):
    """Serve a file for download from HashFS storage.
    
    Args:
        filepath: Storage path from database
    
    Returns:
        File download response
    """
    if not file_manager:
        abort(500, ERROR_FILE_HANDLER_NOT_INIT)
    
    # Check permission
    if not _require_permission(PERMISSION_MODULE, PERMISSION_DOWNLOAD):
        abort(403, ERROR_PERMISSION_DENIED_DOWNLOAD)
    
    try:
        # Check if this is a thumbnail request
        is_thumbnail = '.thumbs' in filepath or request.args.get(QUERY_PARAM_INLINE) == PARAM_VALUE_TRUE
        
        if '.thumbs' in filepath:
            # Thumbnail files are stored outside HashFS in .thumbs directory
            thumb_path = file_manager.hashfs_path.parent / filepath
            if not thumb_path.exists():
                logger.warning(f"Thumbnail not found: {thumb_path}")
                abort(404, ERROR_THUMBNAIL_NOT_FOUND)
            file_path = thumb_path
        else:
            # Regular files from HashFS
            file_path = file_manager.storage.get(filepath)
        
        # Get MIME type
        mime_type = file_manager.get_mime_type(filepath)
        
        logger.info(f"File download by {session.get('user', USER_GUEST_NAME)}: {filepath}")
        
        # Send file - read into BytesIO to avoid Windows long path issues
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
        abort(404, ERROR_FILE_NOT_FOUND_HANDLER)
        
    except Exception as e:
        logger.error(f"Unexpected download error for {filepath}: {e}", exc_info=True)
        abort(500, ERROR_INTERNAL_SERVER)


@bp.route("/delete/<int:file_id>", methods=["DELETE", "POST"])
def delete(file_id):
    """Delete a file by database ID.
    
    Args:
        file_id: Database ID of file version
    
    Query params:
        all_versions: If 'true', delete all versions of the file (same group_id + filename)
    
    Returns:
        JSON response with success/error status
    """
    if not file_manager:
        return jsonify({RESPONSE_ERROR: ERROR_FILE_HANDLER_NOT_INIT}), 500
    
    # Check permission (higher permission level for delete)
    if not _require_permission(PERMISSION_MODULE, PERMISSION_DELETE):
        return jsonify({RESPONSE_ERROR: ERROR_PERMISSION_DENIED_DELETE}), 403
    
    # Check for delete_all_versions parameter
    delete_all_versions = request.args.get(QUERY_PARAM_ALL_VERSIONS, 'false').lower() == PARAM_VALUE_TRUE
    
    try:
        # Delete file (reference-counted in HashFS)
        success = file_manager.delete_file(file_id, delete_all_versions=delete_all_versions)
        
        if success:
            logger.info(f"File deleted by {session.get('user', USER_GUEST_NAME)}: ID {file_id} (all_versions={delete_all_versions})")
            return jsonify({
                RESPONSE_SUCCESS: True,
                RESPONSE_MESSAGE: MSG_FILE_DELETED_SUCCESS
            }), 200
        else:
            return jsonify({RESPONSE_ERROR: ERROR_FAILED_SAVE_FILE}), 500
            
    except Exception as e:
        logger.error(f"Unexpected delete error for file ID {file_id}: {e}", exc_info=True)
        return jsonify({RESPONSE_ERROR: ERROR_INTERNAL_SERVER}), 500


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
        return jsonify({RESPONSE_ERROR: ERROR_FILE_HANDLER_NOT_INIT}), 500
    
    # Check permission (list is covered by view)
    if not _require_permission(PERMISSION_MODULE, PERMISSION_VIEW):
        return jsonify({RESPONSE_ERROR: ERROR_PERMISSION_DENIED_VIEW}), 403
    
    try:
        # Get query parameters
        group_id = request.args.get(QUERY_PARAM_GROUP_ID)
        tag = request.args.get(QUERY_PARAM_TAG)
        limit = request.args.get(QUERY_PARAM_LIMIT, type=int)
        
        files = file_manager.list_files_from_db(group_id=group_id, tag=tag, limit=limit)
        
        return jsonify({
            RESPONSE_SUCCESS: True,
            RESPONSE_FILES: files,
            RESPONSE_COUNT: len(files)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to list files: {e}", exc_info=True)
        return jsonify({RESPONSE_ERROR: ERROR_INTERNAL_SERVER}), 500


@bp.route("/download/by_id/<int:file_id>", methods=["GET"])
def download_by_id(file_id):
    """Download file by database ID from HashFS.
    
    Args:
        file_id: Database ID of file version
    
    Returns:
        File download response
    """
    if not file_manager:
        abort(500, ERROR_FILE_HANDLER_NOT_INIT)
    
    # Check permission
    if not _require_permission(PERMISSION_MODULE, PERMISSION_DOWNLOAD):
        abort(403, ERROR_PERMISSION_DENIED_DOWNLOAD)
    
    # Get file from database
    file_version = file_manager.get_file_by_id(file_id)
    
    if not file_version:
        abort(404, ERROR_FILE_NOT_FOUND_HANDLER)
    
    try:
        # Get file from HashFS
        file_path = file_manager.storage.get(file_version.storage_path)
        
        # Check if file exists
        if not file_path.exists():
            logger.error(f"File not found in HashFS: {file_version.storage_path} (orphaned DB record)")
            abort(404, f"File '{file_version.filename}' {ERROR_ORPHANED_FILE}")
        
        logger.info(f"File download by {session.get('user', USER_GUEST_NAME)}: {file_version.filename} (ID: {file_id})")
        
        # Send file - read into BytesIO to avoid Windows long path issues with send_file
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
        abort(500, ERROR_INTERNAL_SERVER)


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
        abort(500, ERROR_FILE_HANDLER_NOT_INIT)
    
    # Check permission
    if not _require_permission(PERMISSION_MODULE, PERMISSION_VIEW):
        abort(403, ERROR_PERMISSION_DENIED_VIEW)
    
    try:
        versions = file_manager.get_file_versions(group_id, filename)
        return jsonify(versions), 200
    except Exception as e:
        logger.error(f"Error getting file versions: {e}")
        abort(500, ERROR_INTERNAL_SERVER)


@bp.route("/restore", methods=["POST"])
def handle_file_too_large(e):
    """Handle file size exceeded error."""
    return jsonify({RESPONSE_ERROR: MSG_FILE_TOO_LARGE}), 413