"""
File Manager Admin Page - Flask blueprint for file browsing and management UI.

This module provides a web interface for browsing, searching, and managing uploaded files.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any

logger = logging.getLogger(__name__)

bp = Blueprint("file_manager_admin", __name__, url_prefix="/file_manager")

# File manager instance will be injected by main.py
file_manager: Optional[Any] = None


def _get_auth_manager():
    """Get auth_manager dynamically to avoid initialization issues."""
    try:
        from ..modules.auth.auth_manager import auth_manager
        return auth_manager
    except ImportError:
        return None


def _get_displayer_modules():
    """Get displayer modules dynamically."""
    try:
        from ..modules import displayer
        from ..modules.displayer import BSstyle
        from ..modules.utilities import get_home_endpoint
    except ImportError:
        from modules import displayer
        from modules.displayer import BSstyle
        from modules.utilities import get_home_endpoint
    return displayer, BSstyle, get_home_endpoint


def require_file_manager_permission(f):
    """Decorator to require FileManager module permission."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_manager = _get_auth_manager()
        displayer, BSstyle, get_home_endpoint = _get_displayer_modules()
        
        if auth_manager:
            current_user = session.get('user')
            if not current_user:
                flash("Please log in to access File Manager.", "warning")
                return redirect(url_for('common.login'))
            
            # Check permission
            if not auth_manager.has_permission(current_user, "FileManager", "view"):
                disp = displayer.Displayer()
                disp.add_generic("Access Denied")
                disp.set_title("Access Denied")
                disp.add_breadcrumb("Home", get_home_endpoint(), [])
                
                disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
                disp.add_display_item(displayer.DisplayerItemAlert(
                    "<h4><i class='bi bi-shield-lock'></i> File Manager Access Required</h4>"
                    "<p>You do not have permission to access the File Manager.</p>"
                    f"<p><strong>Current User:</strong> {current_user}</p>"
                    "<hr>"
                    "<p>If you need access, please contact your system administrator.</p>",
                    BSstyle.WARNING
                ), column=0)
                
                return render_template("base_content.j2", content=disp.display())
        
        return f(*args, **kwargs)
    return decorated_function


