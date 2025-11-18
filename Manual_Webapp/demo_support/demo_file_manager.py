"""
File Manager Demo Page

Demonstrates file upload functionality.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session
from functools import wraps
from src.modules import displayer, utilities
from src.modules.file_manager import FileManager
from src.modules import settings
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
                    """.format(
                        url_for('file_handler.download', filepath=metadata['path'])
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
    
    # Category dropdown
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


# Export blueprint
bp = demo_file_bp
