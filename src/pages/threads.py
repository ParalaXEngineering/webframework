"""
Thread Monitoring Page - Flask blueprint for thread management and monitoring.

This module provides real-time monitoring of running threads, displaying their
state, progress, and allowing management operations like stopping threads.
"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from ..modules.threaded import threaded_manager

bp = Blueprint("threads", __name__, url_prefix="/threads")


@bp.route("/", methods=["GET"])
def threads():
    """
    Display all currently running threads with their status.
    
    Returns:
        Rendered template showing thread list with names and states
    """
    # Get thread manager instance
    manager = threaded_manager.thread_manager_obj
    
    if manager is None:
        return render_template("threads.j2", threads={})
    
    # Build thread information dictionary
    threads_info = {}
    all_threads = manager.get_all_threads()
    
    for thread in all_threads:
        thread_name = thread.get_name() if hasattr(thread, 'get_name') else thread.m_default_name
        
        # Gather thread state information
        state_info = []
        
        # Running state
        if hasattr(thread, 'm_running'):
            state_info.append(f"Running: {thread.m_running}")
        
        # Progress state
        if hasattr(thread, 'm_running_state'):
            if thread.m_running_state == -1:
                state_info.append("State: Active (no progress info)")
            else:
                state_info.append(f"Progress: {thread.m_running_state}%")
        
        # Process state
        if hasattr(thread, 'm_process_running'):
            state_info.append(f"Process running: {thread.m_process_running}")
        
        # Thread type
        if hasattr(thread, 'm_type'):
            state_info.append(f"Type: {thread.m_type}")
        
        # Error state
        if hasattr(thread, 'm_error') and thread.m_error:
            state_info.append(f"❌ Error: {thread.m_error}")
        
        threads_info[thread_name] = " | ".join(state_info) if state_info else "No state information"
    
    return render_template("threads.j2", threads=threads_info)


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
        return redirect(url_for('thread.threads'))
    
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
        return jsonify({"threads": {}})
    
    threads_info = {}
    all_threads = manager.get_all_threads()
    
    for thread in all_threads:
        thread_name = thread.get_name() if hasattr(thread, 'get_name') else thread.m_default_name
        
        threads_info[thread_name] = {
            "running": getattr(thread, 'm_running', False),
            "state": getattr(thread, 'm_running_state', -1),
            "process_running": getattr(thread, 'm_process_running', False),
            "type": getattr(thread, 'm_type', "unknown"),
            "error": getattr(thread, 'm_error', None)
        }
    
    return jsonify({"threads": threads_info})
