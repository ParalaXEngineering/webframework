"""
Logging Viewer Page - Flask blueprint for real-time log monitoring.

This module provides real-time monitoring of framework log files with a modern
tabbed interface showing log content with automatic updates.
"""

from flask import Blueprint, render_template
from ..modules import displayer
import os

bp = Blueprint("logging", __name__, url_prefix="/logging")


@bp.route("/", methods=["GET"])
def logs():
    """
    Display all log files with real-time updates.
    
    Returns:
        Rendered template showing log content in tabs with auto-refresh.
    """
    disp = displayer.Displayer()
    disp.add_generic("Log Viewer")
    disp.set_title("Log Viewer")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Logs", "logging.logs", [])
    
    # Get logs directory
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    
    # Check if logs directory exists
    if not os.path.exists(logs_dir):
        disp.add_alert("Logs directory not found: {}".format(logs_dir), displayer.BSstyle.ERROR)
        return render_template("base_content.j2", content=disp.display())
    
    # Get all log files
    log_files = []
    try:
        for filename in sorted(os.listdir(logs_dir)):
            if filename.endswith('.log'):
                filepath = os.path.join(logs_dir, filename)
                log_files.append({
                    'name': filename,
                    'path': filepath,
                    'size': os.path.getsize(filepath)
                })
    except Exception as e:
        disp.add_alert("Error reading logs directory: {}".format(str(e)), displayer.BSstyle.ERROR)
        return render_template("base_content.j2", content=disp.display())
    
    if not log_files:
        disp.add_alert("No log files found in: {}".format(logs_dir), displayer.BSstyle.WARNING)
        return render_template("base_content.j2", content=disp.display())
    
    # Statistics section
    total_size = sum(f['size'] for f in log_files)
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [4, 4, 4]
    ))
    
    disp.add_display_item(displayer.DisplayerItemText(
        "<div class='text-center'><h3>{}</h3><small>Log Files</small></div>".format(len(log_files))
    ), 0)
    disp.add_display_item(displayer.DisplayerItemText(
        "<div class='text-center'><h3>{:.2f} KB</h3><small>Total Size</small></div>".format(total_size / 1024)
    ), 1)
    disp.add_display_item(displayer.DisplayerItemText(
        "<div class='text-center'><h3>{}</h3><small>Directory</small></div>".format(os.path.basename(logs_dir))
    ), 2)
    
    disp.add_display_item(displayer.DisplayerItemSeparator(), 0)
    
    # Single dynamic content placeholder for ALL log content
    # LogEmitter will update this with complete log tabs
    initial_content = "<p class='text-muted text-center'><i class='mdi mdi-loading mdi-spin'></i> Loading logs...</p>"
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(
        displayer.DisplayerItemDynamicContent(
            id='logs_content',
            initial_content=initial_content,
            card=False
        ),
        0
    )
    
    # Render page - LogEmitter will update content via reload events
    return render_template("base_content.j2", 
                         content=disp.display(), 
                         target="logging.logs")
