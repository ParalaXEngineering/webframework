"""
File Handler Pages - Flask blueprint for file upload/download/delete routes.

This module provides HTTP endpoints for secure file management operations.
"""

from flask import Blueprint, request, send_file, jsonify, session, abort, url_for, render_template
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
    
    return auth_manager.has_permission(current_user, permission_module, permission_action)


@bp.route("/upload", methods=["POST"])
def upload():
    """Handle file upload with versioning support.
    
    Expected POST data:
        - file: The file to upload (multipart/form-data)
        - category: Top-level category (deprecated, for compatibility)
        - subcategory: Optional subcategory (deprecated, for compatibility)
        - group_id: Group ID for versioning (optional, empty string shown in admin)
        - tags: Comma-separated tags (optional)
    
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
    
    # Get parameters
    category = request.form.get('category', 'general')
    subcategory = request.form.get('subcategory', '')
    group_id = request.form.get('group_id', '')
    tags_str = request.form.get('tags', '')
    
    # Parse tags (comma-separated)
    tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else None
    
    try:
        # Upload file with new parameters
        metadata = file_manager.upload_file(
            file, 
            category=category, 
            subcategory=subcategory,
            group_id=group_id,
            tags=tags
        )
        
        logger.info(f"File uploaded by {session.get('user', 'GUEST')}: {metadata['name']} (group: {metadata['group_id']}, version: {metadata['version']})")
        
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
    """Serve a file for download (supports both legacy paths and database storage).
    
    Args:
        filepath: Relative path to file or storage path from database
    
    Query params:
        version: Optional version ID to download specific version
    
    Returns:
        File download response
    """
    if not file_manager:
        abort(500, "File manager not initialized")
    
    # Check permission
    if not _require_permission("FileManager", "download"):
        abort(403, "Permission denied")
    
    try:
        # Check if this is a hashfs path or traditional filesystem path
        if file_manager.use_hashfs and file_manager.storage:
            try:
                # Try to get file from hashfs
                file_path = file_manager.storage.get(filepath)
            except IOError:
                # Fall back to traditional filesystem
                file_path = file_manager.get_file_path(filepath)
        else:
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
    """List files (supports both filesystem and database queries).
    
    Query params:
        category: Category to list (optional, deprecated)
        subcategory: Subcategory to list (optional, deprecated)
        group_id: Filter by group_id (optional)
        tag: Filter by tag (optional)
        limit: Maximum number of results (optional)
        use_db: If 'true', use database query (default: true)
    
    Returns:
        JSON response with file list
    """
    if not file_manager:
        return jsonify({"error": "File manager not initialized"}), 500
    
    # Check permission
    if not _require_permission("FileManager", "list"):
        return jsonify({"error": "Permission denied"}), 403
    
    use_db = request.args.get('use_db', 'true').lower() == 'true'
    
    try:
        if use_db:
            # Use database query (Phase 3)
            group_id = request.args.get('group_id')
            tag = request.args.get('tag')
            limit = request.args.get('limit', type=int)
            
            files = file_manager.list_files_from_db(group_id=group_id, tag=tag, limit=limit)
        else:
            # Legacy filesystem query
            category = request.args.get('category', '')
            subcategory = request.args.get('subcategory', '')
            files = file_manager.list_files(category, subcategory)
        
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
    """Download file by database ID.
    
    Args:
        file_id: Database ID of file version
    
    Returns:
        File download response
    """
    if not file_manager:
        abort(500, "File manager not initialized")
    
    # Check permission
    if not _require_permission("FileManager", "download"):
        abort(403, "Permission denied")
    
    # Get file from database
    file_version = file_manager.get_file_by_id(file_id)
    
    if not file_version:
        abort(404, "File not found")
    
    logger.info(f"Download request for file_id={file_id}: {file_version.filename}, storage_path={file_version.storage_path}")
    
    try:
        # Try hashfs storage first, fallback to traditional filesystem
        file_path = None
        
        if file_manager.use_hashfs and file_manager.storage:
            try:
                file_path = file_manager.storage.get(file_version.storage_path)
                logger.info(f"HashFS returned path: {file_path}")
            except (OSError, FileNotFoundError) as e:
                logger.warning(f"File not in hashfs ({e}), trying traditional path: {file_version.storage_path}")
        
        # Fallback to traditional filesystem if hashfs failed or not enabled
        if not file_path or not file_path.exists():
            # For traditional filesystem, storage_path is relative to base_path
            # e.g., storage_path="documents/uploads/file.xlsx" -> resources/uploads/documents/uploads/file.xlsx
            fallback_path = file_manager.base_path / file_version.storage_path
            logger.info(f"Trying traditional path: {fallback_path}")
            file_path = fallback_path
        
        # Check if file exists
        if not file_path.exists():
            logger.error(f"File not found on disk: {file_path} (storage_path in DB: {file_version.storage_path})")
            logger.error(f"This is likely an orphaned database record. The file may have been deleted or never uploaded properly.")
            abort(404, f"File '{file_version.filename}' not found on disk (orphaned database record)")
        
        logger.info(f"File download by {session.get('user', 'GUEST')}: {file_version.filename} (ID: {file_id})")
        
        # Send file
        return send_file(
            file_path,
            mimetype=file_version.mime_type,
            as_attachment=True,
            download_name=file_version.filename
        )
        
    except Exception as e:
        logger.error(f"Download by ID error for {file_id}: {e}", exc_info=True)
        raise


@bp.route("/versions/<group_id>/<filename>", methods=["GET"])
def get_versions(group_id, filename):
    """Display version history page for a file.
    
    Args:
        group_id: Group identifier
        filename: Filename
    
    Returns:
        HTML page with version history table
    """
    if not file_manager:
        return "File manager not initialized", 500
    
    # Check permission
    if not _require_permission("FileManager", "view"):
        return render_template("error.j2", error="Permission denied"), 403
    
    try:
        # Import displayer modules
        try:
            from ..modules import displayer
            from ..modules.displayer import BSstyle
            from ..modules.utilities import get_home_endpoint
        except ImportError:
            from modules import displayer
            from modules.displayer import BSstyle
            from modules.utilities import get_home_endpoint
        
        versions = file_manager.get_file_versions(group_id, filename)
        
        # Build version history page
        disp = displayer.Displayer()
        disp.add_generic(f"Version History - {filename}")
        disp.set_title(f"Version History: {filename}")
        disp.add_breadcrumb("Home", get_home_endpoint(), [])
        disp.add_breadcrumb("File Manager", "file_manager_admin.index", [])
        disp.add_breadcrumb("Version History", "file_handler.get_versions", [group_id, filename])
        
        # Header with file info
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        header_html = f"""
        <div class="card mb-3">
            <div class="card-body">
                <h4><i class="bi bi-clock-history"></i> Version History</h4>
                <p class="mb-1"><strong>Filename:</strong> {filename}</p>
                <p class="mb-0"><strong>Group ID:</strong> {group_id}</p>
                <p class="mb-0"><strong>Total Versions:</strong> {len(versions)}</p>
            </div>
        </div>
        """
        disp.add_display_item(displayer.DisplayerItemAlert(header_html, BSstyle.NONE), column=0)
        
        # Version table
        if versions:
            disp.add_master_layout(displayer.DisplayerLayout(
                displayer.Layouts.TABLE,
                ["Version", "Status", "Size", "Checksum", "Uploaded", "Uploaded By", "Actions"],
                subtitle="All Versions"
            ))
            
            # Sort versions by upload date (newest first)
            sorted_versions = sorted(versions, key=lambda v: v['uploaded_at'], reverse=True)
            
            for idx, version in enumerate(sorted_versions):
                # Version number (count from oldest)
                version_num = len(versions) - sorted_versions.index(version)
                version_badge = f"<span class='badge bg-primary'>v{version_num}</span>"
                disp.add_display_item(displayer.DisplayerItemAlert(version_badge, BSstyle.NONE), 
                                    column=0, line=idx)
                
                # Status (current or archived)
                if version.get('is_current'):
                    status_html = "<span class='badge bg-success'><i class='bi bi-check-circle'></i> Current</span>"
                else:
                    status_html = "<span class='badge bg-secondary'>Archived</span>"
                disp.add_display_item(displayer.DisplayerItemAlert(status_html, BSstyle.NONE), 
                                    column=1, line=idx)
                
                # Size
                size_bytes = version.get('size', 0)
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes / 1024:.1f} KB"
                else:
                    size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
                disp.add_display_item(displayer.DisplayerItemText(size_str), 
                                    column=2, line=idx)
                
                # Checksum (truncated)
                checksum = version.get('checksum', 'N/A')
                checksum_short = checksum[:8] + "..." if len(checksum) > 8 else checksum
                disp.add_display_item(displayer.DisplayerItemText(checksum_short), 
                                    column=3, line=idx)
                
                # Uploaded date
                upload_date = version.get('uploaded_at', '')[:16].replace('T', ' ')
                disp.add_display_item(displayer.DisplayerItemText(upload_date), 
                                    column=4, line=idx)
                
                # Uploaded by
                uploaded_by = version.get('uploaded_by', 'Unknown')
                disp.add_display_item(displayer.DisplayerItemText(uploaded_by), 
                                    column=5, line=idx)
                
                # Actions
                file_id = version.get('id')
                download_url = url_for('file_handler.download_by_id', file_id=file_id)
                
                actions_html = f"""
                <a href="{download_url}" class="btn btn-sm btn-primary" title="Download this version">
                    <i class="bi bi-download"></i>
                </a>
                """
                
                # Add "Make Current" button for non-current versions
                if not version.get('is_current'):
                    actions_html += f"""
                    <button class="btn btn-sm btn-success" 
                            onclick="makeCurrentVersion({file_id}, {version_num})" 
                            title="Restore this version as current">
                        <i class="bi bi-arrow-clockwise"></i> Make Current
                    </button>
                    """
                
                actions_html += f'<div id="status-{idx}" class="mt-1"></div>'
                
                disp.add_display_item(displayer.DisplayerItemAlert(actions_html, BSstyle.NONE), 
                                    column=6, line=idx)
            
            # Add restore script
            restore_script = """
            <script>
            function makeCurrentVersion(versionId, versionNum) {
                if (!confirm('Restore version ' + versionNum + ' as the current version?\\n\\nThis will create a new version based on the selected one.')) {
                    return;
                }
                
                fetch('/files/restore', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        target_version_id: versionId
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Version restored successfully!\\n\\nA new version has been created.');
                        location.reload();
                    } else {
                        alert('Error: ' + data.error);
                    }
                })
                .catch(error => {
                    alert('Failed to restore version: ' + error);
                });
            }
            </script>
            """
            disp.add_display_item(displayer.DisplayerItemText(restore_script), column=0)
        
        # Back button
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        disp.add_display_item(displayer.DisplayerItemButton(
            "back_btn", "Back to File Manager",
            icon="arrow-left",
            link=url_for('file_manager_admin.index'),
            color=BSstyle.SECONDARY
        ), column=0)
        
        return render_template("base_content.j2", content=disp.display())
        
    except Exception as e:
        logger.error(f"Failed to display version history: {e}", exc_info=True)
        return render_template("error.j2", error=str(e)), 500


@bp.route("/restore", methods=["POST"])
def restore_version():
    """Restore an old version of a file.
    
    Expected POST data:
        - target_version_id: Version to restore from (required)
        - file_id: Current file version ID (optional, will use target's group to find current)
    
    Returns:
        JSON response with new file metadata
    """
    if not file_manager:
        return jsonify({"error": "File manager not initialized"}), 500
    
    # Check permission (restore requires delete permission)
    if not _require_permission("FileManager", "delete"):
        return jsonify({"error": "Permission denied"}), 403
    
    try:
        target_version_id = request.json.get('target_version_id')
        
        if not target_version_id:
            return jsonify({"error": "Missing target_version_id"}), 400
        
        # Get target version to find group_id and filename
        from ..modules.file_manager_models import FileVersion
        from sqlalchemy.orm import Session
        
        session_db = file_manager.db_session
        target_version = session_db.query(FileVersion).filter_by(id=target_version_id).first()
        
        if not target_version:
            return jsonify({"error": "Target version not found"}), 404
        
        # Find current version in same group
        current_version = session_db.query(FileVersion).filter_by(
            group_id=target_version.group_id,
            filename=target_version.filename,
            is_current=True
        ).first()
        
        if not current_version:
            return jsonify({"error": "Current version not found"}), 404
        
        # Restore version
        restored = file_manager.restore_version(current_version.id, target_version_id)
        
        logger.info(f"Version restored by {session.get('user', 'GUEST')}: {restored.filename}")
        
        return jsonify({
            "success": True,
            "file": {
                "id": restored.id,
                "filename": restored.filename,
                "group_id": restored.group_id,
                "uploaded_at": restored.uploaded_at.isoformat() + "Z"
            }
        }), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
        
    except Exception as e:
        logger.error(f"Failed to restore version: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/update_group_id", methods=["POST"])
def update_group_id():
    """Update group_id of a file (admin function).
    
    Expected POST data:
        - file_id: File version ID
        - new_group_id: New group ID
    
    Returns:
        JSON response with success status
    """
    if not file_manager:
        return jsonify({"error": "File manager not initialized"}), 500
    
    # Check permission (admin only)
    if not _require_permission("FileManager", "admin"):
        return jsonify({"error": "Permission denied"}), 403
    
    try:
        file_id = request.json.get('file_id')
        new_group_id = request.json.get('new_group_id', '')
        
        if file_id is None:
            return jsonify({"error": "Missing file_id"}), 400
        
        # Update group_id
        success = file_manager.update_group_id(file_id, new_group_id)
        
        if success:
            logger.info(f"Group ID updated by {session.get('user', 'GUEST')}: file {file_id} -> {new_group_id}")
            return jsonify({"success": True}), 200
        else:
            return jsonify({"error": "File not found"}), 404
        
    except Exception as e:
        logger.error(f"Failed to update group_id: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@bp.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    """Handle file size exceeded error."""
    return jsonify({"error": "File too large"}), 413

