"""
File Manager Demo Page

Demonstrates file upload, listing, thumbnail display, and deletion functionality.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from src.modules import displayer, utilities
from src.modules.file_manager import FileManager
from src.modules import settings
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

demo_file_bp = Blueprint('demo_files', __name__)


def require_login(f):
    """Decorator to require login for demo pages."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('common.login'))
        return f(*args, **kwargs)
    return decorated_function


@demo_file_bp.route('/file-manager-demo')
@require_login
def file_manager_demo():
    """File manager demo landing page with overview and navigation."""
    disp = displayer.Displayer()
    disp.add_generic("File Manager Demo")
    disp.set_title("File Manager Demo")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("File Manager Demo", "demo_files.file_manager_demo", [])
    
    # Overview section
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    
    overview_html = """
    <div class="card">
        <div class="card-body">
            <h4><i class="bi bi-folder2-open"></i> File Manager Features</h4>
            <p>This demo showcases the framework's file management capabilities:</p>
            <ul>
                <li><strong>Secure Upload:</strong> File type and size validation</li>
                <li><strong>Thumbnails:</strong> Automatic generation for images and PDFs</li>
                <li><strong>Categories:</strong> Organize files by category/subcategory</li>
                <li><strong>Gallery View:</strong> Visual file browser with previews</li>
                <li><strong>Soft Delete:</strong> Move files to trash instead of permanent deletion</li>
            </ul>
        </div>
    </div>
    """
    
    disp.add_display_item(displayer.DisplayerItemAlert(overview_html, displayer.BSstyle.NONE), column=0)
    
    # Navigation cards
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.HORIZONTAL, [6, 6]))
    
    upload_card = f"""
    <div class="card h-100">
        <div class="card-body text-center">
            <i class="bi bi-upload" style="font-size: 3rem; color: var(--bs-primary);"></i>
            <h5 class="card-title mt-3">Upload Files</h5>
            <p class="card-text">Upload and manage files with automatic thumbnail generation</p>
            <a href="{url_for('demo_files.upload_demo')}" class="btn btn-primary">
                <i class="bi bi-upload"></i> Go to Upload
            </a>
        </div>
    </div>
    """
    
    admin_card = f"""
    <div class="card h-100">
        <div class="card-body text-center">
            <i class="bi bi-gear" style="font-size: 3rem; color: var(--bs-success);"></i>
            <h5 class="card-title mt-3">File Administration</h5>
            <p class="card-text">Manage files, view versions, edit metadata, and history</p>
            <a href="{url_for('demo_files.admin_demo')}" class="btn btn-success">
                <i class="bi bi-gear"></i> Manage Files
            </a>
        </div>
    </div>
    """
    
    disp.add_display_item(displayer.DisplayerItemAlert(upload_card, displayer.BSstyle.NONE), column=0)
    disp.add_display_item(displayer.DisplayerItemAlert(admin_card, displayer.BSstyle.NONE), column=1)
    
    return render_template('base_content.j2', content=disp.display())


