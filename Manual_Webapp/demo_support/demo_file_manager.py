"""
File Manager Demo Page

Demonstrates the file upload and display components with FilePond integration.
"""

from flask import Blueprint, render_template, session, request
from src.modules import displayer
from src.modules.file_manager import FileManager
from src.modules import settings
from src.modules.auth import require_permission, auth_manager
import logging

logger = logging.getLogger(__name__)

demo_file_bp = Blueprint('demo_files', __name__)

# File manager instance (injected by main.py)
file_manager = None


def get_latest_uploaded_file():
    """Get the ID of the latest uploaded file.
    
    Returns:
        int or None: File ID of the most recent upload
    """
    try:
        global file_manager
        if file_manager is None:
            logger.warning("file_manager is None in get_latest_uploaded_file")
            return None
        
        files = file_manager.list_files_from_db(limit=1)
        logger.info(f"get_latest_uploaded_file: found {len(files)} files")
        if files:
            file_id = files[0].get('id') if isinstance(files[0], dict) else files[0].id
            logger.info(f"get_latest_uploaded_file: returning file_id={file_id}")
            return file_id
    except Exception as e:
        logger.error(f"Failed to get latest file: {e}", exc_info=True)
    return None


@demo_file_bp.route('/file-manager-demo', methods=['GET'])
@require_permission("FileManager", "view")
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
    
    # Check if user has upload permission for UI display
    has_upload_permission = True
    if auth_manager:
        current_user = session.get('user')
        has_upload_permission = auth_manager.has_permission(current_user, "FileManager", "upload")
    
    # Section 1: Full Upload (user selects everything)
    disp.add_master_layout(
        displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, 
            [12], 
            subtitle="1. Full Upload - User Selects Category, Group ID, and Tags"
        )
    )
    
    if not has_upload_permission:
        disp.add_display_item(
            displayer.DisplayerItemAlert(
                "<p><i class='mdi mdi-lock'></i> You don't have permission to upload files. Contact an administrator to request upload access.</p>",
                displayer.BSstyle.WARNING
            ),
            column=0
        )
    else:
        disp.add_display_item(
            displayer.DisplayerItemAlert(
                "<p>All fields visible - user has full control over metadata.</p>",
                displayer.BSstyle.NONE
            ),
            column=0
        )
        
        # Modern FilePond upload with all fields visible
        disp.add_display_item(displayer.DisplayerItemFileUpload(
            id="file",
            text="Select File"
            # All fields shown because nothing is pre-filled
        ), column=0)
    
    # Section 2: Simple Upload (category and tags pre-filled)
    disp.add_master_layout(
        displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, 
            [12], 
            subtitle="2. Simple Upload - Pre-filled Category and Tags"
        )
    )
    
    if not has_upload_permission:
        disp.add_display_item(
            displayer.DisplayerItemAlert(
                "<p><i class='mdi mdi-lock'></i> You don't have permission to upload files. Contact an administrator to request upload access.</p>",
                displayer.BSstyle.WARNING
            ),
            column=0
        )
    else:
        disp.add_display_item(
            displayer.DisplayerItemAlert(
                "<p>Category set to 'documents' and tags set to 'demo, example'. User only selects the file.</p>",
                displayer.BSstyle.NONE
            ),
            column=0
        )
        
        # Modern FilePond upload with pre-filled values (hides those fields)
        disp.add_display_item(displayer.DisplayerItemFileUpload(
            id="simple_file",
            text="Select File",
            category="documents",
            tags=["demo", "example"]
        ), column=0)
        
        # Show what's pre-filled
        disp.add_display_item(
            displayer.DisplayerItemAlert(
                "<p class='text-muted'><i class='mdi mdi-information'></i> Category: <strong>documents</strong>, Tags: <strong>demo, example</strong></p>",
                displayer.BSstyle.NONE
            ),
            column=0
        )
    
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
                "<p><i class='mdi mdi-information'></i> No files uploaded yet. Upload a file in the sections above to see this example.</p>",
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
                actions=["download", "edit", "history"],
                compact=True
            ),
            column=0
        )
    else:
        disp.add_display_item(
            displayer.DisplayerItemAlert(
                "<p><i class='mdi mdi-information'></i> No files uploaded yet. Upload a file in the sections above to see this example.</p>",
                displayer.BSstyle.WARNING
            ),
            column=0
        )
    
    # Use framework's form handling - submit to this same page
    return render_template("base_content.j2", content=disp.display(), 
                          target="demo_files.file_manager_demo")


# Export blueprint
bp = demo_file_bp