@bp.route("/", methods=["GET"])
@require_file_manager_permission
def index():
    """File manager main page - browse files, view statistics."""
    if not file_manager:
        return "File manager not initialized", 500
    
    displayer, BSstyle, get_home_endpoint = _get_displayer_modules()
    
    disp = displayer.Displayer()
    disp.add_generic("File Manager")
    disp.set_title("File Manager - Browse Files")
    disp.add_breadcrumb("Home", get_home_endpoint(), [])
    disp.add_breadcrumb("File Manager", "file_manager_admin.index", [])
    
    try:
        # Get file list from database (Phase 3 - includes versions, tags, group_id)
        files = file_manager.list_files_from_db()
        
        # Calculate statistics
        total_files = len(files)
        total_size = sum(f['size'] for f in files)
        total_size_mb = total_size / (1024 * 1024)
        
        # Get unique group IDs and tags
        unique_groups = len(set(f.get('group_id', '') for f in files if f.get('group_id')))
        all_tags = set()
        for f in files:
            all_tags.update(f.get('tags', []))
        
        # Statistics section
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.HORIZONTAL, [3, 3, 3, 3]))
        
        disp.add_display_item(displayer.DisplayerItemAlert(
            f"<h3 class='text-center'>{total_files}</h3>"
            f"<p class='text-center mb-0'>Total Files</p>",
            BSstyle.INFO
        ), column=0)
        
        disp.add_display_item(displayer.DisplayerItemAlert(
            f"<h3 class='text-center'>{total_size_mb:.2f} MB</h3>"
            f"<p class='text-center mb-0'>Total Size</p>",
            BSstyle.SUCCESS
        ), column=1)
        
        disp.add_display_item(displayer.DisplayerItemAlert(
            f"<h3 class='text-center'>{unique_groups}</h3>"
            f"<p class='text-center mb-0'>Version Groups</p>",
            BSstyle.PRIMARY
        ), column=2)
        
        disp.add_display_item(displayer.DisplayerItemAlert(
            f"<h3 class='text-center'>{len(all_tags)}</h3>"
            f"<p class='text-center mb-0'>Unique Tags</p>",
            BSstyle.WARNING
        ), column=3)
        
        # File list table with DataTables
        if files:
            # Add table layout with Phase 3 columns including integrity status
            # Multi-delete button (uses form submission)
            disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
            multi_delete_button_html = """
            <button type="submit" formaction="/file_manager/delete-multiple" class="btn btn-danger">
                <i class="bi bi-trash"></i> Delete Selected
            </button>
            """
            disp.add_display_item(
                displayer.DisplayerItemAlert(multi_delete_button_html, displayer.BSstyle.NONE),
                column=0
            )
            
            table_layout_id = disp.add_master_layout(displayer.DisplayerLayout(
                displayer.Layouts.TABLE,
                ["Select", "Preview", "Filename", "Group ID", "Tags", "Version", "Size", "Uploaded", "Integrity", "Actions"],
                subtitle="Files",
                datatable_config={
                    "table_id": "file_list_table",
                    "mode": displayer.TableMode.INTERACTIVE,
                    "page_length": 25,
                    "searchable": True,
                    "ordering": [[2, "asc"]],  # Sort by filename by default
                    "columnDefs": [
                        {"orderable": False, "targets": [0, 1, 9]},  # Disable sorting for checkbox, preview, and actions
                        {"className": "text-center", "targets": [0, 1, 5, 7, 8, 9]}  # Center align some columns
                    ]
                }
            ))
            
            # Populate table rows
            for idx, file_meta in enumerate(files):
                # Checkbox column (using name="file_ids[]" for array submission)
                file_id = file_meta.get('id', 0)
                checkbox_html = f'<input type="checkbox" name="file_ids[]" value="{file_id}">'
                disp.add_display_item(displayer.DisplayerItemAlert(checkbox_html, displayer.BSstyle.NONE), 
                                    column=0, line=idx, layout_id=table_layout_id)
                
                # Preview column (thumbnail or icon)
                preview_html = _generate_preview_html(file_meta)
                disp.add_display_item(displayer.DisplayerItemAlert(preview_html, displayer.BSstyle.NONE), 
                                    column=1, line=idx, layout_id=table_layout_id)
                
                # Filename
                disp.add_display_item(displayer.DisplayerItemText(file_meta['name']), 
                                    column=2, line=idx, layout_id=table_layout_id)
                
                # Group ID (read-only display)
                group_id_val = file_meta.get('group_id', '') or '(none)'
                disp.add_display_item(displayer.DisplayerItemText(group_id_val), 
                                    column=3, line=idx, layout_id=table_layout_id)
                
                # Tags - formatted with commas and line breaks for better datatable display
                # Handle both new format (list) and old format (tags with # separator)
                tags_list = file_meta.get('tags', [])
                if tags_list:
                    # Split any tags that contain # (old format) and flatten the list
                    expanded_tags = []
                    for tag in tags_list:
                        if '#' in tag:
                            expanded_tags.extend(tag.split('#'))
                        else:
                            expanded_tags.append(tag)
                    tags_display = ',<br>'.join(expanded_tags)
                else:
                    tags_display = '(none)'
                disp.add_display_item(displayer.DisplayerItemAlert(tags_display, displayer.BSstyle.NONE), 
                                    column=4, line=idx, layout_id=table_layout_id)
                
                # Version info
                try:
                    # Get versions (group_id can be None/empty for files without a group)
                    versions = file_manager.get_file_versions(file_meta.get('group_id'), file_meta['name'])
                    if versions:
                        current_ver = next((i+1 for i, v in enumerate(reversed(versions)) if v['is_current']), len(versions))
                        version_display = f"v{current_ver}/{len(versions)}"
                    else:
                        version_display = "v1/1"
                except Exception:
                    version_display = "v1/1"
                disp.add_display_item(displayer.DisplayerItemText(version_display), 
                                    column=5, line=idx, layout_id=table_layout_id)
                
                # Size (human readable)
                size_str = _format_file_size(file_meta['size'])
                disp.add_display_item(displayer.DisplayerItemText(size_str), 
                                    column=6, line=idx, layout_id=table_layout_id)
                
                # Upload date
                upload_date = _format_date(file_meta['uploaded_at'])
                disp.add_display_item(displayer.DisplayerItemText(upload_date), 
                                    column=7, line=idx, layout_id=table_layout_id)
                
                # Integrity status
                file_id = file_meta.get('id', 0)
                is_valid, status = file_manager.verify_file_integrity(file_id)
                
                if is_valid:
                    integrity_html = '<span class="badge bg-success" title="File intact"><i class="bi bi-check-circle"></i> OK</span>'
                elif status == "Missing":
                    integrity_html = '<span class="badge bg-warning" title="Physical file not found"><i class="bi bi-exclamation-triangle"></i> Missing</span>'
                elif status == "Checksum mismatch":
                    integrity_html = '<span class="badge bg-danger" title="File corrupted"><i class="bi bi-x-circle"></i> Corrupted</span>'
                elif status == "Not found":
                    integrity_html = '<span class="badge bg-secondary" title="Database record missing"><i class="bi bi-question-circle"></i> Not Found</span>'
                else:
                    integrity_html = f'<span class="badge bg-danger" title="{status}"><i class="bi bi-bug"></i> Error</span>'
                
                disp.add_display_item(displayer.DisplayerItemAlert(integrity_html, displayer.BSstyle.NONE), 
                                    column=8, line=idx, layout_id=table_layout_id)
                
                # Actions (download, edit, history, delete buttons)
                actions = []
                
                # Download
                actions.append({
                    "type": "download",
                    "url": url_for('file_handler.download_by_id', file_id=file_meta.get('id', 0)),
                    "icon": "bi bi-download",
                    "style": "primary",
                    "tooltip": "Download"
                })
                
                # Edit
                actions.append({
                    "type": "custom",
                    "url": url_for('file_manager_admin.edit_file', file_id=file_meta.get('id', 0)),
                    "icon": "bi bi-pencil",
                    "style": "warning",
                    "tooltip": "Edit Metadata"
                })
                
                # History (show for all files that might have versions)
                # Extract version info from the version_display we calculated earlier
                try:
                    versions = file_manager.get_file_versions(file_meta.get('group_id'), file_meta['name'])
                    if versions and len(versions) > 0:
                        # Show history button for files with versions
                        # Use '(none)' as URL placeholder for files without a group
                        group_param = file_meta.get('group_id') or '(none)'
                        actions.append({
                            "type": "custom",
                            "url": url_for('file_handler.get_versions', group_id=group_param, filename=file_meta['name']),
                            "icon": "bi bi-clock-history",
                            "style": "info",
                            "tooltip": "View History"
                        })
                except Exception:
                    pass  # Skip history button if we can't get versions
                
                # Delete
                actions.append({
                    "type": "custom",
                    "url": url_for('file_manager_admin.confirm_delete', file_id=file_meta.get('id', 0)),
                    "icon": "bi bi-trash",
                    "style": "danger",
                    "tooltip": "Delete"
                })
                
                disp.add_display_item(
                    displayer.DisplayerItemActionButtons(
                        id=f"file_actions_{idx}",
                        actions=actions,
                        size="sm"
                    ),
                    column=9, line=idx, layout_id=table_layout_id
                )
        else:
            disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
            disp.add_display_item(displayer.DisplayerItemAlert(
                "<p class='text-center mb-0'>No files found. Upload files to get started!</p>",
                BSstyle.INFO
            ), column=0)
        
        # Note: Multi-delete form wraps the table automatically via form_action parameter
        # Checkboxes use name="file_ids[]" for array submission
        
        return render_template("base_content.j2", content=disp.display())
        
    except Exception as e:
        logger.error(f"File manager index error: {e}", exc_info=True)
        
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        disp.add_display_item(displayer.DisplayerItemAlert(
            f"<h4>Error Loading Files</h4><p>{str(e)}</p>",
            BSstyle.ERROR
        ), column=0)
        
        return render_template("base_content.j2", content=disp.display())


