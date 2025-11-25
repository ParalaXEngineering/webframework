"""
File Manager Admin Page - Flask blueprint for file browsing and management UI.

This module provides a web interface for browsing, searching, and managing uploaded files.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from pathlib import Path
from typing import Optional, Any
from ..modules.utilities import util_format_file_size, util_format_date, util_get_file_icon, util_generate_preview_html
from ..modules.log.logger_factory import get_logger
from ..modules.auth import require_permission
from ..modules.auth.permission_registry import permission_registry
from ..modules import utilities
from ..modules import displayer
from ..modules.displayer import BSstyle

# Register module permissions (view is implicit)
permission_registry.register_module("FileManager", ["upload", "download", "delete", "edit"])

logger = get_logger(__name__)

bp = Blueprint("file_manager_admin", __name__, url_prefix="/file_manager")

# File manager instance will be injected by main.py
file_manager: Optional[Any] = None


def _get_auth_manager():
    """Get auth_manager dynamically to avoid initialization issues."""
    try:
        from ..modules.auth import auth_manager
        return auth_manager
    except ImportError:
        return None


@bp.route("/", methods=["GET"])
@require_permission("FileManager", "view")
def index():
    """File manager main page - browse files, view statistics."""
    if not file_manager:
        return "File manager not initialized", 500
    
    disp = displayer.Displayer()
    disp.add_generic("File Manager", display=False)
    disp.set_title("File Manager - Browse Files")
    disp.add_breadcrumb("File Manager", "file_manager_admin.index", [])
    
    # Check user permissions
    auth_manager = _get_auth_manager()
    current_user = session.get('user', 'GUEST')
    can_upload = auth_manager.has_permission(current_user, "FileManager", "upload") if auth_manager else True
    can_delete = auth_manager.has_permission(current_user, "FileManager", "delete") if auth_manager else True
    can_edit = auth_manager.has_permission(current_user, "FileManager", "edit") if auth_manager else True
    
    try:
        # Get file list from database (Phase 3 - includes versions, tags, group_id)
        files = file_manager.list_files_from_db()
                
        # File list table with DataTables
        if files:            
            table_layout_id = disp.add_master_layout(displayer.DisplayerLayout(
                displayer.Layouts.TABLE,
                ["Select", "Preview", "Filename", "Group ID", "Tags", "Version", "Size", "Uploaded", "Integrity", "Actions"],
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
                preview_html = util_generate_preview_html(file_meta)
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
                size_str = util_format_file_size(file_meta['size'])
                disp.add_display_item(displayer.DisplayerItemText(size_str), 
                                    column=6, line=idx, layout_id=table_layout_id)
                
                # Upload date
                upload_date = util_format_date(file_meta['uploaded_at'])
                disp.add_display_item(displayer.DisplayerItemText(upload_date), 
                                    column=7, line=idx, layout_id=table_layout_id)
            
            # Bulk integrity check (single DB query + N file I/O operations)
            # This is much more efficient than N individual verify_file_integrity() calls
            file_ids = [f.get('id', 0) for f in files]
            integrity_results = file_manager.verify_files_bulk(file_ids)
            
            # Display integrity status for each file
            for idx, file_meta in enumerate(files):
                file_id = file_meta.get('id', 0)
                is_valid, status = integrity_results.get(file_id, (False, "Unknown"))
                
                if is_valid:
                    disp.add_display_item(displayer.DisplayerItemBadge("OK", BSstyle.SUCCESS), 
                                        column=8, line=idx, layout_id=table_layout_id)
                elif status == "Missing":
                    disp.add_display_item(displayer.DisplayerItemBadge("Missing", BSstyle.WARNING), 
                                        column=8, line=idx, layout_id=table_layout_id)
                elif status == "Checksum mismatch":
                    disp.add_display_item(displayer.DisplayerItemBadge("Corrupted", BSstyle.ERROR), 
                                        column=8, line=idx, layout_id=table_layout_id)
                elif status == "Not found":
                    disp.add_display_item(displayer.DisplayerItemBadge("Not Found", BSstyle.SECONDARY), 
                                        column=8, line=idx, layout_id=table_layout_id)
                else:
                    disp.add_display_item(displayer.DisplayerItemBadge(f"Error: {status}", BSstyle.ERROR), 
                                        column=8, line=idx, layout_id=table_layout_id)
                
                # Actions (download, edit, history, delete buttons)
                actions = []
                
                # Download
                actions.append({
                    "type": "download",
                    "url": url_for('file_handler.download_by_id', file_id=file_meta.get('id', 0)),
                    "icon": "mdi mdi-download",
                    "style": "primary",
                    "tooltip": "Download"
                })
                
                # Edit (only if user has edit permission)
                if can_edit:
                    actions.append({
                        "type": "custom",
                        "url": url_for('file_manager_admin.edit_file', file_id=file_meta.get('id', 0)),
                        "icon": "mdi mdi-pencil",
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
                            "url": url_for('file_manager_admin.version_history', group_id=group_param, filename=file_meta['name']),
                            "icon": "mdi mdi-history",
                            "style": "info",
                            "tooltip": "View History"
                        })
                except Exception:
                    pass  # Skip history button if we can't get versions
                
                # Delete (only if user has delete permission)
                if can_delete:
                    actions.append({
                        "type": "custom",
                        "url": url_for('file_manager_admin.confirm_delete', file_id=file_meta.get('id', 0)),
                        "icon": "mdi mdi-delete",
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

            # Add table layout with Phase 3 columns including integrity status
            # Multi-delete button (submit button for form) - only show if user has delete permission
            disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
            if can_delete:
                disp.add_display_item(
                    displayer.DisplayerItemButton(
                        id="delete_selected_btn",
                        text="Delete Selected",
                        icon="trash",
                        color=BSstyle.ERROR
                    ),
                    column=0
                )
            else:
                disp.add_display_item(
                    displayer.DisplayerItemAlert(
                        "<i class='mdi mdi-information'></i> You need 'delete' permission to remove files. Contact your administrator.",
                        BSstyle.INFO
                    ),
                    column=0
                )
        else:
            disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
            if can_upload:
                disp.add_display_item(displayer.DisplayerItemAlert(
                    "No files found. Upload files to get started!",
                    BSstyle.INFO
                ), column=0)
            else:
                disp.add_display_item(displayer.DisplayerItemAlert(
                    "No files found. You need 'upload' permission to add files. Contact your administrator.",
                    BSstyle.WARNING
                ), column=0)
        
        # Multi-delete form wraps the table automatically via form_action parameter
        # Checkboxes use name="file_ids[]" for array submission
        form_action = url_for('file_manager_admin.delete_multiple')
        return render_template("base_content.j2", content=disp.display(), form_action=form_action)
        
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
    
    Creates an HTML img tag for files with thumbnails, or a Bootstrap icon
    for files without thumbnails. Gracefully falls back to icon if thumbnail
    URL generation fails.
    
    Args:
        file_meta: File metadata dictionary containing:
            - 'name': Filename for extension detection
            - 'thumb_150x150' (optional): Relative path to 150x150 thumbnail
        size: CSS size value for preview (default "60px")
        
    Returns:
        HTML string containing either <img> tag or <i> icon tag
        
    Examples:
        >>> _generate_preview_html({'name': 'photo.jpg', 'thumb_150x150': '.thumbs/...'})
        '<img src="/files/download/..." class="img-thumbnail" ...>'
        
        >>> _generate_preview_html({'name': 'document.pdf'})
        '<i class="mdi mdi-file-pdf text-danger" style="font-size: 2rem;"></i>'
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
    icon_class = util_get_file_icon(file_meta['name'])
    return f'<i class="bi {icon_class}" style="font-size: 2rem;"></i>'


@bp.route("/edit/<int:file_id>", methods=["GET", "POST"])
@require_permission("FileManager", "edit")
def edit_file(file_id):
    """Edit file metadata (group_id, tags).
    
    Args:
        file_id: Database ID of the file version to edit
    """
    if not file_manager:
        return "File manager not initialized", 500
    
    disp = displayer.Displayer()
    disp.add_generic("Edit File Metadata")
    disp.set_title("Edit File Metadata")
    
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
    
    preview_html = util_generate_preview_html(file_meta, size="150px")
    
    info_body = f"""
    <div class="row">
        <div class="col-md-2 text-center">
            {preview_html}
        </div>
        <div class="col-md-5">
            <p><strong>Size:</strong> {util_format_file_size(file_version.file_size)}</p>
            <p><strong>Type:</strong> {file_version.mime_type}</p>
            <p><strong>Uploaded:</strong> {util_format_date(file_version.uploaded_at.isoformat())}</p>
        </div>
        <div class="col-md-5">
            <p><strong>Group ID:</strong> {file_version.group_id or '(none)'}</p>
            <p><strong>Version:</strong> v{version_num}</p>
            <p><strong>Checksum:</strong> {file_version.checksum[:16] if file_version.checksum else 'N/A'}...</p>
        </div>
    </div>
    """
    
    disp.add_display_item(displayer.DisplayerItemCard(
        id="file_info_card",
        title=file_version.filename,
        icon="file",
        header_color=BSstyle.INFO,
        body=info_body
    ), column=0)
    
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
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [6, 6]))
    
    disp.add_display_item(displayer.DisplayerItemButton(
        id="save_btn",
        text="Save Changes",
        icon="content-save",
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
    form_action = url_for('file_manager_admin.edit_file', file_id=file_id)
    return render_template("base_content.j2", content=disp.display(), form_action=form_action)


@bp.route('/delete-multiple', methods=['POST'])
@require_permission("FileManager", "delete")
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
@require_permission("FileManager", "delete")
def confirm_delete():
    """Confirmation page for deleting file(s).
    
    GET with file_id: Single file delete confirmation
    POST with file_ids_to_delete: Show multi-delete confirmation or execute deletion
    POST with confirm=true: Execute the deletion
    """
    if not file_manager:
        return "File manager not initialized", 500
    
    disp = displayer.Displayer()
    
    # Check if this is a confirmation (second POST) or deletion request
    is_executing = request.method == 'POST' and request.form.get('Confirm Delete.confirm_deletion') == 'true'
    
    if is_executing:
        # Execute deletion (second POST)
        data = utilities.util_post_to_json(request.form.to_dict())
        data = data["Confirm Delete"]
        file_ids_str = data.get('file_ids_to_delete', '')
        delete_all_versions = data.get('delete_all_versions', 'false') == 'true'
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
            data = utilities.util_post_to_json(request.form.to_dict())
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
        disp.add_generic("Confirm Delete", display=False)
        
        disp.add_breadcrumb("File Manager", "file_manager_admin.index", [])
        disp.add_breadcrumb("Confirm Delete", "file_manager_admin.confirm_delete", [])
        
        # Warning message
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        
        if len(files_to_delete) == 1:
            warning_html = f"You are about to permanently delete the following file: <strong>{files_to_delete[0]['filename']}</strong><br><br>This action cannot be undone."
        else:
            warning_html = f"You are about to permanently delete <strong>{len(files_to_delete)} files</strong><br><br>This action cannot be undone."
        
        disp.add_display_item(displayer.DisplayerItemAlert(warning_html, BSstyle.ERROR, icon="alert", title="Confirm Deletion"), column=0)
        
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
                size_str = util_format_file_size(file_info['size'])
                disp.add_display_item(displayer.DisplayerItemText(size_str), 
                                    column=2, line=idx)
                date_str = util_format_date(file_info['uploaded_at'])
                disp.add_display_item(displayer.DisplayerItemText(date_str), 
                                    column=3, line=idx)
        
        # Hidden fields with file IDs and confirmation flag
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        file_ids_str = ','.join(str(fid) for fid in file_ids)
        disp.add_display_item(displayer.DisplayerItemHidden(id="file_ids_to_delete", value=file_ids_str), column=0)
        disp.add_display_item(displayer.DisplayerItemHidden(id="confirm_deletion", value="true"), column=0)
        
        # Check if any files have versions (group_id set)
        has_versioned_files = any(f['group_id'] != '(none)' for f in files_to_delete)
        
        if has_versioned_files:
            # Add checkbox to delete all versions
            disp.add_display_item(displayer.DisplayerItemAlert(
                "<small class='text-muted'>Some files have version history. Check the box below to delete all versions.</small>",
                BSstyle.NONE
            ), column=0)
            disp.add_display_item(displayer.DisplayerItemInputCheckbox(
                id="delete_all_versions",
                text="Delete ALL versions of these files (removes entire version history)",
                value=False
            ), column=0)
        
        # Buttons
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [6, 6]))
        
        disp.add_display_item(displayer.DisplayerItemButton(
            id="confirm_delete_btn",
            text="Yes, Delete",
            icon="delete-forever",
            color=BSstyle.ERROR
        ), column=0)
        
        disp.add_display_item(displayer.DisplayerItemButton(
            id="cancel_btn",
            text="Cancel",
            icon="close-circle",
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
            success = file_manager.delete_file(fid, delete_all_versions=delete_all_versions)
            if success:
                deleted_count += 1
                logger.info(f"File deleted by {session.get('user', 'GUEST')}: ID {fid} (all_versions={delete_all_versions})")
            else:
                failed_files.append(fid)
        except Exception as e:
            logger.error(f"Failed to delete file {fid}: {e}", exc_info=True)
            failed_files.append(fid)
    
    # Show result page
    disp.add_generic("Deletion Complete")
    disp.set_title("Deletion Complete")
    
    disp.add_breadcrumb("File Manager", "file_manager_admin.index", [])
    disp.add_breadcrumb("Deletion Complete", "file_manager_admin.confirm_delete", [])
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    
    if failed_files:
        result_html = f"""
            <p><strong>{deleted_count}</strong> file(s) deleted successfully.</p>
            <p><strong>{len(failed_files)}</strong> file(s) failed to delete.</p>
        """
        disp.add_display_item(displayer.DisplayerItemAlert(result_html, BSstyle.WARNING, icon="check-circle", title="Partially Complete"), column=0)
    else:
        result_html = f"<p><strong>{deleted_count}</strong> file(s) deleted successfully.</p>"
        disp.add_display_item(displayer.DisplayerItemAlert(result_html, BSstyle.SUCCESS, icon="check-circle", title="Success"), column=0)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        id="return_btn",
        text="Return to File Manager",
        icon="arrow-left",
        link=url_for('file_manager_admin.index'),
        color=BSstyle.PRIMARY
    ), column=0)
    
    return render_template("base_content.j2", content=disp.display())


@bp.route('/version-history/<group_id>/<filename>', methods=['GET'])
@require_permission("FileManager", "view")
def version_history(group_id, filename):
    """Display version history page for a file.
    
    Args:
        group_id: Group identifier (use '(none)' for files without a group)
        filename: Filename
    
    Returns:
        HTML page with version history table
    """
    if not file_manager:
        return "File manager not initialized", 500
    
    try:
        # Convert '(none)' placeholder back to None for files without a group
        actual_group_id = None if group_id == '(none)' else group_id
        versions = file_manager.get_file_versions(actual_group_id, filename)
        
        # Build version history page
        disp = displayer.Displayer()
        disp.add_generic(f"Version History - {filename}", display=False)
        disp.set_title(f"Version History: {filename}")
        disp.add_breadcrumb("File Manager", "file_manager_admin.index", [])
        disp.add_breadcrumb("Version History", "file_manager_admin.version_history", [group_id, filename])
                
        # Version table
        if versions:
            disp.add_master_layout(displayer.DisplayerLayout(
                displayer.Layouts.TABLE,
                ["Preview", "Version", "Status", "Size", "Checksum", "Uploaded", "Uploaded By", "Actions"],
                subtitle="All Versions"
            ))
            
            # Sort versions by upload date (newest first)
            sorted_versions = sorted(versions, key=lambda v: v['uploaded_at'], reverse=True)
            
            for idx, version in enumerate(sorted_versions):
                # Preview
                file_meta = {
                    'name': version['filename'],
                    'id': version['id'],
                    'path': version.get('storage_path', '')
                }
                # Check for thumbnails
                thumb_base = file_manager.hashfs_path.parent / ".thumbs"
                for size_str in ["150x150"]:
                    storage_path_obj = Path(version.get('storage_path', ''))
                    thumb_path = thumb_base / size_str / storage_path_obj.parent / f"{storage_path_obj.stem}_thumb.jpg"
                    if thumb_path.exists():
                        thumb_relative = f".thumbs/{size_str}/{storage_path_obj.parent}/{storage_path_obj.stem}_thumb.jpg"
                        file_meta[f'thumb_{size_str}'] = thumb_relative.replace('\\', '/')
                        break
                
                preview_html = util_generate_preview_html(file_meta, size="50px")
                disp.add_display_item(displayer.DisplayerItemAlert(preview_html, BSstyle.NONE), 
                                    column=0, line=idx)
                
                # Version number (count from oldest)
                version_num = len(versions) - sorted_versions.index(version)
                disp.add_display_item(displayer.DisplayerItemBadge(f"v{version_num}", BSstyle.PRIMARY), 
                                    column=1, line=idx)
                
                # Status (current or archived)
                if version.get('is_current'):
                    disp.add_display_item(displayer.DisplayerItemBadge("Current", BSstyle.SUCCESS), 
                                        column=2, line=idx)
                else:
                    disp.add_display_item(displayer.DisplayerItemBadge("Archived", BSstyle.SECONDARY), 
                                        column=2, line=idx)
                
                # Size
                size_str = util_format_file_size(version.get('file_size', 0))
                disp.add_display_item(displayer.DisplayerItemText(size_str), 
                                    column=3, line=idx)
                
                # Checksum (truncated)
                checksum = version.get('checksum', 'N/A')
                checksum_short = checksum[:8] + "..." if len(checksum) > 8 else checksum
                disp.add_display_item(displayer.DisplayerItemText(checksum_short), 
                                    column=4, line=idx)
                
                # Uploaded date
                upload_date = util_format_date(version.get('uploaded_at', ''))
                disp.add_display_item(displayer.DisplayerItemText(upload_date), 
                                    column=5, line=idx)
                
                # Uploaded by
                uploaded_by = version.get('uploaded_by', 'Unknown')
                disp.add_display_item(displayer.DisplayerItemText(uploaded_by), 
                                    column=6, line=idx)
                
                # Actions
                file_id = version.get('id')
                download_url = url_for('file_handler.download_by_id', file_id=file_id)
                
                # Action buttons
                actions = []
                
                # Download button
                actions.append({
                    "type": "download",
                    "url": download_url,
                    "icon": "mdi mdi-download",
                    "style": "primary",
                    "tooltip": "Download this version"
                })
                
                # Restore button for non-current versions (simple GET link)
                if not version.get('is_current'):
                    restore_url = url_for('file_manager_admin.restore_version', 
                                        target_version_id=file_id,
                                        group_id=group_id,
                                        filename=filename)
                    actions.append({
                        "type": "custom",
                        "url": restore_url,
                        "icon": "mdi mdi-restore",
                        "style": "success",
                        "tooltip": f"Restore v{version_num} as current"
                    })
                
                disp.add_display_item(
                    displayer.DisplayerItemActionButtons(
                        id=f"version_actions_{idx}",
                        actions=actions,
                        size="sm"
                    ),
                    column=7, line=idx
                )
        
        # Back button
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        disp.add_display_item(displayer.DisplayerItemButton(
            id="back_btn",
            text="Back to File Manager",
            icon="arrow-left",
            link=url_for('file_manager_admin.index'),
            color=BSstyle.SECONDARY
        ), column=0)
        
        return render_template("base_content.j2", content=disp.display())
        
    except Exception as e:
        logger.error(f"Failed to display version history: {e}", exc_info=True)
        
        disp = displayer.Displayer()
        disp.add_generic("Error")
        disp.set_title("Version History Error")
        disp.add_breadcrumb("File Manager", "file_manager_admin.index", [])
        
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        disp.add_display_item(displayer.DisplayerItemAlert(
            f"<h4>Error Loading Version History</h4><p>{str(e)}</p>",
            BSstyle.ERROR
        ), column=0)
        
        return render_template("base_content.j2", content=disp.display()), 500


@bp.route('/restore-version/<int:target_version_id>/<group_id>/<filename>', methods=['GET'])
@require_permission("FileManager", "edit")
def restore_version(target_version_id, group_id, filename):
    """Restore an old version of a file using a simple GET link.
    
    Args:
        target_version_id: Version to restore from
        group_id: Group identifier for redirect
        filename: Filename for redirect
    
    Returns:
        Redirect to version history with flash message
    """
    if not file_manager:
        flash("File manager not initialized", "error")
        return redirect(url_for('file_manager_admin.index'))
    
    try:
        # Get target version to find group_id and filename
        from ..modules.file_manager import FileVersion
        
        session_db = file_manager.db_session
        target_version = session_db.query(FileVersion).filter_by(id=target_version_id).first()
        
        if not target_version:
            flash("Target version not found", "error")
            return redirect(url_for('file_manager_admin.index'))
        
        # Find current version in same group
        current_version = session_db.query(FileVersion).filter_by(
            group_id=target_version.group_id,
            filename=target_version.filename,
            is_current=True
        ).first()
        
        if not current_version:
            flash("Current version not found", "error")
            return redirect(url_for('file_manager_admin.index'))
        
        # Restore version
        restored = file_manager.restore_version(current_version.id, target_version_id)
        
        logger.info(f"Version restored by {session.get('user', 'GUEST')}: {restored.filename}")
        flash("Version restored successfully! A new version has been created.", "success")
        
    except Exception as e:
        logger.error(f"Failed to restore version: {e}", exc_info=True)
        flash(f"Failed to restore version: {str(e)}", "error")
    
    # Redirect back to version history page
    return redirect(url_for('file_manager_admin.version_history', group_id=group_id, filename=filename))
