"""
Thread Status Emitter

Background thread that periodically emits thread status updates via SocketIO.
"""
import threading
import time
from typing import Optional

try:
    from ..logger_factory import get_logger
    from . import threaded_manager
except ImportError:
    from logger_factory import get_logger
    import threaded_manager


class ThreadEmitter:
    """Emits thread status updates via SocketIO at regular intervals."""
    
    def __init__(self, socket_io, interval: float = 1.0):
        """
        Initialize thread emitter.
        
        Args:
            socket_io: SocketIO instance for emission
            interval: Update interval in seconds (default: 1.0)
        """
        self.socket = socket_io
        self.interval = interval
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self.logger = get_logger("threaded.emitter")
        
    def start(self):
        """Start the emitter background thread."""
        if self.running:
            self.logger.warning("Thread emitter already running")
            return
            
        self.running = True
        self._thread = threading.Thread(target=self._emit_loop, daemon=True)
        self._thread.start()
        self.logger.info(f"Thread emitter started (interval={self.interval}s)")
    
    def stop(self):
        """Stop the emitter background thread."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        self.logger.info("Thread emitter stopped")
    
    def _emit_loop(self):
        """Main emission loop - runs in background thread."""
        while self.running:
            try:
                self._emit_thread_update()
                self._emit_thread_cards()
            except Exception as e:
                self.logger.error(f"Error emitting thread update: {e}")
            
            time.sleep(self.interval)
    
    def _emit_thread_update(self):
        """Collect and emit current thread status."""
        manager = threaded_manager.thread_manager_obj
        if not manager:
            return
        
        # Get running and completed threads
        running_threads, completed_threads = manager.get_all_threads_with_history()
        
        # Build thread data
        threads_data = {
            'running': [],
            'completed': [],
            'stats': {
                'total': len(running_threads),
                'running': sum(1 for t in running_threads if getattr(t, 'm_running', False)),
                'with_error': sum(1 for t in running_threads if getattr(t, 'm_error', None))
            }
        }
        
        # Collect running thread data
        for thread in running_threads:
            thread_info = self._get_thread_info(thread, is_running=True)
            threads_data['running'].append(thread_info)
        
        # Collect completed thread data (last 10 for performance)
        for thread in list(reversed(completed_threads))[:10]:
            thread_info = self._get_thread_info(thread, is_running=False)
            threads_data['completed'].append(thread_info)
        
        # Emit to all connected clients
        try:
            self.socket.emit('thread_update', threads_data)
        except Exception as e:
            self.logger.error(f"Failed to emit thread update: {e}")
    
    def _get_thread_info(self, thread, is_running: bool) -> dict:
        """Extract thread information for transmission.
        
        Args:
            thread: Thread object
            is_running: Whether thread is in running pool
            
        Returns:
            Dictionary with thread information
        """
        thread_name = thread.get_name() if hasattr(thread, 'get_name') else thread.m_default_name
        
        # Get status
        status = 'running' if is_running else 'completed'
        if hasattr(thread, 'm_error') and thread.m_error:
            status = 'error'
        elif hasattr(thread, 'm_running') and not thread.m_running and is_running:
            status = 'stopped'
        
        # Get progress
        progress = -1
        if hasattr(thread, 'm_running_state'):
            progress = thread.m_running_state
        
        # Get console output (last 30 lines for running, 20 for completed)
        console_lines = []
        if hasattr(thread, 'console_get_output'):
            line_count = 30 if is_running else 20
            console_lines = thread.console_get_output(line_count)
        
        # Get log entries (last 20 for running, 10 for completed)
        log_entries = []
        if hasattr(thread, 'log_get_entries'):
            log_count = 20 if is_running else 10
            entries = thread.log_get_entries(log_count)
            # Convert log entries to simple dicts
            log_entries = [
                {
                    'level': entry.get('level', 'INFO'),
                    'message': entry.get('message', ''),
                    'timestamp': entry.get('timestamp', '')
                }
                for entry in entries
            ]
        
        # Get error message
        error_msg = None
        if hasattr(thread, 'm_error') and thread.m_error:
            error_msg = str(thread.m_error)
        
        return {
            'name': thread_name,
            'status': status,
            'progress': progress,
            'console': console_lines,
            'logs': log_entries,
            'error': error_msg,
            'is_running': is_running
        }
    
    def _emit_thread_cards(self):
        """Emit reload event for entire thread list."""
        manager = threaded_manager.thread_manager_obj
        if not manager:
            return
        
        # Get all threads (running + completed history)
        running, completed = manager.get_all_threads_with_history()
        
        # Limit completed to last 10
        completed = list(completed)[-10:] if completed else []
        
        # Render complete HTML for all threads
        html_content = self._render_all_threads(running, completed)
        
        # Emit single reload for entire threads section
        try:
            self.socket.emit('reload', {
                'id': 'threads_content',
                'content': html_content
            })
        except Exception as e:
            self.logger.error(f"Failed to emit reload: {e}")
    
    def _render_all_threads(self, running_threads, completed_threads) -> str:
        """Render HTML for all threads (running + completed)."""
        html = ""
        
        # Running threads section
        if running_threads:
            html += "<h4><i class='mdi mdi-play-circle'></i> Running Threads ({})</h4>".format(len(running_threads))
            
            for thread in running_threads:
                html += self._render_single_thread(thread, is_completed=False)
                html += "<hr class='my-3'>"
        
        # Completed threads section
        if completed_threads:
            html += "<h4 class='mt-4'><i class='mdi mdi-history'></i> Completed Threads History ({}) - Last 10</h4>".format(len(completed_threads))
            
            for thread in reversed(completed_threads):  # Newest first
                html += self._render_single_thread(thread, is_completed=True)
                html += "<hr class='my-3'>"
        
        # No threads message
        if not running_threads and not completed_threads:
            html = "<div class='alert alert-info'>No threads currently running. Visit the Threading Demo to start some!</div>"
        
        return html
    
    def _render_single_thread(self, thread, is_completed=False) -> str:
        """Render HTML for a single thread card."""
        thread_name = thread.get_name()
        thread_id = thread_name.replace(' ', '_').replace(':', '_')
        
        # Get thread data
        is_running = hasattr(thread, 'm_running') and thread.m_running
        progress = getattr(thread, 'm_progress', 0)
        has_error = hasattr(thread, 'm_error') and thread.m_error
        
        # Determine status badge
        if has_error:
            status_badge = '<span class="badge bg-danger">Error</span>'
        elif is_running:
            status_badge = '<span class="badge bg-success">Running</span>'
        elif is_completed:
            status_badge = '<span class="badge bg-secondary">Completed</span>'
        else:
            status_badge = '<span class="badge bg-secondary">Stopped</span>'
        
        # Build card header with action buttons
        card_html = f"""