def _generate_preview_html(file_meta: dict, size: str = "60px") -> str:
    """Generate preview HTML for a file (thumbnail or icon).
    
    Args:
        file_meta: File metadata dictionary
        size: Preview size (default "60px")
        
    Returns:
        HTML string for preview
    """
    # Check if thumbnail exists
    if 'thumb_150x150' in file_meta:
        thumb_path = file_meta['thumb_150x150']
        try:
            thumb_url = url_for('file_handler.download', filepath=thumb_path, inline='true')
            return f'<img src="{thumb_url}" alt="Preview" class="img-thumbnail" style="max-width: {size}; max-height: {size};">'
        except Exception:
            # Fall back to icon if url_for fails
            pass
    
    # No thumbnail - show file type icon
    ext = Path(file_meta['name']).suffix.lower()
    icon_class = _get_file_icon(ext)
    return f'<i class="bi {icon_class}" style="font-size: 2rem;"></i>'


def _get_file_icon(extension: str) -> str:
    """Get Bootstrap icon class for file extension.
    
    Args:
        extension: File extension (e.g., ".pdf")
        
    Returns:
        Bootstrap icon class name
    """
    icon_map = {
        '.pdf': 'bi-file-earmark-pdf-fill text-danger',
        '.doc': 'bi-file-earmark-word-fill text-primary',
        '.docx': 'bi-file-earmark-word-fill text-primary',
        '.xls': 'bi-file-earmark-excel-fill text-success',
        '.xlsx': 'bi-file-earmark-excel-fill text-success',
        '.ppt': 'bi-file-earmark-ppt-fill text-warning',
        '.pptx': 'bi-file-earmark-ppt-fill text-warning',
        '.zip': 'bi-file-earmark-zip-fill text-secondary',
        '.7z': 'bi-file-earmark-zip-fill text-secondary',
        '.rar': 'bi-file-earmark-zip-fill text-secondary',
        '.txt': 'bi-file-earmark-text',
        '.csv': 'bi-file-earmark-spreadsheet',
        '.jpg': 'bi-file-earmark-image text-info',
        '.jpeg': 'bi-file-earmark-image text-info',
        '.png': 'bi-file-earmark-image text-info',
        '.gif': 'bi-file-earmark-image text-info',
        '.bmp': 'bi-file-earmark-image text-info',
        '.webp': 'bi-file-earmark-image text-info',
    }
    
    return icon_map.get(extension, 'bi-file-earmark')


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def _format_date(iso_date_str: str) -> str:
    """Format ISO date string to readable format.
    
    Args:
        iso_date_str: ISO 8601 date string
        
    Returns:
        Formatted date string
    """
    try:
        dt = datetime.fromisoformat(iso_date_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except Exception:
        return iso_date_str


@bp.route("/upload_form", methods=["GET", "POST"])
@require_file_manager_permission
def upload_form():
    """Display file upload form and handle uploads."""
    displayer, BSstyle, get_home_endpoint = _get_displayer_modules()
    
    disp = displayer.Displayer()
    disp.add_generic("Upload Files")
    disp.set_title("File Manager - Upload")
    disp.add_breadcrumb("Home", get_home_endpoint(), [])
    disp.add_breadcrumb("File Manager", "file_manager_admin.index", [])
    disp.add_breadcrumb("Upload", "file_manager_admin.upload_form", [])
    
    # Handle POST (form submission)
    if request.method == "POST":
        try:
            from ..modules import utilities
            
            # Check if file was uploaded
            if 'file' not in request.files:
                raise ValueError("No file selected")
            
            uploaded_file = request.files['file']
            
            # Get form data
            data_in = utilities.util_post_to_json(request.form.to_dict())
            form_data = data_in.get("Upload Files", {})
            
            category = form_data.get("category", "general")
            subcategory = form_data.get("subcategory", "")
            group_id = form_data.get("group_id", "")
            
            # Handle "(none)" values from dropdowns
            if subcategory == "(none)":
                subcategory = ""
            if group_id == "(none)":
                group_id = ""
            
            # Handle tags (can be list from multi-select or empty)
            tags_input = form_data.get("tags", [])
            if isinstance(tags_input, list):
                tags = tags_input
            elif isinstance(tags_input, str) and tags_input:
                tags = [tags_input]
            else:
                tags = []
            
            # Upload file using file manager
            result = file_manager.upload_file(
                uploaded_file,
                category=category,
                subcategory=subcategory,
                group_id=group_id,
                tags=tags
            )
            
            # Flash success message and redirect
            flash_msg = f"File '{result['name']}' uploaded successfully ({_format_file_size(result['size'])})"
            if group_id:
                flash_msg += f" to group '{group_id}'"
            if tags:
                flash_msg += f" with tags: {', '.join(tags)}"
            
            flash(flash_msg, "success")
            return redirect(url_for('file_manager_admin.index'))
            
        except Exception as e:
            logger.error(f"Upload error: {e}", exc_info=True)
            
            # Show error and fall through to display form again
            disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
            disp.add_display_item(displayer.DisplayerItemAlert(
                f"<h4><i class='bi bi-x-circle'></i> Upload Failed</h4><p>{str(e)}</p>",
                BSstyle.ERROR
            ), column=0)
    
    # Display upload form (GET request or after error)
    
    # Get available options from file manager
    categories = file_manager.get_categories() if file_manager else ["general"]
    group_ids = file_manager.get_group_ids() if file_manager else []
    tags = file_manager.get_tags() if file_manager else []
    
    # Form layout
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle="Upload New File"))
    
    # File input (using HTML since Displayer doesn't have file input)
    file_input_html = """
    <div class="mb-3">
        <label for="file" class="form-label">Select File</label>
        <input type="file" class="form-control" id="file" name="file" required>
        <div class="form-text">Maximum file size: 50 MB. Allowed types: PDF, Images, Office documents, Archives.</div>
    </div>
    """
    disp.add_display_item(displayer.DisplayerItemAlert(file_input_html, BSstyle.NONE), column=0)
    
    # Category dropdown
    disp.add_display_item(displayer.DisplayerItemInputSelect(
        id="category",
        text="Category",
        choices=categories,
        value="general"
    ), column=0)
    
    # Group ID dropdown (optional)
    if group_ids:
        group_id_choices = ["(none)"] + group_ids
        disp.add_display_item(displayer.DisplayerItemInputSelect(
            id="group_id",
            text="Group ID (Optional)",
            choices=group_id_choices,
            value="(none)"
        ), column=0)
    
    # Tags multi-select
    disp.add_display_item(displayer.DisplayerItemInputMultiSelect(
        id="tags",
        text="Tags (Optional)",
        choices=tags,
        value=[]
    ), column=0)
    
    # Buttons
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.HORIZONTAL, [6, 6]))
    
    disp.add_display_item(displayer.DisplayerItemButton(
        id="upload_btn",
        text="Upload File",
        icon="upload",
        color=BSstyle.PRIMARY
    ), column=0)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        id="cancel_btn",
        text="Cancel",
        icon="close-circle",
        link=url_for('file_manager_admin.index'),
        color=BSstyle.SECONDARY
    ), column=1)
    
    # Form should post back to this same URL
    form_action = url_for('file_manager_admin.upload_form')
    return render_template("base_content.j2", content=disp.display(), form_action=form_action)


