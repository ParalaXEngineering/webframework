"""
File Manager Demo Page

Demonstrates the file upload and display components with FilePond integration.
"""

from flask import Blueprint, render_template, session, redirect, url_for, request
from functools import wraps
from src.modules import displayer
from src.modules.file_manager import FileManager
from src.modules import settings
import logging

logger = logging.getLogger(__name__)

demo_file_bp = Blueprint('demo_files', __name__)

# File manager instance (injected by main.py)
file_manager = None


def require_login(f):
    """Decorator to require login for demo pages."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('common.login'))
        return f(*args, **kwargs)
    return decorated_function


def get_latest_uploaded_file():
    """Get the ID of the latest uploaded file.
    
    Returns:
        int or None: File ID of the most recent upload
    """
    try:
        global file_manager
        if file_manager is None:
            print("DEBUG: file_manager is None in get_latest_uploaded_file")
            logger.warning("file_manager is None in get_latest_uploaded_file")
            return None
        
        files = file_manager.list_files_from_db(limit=1)
        print(f"DEBUG: get_latest_uploaded_file: found {len(files)} files")
        logger.info(f"get_latest_uploaded_file: found {len(files)} files")
        if files:
            file_id = files[0].get('id') if isinstance(files[0], dict) else files[0].id
            print(f"DEBUG: get_latest_uploaded_file: returning file_id={file_id}")
            logger.info(f"get_latest_uploaded_file: returning file_id={file_id}")
            return file_id
    except Exception as e:
        print(f"DEBUG: Failed to get latest file: {e}")
        logger.error(f"Failed to get latest file: {e}", exc_info=True)
    return None


@demo_file_bp.route('/file-manager-demo', methods=['GET', 'POST'])
@require_login
def file_manager_demo():
    """File Manager Demo - Upload and display components."""
    
    disp = displayer.Displayer()
    disp.add_generic("File Manager Demo")
    
    disp.add_breadcrumb("Home", "framework_index", [])
    disp.add_breadcrumb("File Manager Demo", "demo_files.file_manager_demo", [])
    
    # Get file manager instance
    global file_manager
    if file_manager is None:
        file_manager = FileManager(settings.settings_manager)
    
    # Handle file upload POST
    upload_result = None
    if request.method == 'POST':
        logger.info(f"POST request received. Form keys: {list(request.form.keys())}")
        logger.info(f"Files keys: {list(request.files.keys())}")
        
        # Check which upload form was used
        # Framework prefixes field names with page title: "File Manager Demo.file"
        file = None
        is_simple_upload = False
        
        # Check for files with or without prefix
        for key in request.files:
            file_storage = request.files[key]
            if file_storage.filename:
                # Determine which upload based on field name
                if 'simple_file' in key:
                    file = file_storage
                    is_simple_upload = True
                    logger.info(f"Simple upload - file: {file.filename}")
                    break
                elif 'file' in key:
                    file = file_storage
                    logger.info(f"Full upload - file: {file.filename}")
                    break
        
        if not file:
            logger.warning(f"No valid file found in request. Files: {request.files}")
        
        if file:
            try:
                # Get form data
                if is_simple_upload:
                    # Pre-filled values for simple upload
                    category = 'documents'
                    group_id = ''
                    tags = ['demo', 'example']
                else:
                    # User-selected values for full upload
                    # Framework may prefix form field names too
                    category = None
                    for key in request.form:
                        if 'category' in key:
                            category = request.form.get(key, 'general')
                            break
                    if not category:
                        category = 'general'
                    
                    group_id = ''
                    for key in request.form:
                        if 'group_id' in key:
                            group_id = request.form.get(key, '')
                            break
                    if group_id == '(none)':
                        group_id = ''
                    
                    # Tags might be a multiselect
                    tags = []
                    for key in request.form:
                        if 'tags' in key:
                            tags = request.form.getlist(key)
                            break
                
                logger.info(f"Uploading: category={category}, group_id={group_id}, tags={tags}")
                
                metadata = file_manager.upload_file(
                    file,
                    category=category,
                    group_id=group_id,
                    tags=tags if tags else []
                )
                upload_result = {
                    'success': True,
                    'filename': metadata['name'],
                    'size': metadata['size']
                }
                logger.info(f"File uploaded successfully: {metadata['name']}")
            except Exception as e:
                upload_result = {
                    'success': False,
                    'error': str(e)
                }
                logger.error(f"Upload failed: {e}", exc_info=True)
        else:
            logger.warning("POST request but no file to upload")
    
    # Get available options
    categories = file_manager.get_categories()
    group_ids = file_manager.get_group_ids()
    tags = file_manager.get_tags()
    
    # Show upload result if any
    if upload_result:
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        if upload_result['success']:
            disp.add_display_item(
                displayer.DisplayerItemAlert(
                    f"<strong><i class='bi bi-check-circle'></i> Upload Successful!</strong><br>"
                    f"File: {upload_result['filename']}<br>"
                    f"Size: {upload_result['size'] / 1024:.1f} KB",
                    displayer.BSstyle.SUCCESS
                ),
                column=0
            )
        else:
            disp.add_display_item(
                displayer.DisplayerItemAlert(
                    f"<strong><i class='bi bi-x-circle'></i> Upload Failed</strong><br>{upload_result['error']}",
                    displayer.BSstyle.WARNING
                ),
                column=0
            )
    

    # Section 1: Full Upload (user selects everything)
    disp.add_master_layout(
        displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, 
            [12], 
            subtitle="1. Full Upload - User Selects Category, Group ID, and Tags"
        )
    )
    disp.add_display_item(
        displayer.DisplayerItemAlert(
            "<p>All fields visible - user has full control over metadata.</p>",
            displayer.BSstyle.NONE
        ),
        column=0
    )
    
    # Simple file input
    disp.add_display_item(displayer.DisplayerItemInputFile(
        id="file",
        text="Select File"
    ), column=0)
    
    # Category dropdown
    disp.add_display_item(displayer.DisplayerItemInputSelect(
        id="category",
        text="Category",
        choices=categories,
        value="general"
    ), column=0)
    
    # Group ID dropdown
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
    
    # Upload button (framework handles form submission via target parameter in render_template)
    disp.add_display_item(displayer.DisplayerItemButton(
        id="upload_btn",
        text="Upload File",
        icon="upload",
        color=displayer.BSstyle.PRIMARY
    ), column=0)
    
    # Section 2: Simple Upload (category and tags pre-filled)
    disp.add_master_layout(
        displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, 
            [12], 
            subtitle="2. Simple Upload - Pre-filled Category and Tags"
        )
    )
    disp.add_display_item(
        displayer.DisplayerItemAlert(
            "<p>Category set to 'documents' and tags set to 'demo, example'. User only selects the file.</p>",
            displayer.BSstyle.NONE
        ),
        column=0
    )
    
    # File input only
    disp.add_display_item(displayer.DisplayerItemInputFile(
        id="simple_file",
        text="Select File"
    ), column=0)
    
    # Show pre-filled values
    disp.add_display_item(
        displayer.DisplayerItemAlert(
            "<p class='text-muted'><i class='bi bi-info-circle'></i> Category: <strong>documents</strong>, Tags: <strong>demo, example</strong></p>",
            displayer.BSstyle.NONE
        ),
        column=0
    )
    
    # Upload button
    disp.add_display_item(displayer.DisplayerItemButton(
        id="simple_upload_btn",
        text="Upload File",
        icon="upload",
        color=displayer.BSstyle.SUCCESS
    ), column=0)
    
    # Get latest file for display examples
    latest_file_id = get_latest_uploaded_file()
    logger.info(f"Latest file ID for display: {latest_file_id}")
    
    # Section 3: Latest File - Full Display with Actions
    disp.add_master_layout(
        displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, 
            [12], 
            subtitle="3. Latest File - Full Card with Preview and Actions"
        )
    )
    
    if latest_file_id:
        print(f"DEBUG: Adding DisplayerItemFileDisplay with file_id={latest_file_id}")
        disp.add_display_item(
            displayer.DisplayerItemAlert(
                "<p>Full card view with preview, metadata, and action buttons.</p>",
                displayer.BSstyle.NONE
            ),
            column=0
        )
        disp.add_display_item(
            displayer.DisplayerItemFileDisplay(
                file_id=latest_file_id,
                actions=["download", "edit", "history"]
            ),
            column=0
        )
    else:
        disp.add_display_item(
            displayer.DisplayerItemAlert(
                "<p><i class='bi bi-info-circle'></i> No files uploaded yet. Upload a file in the sections above to see this example.</p>",
                displayer.BSstyle.WARNING
            ),
            column=0
        )
    
    # Section 4: Latest File - Compact Download Only
    disp.add_master_layout(
        displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, 
            [12], 
            subtitle="4. Latest File - Compact Download Link Only"
        )
    )
    
    if latest_file_id:
        disp.add_display_item(
            displayer.DisplayerItemAlert(
                "<p>Compact single-line layout with just the download button.</p>",
                displayer.BSstyle.NONE
            ),
            column=0
        )
        disp.add_display_item(
            displayer.DisplayerItemFileDisplay(
                file_id=latest_file_id,
                actions=["download"],
                compact=True
            ),
            column=0
        )
    else:
        disp.add_display_item(
            displayer.DisplayerItemAlert(
                "<p><i class='bi bi-info-circle'></i> No files uploaded yet. Upload a file in the sections above to see this example.</p>",
                displayer.BSstyle.WARNING
            ),
            column=0
        )
    
    # Use framework's form handling - submit to this same page
    return render_template("base_content.j2", content=disp.display(), 
                          target="demo_files.file_manager_demo")


# Export blueprint
bp = demo_file_bp
