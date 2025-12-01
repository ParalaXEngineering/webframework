"""
File Manager Admin Page - Flask blueprint for file browsing and management UI.

This module provides a web interface for browsing, searching, and managing uploaded files.
"""

# Standard library
from pathlib import Path
from typing import Optional, Any

# Third-party
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

# Local modules
from ..modules import displayer, utilities
from ..modules.auth import require_permission, auth_manager
from ..modules.auth.permission_registry import permission_registry
from ..modules.displayer import BSstyle
from ..modules.log.logger_factory import get_logger
from ..modules.utilities import (
    util_format_file_size,
    util_format_date,
    util_get_file_icon,
    util_generate_preview_html,
)

# Framework modules - constants and i18n
from ..modules.constants import (
    STATUS_BAD_REQUEST,
    STATUS_NOT_FOUND,
    STATUS_SERVER_ERROR,
)
from ..modules.i18n.messages import (
    ERROR_FILE_MANAGER_NOT_INITIALIZED,
    ERROR_FILE_NOT_FOUND_FM,
    ERROR_FILE_NOT_FOUND_DESC,
    ERROR_UPDATE_FAILED,
    ERROR_LOADING_FILES,
    ERROR_LOADING_VERSION_HISTORY,
    TEXT_FILE_MANAGER,
    TEXT_FILE_MANAGER_BROWSE,
    TEXT_EDIT_FILE_METADATA,
    TEXT_CONFIRM_DELETE,
    TEXT_DELETION_COMPLETE,
    TEXT_VERSION_HISTORY,
    TEXT_VERSION_HISTORY_FILE,
    TEXT_BREADCRUMB_FILE_MANAGER,
    TEXT_BREADCRUMB_EDIT_FILE,
    TEXT_BREADCRUMB_CONFIRM_DELETE,
    TEXT_BREADCRUMB_DELETION_COMPLETE,
    TEXT_BREADCRUMB_VERSION_HISTORY,
    BUTTON_DELETE_SELECTED,
    BUTTON_SAVE_CHANGES,
    BUTTON_CANCEL,
    BUTTON_YES_DELETE,
    BUTTON_RETURN_FILE_MANAGER,
    BUTTON_BACK_FILE_MANAGER,
    TOOLTIP_DOWNLOAD,
    TOOLTIP_EDIT_METADATA,
    TOOLTIP_VIEW_HISTORY,
    TOOLTIP_DELETE,
    TOOLTIP_DOWNLOAD_VERSION,
    TOOLTIP_RESTORE_VERSION,
    TOOLTIP_DELETE_VERSION,
    BADGE_MISSING,
    BADGE_CORRUPTED,
    BADGE_NOT_FOUND,
    BADGE_CURRENT,
    BADGE_ARCHIVED,
    BADGE_VERSION,
    LABEL_FILE_INFORMATION,
    LABEL_EDIT_METADATA,
    LABEL_FILES_TO_DELETE,
    LABEL_ALL_VERSIONS,
    LABEL_GROUP_ID,
    LABEL_TAGS,
    LABEL_SIZE,
    LABEL_TYPE,
    LABEL_UPLOADED,
    LABEL_VERSION,
    LABEL_CHECKSUM,
    LABEL_UPLOADED_BY,
    TABLE_HEADER_SELECT,
    TABLE_HEADER_PREVIEW,
    TABLE_HEADER_FILENAME,
    TABLE_HEADER_GROUP_ID,
    TABLE_HEADER_TAGS,
    TABLE_HEADER_VERSION,
    TABLE_HEADER_SIZE,
    TABLE_HEADER_UPLOADED,
    TABLE_HEADER_INTEGRITY,
    TABLE_HEADER_ACTIONS,
    TABLE_HEADER_STATUS,
    TABLE_HEADER_CHECKSUM,
    TEXT_NO_FILES_UPLOAD,
    TEXT_NO_FILES_PERMISSION,
    TEXT_NO_DELETE_PERMISSION,
    TEXT_VERSIONING_INFO,
    TEXT_TAGS_INFO,
    TEXT_VERSIONS_DELETED_WARNING,
    MSG_NO_FILES_SELECTED,
    MSG_UPDATE_SUCCESS,
    MSG_VERSION_RESTORED,
    MSG_VERSION_DELETED,
    MSG_VERSIONS_DELETED,
    MSG_FILE_MANAGER_NOT_INIT,
    MSG_TARGET_VERSION_NOT_FOUND,
    MSG_CURRENT_VERSION_NOT_FOUND,
    MSG_DELETE_VERSION_FAILED,
    MSG_DELETE_VERSION_ERROR,
    MSG_RESTORE_VERSION_ERROR,
    DELETE_CONFIRM_SINGLE,
    DELETE_CONFIRM_MULTIPLE,
    DELETE_RESULT_PARTIAL,
    DELETE_RESULT_SUCCESS,
    TITLE_CONFIRM_DELETION,
    TITLE_PARTIALLY_COMPLETE,
    TITLE_SUCCESS,
)