@bp.route("/edit/<int:file_id>", methods=["GET", "POST"])
@require_file_manager_permission
def edit_file(file_id):
    """Edit file metadata (group_id, tags).
    
    Args:
        file_id: Database ID of the file version to edit
    """
    if not file_manager:
        return "File manager not initialized", 500
    
    displayer, BSstyle, get_home_endpoint = _get_displayer_modules()
    
    disp = displayer.Displayer()
    disp.add_generic("Edit File Metadata")
    disp.set_title("Edit File Metadata")
    
    disp.add_breadcrumb("Home", get_home_endpoint(), [])
    disp.add_breadcrumb("File Manager", "file_manager_admin.index", [])
    disp.add_breadcrumb("Edit File", "file_manager_admin.edit_file", [f"file_id={file_id}"])
    
    # Get file from database
    file_version = file_manager.get_file_by_id(file_id)
    
    if not file_version:
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        disp.add_display_item(displayer.DisplayerItemAlert(
            "<h4>File Not Found</h4><p>The requested file could not be found.</p>",
            BSstyle.ERROR
        ), column=0)
        return render_template("base_content.j2", content=disp.display())
    
    # Handle form submission
    if request.method == 'POST':
        try:
            from ..modules import utilities
            data_in = utilities.util_post_to_json(request.form.to_dict())
            form_data = data_in.get("Edit File Metadata", {})
            
            new_group_id = form_data.get("group_id", "").strip()
            if new_group_id == "(none)":
                new_group_id = ""
            
            # Handle tags (can be list from multi-select or string)
            tags_input = form_data.get("tags", [])
            if isinstance(tags_input, list):
                new_tags = tags_input
            elif isinstance(tags_input, str):
                new_tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()] if tags_input else []
            else:
                new_tags = []
            
            # Update group_id
            if new_group_id != (file_version.group_id or ""):
                success = file_manager.update_group_id(file_id, new_group_id)
                if not success:
                    raise Exception("Failed to update group_id")
                logger.info(f"Updated group_id for file {file_id}: {file_version.group_id} -> {new_group_id}")
            
            # Update tags
            current_tags = [tag.tag_name for tag in file_version.tags]
            if set(new_tags) != set(current_tags):
                # Remove old tags
                file_version.tags.clear()
                
                # Add new tags
                from ..modules.file_manager import FileTag
                for tag_name in new_tags:
                    tag = file_manager.db_session.query(FileTag).filter_by(tag_name=tag_name).first()
                    if not tag:
                        tag = FileTag(tag_name=tag_name)
                        file_manager.db_session.add(tag)
                    file_version.tags.append(tag)
                
                file_manager.db_session.commit()
                logger.info(f"Updated tags for file {file_id}: {current_tags} -> {new_tags}")
            
            # Flash success and redirect
            flash(f"Metadata for '{file_version.filename}' updated successfully.", "success")
            return redirect(url_for('file_manager_admin.index'))
            
        except Exception as e:
            logger.error(f"Edit file error: {e}", exc_info=True)
            disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
            disp.add_display_item(displayer.DisplayerItemAlert(
                f"<h4>Update Failed</h4><p>{str(e)}</p>",
                BSstyle.ERROR
            ), column=0)
    
    # Display edit form (GET request or after error)
    current_tags = [tag.tag_name for tag in file_version.tags]
    
    # File info section
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle="File Information"))
    
    # Get version number
    version_num = 1
    if file_version.group_id:
        try:
            versions = file_manager.get_file_versions(file_version.group_id, file_version.filename)
            version_num = next((i+1 for i, v in enumerate(reversed(versions)) if v['id'] == file_id), len(versions))
        except Exception:
            version_num = 1
    
    # Generate preview
    file_meta = {
        'name': file_version.filename,
        'id': file_id,
        'path': file_version.storage_path
    }
    # Add thumbnail if exists
    thumb_base = file_manager.hashfs_path.parent / ".thumbs"
    for size_str in ["150x150"]:
        storage_path_obj = Path(file_version.storage_path)
        thumb_path = thumb_base / size_str / storage_path_obj.parent / f"{storage_path_obj.stem}_thumb.jpg"
        if thumb_path.exists():
            thumb_relative = f".thumbs/{size_str}/{storage_path_obj.parent}/{storage_path_obj.stem}_thumb.jpg"
            file_meta[f'thumb_{size_str}'] = thumb_relative.replace('\\', '/')
            break
    
    preview_html = _generate_preview_html(file_meta, size="150px")
    
    info_html = f"""
    <div class="card">
        <div class="card-body">
            <h5 class="card-title"><i class="bi bi-file-earmark"></i> {file_version.filename}</h5>
            <hr>
            <div class="row">
                <div class="col-md-2 text-center">
                    {preview_html}
                </div>
                <div class="col-md-5">
                    <p><strong>Size:</strong> {_format_file_size(file_version.file_size)}</p>
                    <p><strong>Type:</strong> {file_version.mime_type}</p>
                    <p><strong>Uploaded:</strong> {_format_date(file_version.uploaded_at.isoformat())}</p>
                </div>
                <div class="col-md-5">
                    <p><strong>Group ID:</strong> {file_version.group_id or '(none)'}</p>
                    <p><strong>Version:</strong> v{version_num}</p>
                    <p><strong>Checksum:</strong> {file_version.checksum[:16] if file_version.checksum else 'N/A'}...</p>
                </div>
            </div>
        </div>
    </div>
    """
    
    disp.add_display_item(displayer.DisplayerItemAlert(info_html, BSstyle.NONE), column=0)
    
    # Edit form
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle="Edit Metadata"))
    
    # Get all existing group IDs from database
    from ..modules.file_manager import FileGroup
    existing_groups = file_manager.db_session.query(FileGroup).all()
    group_choices = ["(none)"] + [g.group_id for g in existing_groups]
    
    # Group ID dropdown with explanatory text above
    disp.add_display_item(displayer.DisplayerItemAlert(
        "<small class='text-muted'>Group ID for versioning. Files with the same group_id and filename are treated as versions of the same file.</small>",
        BSstyle.NONE
    ), column=0)
    
    current_group = file_version.group_id if file_version.group_id else "(none)"
    disp.add_display_item(displayer.DisplayerItemInputSelect(
        id="group_id",
        text="Group ID",
        choices=group_choices,
        value=current_group
    ), column=0)
    
    # Get configured tags
    available_tags = file_manager.get_tags()
    
    # Tags multi-select with explanatory text above
    disp.add_display_item(displayer.DisplayerItemAlert(
        "<small class='text-muted'>Organize files with tags for easy searching and filtering.</small>",
        BSstyle.NONE
    ), column=0)
    
    disp.add_display_item(displayer.DisplayerItemInputMultiSelect(
        id="tags",
        text="Tags",
        choices=available_tags,
        value=current_tags
    ), column=0)
    
    # Buttons
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.HORIZONTAL, [6, 6]))
    
    disp.add_display_item(displayer.DisplayerItemButton(
        id="save_btn",
        text="Save Changes",
        icon="save",
        color=BSstyle.PRIMARY
    ), column=0)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        id="cancel_btn",
        text="Cancel",
        icon="x-circle",
        link=url_for('file_manager_admin.index'),
        color=BSstyle.SECONDARY
    ), column=1)
    
    # Form should post back to this same URL
    form_action = url_for('file_manager_admin.edit_file', file_id=file_id)
    return render_template("base_content.j2", content=disp.display(), form_action=form_action)


