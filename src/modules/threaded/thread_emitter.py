"""
Thread Status Emitter

Background thread that periodically emits thread status updates via SocketIO as JSON data.
"""
import threading
import time
from typing import Optional, List, Dict

try:
    from ..log.logger_factory import get_logger
    from . import threaded_manager
except ImportError:
    from log.logger_factory import get_logger
    import threaded_manager


class ThreadEmitter:
    """Emits thread status updates via SocketIO at regular intervals as structured JSON."""
    
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
        self.logger = get_logger("threaded_emitter")
        
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
            except Exception as e:
                self.logger.error(f"Error emitting thread update: {e}")
            
            time.sleep(self.interval)
    
    def _emit_thread_update(self):
        """Collect and emit current thread status as HTML."""
        manager = threaded_manager.thread_manager_obj
        if not manager:
            return
        
        # Get running and completed threads
        running_threads, completed_threads = manager.get_all_threads_with_history()
        
        # Limit completed to last 10
        completed_threads = list(completed_threads)[-10:] if completed_threads else []
        
        # Build HTML content
        html_content = self._render_threads_html(running_threads, completed_threads)
        
        # Emit reload event for threads_content div
        try:
            self.socket.emit('reload', {
                'id': 'threads_content',
                'content': html_content
            })
        except Exception as e:
            self.logger.error(f"Failed to emit reload: {e}")
    
    def _render_threads_html(self, running_threads, completed_threads) -> str:
        """Render HTML for all threads.
        
        Args:
            running_threads: List of running threads
            completed_threads: List of completed threads
            
        Returns:
            HTML string with thread cards
        """
        if not running_threads and not completed_threads:
            return "<div class='alert alert-info'>No threads currently running. Visit the Threading Demo to start some!</div>"
        
        html_parts = []
        
        # Running threads section
        if running_threads:
            html_parts.append(f"<h4><i class='mdi mdi-play-circle'></i> Running Threads ({len(running_threads)})</h4>")
            for thread in running_threads:
                html_parts.append(self._render_thread_card(thread, is_running=True))
                html_parts.append("<hr class='my-3'>")
        
        # Completed threads section
        if completed_threads:
            html_parts.append(f"<h4 class='mt-4'><i class='mdi mdi-history'></i> Completed Threads History ({len(completed_threads)}) - Last 10</h4>")
            for thread in reversed(completed_threads):  # Newest first
                html_parts.append(self._render_thread_card(thread, is_running=False))
                html_parts.append("<hr class='my-3'>")
        
        return '\n'.join(html_parts)
    
    def _render_thread_card(self, thread, is_running: bool) -> str:
        """Render HTML card for a single thread.
        
        Args:
            thread: Thread object
            is_running: Whether thread is currently running
            
        Returns:
            HTML string for thread card
        """
        thread_name = thread.get_name()
        thread_id = thread_name.replace(' ', '_').replace(':', '_')
        
        # Get thread status using proper getters
        progress = thread.get_progress()
        error = thread.get_error()
        is_actually_running = thread.is_running()
        
        # Status badge
        if error:
            status_badge = '<span class="badge bg-danger">Error</span>'
        elif is_actually_running:
            status_badge = '<span class="badge bg-success">Running</span>'
        else:
            status_badge = '<span class="badge bg-secondary">Completed</span>'
        
        # Build card HTML
        card_html = [f"<h3 class='text-primary mt-3'>{thread_name} {status_badge}"]
        
        if progress > 0:
            card_html.append(f' <span class="badge bg-info">{progress}%</span>')
        
        # Action buttons for running threads
        if is_actually_running:
            card_html.append(f"""
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
</div>""")
        
        card_html.append("</h3>")
        
        # Get console data using proper getter
        console_data = thread.get_console_data()
        if not console_data:
            card_html.append("<p class='text-muted'>No data available</p>")
            return '\n'.join(card_html)
        
        # Simple display of console output and logs (no tabs for now - simpler)
        console_output = console_data.get('console_output', [])
        if console_output:
            card_html.append("<h5>Console Output:</h5>")
            card_html.append("<div style='background:#1e1e1e; color:#d4d4d4; padding:10px; border-radius:5px; max-height:300px; overflow-y:auto; font-family:monospace;'>")
            for line in console_output[-30:]:  # Last 30 lines
                card_html.append(f"{line}<br>")
            card_html.append("</div>")
        
        logs = console_data.get('logs', [])
        if logs:
            card_html.append("<h5 class='mt-3'>Recent Logs:</h5>")
            card_html.append("<div style='max-height:200px; overflow-y:auto;'>")
            for log in logs[-20:]:  # Last 20 logs
                level = log.get('level', 'info').upper()
                level_badge_class = {'DEBUG': 'secondary', 'INFO': 'info', 'WARNING': 'warning', 'ERROR': 'danger'}.get(level, 'secondary')
                card_html.append(f"<div><span class='badge bg-{level_badge_class}'>{level}</span> {log.get('message', '')}</div>")
            card_html.append("</div>")
        
        if error:
            card_html.append(f"<div class='alert alert-danger mt-3'><strong>Error:</strong> {error}</div>")
        
        return '\n'.join(card_html)


# Global emitter instance
thread_emitter_obj: Optional[ThreadEmitter] = None


def initialize_thread_emitter(socketio_obj, interval=2.0):
    """Initialize the thread emitter singleton.
    
    Args:
        socketio_obj: SocketIO instance
        interval: Emission interval in seconds
        
    Returns:
        ThreadEmitter instance
    """
    global thread_emitter_obj
    if thread_emitter_obj is None:
        thread_emitter_obj = ThreadEmitter(socketio_obj, interval)
    return thread_emitter_obj


def get_thread_emitter() -> Optional[ThreadEmitter]:
    """Get the thread emitter singleton.
    
    Returns:
        ThreadEmitter instance or None if not initialized
    """
    return thread_emitter_obj