logger = get_logger(__name__)

# Constants - Domain-specific to file manager module
PERMISSION_MODULE = "FileManager"
PERMISSION_UPLOAD = "upload"
PERMISSION_DOWNLOAD = "download"
PERMISSION_DELETE = "delete"
PERMISSION_EDIT = "edit"
PERMISSION_VIEW = "view"

# Constants - File/group display (domain-specific to file manager)
GROUP_NONE = "(none)"
INTEGRITY_STATUS_OK = "OK"

# Constants - Integrity check status codes (technical, returned by file_manager)
INTEGRITY_STATUS_MISSING = "Missing"
INTEGRITY_STATUS_CHECKSUM_MISMATCH = "Checksum mismatch"
INTEGRITY_STATUS_NOT_FOUND = "Not found"
INTEGRITY_STATUS_UNKNOWN = "Unknown"

# Register module permissions (view is implicit)
permission_registry.register_module(PERMISSION_MODULE, [PERMISSION_UPLOAD, PERMISSION_DOWNLOAD, PERMISSION_DELETE, PERMISSION_EDIT])

bp = Blueprint("file_manager_admin", __name__, url_prefix="/file_manager")

# File manager instance will be injected by main.py
file_manager: Optional[Any] = None

@bp.route("/", methods=["GET"])
@require_permission(PERMISSION_MODULE, PERMISSION_VIEW)
def index():
    """File manager main page - browse files, view statistics."""
    if not file_manager:
        return ERROR_FILE_MANAGER_NOT_INITIALIZED, STATUS_SERVER_ERROR
    
    disp = displayer.Displayer()
    disp.add_generic(TEXT_FILE_MANAGER, display=False)
    disp.set_title(TEXT_FILE_MANAGER_BROWSE)
    disp.add_breadcrumb(TEXT_BREADCRUMB_FILE_MANAGER, "file_manager_admin.index", [])
    
    # Check user permissions
    current_user = session.get('user', 'GUEST')
    can_upload = auth_manager.has_permission(current_user, PERMISSION_MODULE, PERMISSION_UPLOAD) if auth_manager else True
    can_delete = auth_manager.has_permission(current_user, PERMISSION_MODULE, PERMISSION_DELETE) if auth_manager else True
    can_edit = auth_manager.has_permission(current_user, PERMISSION_MODULE, PERMISSION_EDIT) if auth_manager else True
    
    try:
        # Get file list from database (Phase 3 - includes versions, tags, group_id)
        files = file_manager.list_files_from_db()
                
        # File list table with DataTables
        if files:            
            table_layout_id = disp.add_master_layout(displayer.DisplayerLayout(
                displayer.Layouts.TABLE,
                [TABLE_HEADER_SELECT, TABLE_HEADER_PREVIEW, TABLE_HEADER_FILENAME, TABLE_HEADER_GROUP_ID, TABLE_HEADER_TAGS, TABLE_HEADER_VERSION, TABLE_HEADER_SIZE, TABLE_HEADER_UPLOADED, TABLE_HEADER_INTEGRITY, TABLE_HEADER_ACTIONS],
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
                group_id_val = file_meta.get('group_id', '') or GROUP_NONE
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
                    tags_display = GROUP_NONE
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
                is_valid, status = integrity_results.get(file_id, (False, INTEGRITY_STATUS_UNKNOWN))
                
                if is_valid:
                    disp.add_display_item(displayer.DisplayerItemBadge(INTEGRITY_STATUS_OK, BSstyle.SUCCESS), 
                                        column=8, line=idx, layout_id=table_layout_id)
                elif status == INTEGRITY_STATUS_MISSING:
                    disp.add_display_item(displayer.DisplayerItemBadge(BADGE_MISSING, BSstyle.WARNING), 
                                        column=8, line=idx, layout_id=table_layout_id)
                elif status == INTEGRITY_STATUS_CHECKSUM_MISMATCH:
                    disp.add_display_item(displayer.DisplayerItemBadge(BADGE_CORRUPTED, BSstyle.ERROR), 
                                        column=8, line=idx, layout_id=table_layout_id)
                elif status == INTEGRITY_STATUS_NOT_FOUND:
                    disp.add_display_item(displayer.DisplayerItemBadge(BADGE_NOT_FOUND, BSstyle.SECONDARY), 
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
                    "tooltip": str(TOOLTIP_DOWNLOAD)
                })
                
                # Edit (only if user has edit permission)
                if can_edit:
                    actions.append({
                        "type": "custom",
                        "url": url_for('file_manager_admin.edit_file', file_id=file_meta.get('id', 0)),
                        "icon": "mdi mdi-pencil",
                        "style": "warning",
                        "tooltip": str(TOOLTIP_EDIT_METADATA)
                    })
                
                # History (show for all files that might have versions)
                # Extract version info from the version_display we calculated earlier
                try:
                    versions = file_manager.get_file_versions(file_meta.get('group_id'), file_meta['name'])
                    if versions and len(versions) > 0:
                        # Show history button for files with versions
                        # Use '(none)' as URL placeholder for files without a group
                        group_param = file_meta.get('group_id') or GROUP_NONE
                        actions.append({
                            "type": "custom",
                            "url": url_for('file_manager_admin.version_history', group_id=group_param, filename=file_meta['name']),
                            "icon": "mdi mdi-history",
                            "style": "info",
                            "tooltip": str(TOOLTIP_VIEW_HISTORY)
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
                        "tooltip": str(TOOLTIP_DELETE)
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
                        text=str(BUTTON_DELETE_SELECTED),
                        icon="trash",
                        color=BSstyle.ERROR
                    ),
                    column=0
                )
            else:
                disp.add_display_item(
                    displayer.DisplayerItemAlert(
                        f"<i class='mdi mdi-information'></i> {TEXT_NO_DELETE_PERMISSION}",
                        BSstyle.INFO
                    ),
                    column=0
                )
        else:
            disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
            if can_upload:
                disp.add_display_item(displayer.DisplayerItemAlert(
                    str(TEXT_NO_FILES_UPLOAD),
                    BSstyle.INFO
                ), column=0)
            else:
                disp.add_display_item(displayer.DisplayerItemAlert(
                    str(TEXT_NO_FILES_PERMISSION),
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
            f"<h4>{ERROR_LOADING_FILES}</h4><p>{str(e)}</p>",
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
@require_permission(PERMISSION_MODULE, PERMISSION_EDIT)
def edit_file(file_id):
    """Edit file metadata (group_id, tags).
    
    Args:
        file_id: Database ID of the file version to edit
    """
    if not file_manager:
        return ERROR_FILE_MANAGER_NOT_INITIALIZED, STATUS_SERVER_ERROR
    
    disp = displayer.Displayer()
    disp.add_generic(TEXT_EDIT_FILE_METADATA)
    disp.set_title(TEXT_EDIT_FILE_METADATA)
    
    disp.add_breadcrumb(TEXT_BREADCRUMB_FILE_MANAGER, "file_manager_admin.index", [])
    disp.add_breadcrumb(TEXT_BREADCRUMB_EDIT_FILE, "file_manager_admin.edit_file", [f"file_id={file_id}"])
    
    # Get file from database
    file_version = file_manager.get_file_by_id(file_id)
    
    if not file_version:
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        disp.add_display_item(displayer.DisplayerItemAlert(
            f"<h4>{ERROR_FILE_NOT_FOUND_FM}</h4><p>{ERROR_FILE_NOT_FOUND_DESC}</p>",
            BSstyle.ERROR
        ), column=0)
        return render_template("base_content.j2", content=disp.display())
    
    # Handle form submission
    if request.method == 'POST':
        try:
            data_in = utilities.util_post_to_json(request.form.to_dict())
            form_data = data_in.get("Edit File Metadata", {})
            
            new_group_id = form_data.get("group_id", "").strip()
            if new_group_id == GROUP_NONE:
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
            flash(MSG_UPDATE_SUCCESS.format(filename=file_version.filename), "success")
            return redirect(url_for('file_manager_admin.index'))
            
        except Exception as e:
            logger.error(f"Edit file error: {e}", exc_info=True)
            disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
            disp.add_display_item(displayer.DisplayerItemAlert(
                f"<h4>{ERROR_UPDATE_FAILED}</h4><p>{str(e)}</p>",
                BSstyle.ERROR
            ), column=0)
    
    # Display edit form (GET request or after error)
    current_tags = [tag.tag_name for tag in file_version.tags]
    
    # File info section
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle=str(LABEL_FILE_INFORMATION)))
    
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
            <p><strong>{LABEL_SIZE}:</strong> {util_format_file_size(file_version.file_size)}</p>
            <p><strong>{LABEL_TYPE}:</strong> {file_version.mime_type}</p>
            <p><strong>{LABEL_UPLOADED}:</strong> {util_format_date(file_version.uploaded_at.isoformat())}</p>
        </div>
        <div class="col-md-5">
            <p><strong>{LABEL_GROUP_ID}:</strong> {file_version.group_id or GROUP_NONE}</p>
            <p><strong>{LABEL_VERSION}:</strong> v{version_num}</p>
            <p><strong>{LABEL_CHECKSUM}:</strong> {file_version.checksum[:16] if file_version.checksum else 'N/A'}...</p>
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
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle=str(LABEL_EDIT_METADATA)))
    
    # Get all existing group IDs from database
    from ..modules.file_manager import FileGroup
    existing_groups = file_manager.db_session.query(FileGroup).all()
    group_choices = [GROUP_NONE] + [g.group_id for g in existing_groups]
    
    # Group ID dropdown with explanatory text above
    disp.add_display_item(displayer.DisplayerItemAlert(
        f"<small class='text-muted'>{TEXT_VERSIONING_INFO}</small>",
        BSstyle.NONE
    ), column=0)
    
    current_group = file_version.group_id if file_version.group_id else GROUP_NONE
    disp.add_display_item(displayer.DisplayerItemInputSelect(
        id="group_id",
        text=str(LABEL_GROUP_ID),
        choices=group_choices,
        value=current_group
    ), column=0)
    
    # Get configured tags
    available_tags = file_manager.get_tags()
    
    # Tags multi-select with explanatory text above
    disp.add_display_item(displayer.DisplayerItemAlert(
        f"<small class='text-muted'>{TEXT_TAGS_INFO}</small>",
        BSstyle.NONE
    ), column=0)
    
    disp.add_display_item(displayer.DisplayerItemInputMultiSelect(
        id="tags",
        text=str(LABEL_TAGS),
        choices=available_tags,
        value=current_tags
    ), column=0)
    
    # Buttons
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [6, 6]))
    
    disp.add_display_item(displayer.DisplayerItemButton(
        id="save_btn",
        text=str(BUTTON_SAVE_CHANGES),
        icon="content-save",
        color=BSstyle.PRIMARY
    ), column=0)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        id="cancel_btn",
        text=str(BUTTON_CANCEL),
        icon="close-circle",
        link=url_for('file_manager_admin.index'),
        color=BSstyle.SECONDARY
    ), column=1)
    
    # Form should post back to this same URL
    form_action = url_for('file_manager_admin.edit_file', file_id=file_id)
    return render_template("base_content.j2", content=disp.display(), form_action=form_action)