@demo_file_bp.route('/upload-demo', methods=['GET', 'POST'])
@require_login
def upload_demo():
    """File upload demonstration."""
    disp = displayer.Displayer()
    disp.add_generic("Upload Demo")
    disp.set_title("File Upload Demo")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("File Manager Demo", "demo_files.file_manager_demo", [])
    disp.add_breadcrumb("Upload", "demo_files.upload_demo", [])
    
    # Initialize file manager
    file_mgr = FileManager(settings.settings_manager)
    
    # Handle file upload
    if request.method == 'POST':
        try:
            
            # Framework prefixes input IDs with page title
            file_key = 'Upload Demo.demo_file'
            
            if file_key in request.files:
                file = request.files[file_key]
                
                if file.filename:
                    # Get form data
                    data_in = utilities.util_post_to_json(request.form.to_dict())
                    upload_category = data_in.get("Upload Demo", {}).get("category", "demo")
                    group_id = data_in.get("Upload Demo", {}).get("group_id", "")
                    tags_str = data_in.get("Upload Demo", {}).get("tags", "")
                    
                    # Parse tags
                    tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else None
                    
                    # Upload file with new parameters
                    metadata = file_mgr.upload_file(
                        file, 
                        category=upload_category, 
                        subcategory="uploads",
                        group_id=group_id,
                        tags=tags
                    )
                    
                    # Show success with metadata
                    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
                    
                    success_html = f"""
                    <h5><i class='bi bi-check-circle'></i> File Uploaded Successfully!</h5>
                    <hr>
                    <div class="row">
                        <div class="col-md-6">
                            <strong>Filename:</strong> {metadata['name']}<br>
                            <strong>Group ID:</strong> {metadata['group_id'] or '(none)'}<br>
                            <strong>Version:</strong> {metadata['version']}<br>
                            <strong>Size:</strong> {metadata['size']} bytes ({metadata['size'] / 1024:.2f} KB)<br>
                            <strong>Uploaded:</strong> {metadata['uploaded_at']}<br>
                            <strong>Tags:</strong> {', '.join(metadata['tags']) if metadata['tags'] else '(none)'}<br>
                            <strong>Checksum:</strong> {metadata['checksum'][:16]}...
                        </div>
                        <div class="col-md-6">
                    """
                    
                    # Show thumbnails if generated
                    if 'thumb_150x150' in metadata:
                        success_html += f"""
                            <strong>Thumbnails Generated:</strong><br>
                            <img src="{url_for('file_handler.download', filepath=metadata['thumb_150x150'])}?inline=true" 
                                 alt="Small thumb" class="img-thumbnail m-1" style="max-width: 150px;">
                        """
                        if 'thumb_300x300' in metadata:
                            success_html += f"""
                            <img src="{url_for('file_handler.download', filepath=metadata['thumb_300x300'])}?inline=true" 
                                 alt="Medium thumb" class="img-thumbnail m-1" style="max-width: 150px;">
                            """
                    
                    success_html += """
                        </div>
                    </div>
                    <hr>
                    <a href="{}" class="btn btn-primary">
                        <i class='bi bi-download'></i> Download File
                    </a>
                    <a href="{}" class="btn btn-success">
                        <i class='bi bi-gear'></i> Manage Files
                    </a>
                    """.format(
                        url_for('file_handler.download', filepath=metadata['path']),
                        url_for('demo_files.admin_demo')
                    )
                    
                    disp.add_display_item(displayer.DisplayerItemAlert(success_html, displayer.BSstyle.SUCCESS), column=0)
                else:
                    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
                    disp.add_display_item(displayer.DisplayerItemAlert(
                        "<strong>Error:</strong> No file selected",
                        displayer.BSstyle.WARNING
                    ), column=0)
            else:
                disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
                disp.add_display_item(displayer.DisplayerItemAlert(
                    "<strong>Error:</strong> No file in request",
                    displayer.BSstyle.WARNING
                ), column=0)
                
        except ValueError as e:
            # Validation error
            disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
            disp.add_display_item(displayer.DisplayerItemAlert(
                f"<strong>Upload Failed:</strong> {e}",
                displayer.BSstyle.ERROR
            ), column=0)
            
        except Exception as e:
            logger.error(f"Upload error: {e}", exc_info=True)
            disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
            disp.add_display_item(displayer.DisplayerItemAlert(
                f"<strong>System Error:</strong> {e}",
                displayer.BSstyle.ERROR
            ), column=0)
    
    # Upload form
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle="Upload a File"))
    
    # Category dropdown (fixed: use DisplayerItemInputSelect instead of InputString)
    categories = file_mgr.get_categories()
    disp.add_display_item(displayer.DisplayerItemInputSelect(
        id="category",
        text="Category",
        choices=categories,
        value="demo"
    ), column=0)
    
    # Group ID input
    disp.add_display_item(displayer.DisplayerItemInputString(
        id="group_id",
        text="Group ID (optional - for versioning)",
        value="demo_group"
    ), column=0)
    
    # Tags input
    disp.add_display_item(displayer.DisplayerItemInputString(
        id="tags",
        text="Tags (comma-separated, optional)",
        value=""
    ), column=0)
    
    disp.add_display_item(displayer.DisplayerItemInputFile(
        "demo_file", "Select File"
    ), column=0)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.HORIZONTAL, [6, 6]))
    
    disp.add_display_item(displayer.DisplayerItemButton(
        id="upload_btn",
        text="Upload File",
        icon="upload",
        color=displayer.BSstyle.PRIMARY
    ), column=0)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        id="back_btn",
        text="Back to Demo Home",
        icon="arrow-left",
        link=url_for('demo_files.file_manager_demo'),
        color=displayer.BSstyle.SECONDARY
    ), column=1)
    
    return render_template("base_content.j2", content=disp.display(), target="demo_files.upload_demo")


