"""
Thread Monitoring Page - Flask blueprint for thread management and monitoring.

This module provides real-time monitoring of running threads with a modern
card-based interface showing console output, logs, and process information.
"""

# Third-party
from flask import Blueprint, render_template, request, flash, redirect, url_for

# Framework modules - constants and i18n
from ..modules.constants import METHOD_GET, METHOD_POST, GET_POST
from ..modules.i18n.messages import (
    TEXT_THREAD_MONITOR,
    TEXT_BREADCRUMB_THREADS,
    TEXT_LOADING_THREADS,
    TEXT_THREAD_STOPPED,
    TEXT_THREAD_NOT_FOUND_STOP,
    TEXT_THREAD_FORCE_KILLED,
    TEXT_THREAD_NOT_FOUND_KILL,
    TEXT_THREAD_MANAGER_NOT_INIT,
    TEXT_STAT_TOTAL,
    TEXT_STAT_RUNNING,
    TEXT_STAT_WITH_PROCESS,
    TEXT_STAT_WITH_ERROR
)

# Framework modules - core functionality
from ..modules import displayer
from ..modules.app_context import app_context

# =============================================================================
# Domain-Specific Constants (Threads Module)
# =============================================================================

# Blueprint Configuration
BP_NAME = "threads"
BP_URL_PREFIX = "/threads"
bp = Blueprint(BP_NAME, __name__, url_prefix=BP_URL_PREFIX)

# Route Paths
ROUTE_MAIN = "/"
ROUTE_DELETE = "/delete"

# Form Field Names
FIELD_ACTION = "action"
FIELD_THREAD_NAME = "thread_name"

# Action Values
ACTION_STOP = "stop"
ACTION_FORCE_KILL = "force_kill"

# Query Parameters
PARAM_THREAD_NAME = "thread_name"

# Flash Message Categories
FLASH_CATEGORY_WARNING = "warning"
FLASH_CATEGORY_ERROR = "error"

# Template Configuration
TEMPLATE_BASE_CONTENT = "base_content.j2"

# Statistics Keys (from threaded_manager)
STAT_TOTAL = "total"
STAT_RUNNING = "running"
STAT_WITH_PROCESS = "with_process"
STAT_WITH_ERROR = "with_error"

# Dynamic Content Configuration
DYNAMIC_CONTENT_ID = "threads_content"
DYNAMIC_CONTENT_CARD = False

# Layout Configuration
LAYOUT_STATS = [3, 3, 3, 3]
LAYOUT_FULL_WIDTH = [12]


@bp.route(ROUTE_MAIN, methods=GET_POST)
def threads():
    """
    Display all currently running threads with modern card interface.
    
    Returns:
        Rendered template showing thread cards with tabs for console, logs, etc.
    """

    disp = displayer.Displayer()
    disp.add_generic(TEXT_THREAD_MONITOR)
    disp.set_title(TEXT_THREAD_MONITOR)
    
    disp.add_breadcrumb(TEXT_BREADCRUMB_THREADS, f"{BP_NAME}.{threads.__name__}", [])
    
    # Get thread manager instance
    manager = app_context.thread_manager
    
    # Handle POST requests (stop or force kill thread)
    if request.method == METHOD_POST:
        action = request.form.get(FIELD_ACTION)
        thread_name = request.form.get(FIELD_THREAD_NAME)
        
        if manager and action == ACTION_STOP and thread_name:
            thread = manager.get_thread(thread_name)
            if thread:
                manager.del_thread(thread)
                flash(TEXT_THREAD_STOPPED.format(thread_name), FLASH_CATEGORY_WARNING)
            else:
                flash(TEXT_THREAD_NOT_FOUND_STOP.format(thread_name), FLASH_CATEGORY_ERROR)
        elif manager and action == ACTION_FORCE_KILL and thread_name:
            thread = manager.get_thread(thread_name)
            if thread:
                # Force kill: stop thread and remove from manager
                if hasattr(thread, 'stop'):
                    thread.stop()
                manager.del_thread(thread)
                flash(TEXT_THREAD_FORCE_KILLED.format(thread_name), FLASH_CATEGORY_ERROR)
            else:
                flash(TEXT_THREAD_NOT_FOUND_KILL.format(thread_name), FLASH_CATEGORY_ERROR)
    
    if manager is None:
        flash(TEXT_THREAD_MANAGER_NOT_INIT, FLASH_CATEGORY_ERROR)
        return render_template(TEMPLATE_BASE_CONTENT, content=disp.display())
    
    # Statistics section
    stats = manager.get_thread_stats()
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, LAYOUT_STATS
    ))
    
    disp.add_display_item(displayer.DisplayerItemText(
        f"<div class='text-center'><h3>{stats[STAT_TOTAL]}</h3><small>{TEXT_STAT_TOTAL}</small></div>"
    ), 0)
    disp.add_display_item(displayer.DisplayerItemText(
        f"<div class='text-center'><h3>{stats[STAT_RUNNING]}</h3><small>{TEXT_STAT_RUNNING}</small></div>"
    ), 1)
    disp.add_display_item(displayer.DisplayerItemText(
        f"<div class='text-center'><h3>{stats[STAT_WITH_PROCESS]}</h3><small>{TEXT_STAT_WITH_PROCESS}</small></div>"
    ), 2)
    disp.add_display_item(displayer.DisplayerItemText(
        f"<div class='text-center'><h3>{stats[STAT_WITH_ERROR]}</h3><small>{TEXT_STAT_WITH_ERROR}</small></div>"
    ), 3)
    
    disp.duplicate_master_layout()
    disp.add_display_item(displayer.DisplayerItemSeparator(), 0)
    
    # Single dynamic content placeholder for ALL threads
    # ThreadEmitter will update this with complete thread list (running + completed)
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, LAYOUT_FULL_WIDTH
    ))
    disp.add_display_item(
        displayer.DisplayerItemDynamicContent(
            id=DYNAMIC_CONTENT_ID,
            initial_content=TEXT_LOADING_THREADS,
            card=DYNAMIC_CONTENT_CARD
        ),
        0
    )
    
    # Render page - ThreadEmitter will update content via reload events
    return render_template(TEMPLATE_BASE_CONTENT, 
                         content=disp.display(), 
                         target=f"{BP_NAME}.{threads.__name__}")


@bp.route(ROUTE_DELETE, methods=[METHOD_GET])
def delete_thread():
    """
    Delete a thread: kill if running (marks as aborted), or remove completed from history.
    
    Query Parameters:
        thread_name: Name of the thread to delete
        
    Returns:
        Redirect back to threads page
    """
    
    thread_name = request.args.get(PARAM_THREAD_NAME)
    
    if thread_name:
        manager = app_context.thread_manager
        if manager:
            # Check if thread is running
            thread = manager.get_thread(thread_name)
            if thread:
                # It's running - stop it and mark as aborted (stays in history)
                thread.delete()  # This calls del_thread internally and marks as aborted
            else:
                # Not running - it's completed, remove from history
                manager.remove_from_history(thread_name)
    
    return redirect(url_for(f"{BP_NAME}.{threads.__name__}"))