<h3 class="text-primary mt-3">{thread_name} {status_badge}"""
        
        if progress > 0:
            card_html += f' <span class="badge bg-info">{progress}%</span>'
        
        # Add action buttons for running threads
        if is_running:
            card_html += f"""
<div class='float-end'>
    <form method='POST' style='display:inline-block; margin-left:5px;'>
        <input type='hidden' name='thread_name' value='{thread_name}'>
        <button type='submit' name='action' value='stop' class='btn btn-sm btn-warning' title='Stop Thread'>
            <i class='mdi mdi-stop'></i> Stop
        </button>
    </form>
    <form method='POST' style='display:inline-block; margin-left:5px;'>
        <input type='hidden' name='thread_name' value='{thread_name}'>
        <button type='submit' name='action' value='force_kill' class='btn btn-sm btn-danger' title='Force Kill Thread'>
            <i class='mdi mdi-close-octagon'></i> Force Kill
        </button>
    </form>
</div>"""
        
        card_html += "</h3>\n"
        
        # Get thread data for tabs
        console_data = thread.get_console_data() if hasattr(thread, 'get_console_data') else None
        
        if not console_data:
            card_html += "<p class='text-muted'>No data available</p>"
            return card_html
        
        # Build console HTML
        console_output = console_data.get('console', [])
        if console_output:
            console_html = "<div style='background:#1e1e1e; color:#d4d4d4; padding:10px; border-radius:5px; max-height:400px; overflow-y:auto; font-family:monospace;'>"
            for line in console_output[-50:]:  # Last 50 lines
                console_html += "{}<br>".format(line)
            console_html += "</div>"
        else:
            console_html = "<p class='text-muted'>No console output</p>"
        
        # Build logs HTML
        logs = console_data.get('logs', [])
        if logs:
            logs_html = "<div style='max-height:400px; overflow-y:auto;'>"
            logs_html += "<table class='table table-sm table-striped'>"
            logs_html += "<thead><tr><th>Level</th><th>Message</th><th>Data</th></tr></thead><tbody>"
            for log in logs[-30:]:  # Last 30 logs
                level = log.get('level', 'info')
                level_badge = {
                    'debug': 'secondary',
                    'info': 'info',
                    'warning': 'warning',
                    'error': 'danger'
                }.get(level, 'secondary')
                logs_html += "<tr><td><span class='badge bg-{}'>  {}</span></td>".format(level_badge, level)
                logs_html += "<td>{}</td>".format(log.get('message', ''))
                logs_html += "<td><small>{}</small></td></tr>".format(log.get('data', {}))
            logs_html += "</tbody></table></div>"
        else:
            logs_html = "<p class='text-muted'>No logs available</p>"
        
        # Build process HTML
        process_html = "<dl class='row'>"
        process_html += "<dt class='col-sm-4'>Process Running:</dt><dd class='col-sm-8'>No</dd>"
        process_html += "<dt class='col-sm-4'>Output:</dt><dd class='col-sm-8'><i class='text-muted'>No process output</i></dd>"
        process_html += "</dl>"
        
        # Build info HTML  
        info_html = "<dl class='row'>"
        info_html += "<dt class='col-sm-4'>Name:</dt><dd class='col-sm-8'>{}</dd>".format(thread_name)
        info_html += "<dt class='col-sm-4'>Running:</dt><dd class='col-sm-8'>{}</dd>".format('Yes' if is_running else 'No')
        info_html += "<dt class='col-sm-4'>Progress:</dt><dd class='col-sm-8'>{}%</dd>".format(progress)
        
        if hasattr(thread, 'm_error') and thread.m_error:
            info_html += "<dt class='col-sm-4'>Error:</dt><dd class='col-sm-8'><span class='text-danger'>{}</span></dd>".format(thread.m_error)
        
        info_html += "</dl>"
        info_html += "<p class='text-muted'><i class='mdi mdi-information'></i> Use the Stop or Force Kill buttons in the card header to control this thread.</p>"
        
        # Build tabs HTML
        tabs_html = f"""
