"""
Logging Viewer Page - Flask blueprint for real-time log monitoring.

This module provides real-time monitoring of framework log files with a modern
tabbed interface showing log content with automatic updates.
"""

from flask import Blueprint, render_template, request, redirect, url_for
from ..modules import displayer
import os

bp = Blueprint("logging", __name__, url_prefix="/logging")


@bp.route("/", methods=["GET", "POST"])
def logs():
    """
    Display all log files with real-time updates.
    
    Returns:
        Rendered template showing log content in tabs with auto-refresh.
    """
    from ..modules import log_emitter
    
    # Handle live mode toggle from POST
    if request.method == "POST":
        try:
            enabled = request.form.get('enabled', 'false').lower() == 'true'
            if log_emitter.log_emitter_obj:
                log_emitter.log_emitter_obj.set_live_mode(enabled)
                print(f"Live mode set to: {enabled}")
        except Exception as e:
            print(f"Error toggling live mode: {e}")
        
        # Redirect to GET to avoid form resubmission
        return redirect(url_for('logging.logs'))
    
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
    
    # Live mode control button
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    
    # Check current live mode status
    live_mode_active = log_emitter.log_emitter_obj.live_mode if log_emitter.log_emitter_obj else False
    
    if live_mode_active:
        live_mode_button = """
        <div class='mb-3'>
            <form method='post' style='display: inline;'>
                <input type='hidden' name='enabled' value='false'>
                <button type='submit' class='btn btn-primary'>
                    <i class='mdi mdi-pause'></i> Disable Live Mode
                </button>
            </form>
            <small class='text-muted ms-2'>Live updates enabled (updates every 2s)</small>
        </div>
        """
    else:
        live_mode_button = """
        <div class='mb-3'>
            <form method='post' style='display: inline;'>
                <input type='hidden' name='enabled' value='true'>
                <button type='submit' class='btn btn-secondary'>
                    <i class='mdi mdi-play'></i> Enable Live Mode
                </button>
            </form>
            <small class='text-muted ms-2'>Enable to get real-time log updates</small>
        </div>
        """
    
    disp.add_display_item(displayer.DisplayerItemText(live_mode_button), 0)
    
    disp.add_display_item(displayer.DisplayerItemSeparator(), 0)
    
    # Get initial content from log emitter (optimized with fewer lines)
    # Only load initial content if live mode is OFF (to avoid double processing)
    print("About to get initial content...")
    if log_emitter.log_emitter_obj:
        if live_mode_active:
            # Live mode is on, show placeholder - will be updated immediately by live updates
            initial_content = "<div class='text-center p-5'><div class='spinner-border text-primary' role='status'><span class='visually-hidden'>Loading...</span></div><p class='mt-3'>Loading live content...</p></div>"
            print("Live mode active - using placeholder")
        else:
            # Live mode is off, load initial content
            try:
                initial_content = log_emitter.log_emitter_obj.get_initial_content(max_lines_per_file=50)
                print("Got initial content successfully")
            except Exception as e:
                print(f"Error getting initial content: {e}")
                initial_content = f"<p class='text-danger text-center'>Error loading logs: {str(e)}</p>"
    else:
        initial_content = "<p class='text-muted text-center'>Log emitter not initialized</p>"
        print("Log emitter not initialized")
    
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
    
    # Render page - LogEmitter will update content via reload events when live mode is enabled
    print("About to render template...")
    return render_template("base_content.j2", 
                         content=disp.display(), 
                         target="logging.logs")