@bp.route('/delete-multiple', methods=['POST'])
@require_permission(PERMISSION_MODULE, PERMISSION_DELETE)
def delete_multiple():
    """Handle multiple file deletion from checkboxes (redirects to confirm_delete)."""
    if not file_manager:
        return ERROR_FILE_MANAGER_NOT_INITIALIZED, STATUS_SERVER_ERROR
    
    # Get selected file IDs from form array
    file_ids_list = request.form.getlist('file_ids[]')
    
    if not file_ids_list:
        flash(MSG_NO_FILES_SELECTED, "warning")
        return redirect(url_for('file_manager_admin.index'))
    
    # Convert to comma-separated string for confirm_delete
    file_ids_str = ','.join(file_ids_list)
    
    # Redirect to confirmation page
    return redirect(url_for('file_manager_admin.confirm_delete') + f'?file_ids={file_ids_str}')


@bp.route('/confirm-delete', methods=['GET', 'POST'])
@require_permission(PERMISSION_MODULE, PERMISSION_DELETE)
def confirm_delete():
    """Confirmation page for deleting file(s).
    
    GET with file_id: Single file delete confirmation
    POST with file_ids_to_delete: Show multi-delete confirmation or execute deletion
    POST with confirm=true: Execute the deletion
    """
    if not file_manager:
        return ERROR_FILE_MANAGER_NOT_INITIALIZED, STATUS_SERVER_ERROR
    
    disp = displayer.Displayer()
    
    # Check if this is a confirmation (second POST) or deletion request
    is_executing = request.method == 'POST' and request.form.get(f'{TEXT_CONFIRM_DELETE}.confirm_deletion') == 'true'
    
    if is_executing:
        # Execute deletion (second POST)
        data = utilities.util_post_to_json(request.form.to_dict())
        data = data["Confirm Delete"]
        file_ids_str = data.get('file_ids_to_delete', '')
        # Always delete all versions (full deletion)
        delete_all_versions = True
        if not file_ids_str:
            return "No files specified", STATUS_BAD_REQUEST
        
        try:
            file_ids = [int(fid) for fid in file_ids_str.split(',') if fid.strip()]
        except ValueError:
            return "Invalid file IDs", STATUS_BAD_REQUEST
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
                    return "Invalid file IDs", STATUS_BAD_REQUEST
            else:
                return "No files specified", STATUS_BAD_REQUEST
        else:
            # First POST from inline delete form
            data = utilities.util_post_to_json(request.form.to_dict())
            multi_file_ids = data.get('file_ids_to_delete', '')
            if multi_file_ids:
                try:
                    file_ids = [int(fid) for fid in multi_file_ids.split(',') if fid.strip()]
                except ValueError:
                    return "Invalid file IDs", STATUS_BAD_REQUEST
            else:
                return "No files specified", STATUS_BAD_REQUEST
        
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
                    'group_id': file_meta.group_id or GROUP_NONE
                })
        
        if not files_to_delete:
            return "No valid files found", STATUS_NOT_FOUND
        
        # Build confirmation page
        disp.add_generic(TEXT_CONFIRM_DELETE, display=False)
        
        disp.add_breadcrumb(TEXT_BREADCRUMB_FILE_MANAGER, "file_manager_admin.index", [])
        disp.add_breadcrumb(TEXT_BREADCRUMB_CONFIRM_DELETE, "file_manager_admin.confirm_delete", [])
        
        # Warning message
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        
        if len(files_to_delete) == 1:
            warning_html = DELETE_CONFIRM_SINGLE.format(filename=files_to_delete[0]['filename'])
        else:
            warning_html = DELETE_CONFIRM_MULTIPLE.format(count=len(files_to_delete))
        
        disp.add_display_item(displayer.DisplayerItemAlert(warning_html, BSstyle.ERROR, icon="alert", title=str(TITLE_CONFIRM_DELETION)), column=0)
        
        # File list table
        if len(files_to_delete) > 1:
            disp.add_master_layout(displayer.DisplayerLayout(
                displayer.Layouts.TABLE,
                [TABLE_HEADER_FILENAME, TABLE_HEADER_GROUP_ID, TABLE_HEADER_SIZE, TABLE_HEADER_UPLOADED],
                subtitle=str(LABEL_FILES_TO_DELETE)
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
        has_versioned_files = any(f['group_id'] != GROUP_NONE for f in files_to_delete)
        
        if has_versioned_files:
            # Inform user that all versions will be deleted
            disp.add_display_item(displayer.DisplayerItemAlert(
                f"<i class='mdi mdi-information-outline'></i> {TEXT_VERSIONS_DELETED_WARNING}",
                BSstyle.INFO
            ), column=0)
        
        # Buttons
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [6, 6]))
        
        disp.add_display_item(displayer.DisplayerItemButton(
            id="confirm_delete_btn",
            text=str(BUTTON_YES_DELETE),
            icon="delete-forever",
            color=BSstyle.ERROR
        ), column=0)
        
        disp.add_display_item(displayer.DisplayerItemButton(
            id="cancel_btn",
            text=str(BUTTON_CANCEL),
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
    disp.add_generic(TEXT_DELETION_COMPLETE)
    disp.set_title(TEXT_DELETION_COMPLETE)
    
    disp.add_breadcrumb(TEXT_BREADCRUMB_FILE_MANAGER, "file_manager_admin.index", [])
    disp.add_breadcrumb(TEXT_BREADCRUMB_DELETION_COMPLETE, "file_manager_admin.confirm_delete", [])
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    
    if failed_files:
        result_html = DELETE_RESULT_PARTIAL.format(deleted_count=deleted_count, failed_count=len(failed_files))
        disp.add_display_item(displayer.DisplayerItemAlert(result_html, BSstyle.WARNING, icon="check-circle", title=str(TITLE_PARTIALLY_COMPLETE)), column=0)
    else:
        result_html = DELETE_RESULT_SUCCESS.format(deleted_count=deleted_count)
        disp.add_display_item(displayer.DisplayerItemAlert(result_html, BSstyle.SUCCESS, icon="check-circle", title=str(TITLE_SUCCESS)), column=0)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        id="return_btn",
        text=str(BUTTON_RETURN_FILE_MANAGER),
        icon="arrow-left",
        link=url_for('file_manager_admin.index'),
        color=BSstyle.PRIMARY
    ), column=0)
    
    return render_template("base_content.j2", content=disp.display())