<ul class="nav nav-tabs" id="myTab" role="tablist">
    <li class="nav-item" role="presentation">
        <a class="nav-link active" id="tab1-tab-{thread_id}" data-bs-toggle="tab" href="#tab1_{thread_id}" role="tab">Console</a>
    </li>
    <li class="nav-item" role="presentation">
        <a class="nav-link" id="tab2-tab-{thread_id}" data-bs-toggle="tab" href="#tab2_{thread_id}" role="tab">Logs</a>
    </li>
    <li class="nav-item" role="presentation">
        <a class="nav-link" id="tab3-tab-{thread_id}" data-bs-toggle="tab" href="#tab3_{thread_id}" role="tab">Process</a>
    </li>
    <li class="nav-item" role="presentation">
        <a class="nav-link" id="tab4-tab-{thread_id}" data-bs-toggle="tab" href="#tab4_{thread_id}" role="tab">Info</a>
    </li>
</ul>

<div class="tab-content" id="myTabContent-{thread_id}">
    <div class="tab-pane fade show active" id="tab1_{thread_id}" role="tabpanel">
        {console_html}
    </div>
    <div class="tab-pane fade" id="tab2_{thread_id}" role="tabpanel">
        {logs_html}
    </div>
    <div class="tab-pane fade" id="tab3_{thread_id}" role="tabpanel">
        {process_html}
    </div>
    <div class="tab-pane fade" id="tab4_{thread_id}" role="tabpanel">
        {info_html}
    </div>
</div>
"""
        
        # Combine header and tabs
        card_html += tabs_html
        
        return card_html


# Global emitter instance
thread_emitter_obj: Optional[ThreadEmitter] = None