@demo_file_bp.route('/admin-demo')
@require_login
def admin_demo():
    """File administration with version management and history."""
    disp = displayer.Displayer()
    disp.add_generic("File Administration")
    disp.set_title("File Administration")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("File Manager Demo", "demo_files.file_manager_demo", [])
    disp.add_breadcrumb("Admin", "demo_files.admin_demo", [])
    
    try:
        file_mgr = FileManager(settings.settings_manager)
        
        # Get filters
        group_id = request.args.get('group_id', None)
        tag = request.args.get('tag', None)
        
        # List files from database (Phase 3)
        files = file_mgr.list_files_from_db(
            group_id=group_id if group_id else None,
            tag=tag if tag else None
        )
        
        if files:
            # Statistics
            total_size = sum(f['size'] for f in files)
            unique_groups = len(set(f.get('group_id', '') for f in files if f.get('group_id')))
            
            disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.HORIZONTAL, [3, 3, 3, 3]))
            
            disp.add_display_item(displayer.DisplayerItemAlert(
                f"<h4 class='text-center'>{len(files)}</h4><p class='text-center mb-0'>Files</p>",
                displayer.BSstyle.INFO
            ), column=0)
            
            disp.add_display_item(displayer.DisplayerItemAlert(
                f"<h4 class='text-center'>{total_size / (1024*1024):.2f} MB</h4><p class='text-center mb-0'>Total Size</p>",
                displayer.BSstyle.SUCCESS
            ), column=1)
            
            disp.add_display_item(displayer.DisplayerItemAlert(
                f"<h4 class='text-center'>{unique_groups}</h4><p class='text-center mb-0'>Groups</p>",
                displayer.BSstyle.PRIMARY
            ), column=2)
            
            disp.add_display_item(displayer.DisplayerItemAlert(
                f"<h4 class='text-center'>{tag or 'All'}</h4><p class='text-center mb-0'>Tag Filter</p>",
                displayer.BSstyle.WARNING
            ), column=3)
            
            # File grid with admin actions
            disp.add_master_layout(displayer.DisplayerLayout(
                displayer.Layouts.TABLE,
                ["Preview", "Filename", "Group ID", "Tags", "Version", "Size", "Uploaded", "Actions"],
                subtitle="File Administration"
            ))
            
            for idx, file_meta in enumerate(files):
                # Preview column
                ext = Path(file_meta['name']).suffix.lower()
                
                if 'thumb_150x150' in file_meta:
                    # Show thumbnail
                    preview_html = f"""
                    <a href="{url_for('file_handler.download_by_id', file_id=file_meta.get('id', 0))}" target="_blank">
                        <img src="{url_for('file_handler.download', filepath=file_meta['thumb_150x150'])}?inline=true" 
                             alt="{file_meta['name']}" class="img-thumbnail" style="max-width: 120px; max-height: 120px;">
                    </a>
                    """
                else:
                    # Show file icon
                    icon_map = {
                        '.pdf': 'bi-file-earmark-pdf-fill text-danger',
                        '.doc': 'bi-file-earmark-word-fill text-primary',
                        '.docx': 'bi-file-earmark-word-fill text-primary',
                        '.xls': 'bi-file-earmark-excel-fill text-success',
                        '.xlsx': 'bi-file-earmark-excel-fill text-success',
                        '.zip': 'bi-file-earmark-zip-fill text-secondary',
                        '.txt': 'bi-file-earmark-text',
                    }
                    icon = icon_map.get(ext, 'bi-file-earmark')
                    preview_html = f"<i class='bi {icon}' style='font-size: 3rem;'></i>"
                
                disp.add_display_item(displayer.DisplayerItemAlert(preview_html, displayer.BSstyle.NONE), 
                                    column=0, line=idx)
                
                # Filename column
                disp.add_display_item(displayer.DisplayerItemText(file_meta['name']),
                                    column=1, line=idx)
                
                # Group ID column - editable
                group_id_val = file_meta.get('group_id', '') or '(none)'
                group_id_html = f"""
                <span id="group-display-{idx}">{group_id_val}</span>
                <a href="javascript:editGroupId({idx}, '{file_meta['id']}', '{group_id_val}')" 
                   class="ms-2" title="Edit Group ID">
                    <i class="bi bi-pencil-square"></i>
                </a>
                """
                disp.add_display_item(displayer.DisplayerItemAlert(group_id_html, displayer.BSstyle.NONE),
                                    column=2, line=idx)
                
                # Tags column
                tags_display = ', '.join(file_meta.get('tags', [])) or '(none)'
                disp.add_display_item(displayer.DisplayerItemText(tags_display),
                                    column=3, line=idx)
                
                # Version column - show version count and current version
                if file_meta.get('group_id'):
                    try:
                        versions = file_mgr.get_file_versions(file_meta['group_id'], file_meta['name'])
                        current_ver = next((i+1 for i, v in enumerate(reversed(versions)) if v['is_current']), len(versions))
                        version_display = f"v{current_ver}/{len(versions)}"
                    except:
                        version_display = "v1/1"
                else:
                    version_display = "v1/1"
                disp.add_display_item(displayer.DisplayerItemText(version_display),
                                    column=4, line=idx)
                
                # Size column
                size_str = f"{file_meta['size'] / 1024:.1f} KB" if file_meta['size'] < 1024*1024 else f"{file_meta['size'] / (1024*1024):.2f} MB"
                disp.add_display_item(displayer.DisplayerItemText(size_str),
                                    column=5, line=idx)
                
                # Uploaded date column
                uploaded_date = file_meta['uploaded_at'][:16].replace('T', ' ')
                disp.add_display_item(displayer.DisplayerItemText(uploaded_date),
                                    column=6, line=idx)
                
                # Actions column - enhanced with version management
                actions = [
                    {
                        "type": "download",
                        "url": url_for('file_handler.download_by_id', file_id=file_meta['id']),
                        "icon": "mdi mdi-download",
                        "style": "primary",
                        "tooltip": "Download file"
                    }
                ]
                
                # Add history button if file has group_id (versioning enabled)
                if file_meta.get('group_id'):
                    actions.append({
                        "type": "custom",
                        "url": f"javascript:viewHistory('{file_meta['group_id']}', '{file_meta['name']}')",
                        "icon": "mdi mdi-history",
                        "style": "info",
                        "tooltip": "View version history"
                    })
                
                # Add delete button
                actions.append({
                    "type": "delete",
                    "url": f"javascript:deleteFile('{file_meta['path']}', {idx})",
                    "icon": "mdi mdi-delete",
                    "style": "danger",
                    "tooltip": "Delete file"
                })
                
                disp.add_display_item(
                    displayer.DisplayerItemActionButtons(
                        id=f"file_actions_{idx}",
                        actions=actions,
                        size="sm"
                    ),
                    column=7, line=idx
                )
                
                # Add status div for feedback
                disp.add_display_item(
                    displayer.DisplayerItemText(f'<div id="status-{idx}"></div>'),
                    column=2, line=idx
                )
            
            # Add admin scripts
            admin_scripts = """
            <script>
            function editGroupId(idx, fileId, currentGroupId) {
                const newGroupId = prompt('Edit Group ID:\\n(Leave empty for standalone file)', currentGroupId === '(none)' ? '' : currentGroupId);
                if (newGroupId === null) return; // Cancelled
                
                const statusDiv = document.getElementById('status-' + idx);
                statusDiv.innerHTML = '<small class="text-info">Updating...</small>';
                
                fetch('/files/update_group_id', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({file_id: fileId, group_id: newGroupId})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('group-display-' + idx).textContent = newGroupId || '(none)';
                        statusDiv.innerHTML = '<small class="text-success">✓ Updated</small>';
                        setTimeout(() => statusDiv.innerHTML = '', 2000);
                    } else {
                        statusDiv.innerHTML = '<small class="text-danger">Error: ' + data.error + '</small>';
                    }
                })
                .catch(error => {
                    statusDiv.innerHTML = '<small class="text-danger">Failed: ' + error + '</small>';
                });
            }
            
            function viewHistory(groupId, filename) {
                window.location.href = `/files/versions/${groupId}/${filename}`;
            }
            
            function deleteFile(filepath, idx) {
                if (!confirm('Delete this file?\\n\\nFile: ' + filepath + '\\n\\nIt will be moved to trash.')) {
                    return;
                }
                
                const statusDiv = document.getElementById('status-' + idx);
                statusDiv.innerHTML = '<small class="text-info">Deleting...</small>';
                
                fetch('/files/delete/' + filepath, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        statusDiv.innerHTML = '<small class="text-success">✓ Deleted</small>';
                        setTimeout(() => location.reload(), 1000);
                    } else {
                        statusDiv.innerHTML = '<small class="text-danger">Error: ' + data.error + '</small>';
                    }
                })
                .catch(error => {
                    statusDiv.innerHTML = '<small class="text-danger">Failed: ' + error + '</small>';
                });
            }
            </script>
            """
            
            # Add script as hidden HTML item at the end
            disp.add_display_item(displayer.DisplayerItemText(admin_scripts), column=0)
            
        else:
            # No files
            disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
            disp.add_display_item(displayer.DisplayerItemAlert(
                "<p class='text-center mb-0'>No files found.</p>"
                "<p class='text-center'><a href='" + url_for('demo_files.upload_demo') + "' class='btn btn-primary mt-2'>"
                "<i class='bi bi-upload'></i> Upload Files</a></p>",
                displayer.BSstyle.INFO
            ), column=0)
        
        # Back button
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        disp.add_display_item(displayer.DisplayerItemButton(
            "back_btn", "Back to Demo Home",
            icon="arrow-left",
            link=url_for('demo_files.file_manager_demo'),
            color=displayer.BSstyle.SECONDARY
        ), column=0)
        
    except Exception as e:
        logger.error(f"Admin error: {e}", exc_info=True)
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        disp.add_display_item(displayer.DisplayerItemAlert(
            f"<strong>Error loading admin page:</strong> {e}",
            displayer.BSstyle.ERROR
        ), column=0)
    
    return render_template("base_content.j2", content=disp.display())


# Export blueprint
bp = demo_file_bp