@bp.route('/delete-multiple', methods=['POST'])
@require_file_manager_permission
def delete_multiple():
    """Handle multiple file deletion from checkboxes (redirects to confirm_delete)."""
    if not file_manager:
        return "File manager not initialized", 500
    
    # Get selected file IDs from form array
    file_ids_list = request.form.getlist('file_ids[]')
    
    if not file_ids_list:
        flash("No files selected for deletion.", "warning")
        return redirect(url_for('file_manager_admin.index'))
    
    # Convert to comma-separated string for confirm_delete
    file_ids_str = ','.join(file_ids_list)
    
    # Redirect to confirmation page
    return redirect(url_for('file_manager_admin.confirm_delete') + f'?file_ids={file_ids_str}')


@bp.route('/confirm-delete', methods=['GET', 'POST'])
def confirm_delete():
    """Confirmation page for deleting file(s).
    
    GET with file_id: Single file delete confirmation
    POST with file_ids_to_delete: Show multi-delete confirmation or execute deletion
    POST with confirm=true: Execute the deletion
    """
    if not file_manager:
        return "File manager not initialized", 500
    
    # Get modules
    displayer, BSstyle, get_home_endpoint = _get_displayer_modules()
    auth_manager = _get_auth_manager()
    
    # Check permission
    if auth_manager:
        current_user = session.get('user', 'GUEST')
        if not auth_manager.has_permission(current_user, "FileManager", "delete"):
            return render_template("error.j2", error="Permission denied"), 403
    
    disp = displayer.Displayer()
    
    # Check if this is a confirmation (second POST) or deletion request
    from modules.utilities import util_post_to_json
    is_executing = request.method == 'POST' and request.form.get('confirm_deletion') == 'true'
    
    if is_executing:
        # Execute deletion (second POST)
        data = util_post_to_json(request.form.to_dict())
        file_ids_str = data.get('file_ids_to_delete', '')
        if not file_ids_str:
            return "No files specified", 400
        
        try:
            file_ids = [int(fid) for fid in file_ids_str.split(',') if fid.strip()]
        except ValueError:
            return "Invalid file IDs", 400
    else:
        # Show confirmation page (GET or first POST)
        if request.method == 'GET':
            # Handle both single file (?file_id=123) and multiple (?file_ids=1,2,3)
            single_file_id = request.args.get('file_id', type=int)
            multi_file_ids_str = request.args.get('file_ids', '')
            
            if single_file_id:
                file_ids = [single_file_id]
            elif multi_file_ids_str:
                try:
                    file_ids = [int(fid) for fid in multi_file_ids_str.split(',') if fid.strip()]
                except ValueError:
                    return "Invalid file IDs", 400
            else:
                return "No files specified", 400
        else:
            # First POST from inline delete form
            data = util_post_to_json(request.form.to_dict())
            multi_file_ids = data.get('file_ids_to_delete', '')
            if multi_file_ids:
                try:
                    file_ids = [int(fid) for fid in multi_file_ids.split(',') if fid.strip()]
                except ValueError:
                    return "Invalid file IDs", 400
            else:
                return "No files specified", 400
        
        # Get file metadata
        files_to_delete = []
        for fid in file_ids:
            file_meta = file_manager.get_file_by_id(fid)
            if file_meta:
                files_to_delete.append({
                    'id': fid,
                    'filename': file_meta.filename,
                    'size': file_meta.file_size,
                    'uploaded_at': file_meta.uploaded_at.isoformat() + "Z",
                    'group_id': file_meta.group_id or '(none)'
                })
        
        if not files_to_delete:
            return "No valid files found", 404
        
        # Build confirmation page
        disp.add_generic("Confirm Delete")
        disp.set_title("Confirm File Deletion")
        
        from modules.utilities import get_home_endpoint
        disp.add_breadcrumb("Home", get_home_endpoint(), [])
        disp.add_breadcrumb("File Manager", "file_manager_admin.index", [])
        disp.add_breadcrumb("Confirm Delete", "file_manager_admin.confirm_delete", [])
        
        # Warning message
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        
        if len(files_to_delete) == 1:
            warning_html = f"""
            <div class="alert alert-danger" role="alert">
                <h4 class="alert-heading"><i class="bi bi-exclamation-triangle-fill"></i> Confirm Deletion</h4>
                <p>You are about to permanently delete the following file:</p>
                <hr>
                <p class="mb-0"><strong>{files_to_delete[0]['filename']}</strong></p>
                <p class="mb-0 text-muted">This action cannot be undone.</p>
            </div>
            """
        else:
            warning_html = f"""
            <div class="alert alert-danger" role="alert">
                <h4 class="alert-heading"><i class="bi bi-exclamation-triangle-fill"></i> Confirm Multiple Deletion</h4>
                <p>You are about to permanently delete <strong>{len(files_to_delete)} files</strong>:</p>
                <p class="mb-0 text-muted">This action cannot be undone.</p>
            </div>
            """
        
        disp.add_display_item(displayer.DisplayerItemAlert(warning_html, BSstyle.NONE), column=0)
        
        # File list table
        if len(files_to_delete) > 1:
            disp.add_master_layout(displayer.DisplayerLayout(
                displayer.Layouts.TABLE,
                ["Filename", "Group ID", "Size", "Uploaded"],
                subtitle="Files to Delete"
            ))
            
            for idx, file_info in enumerate(files_to_delete):
                disp.add_display_item(displayer.DisplayerItemText(file_info['filename']), 
                                    column=0, line=idx)
                disp.add_display_item(displayer.DisplayerItemText(file_info['group_id']), 
                                    column=1, line=idx)
                size_str = _format_file_size(file_info['size'])
                disp.add_display_item(displayer.DisplayerItemText(size_str), 
                                    column=2, line=idx)
                date_str = _format_date(file_info['uploaded_at'])
                disp.add_display_item(displayer.DisplayerItemText(date_str), 
                                    column=3, line=idx)
        
        # Hidden fields with file IDs and confirmation flag
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        file_ids_str = ','.join(str(fid) for fid in file_ids)
        hidden_fields_html = f"""
        <input type="hidden" name="file_ids_to_delete" value="{file_ids_str}">
        <input type="hidden" name="confirm_deletion" value="true">
        """
        disp.add_display_item(displayer.DisplayerItemAlert(hidden_fields_html, BSstyle.NONE), column=0)
        
        # Buttons
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.HORIZONTAL, [6, 6]))
        
        disp.add_display_item(displayer.DisplayerItemButton(
            id="confirm_delete_btn",
            text="Yes, Delete",
            icon="trash",
            color=BSstyle.ERROR
        ), column=0)
        
        disp.add_display_item(displayer.DisplayerItemButton(
            id="cancel_btn",
            text="Cancel",
            icon="x-circle",
            link=url_for('file_manager_admin.index'),
            color=BSstyle.SECONDARY
        ), column=1)
        
        return render_template("base_content.j2", content=disp.display(), 
                             form_action=url_for('file_manager_admin.confirm_delete'))
    
    # Execute deletion (is_executing == True)
    # Delete files
    deleted_count = 0
    failed_files = []
    
    for fid in file_ids:
        try:
            success = file_manager.delete_file(fid)
            if success:
                deleted_count += 1
                logger.info(f"File deleted by {session.get('user', 'GUEST')}: ID {fid}")
            else:
                failed_files.append(fid)
        except Exception as e:
            logger.error(f"Failed to delete file {fid}: {e}", exc_info=True)
            failed_files.append(fid)
    
    # Show result page
    disp.add_generic("Deletion Complete")
    disp.set_title("Deletion Complete")
    
    disp.add_breadcrumb("Home", get_home_endpoint(), [])
    disp.add_breadcrumb("File Manager", "file_manager_admin.index", [])
    disp.add_breadcrumb("Deletion Complete", "file_manager_admin.confirm_delete", [])
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    
    if failed_files:
        result_html = f"""
        <div class="alert alert-warning" role="alert">
            <h4 class="alert-heading"><i class="bi bi-check-circle"></i> Partially Complete</h4>
            <p><strong>{deleted_count}</strong> file(s) deleted successfully.</p>
            <p><strong>{len(failed_files)}</strong> file(s) failed to delete.</p>
        </div>
        """
    else:
        result_html = f"""
        <div class="alert alert-success" role="alert">
            <h4 class="alert-heading"><i class="bi bi-check-circle-fill"></i> Success</h4>
            <p><strong>{deleted_count}</strong> file(s) deleted successfully.</p>
        </div>
        """
    
    disp.add_display_item(displayer.DisplayerItemAlert(result_html, BSstyle.NONE), column=0)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        id="return_btn",
        text="Return to File Manager",
        icon="arrow-left",
        link=url_for('file_manager_admin.index'),
        color=BSstyle.PRIMARY
    ), column=0)
    
    return render_template("base_content.j2", content=disp.display())
