"""
File Manager Admin Page - Flask blueprint for file browsing and management UI.

This module provides a web interface for browsing, searching, and managing uploaded files.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

bp = Blueprint("file_manager_admin", __name__, url_prefix="/file_manager")

# File manager instance will be injected by main.py
file_manager = None


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
        # Get file list (no filtering by URL params needed - DataTables handles it)
        files = file_manager.list_files()
        
        # Calculate statistics
        total_files = len(files)
        total_size = sum(f['size'] for f in files)
        total_size_mb = total_size / (1024 * 1024)
        
        # Get unique categories
        categories = set()
        for f in files:
            path_parts = f['path'].split('/')
            if len(path_parts) > 0:
                categories.add(path_parts[0])
        
        # Statistics section
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.HORIZONTAL, [4, 4, 4]))
        
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
            f"<h3 class='text-center'>{len(categories)}</h3>"
            f"<p class='text-center mb-0'>Categories</p>",
            BSstyle.PRIMARY
        ), column=2)
        
        # File list table with DataTables
        if files:
            # Add table layout
            table_layout_id = disp.add_master_layout(displayer.DisplayerLayout(
                displayer.Layouts.TABLE,
                ["Preview", "Filename", "Path", "Size", "Uploaded", "Actions"],
                subtitle="Files",
                datatable_config={
                    "table_id": "file_list_table",
                    "mode": displayer.TableMode.INTERACTIVE,
                    "page_length": 25,
                    "searchable": True
                }
            ))
            
            # Populate table rows
            for idx, file_meta in enumerate(files):
                # Preview column (thumbnail or icon)
                preview_html = _generate_preview_html(file_meta)
                disp.add_display_item(displayer.DisplayerItemAlert(preview_html, displayer.BSstyle.NONE), 
                                    column=0, line=idx, layout_id=table_layout_id)
                
                # Filename
                disp.add_display_item(displayer.DisplayerItemText(file_meta['name']), 
                                    column=1, line=idx, layout_id=table_layout_id)
                
                # Path
                disp.add_display_item(displayer.DisplayerItemText(file_meta['path']), 
                                    column=2, line=idx, layout_id=table_layout_id)
                
                # Size (human readable)
                size_str = _format_file_size(file_meta['size'])
                disp.add_display_item(displayer.DisplayerItemText(size_str), 
                                    column=3, line=idx, layout_id=table_layout_id)
                
                # Upload date
                upload_date = _format_date(file_meta['uploaded_at'])
                disp.add_display_item(displayer.DisplayerItemText(upload_date), 
                                    column=4, line=idx, layout_id=table_layout_id)
                
                # Actions (download + delete buttons)
                download_url = url_for('file_handler.download', filepath=file_meta['path'])
                actions_html = f"""
                <a href="{download_url}" class="btn btn-sm btn-primary" title="Download">
                    <i class="bi bi-download"></i>
                </a>
                <button class="btn btn-sm btn-danger" 
                        onclick="deleteFile('{file_meta['path']}')" title="Delete">
                    <i class="bi bi-trash"></i>
                </button>
                """
                disp.add_display_item(displayer.DisplayerItemAlert(actions_html, displayer.BSstyle.NONE), 
                                    column=5, line=idx, layout_id=table_layout_id)
        else:
            disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
            disp.add_display_item(displayer.DisplayerItemAlert(
                "<p class='text-center mb-0'>No files found. Upload files to get started!</p>",
                BSstyle.INFO
            ), column=0)
        
        # Add delete confirmation script
        delete_script = """
        <script>
        function deleteFile(filepath) {
            if (!confirm('Are you sure you want to delete this file?\\n\\nFile: ' + filepath + '\\n\\nThis will move it to trash.')) {
                return;
            }
            
            fetch('/files/delete/' + filepath, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('File deleted successfully');
                    location.reload();
                } else {
                    alert('Error: ' + data.error);
                }
            })
            .catch(error => {
                alert('Failed to delete file: ' + error);
            });
        }
        </script>
        """
        
        # Add script as hidden HTML item
        disp.add_display_item(displayer.DisplayerItemText(delete_script), column=0)
        
        return render_template("base_content.j2", content=disp.display())
        
    except Exception as e:
        logger.error(f"File manager index error: {e}", exc_info=True)
        
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        disp.add_display_item(displayer.DisplayerItemAlert(
            f"<h4>Error Loading Files</h4><p>{str(e)}</p>",
            BSstyle.ERROR
        ), column=0)
        
        return render_template("base_content.j2", content=disp.display())


def _generate_preview_html(file_meta: dict) -> str:
    """Generate preview HTML for a file (thumbnail or icon).
    
    Args:
        file_meta: File metadata dictionary
        
    Returns:
        HTML string for preview
    """
    # Check if thumbnail exists
    if 'thumb_150x150' in file_meta:
        thumb_path = file_meta['thumb_150x150']
        return f"""
        <img src="{url_for('file_handler.download', filepath=thumb_path, inline='true')}" 
             alt="Preview" class="img-thumbnail" style="max-width: 60px; max-height: 60px;">
        """
    
    # Otherwise show file type icon
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


@bp.route("/upload_form", methods=["GET"])
@require_file_manager_permission
def upload_form():
    """Display file upload form."""
    displayer, BSstyle, get_home_endpoint = _get_displayer_modules()
    
    disp = displayer.Displayer()
    disp.add_generic("Upload Files")
    disp.set_title("File Manager - Upload")
    disp.add_breadcrumb("Home", get_home_endpoint(), [])
    disp.add_breadcrumb("File Manager", "file_manager_admin.index", [])
    disp.add_breadcrumb("Upload", "file_manager_admin.upload_form", [])
    
    # Get available categories
    categories = file_manager.get_categories() if file_manager else ["general"]
    
    # Build category options HTML
    category_options = ""
    for cat in categories:
        selected = 'selected' if cat == 'general' else ''
        category_options += f'<option value="{cat}" {selected}>{cat.title()}</option>\n'
    
    # Upload form
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle="Upload New Files"))
    
    upload_form_html = f"""
    <form id="uploadForm" enctype="multipart/form-data" class="needs-validation" novalidate>
        <div class="mb-3">
            <label for="fileInput" class="form-label">Select File(s)</label>
            <input type="file" class="form-control" id="fileInput" name="file" required multiple>
            <div class="form-text">Maximum file size: 50 MB. Allowed types: PDF, Images, Office documents, Archives.</div>
        </div>
        
        <div class="mb-3">
            <label for="categoryInput" class="form-label">Category</label>
            <select class="form-select" id="categoryInput" name="category" required>
                {category_options}
            </select>
            <div class="form-text">Choose a category to organize your files</div>
        </div>
        
        <div class="mb-3">
            <label for="subcategoryInput" class="form-label">Subcategory (Optional)</label>
            <input type="text" class="form-control" id="subcategoryInput" name="subcategory" 
                   placeholder="e.g., 2025, user123">
            <div class="form-text">Further organize files within category (e.g., year, project name, user ID)</div>
        </div>
        
        <div class="mb-3">
            <div class="progress" style="display:none;" id="uploadProgress">
                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                     role="progressbar" style="width: 0%"></div>
            </div>
        </div>
        
        <button type="submit" class="btn btn-primary" id="uploadBtn">
            <i class="bi bi-upload"></i> Upload Files
        </button>
        <a href="{url_for('file_manager_admin.index')}" class="btn btn-secondary">
            <i class="bi bi-x-circle"></i> Cancel
        </a>
    </form>
    
    <div id="uploadResults" class="mt-3"></div>
    
    <script>
    document.getElementById('uploadForm').addEventListener('submit', async function(e) {{
        e.preventDefault();
        
        const formData = new FormData();
        const fileInput = document.getElementById('fileInput');
        const category = document.getElementById('categoryInput').value;
        const subcategory = document.getElementById('subcategoryInput').value;
        const resultsDiv = document.getElementById('uploadResults');
        const progressBar = document.getElementById('uploadProgress');
        const uploadBtn = document.getElementById('uploadBtn');
        
        resultsDiv.innerHTML = '';
        uploadBtn.disabled = true;
        
        // Upload each file separately
        const files = fileInput.files;
        let successCount = 0;
        let errorCount = 0;
        
        for (let i = 0; i < files.length; i++) {{
            const file = files[i];
            const fileData = new FormData();
            fileData.append('file', file);
            fileData.append('category', category);
            fileData.append('subcategory', subcategory);
            
            try {{
                progressBar.style.display = 'block';
                progressBar.querySelector('.progress-bar').style.width = ((i / files.length) * 100) + '%';
                
                const response = await fetch('/files/upload', {{
                    method: 'POST',
                    body: fileData
                }});
                
                const data = await response.json();
                
                if (data.success) {{
                    successCount++;
                    resultsDiv.innerHTML += `
                        <div class="alert alert-success alert-dismissible fade show">
                            <i class="bi bi-check-circle"></i> Uploaded: ${{file.name}}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    `;
                }} else {{
                    errorCount++;
                    resultsDiv.innerHTML += `
                        <div class="alert alert-danger alert-dismissible fade show">
                            <i class="bi bi-x-circle"></i> Failed: ${{file.name}} - ${{data.error}}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    `;
                }}
            }} catch (error) {{
                errorCount++;
                resultsDiv.innerHTML += `
                    <div class="alert alert-danger alert-dismissible fade show">
                        <i class="bi bi-x-circle"></i> Error: ${{file.name}} - ${{error.message}}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                `;
            }}
        }}
        
        progressBar.querySelector('.progress-bar').style.width = '100%';
        
        // Show summary
        if (successCount > 0 || errorCount > 0) {{
            resultsDiv.innerHTML = `
                <div class="alert alert-info">
                    <strong>Upload Complete:</strong> ${{successCount}} succeeded, ${{errorCount}} failed
                </div>
            ` + resultsDiv.innerHTML;
        }}
        
        uploadBtn.disabled = false;
        if (successCount > 0) {{
            setTimeout(() => window.location.href = '{url_for('file_manager_admin.index')}', 2000);
        }}
    }});
    </script>
    """
    
    disp.add_display_item(displayer.DisplayerItemAlert(upload_form_html, BSstyle.NONE), column=0)
    
    return render_template("base_content.j2", content=disp.display())