@bp.route('/version-history/<group_id>/<filename>', methods=['GET'])
@require_permission(PERMISSION_MODULE, PERMISSION_VIEW)
def version_history(group_id, filename):
    """Display version history page for a file.
    
    Args:
        group_id: Group identifier (use '(none)' for files without a group)
        filename: Filename
    
    Returns:
        HTML page with version history table
    """
    if not file_manager:
        return ERROR_FILE_MANAGER_NOT_INITIALIZED, STATUS_SERVER_ERROR
    
    try:
        # Convert '(none)' placeholder back to None for files without a group
        actual_group_id = None if group_id == GROUP_NONE else group_id
        versions = file_manager.get_file_versions(actual_group_id, filename)
        
        # Build version history page
        disp = displayer.Displayer()
        disp.add_generic(TEXT_VERSION_HISTORY_FILE.format(filename=filename), display=False)
        disp.set_title(TEXT_VERSION_HISTORY_FILE.format(filename=filename))
        disp.add_breadcrumb(TEXT_BREADCRUMB_FILE_MANAGER, "file_manager_admin.index", [])
        disp.add_breadcrumb(TEXT_BREADCRUMB_VERSION_HISTORY, "file_manager_admin.version_history", [group_id, filename])
                
        # Version table
        if versions:
            disp.add_master_layout(displayer.DisplayerLayout(
                displayer.Layouts.TABLE,
                [TABLE_HEADER_PREVIEW, TABLE_HEADER_VERSION, TABLE_HEADER_STATUS, TABLE_HEADER_SIZE, TABLE_HEADER_CHECKSUM, TABLE_HEADER_UPLOADED, LABEL_UPLOADED_BY, TABLE_HEADER_ACTIONS],
                subtitle=str(LABEL_ALL_VERSIONS)
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
                disp.add_display_item(displayer.DisplayerItemBadge(BADGE_VERSION.format(version=version_num), BSstyle.PRIMARY), 
                                    column=1, line=idx)
                
                # Status (current or archived)
                if version.get('is_current'):
                    disp.add_display_item(displayer.DisplayerItemBadge(BADGE_CURRENT, BSstyle.SUCCESS), 
                                        column=2, line=idx)
                else:
                    disp.add_display_item(displayer.DisplayerItemBadge(BADGE_ARCHIVED, BSstyle.SECONDARY), 
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
                    "tooltip": str(TOOLTIP_DOWNLOAD_VERSION)
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
                        "tooltip": str(TOOLTIP_RESTORE_VERSION.format(version=version_num))
                    })
                
                # Delete single version button (only if more than one version exists)
                if len(versions) > 1:
                    delete_version_url = url_for('file_manager_admin.delete_single_version',
                                                file_id=file_id,
                                                group_id=group_id,
                                                filename=filename)
                    actions.append({
                        "type": "custom",
                        "url": delete_version_url,
                        "icon": "mdi mdi-delete",
                        "style": "danger",
                        "tooltip": str(TOOLTIP_DELETE_VERSION.format(version=version_num)),
                        "confirm": f"Delete version {version_num} of {filename}?"
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
            text=str(BUTTON_BACK_FILE_MANAGER),
            icon="arrow-left",
            link=url_for('file_manager_admin.index'),
            color=BSstyle.SECONDARY
        ), column=0)
        
        return render_template("base_content.j2", content=disp.display())
        
    except Exception as e:
        logger.error(f"Failed to display version history: {e}", exc_info=True)
        
        disp = displayer.Displayer()
        disp.add_generic(ERROR_LOADING_VERSION_HISTORY)
        disp.set_title(ERROR_LOADING_VERSION_HISTORY)
        disp.add_breadcrumb(TEXT_BREADCRUMB_FILE_MANAGER, "file_manager_admin.index", [])
        
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        disp.add_display_item(displayer.DisplayerItemAlert(
            f"<h4>{ERROR_LOADING_VERSION_HISTORY}</h4><p>{str(e)}</p>",
            BSstyle.ERROR
        ), column=0)
        
        return render_template("base_content.j2", content=disp.display()), 500


@bp.route('/restore-version/<int:target_version_id>/<group_id>/<filename>', methods=['GET'])
@require_permission(PERMISSION_MODULE, PERMISSION_EDIT)
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
        flash(MSG_FILE_MANAGER_NOT_INIT, "error")
        return redirect(url_for('file_manager_admin.index'))
    
    try:
        # Get target version to find group_id and filename
        from ..modules.file_manager import FileVersion
        
        session_db = file_manager.db_session
        target_version = session_db.query(FileVersion).filter_by(id=target_version_id).first()
        
        if not target_version:
            flash(MSG_TARGET_VERSION_NOT_FOUND, "error")
            return redirect(url_for('file_manager_admin.index'))
        
        # Find current version in same group
        current_version = session_db.query(FileVersion).filter_by(
            group_id=target_version.group_id,
            filename=target_version.filename,
            is_current=True
        ).first()
        
        if not current_version:
            flash(MSG_CURRENT_VERSION_NOT_FOUND, "error")
            return redirect(url_for('file_manager_admin.index'))
        
        # Restore version
        restored = file_manager.restore_version(current_version.id, target_version_id)
        
        logger.info(f"Version restored by {session.get('user', 'GUEST')}: {restored.filename}")
        flash(MSG_VERSION_RESTORED, "success")
        
    except Exception as e:
        logger.error(f"Failed to restore version: {e}", exc_info=True)
        flash(MSG_RESTORE_VERSION_ERROR.format(error=str(e)), "error")
    
    # Redirect back to version history page
    return redirect(url_for('file_manager_admin.version_history', group_id=group_id, filename=filename))


@bp.route('/delete-single-version/<int:file_id>/<group_id>/<filename>', methods=['GET'])
@require_permission(PERMISSION_MODULE, PERMISSION_DELETE)
def delete_single_version(file_id, group_id, filename):
    """Delete a single version of a file (not all versions).
    
    Args:
        file_id: Database ID of the specific version to delete
        group_id: Group identifier for redirect
        filename: Filename for redirect
    
    Returns:
        Redirect to version history with flash message
    """
    if not file_manager:
        flash(MSG_FILE_MANAGER_NOT_INIT, "error")
        return redirect(url_for('file_manager_admin.index'))
    
    try:
        # Delete only this specific version (delete_all_versions=False)
        success = file_manager.delete_file(file_id, delete_all_versions=False)
        
        if success:
            logger.info(f"Single version deleted by {session.get('user', 'GUEST')}: ID {file_id}")
            flash(MSG_VERSION_DELETED, "success")
        else:
            flash(MSG_DELETE_VERSION_FAILED, "error")
        
    except Exception as e:
        logger.error(f"Failed to delete single version {file_id}: {e}", exc_info=True)
        flash(MSG_DELETE_VERSION_ERROR.format(error=str(e)), "error")
    
    # Check if there are remaining versions
    actual_group_id = None if group_id == GROUP_NONE else group_id
    remaining_versions = file_manager.get_file_versions(actual_group_id, filename)
    
    if remaining_versions:
        # Redirect back to version history page
        return redirect(url_for('file_manager_admin.version_history', group_id=group_id, filename=filename))
    else:
        # No more versions, redirect to main file manager
        flash(MSG_VERSIONS_DELETED, "info")
        return redirect(url_for('file_manager_admin.index'))
