"""
Thread Monitoring Page - Enhanced version with tabbed interface.

This module provides real-time monitoring of running threads with:
- Console output tab
- Logs tab  
- Process output tab
- Thread management (kill, etc.)
"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from ..modules.threaded import threaded_manager

bp = Blueprint("threads", __name__, url_prefix="/threads")


@bp.route("/", methods=["GET"])
def threads():
    """
    Display all currently running threads with their status.
    
    Returns:
        Rendered template showing thread list with enhanced information
    """
    # Get thread manager instance
    manager = threaded_manager.thread_manager_obj
    
    if manager is None:
        return render_template("threads_enhanced.j2", threads={}, stats={})
    
    # Build thread information dictionary
    threads_info = {}
    all_threads = manager.get_all_threads()
    
    for thread in all_threads:
        thread_name = thread.get_name() if hasattr(thread, 'get_name') else thread.m_default_name
        
        # Gather comprehensive thread information
        info = {
            "running": getattr(thread, 'm_running', False),
            "progress": getattr(thread, 'm_running_state', -1),
            "process_running": getattr(thread, 'm_process_running', False),
            "type": getattr(thread, 'm_type', "unknown"),
            "error": getattr(thread, 'm_error', None),
            "background": getattr(thread, 'm_background', False),
        }
        
        threads_info[thread_name] = info
    
    # Get manager statistics
    stats = manager.get_thread_stats()
    
    return render_template("threads_enhanced.j2", threads=threads_info, stats=stats)


@bp.route("/", methods=["POST"])
def threads_post():
    """
    Handle thread management actions (kill thread).
    
    Expects POST data with thread name to kill.
    
    Returns:
        Redirect back to threads page after action
    """
    # Get thread manager instance
    manager = threaded_manager.thread_manager_obj
    
    if manager is None:
        return redirect(url_for('threads.threads'))
    
    # Get thread name from POST data
    form_data = request.form.to_dict()
    
    # The hidden input name contains the thread name as key
    thread_name = list(form_data.keys())[0] if form_data else None
    
    if thread_name:
        # Find and kill the thread
        thread = manager.get_thread(thread_name)
        if thread:
            manager.del_thread(thread)
    
    return redirect(url_for('threads.threads'))


@bp.route("/api/threads", methods=["GET"])
def api_threads():
    """
    API endpoint for real-time thread status updates.
    
    Returns:
        JSON object with thread states for live updates
    """
    manager = threaded_manager.thread_manager_obj
    
    if manager is None:
        return jsonify({"threads": {}, "stats": {}})
    
    threads_info = {}
    all_threads = manager.get_all_threads()
    
    for thread in all_threads:
        thread_name = thread.get_name() if hasattr(thread, 'get_name') else thread.m_default_name
        
        threads_info[thread_name] = {
            "running": getattr(thread, 'm_running', False),
            "state": getattr(thread, 'm_running_state', -1),
            "process_running": getattr(thread, 'm_process_running', False),
            "type": getattr(thread, 'm_type', "unknown"),
            "error": getattr(thread, 'm_error', None),
            "background": getattr(thread, 'm_background', False),
        }
    
    stats = manager.get_thread_stats()
    
    return jsonify({"threads": threads_info, "stats": stats})


@bp.route("/api/thread/<thread_name>/console", methods=["GET"])
def api_thread_console(thread_name):
    """
    API endpoint to get console output for a specific thread.
    
    Args:
        thread_name: Name of the thread
        
    Returns:
        JSON with console output
    """
    manager = threaded_manager.thread_manager_obj
    
    if manager is None:
        return jsonify({"error": "Thread manager not initialized"})
    
    thread = manager.get_thread(thread_name)
    
    if thread is None:
        return jsonify({"error": "Thread not found"})
    
    # Get console data
    if hasattr(thread, 'get_console_data'):
        data = thread.get_console_data()
        return jsonify(data)
    else:
        return jsonify({"error": "Thread does not support console output"})


@bp.route("/api/thread/<thread_name>/logs", methods=["GET"])
def api_thread_logs(thread_name):
    """
    API endpoint to get log entries for a specific thread.
    
    Args:
        thread_name: Name of the thread
        
    Returns:
        JSON with log entries
    """
    manager = threaded_manager.thread_manager_obj
    
    if manager is None:
        return jsonify({"error": "Thread manager not initialized"})
    
    thread = manager.get_thread(thread_name)
    
    if thread is None:
        return jsonify({"error": "Thread not found"})
    
    # Get log data
    if hasattr(thread, 'log_get_entries'):
        logs = thread.log_get_entries()
        return jsonify({"logs": logs})
    else:
        return jsonify({"error": "Thread does not support logging"})


@bp.route("/thread/<thread_name>", methods=["GET"])
def thread_detail(thread_name):
    """
    Display detailed view of a single thread with tabbed interface.
    
    Args:
        thread_name: Name of the thread to display
        
    Returns:
        Rendered template with thread details
    """
    manager = threaded_manager.thread_manager_obj
    
    if manager is None:
        return render_template("error.j2", error="Thread manager not initialized")
    
    thread = manager.get_thread(thread_name)
    
    if thread is None:
        return render_template("error.j2", error=f"Thread '{thread_name}' not found")
    
    # Get all thread data
    thread_data = {
        "name": thread_name,
        "running": getattr(thread, 'm_running', False),
        "progress": getattr(thread, 'm_running_state', -1),
        "process_running": getattr(thread, 'm_process_running', False),
        "type": getattr(thread, 'm_type', "unknown"),
        "error": getattr(thread, 'm_error', None),
        "background": getattr(thread, 'm_background', False),
    }
    
    # Get console data if available
    if hasattr(thread, 'get_console_data'):
        console_data = thread.get_console_data()
    else:
        console_data = {
            "console_output": [],
            "logs": [],
            "process_output": []
        }
    
    return render_template("thread_detail.j2", thread=thread_data, console_data=console_data)
