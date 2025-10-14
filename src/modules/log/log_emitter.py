"""
Log File Emitter

Background thread that periodically emits log file content via SocketIO.
Monitors all .log files in the logs directory and sends updates.
"""
import threading
import time
import os
import re
from typing import Optional, List, Dict

try:
    from .logger_factory import get_logger
    from .. import displayer
except ImportError:
    from log.logger_factory import get_logger
    import displayer


class LogEmitter:
    """Emits log file content via SocketIO at regular intervals."""
    
    def __init__(self, socket_io, logs_dir: str, interval: float = 2.0, max_lines: int = 1000, app=None):
        """
        Initialize log emitter.
        
        Args:
            socket_io: SocketIO instance for emission
            logs_dir: Path to logs directory
            interval: Update interval in seconds (default: 2.0)
            max_lines: Maximum lines to show per log file (default: 1000)
            app: Flask app instance (needed for template rendering in background thread)
        """
        self.socket = socket_io
        self.logs_dir = logs_dir
        self.interval = interval
        self.max_lines = max_lines
        self.app = app  # Store Flask app for context
        self.running = False
        self.live_mode = False  # Live mode disabled by default
        self._thread: Optional[threading.Thread] = None
        #self.logger = get_logger("log_emitter")
        
    def start(self):
        """Start the emitter background thread."""
        if self.running:
            #self.logger.warning("Log emitter already running")
            return
            
        self.running = True
        self._thread = threading.Thread(target=self._emit_loop, daemon=True)
        self._thread.start()
        #self.logger.info(f"Log emitter started")
    
    def stop(self):
        """Stop the emitter background thread."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        #self.logger.info("Log emitter stopped")
    
    def _emit_loop(self):
        """Main emission loop - runs in background thread."""
        while self.running:
            try:
                # Only emit if live mode is enabled
                if self.live_mode:
                    self._emit_log_content()
            except Exception as e:
                #self.logger.error(f"Error emitting log content: {e}")
                pass
            
            time.sleep(self.interval)
    
    def set_live_mode(self, enabled: bool):
        """
        Enable or disable live mode for real-time updates.
        
        Args:
            enabled: True to enable live updates, False to disable
        """
        self.live_mode = enabled
        #self.logger.info(f"Live mode {'enabled' if enabled else 'disabled'}")
        
        # Don't emit immediately - let the background thread handle it
        # This prevents blocking the HTTP response
    
    def get_initial_content(self, max_lines_per_file: int = 50) -> str:
        """
        Get initial log content for display (optimized, fewer lines).
        
        Args:
            max_lines_per_file: Maximum lines to show per file (default: 50)
            
        Returns:
            HTML string with log content
        """
        if not os.path.exists(self.logs_dir):
            return "<div class='alert alert-info'>Logs directory not found</div>"
        
        try:
            # Get all log files
            log_files = []
            for filename in sorted(os.listdir(self.logs_dir)):
                if filename.endswith('.log'):
                    filepath = os.path.join(self.logs_dir, filename)
                    if os.path.isfile(filepath):
                        log_files.append({
                            'name': filename,
                            'path': filepath
                        })
            
            if not log_files:
                return "<div class='alert alert-info'>No log files found</div>"
            
            # Render with limited lines
            return self._render_log_tabs_with_framework(log_files, max_lines_per_file=max_lines_per_file)
            
        except Exception as e:
            #self.logger.error(f"Error getting initial content: {e}")
            return f"<div class='alert alert-danger'>Error loading logs: {str(e)}</div>"
    
    def _emit_log_content(self):
        """Read all log files and emit their content."""
        if not os.path.exists(self.logs_dir):
            return
        
        try:
            # Get all log files
            log_files = []
            for filename in sorted(os.listdir(self.logs_dir)):
                if filename.endswith('.log'):
                    filepath = os.path.join(self.logs_dir, filename)
                    if os.path.isfile(filepath):
                        log_files.append({
                            'name': filename,
                            'path': filepath
                        })
            
            if not log_files:
                return
            
            # Render using framework's TABS layout (use 50 lines for performance)
            html = self._render_log_tabs_with_framework(log_files, max_lines_per_file=50)
            
            # Emit via socket
            self.socket.emit('reload', {
                'id': 'logs_content',
                'content': html
            })
            
        except Exception as e:
            #self.logger.error(f"Error in _emit_log_content: {e}")
            pass
    
    def _render_log_tabs_with_framework(self, log_files: List[Dict], max_lines_per_file: int = None) -> str:
        """
        Render log files using ONLY the framework's TABS layout.
        
        Args:
            log_files: List of dicts with 'name' and 'path' keys
            max_lines_per_file: Maximum lines to show per file (None = use self.max_lines)
            
        Returns:
            HTML string
        """
        render_start_time = time.time()
        
        if not log_files:
            return "<p class='text-muted'>No log files found</p>"
        
        # Use provided max_lines or default
        lines_limit = max_lines_per_file if max_lines_per_file is not None else self.max_lines
        
        # Create a Displayer instance
        create_disp_start = time.time()
        disp = displayer.Displayer()
        disp.add_generic("Logs", display=False)
        
        # Add TABS layout - one tab per log file
        tab_titles = [f['name'] for f in log_files]
        master_layout_id = disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.TABS,
            tab_titles
        ))
        create_disp_time = time.time() - create_disp_start
        
        #self.logger.debug(f"Created TABS master layout with ID {master_layout_id}, {len(tab_titles)} tabs")
        
        # Debug: Check master layout structure
        master_layout = disp.find_layout(layout_id=master_layout_id)
        #if master_layout:
        #    self.logger.debug(f"Master layout type: {master_layout.get('type')}, lines structure: {len(master_layout.get('lines', [[]]))} rows, {len(master_layout.get('lines', [[]])[0])} columns")
        
        # For each log file, add a TABLE layout inside its tab
        parse_start = time.time()
        for tab_index, log_file in enumerate(log_files):
            # Read and parse log entries with lines limit
            log_entries = self._read_and_parse_log_file(log_file['path'], max_lines=lines_limit)
            
            #self.logger.debug(f"Tab {tab_index}: Adding slave layout for {log_file['name']}, parent layout ID: {master_layout_id}")
            
            # Add TABLE layout in this tab column
            # IMPORTANT: Must explicitly pass master_layout_id, not rely on default -1
            slave = disp.add_slave_layout(
                displayer.DisplayerLayout(
                    displayer.Layouts.TABLE,
                    ["#", "Timestamp", "Level", "File:Line", "Message"]
                ),
                column=tab_index,
                layout_id=master_layout_id  # Explicitly target the TABS master layout
            )
            
            # Debug: Check if slave layout was created successfully
            if slave is None or slave == -1:
                #self.logger.error(f"Failed to create slave layout for tab {tab_index} ({log_file['name']}): returned {slave}")
                continue
            
            #self.logger.debug(f"Created slave layout {slave} for tab {tab_index} ({log_file['name']})")
            
            # Add log entries as rows
            current_line = 0
            for i, entry in enumerate(log_entries, 1):
                # Column 0: Line number
                disp.add_display_item(
                    displayer.DisplayerItemText(str(i)),
                    column=0,
                    line=current_line,
                    layout_id=slave
                )
                
                # Column 1: Timestamp
                timestamp_html = f"<small style='font-family: monospace;'>{entry['timestamp']}</small>"
                disp.add_display_item(
                    displayer.DisplayerItemText(timestamp_html),
                    column=1,
                    line=current_line,
                    layout_id=slave
                )
                
                # Column 2: Level badge
                level_badge = self._get_level_badge(entry['level'])
                disp.add_display_item(
                    displayer.DisplayerItemText(level_badge),
                    column=2,
                    line=current_line,
                    layout_id=slave
                )
                
                # Column 3: File:line
                file_line_text = entry['file_line'] if entry['file_line'] else ""
                disp.add_display_item(
                    displayer.DisplayerItemText(f"<small>{file_line_text}</small>"),
                    column=3,
                    line=current_line,
                    layout_id=slave
                )
                
                # Column 4: Message
                disp.add_display_item(
                    displayer.DisplayerItemText(entry['message']),
                    column=4,
                    line=current_line,
                    layout_id=slave
                )
                
                current_line += 1
        
        parse_time = time.time() - parse_start
        
        # Render using Flask's render_template_string
        from flask import render_template_string
        
        template_start = time.time()
        # Get the content dictionary
        content_dict = disp.display(bypass_auth=True)
        display_time = time.time() - template_start
        
        # The content_dict has module names as keys (e.g., 'Logs')
        # NOT a 'modules' list!
        if 'Logs' not in content_dict:
            return "<div class='alert alert-warning'>No log module found</div>"
        
        module_data = content_dict['Logs']
        if 'layouts' not in module_data or len(module_data['layouts']) == 0:
            return "<div class='alert alert-warning'>No layouts found</div>"
        
        # Find the TABS layout
        tabs_layout = None
        for layout in module_data['layouts']:
            if layout.get('type') == 'TABS':
                tabs_layout = layout
                break
        
        if not tabs_layout:
            return "<div class='alert alert-warning'>No TABS layout found</div>"
        
        # Render using the displayer layouts template macro
        # Need to be within Flask app context for template rendering in background thread
        template_string = """
{% import 'displayer/layouts.j2' as layouts %}
{{ layouts.display_layout(layout) }}
"""
        
        try:
            # Use stored app context for background thread
            render_html_start = time.time()
            if self.app:
                with self.app.app_context():
                    html = render_template_string(template_string, layout=tabs_layout)
                render_html_time = time.time() - render_html_start
                
                total_time = time.time() - render_start_time
                #self.logger.info(f"RENDERING TIMES: create_disp={create_disp_time:.3f}s, parse={parse_time:.3f}s, display={display_time:.3f}s, render_html={render_html_time:.3f}s, TOTAL={total_time:.3f}s")
                
                return html
            else:
                # Fallback if no app provided
                #self.logger.warning("No Flask app context available")
                return "<div class='alert alert-warning'>No Flask app context</div>"
        except Exception as e:
            #self.logger.error(f"Template rendering failed: {e}")
            return f"<div class='alert alert-danger'>Error: {str(e)}</div>"
    
    def _read_and_parse_log_file(self, filepath: str, max_lines: int = None) -> List[Dict]:
        """
        Read and parse log file into structured entries.
        
        Args:
            filepath: Path to log file
            max_lines: Maximum lines to read (None = use self.max_lines)
            
        Returns:
            List of parsed log entry dicts
        """
        start_time = time.time()
        lines_limit = max_lines if max_lines is not None else self.max_lines
        
        try:
            # Only truncate file if using default max_lines (live mode)
            if max_lines is None:
                self._truncate_log_file(filepath)
            
            # Read file and get last N lines
            read_start = time.time()
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            read_time = time.time() - read_start
            
            # Get last N lines only (optimize for initial load)
            lines = lines[-lines_limit:] if len(lines) > lines_limit else lines
            
            # Parse each line
            parse_start = time.time()
            entries = []
            for line in lines:
                if line.strip():
                    parsed = self._parse_log_line(line)
                    entries.append(parsed)
            parse_time = time.time() - parse_start
            
            total_time = time.time() - start_time
            #self.logger.info(f"File {os.path.basename(filepath)}: read={read_time:.3f}s, parse={parse_time:.3f}s, total={total_time:.3f}s, lines={len(entries)}")
            
            return entries
            
        except Exception as e:
            self.logger.error(f"Error reading log file {filepath}: {e}")
            return []
    
    def _truncate_log_file(self, filepath: str):
        """
        Truncate log file to keep only last N lines.
        
        Args:
            filepath: Path to log file
        """
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            # Only truncate if file has more than max_lines
            if len(lines) > self.max_lines:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.writelines(lines[-self.max_lines:])
        except Exception as e:
            #self.logger.error(f"Error truncating log file {filepath}: {e}")
            pass
    
    def _parse_log_line(self, line: str) -> Dict:
        """
        Parse a log line into components.
        
        Expected formats:
        1. "2025-10-09 15:45:54,146 - INFO - log.emitter - log_emitter.py:53 - Log emitter started"
           timestamp - LEVEL - module - file:line - message
        2. "2024-01-15 10:30:45,123 - LEVEL - message" (fallback)
        
        Args:
            line: Raw log line
            
        Returns:
            Dict with timestamp, file_line, level, message
        """
        # Pattern 1: timestamp - LEVEL - module - file:line - message
        pattern1 = r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d{3})\s*-\s*(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*-\s*([^\-]+?)\s*-\s*([^\-]+?\.py:\d+)\s*-\s*(.*)$'
        match1 = re.match(pattern1, line.strip())
        
        if match1:
            return {
                'timestamp': match1.group(1),
                'file_line': match1.group(4),  # file.py:215
                'level': match1.group(2),
                'message': match1.group(5)
            }
        
        # Pattern 2: timestamp - LEVEL - message (fallback)
        pattern2 = r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d{3})\s*-\s*(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*-\s*(.*)$'
        match2 = re.match(pattern2, line.strip())
        
        if match2:
            return {
                'timestamp': match2.group(1),
                'file_line': '',
                'level': match2.group(2),
                'message': match2.group(3)
            }
        
        # If no pattern matches, treat entire line as message
        return {
            'timestamp': '',
            'file_line': '',
            'level': 'INFO',
            'message': line.strip()
        }
    
    def _get_level_badge(self, level: str) -> str:
        """
        Get Bootstrap badge HTML for log level.
        
        Args:
            level: Log level
            
        Returns:
            HTML badge string
        """
        level_colors = {
            'DEBUG': 'secondary',
            'INFO': 'info',
            'WARNING': 'warning',
            'ERROR': 'danger',
            'CRITICAL': 'dark'
        }
        
        color = level_colors.get(level, 'secondary')
        return f'<span class="badge bg-{color}">{level}</span>'


# Global log emitter instance
log_emitter_obj: Optional[LogEmitter] = None


def initialize_log_emitter(socket_io, logs_dir: str, interval: float = 2.0, app=None):
    """
    Initialize and start the global log emitter.
    
    Args:
        socket_io: SocketIO instance
        logs_dir: Path to logs directory
        interval: Update interval in seconds
        app: Flask app instance (needed for template rendering in background thread)
    """
    global log_emitter_obj
    
    if log_emitter_obj is not None:
        logger = get_logger("log.emitter")
        logger.warning("Log emitter already initialized")
        return
    
    log_emitter_obj = LogEmitter(socket_io, logs_dir, interval, app=app)
    log_emitter_obj.start()


def cleanup_log_emitter():
    """Stop and cleanup the global log emitter."""
    global log_emitter_obj
    
    if log_emitter_obj is not None:
        log_emitter_obj.stop()
        log_emitter_obj = None
