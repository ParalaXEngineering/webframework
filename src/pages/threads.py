"""
Thread Monitoring Page - Flask blueprint for thread management and monitoring.

This module provides real-time monitoring of running threads with a modern
card-based interface showing console output, logs, and process information.
"""

from flask import Blueprint, render_template, request, flash
from ..modules import displayer
from ..modules.threaded import threaded_manager

bp = Blueprint("threads", __name__, url_prefix="/threads")


@bp.route("/", methods=["GET", "POST"])
def threads():
    """
    Display all currently running threads with modern card interface.
    
    Returns:
        Rendered template showing thread cards with tabs for console, logs, etc.
    """
    disp = displayer.Displayer()
    disp.add_generic("Thread Monitor")
    disp.set_title("Thread Monitor")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Threads", "threads.threads", [])
    
    # Get thread manager instance
    manager = threaded_manager.thread_manager_obj
    
    # Handle POST requests (stop or force kill thread)
    if request.method == 'POST':
        action = request.form.get('action')
        thread_name = request.form.get('thread_name')
        
        if manager and action == 'stop' and thread_name:
            thread = manager.get_thread(thread_name)
            if thread:
                manager.del_thread(thread)
                flash("✓ Stopped thread: {}".format(thread_name), "warning")
            else:
                flash("✗ Thread not found: {}".format(thread_name), "error")
        elif manager and action == 'force_kill' and thread_name:
            thread = manager.get_thread(thread_name)
            if thread:
                # Force kill: stop thread and remove from manager
                if hasattr(thread, 'stop'):
                    thread.stop()
                manager.del_thread(thread)
                flash("✓ Force killed thread: {}".format(thread_name), "error")
            else:
                flash("✗ Thread not found: {}".format(thread_name), "error")
    
    if manager is None:
        flash("Thread manager not initialized", "error")
        return render_template("base_content.j2", content=disp.display())
    
    # Statistics section
    stats = manager.get_thread_stats()
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 3, 3, 3]
    ))
    
    disp.add_display_item(displayer.DisplayerItemText(
        "<div class='text-center'><h3>{}</h3><small>Total Threads</small></div>".format(stats['total'])
    ), 0)
    disp.add_display_item(displayer.DisplayerItemText(
        "<div class='text-center'><h3>{}</h3><small>Running</small></div>".format(stats['running'])
    ), 1)
    disp.add_display_item(displayer.DisplayerItemText(
        "<div class='text-center'><h3>{}</h3><small>With Process</small></div>".format(stats['with_process'])
    ), 2)
    disp.add_display_item(displayer.DisplayerItemText(
        "<div class='text-center'><h3>{}</h3><small>With Errors</small></div>".format(stats['with_error'])
    ), 3)
    
    disp.duplicate_master_layout()
    disp.add_display_item(displayer.DisplayerItemSeparator(), 0)
    
    # Single dynamic content placeholder for ALL threads
    # ThreadEmitter will update this with complete thread list (running + completed)
    initial_content = "<p class='text-muted text-center'><i class='mdi mdi-loading mdi-spin'></i> Loading threads...</p>"
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(
        displayer.DisplayerItemDynamicContent(
            id='threads_content',
            initial_content=initial_content,
            card=False
        ),
        0
    )
    
    # Render page - ThreadEmitter will update content via reload events
    return render_template("base_content.j2", 
                         content=disp.display(), 
                         target="threads.threads")


@bp.route("/delete", methods=["GET"])
def delete_thread():
    """
    Delete a thread: kill if running (marks as aborted), or remove completed from history.
    
    Query Parameters:
        thread_name: Name of the thread to delete
        
    Returns:
        Redirect back to threads page
    """
    from flask import redirect, url_for
    
    thread_name = request.args.get('thread_name')
    
    if thread_name:
        manager = threaded_manager.thread_manager_obj
        if manager:
            # Check if thread is running
            thread = manager.get_thread(thread_name)
            if thread:
                # It's running - stop it and mark as aborted (stays in history)
                thread.delete()  # This calls del_thread internally and marks as aborted
            else:
                # Not running - it's completed, remove from history
                manager.remove_from_history(thread_name)
    
    return redirect(url_for('threads.threads'))
