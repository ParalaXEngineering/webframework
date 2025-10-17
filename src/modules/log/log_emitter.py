"""
Log File Emitter

Background thread that periodically emits log file content via SocketIO.
Monitors all .log files in the logs directory and sends updates as JSON data.
"""
import threading
import time
import os
import re
from typing import Optional, List, Dict, Set

try:
    from .logger_factory import get_logger
    from ..socketio_manager import socketio_manager
except ImportError:
    from log.logger_factory import get_logger
    from socketio_manager import socketio_manager


class LogEmitter:
    """Emits log file content via SocketIO at regular intervals as structured JSON."""
    
    def __init__(self, socket_io, logs_dir: str, interval: float = 2.0, max_lines: int = 1000):
        """
        Initialize log emitter.
        
        Args:
            socket_io: SocketIO instance for emission
            logs_dir: Path to logs directory
            interval: Update interval in seconds (default: 2.0)
            max_lines: Maximum lines to show per log file (default: 1000)
        """
        self.socket = socket_io
        self.logs_dir = logs_dir
        self.interval = interval
        self.max_lines = max_lines
        self.running = False
        
        # Multi-user support: Track which users have live mode enabled
        self.live_mode_users: Set[str] = set()  # Set of usernames with live mode enabled
        self._lock = threading.Lock()  # Thread-safe access to live_mode_users
        
        self._thread: Optional[threading.Thread] = None
        self.logger = get_logger("log.emitter")
        
    def start(self):
        """Start the emitter background thread."""
        if self.running:
            self.logger.warning("Log emitter already running")
            return
            
        self.running = True
        self._thread = threading.Thread(target=self._emit_loop, daemon=True)
        self._thread.start()
        self.logger.info("Log emitter started")
    
    def stop(self):
        """Stop the emitter background thread."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        self.logger.info("Log emitter stopped")
    
    def _emit_loop(self):
        """Main emission loop - runs in background thread."""
        while self.running:
            try:
                # Only emit if at least one user has live mode enabled
                with self._lock:
                    has_live_users = len(self.live_mode_users) > 0
                
                if has_live_users:
                    self._emit_log_content()
            except Exception as e:
                self.logger.error(f"Error emitting log content: {e}")
            
            time.sleep(self.interval)
    
    def set_live_mode(self, username: str, enabled: bool):
        """
        Enable or disable live mode for a specific user.
        
        Args:
            username: Username to enable/disable live mode for
            enabled: True to enable live updates, False to disable
        """
        with self._lock:
            if enabled:
                self.live_mode_users.add(username)
                self.logger.info(f"Live mode enabled for user: {username}")
            else:
                self.live_mode_users.discard(username)
                self.logger.info(f"Live mode disabled for user: {username}")
    
    def is_live_mode_enabled(self, username: str) -> bool:
        """
        Check if live mode is enabled for a specific user.
        
        Args:
            username: Username to check
            
        Returns:
            True if live mode enabled for this user
        """
        with self._lock:
            return username in self.live_mode_users
    
    def get_log_data(self, max_lines_per_file: int = 50) -> Dict:
        """
        Get structured log data for all log files.
        
        Args:
            max_lines_per_file: Maximum lines to read per file (default: 50)
            
        Returns:
            Dictionary with log file data: {
                'files': [{'name': str, 'entries': [parsed_entries]}],
                'error': str (optional)
            }
        """
        if not os.path.exists(self.logs_dir):
            return {'error': 'Logs directory not found'}
        
        try:
            log_files_data = []
            for filename in sorted(os.listdir(self.logs_dir)):
                if filename.endswith('.log'):
                    filepath = os.path.join(self.logs_dir, filename)
                    if os.path.isfile(filepath):
                        entries = self._read_and_parse_log_file(filepath, max_lines=max_lines_per_file)
                        log_files_data.append({
                            'name': filename,
                            'entries': entries
                        })
            
            return {'files': log_files_data}
            
        except Exception as e:
            self.logger.error(f"Error getting log data: {e}")
            return {'error': str(e)}
    
    def _emit_log_content(self):
        """Read all log files and emit their content as JSON to users with live mode enabled."""
        try:
            # Get structured log data
            log_data = self.get_log_data(max_lines_per_file=50)
            
            # Get copy of live mode users (thread-safe)
            with self._lock:
                live_users = list(self.live_mode_users)
            
            # Emit to each user with live mode enabled
            for username in live_users:
                try:
                    socketio_manager.emit_to_user('log_update', log_data, username=username)
                except Exception as e:
                    self.logger.error(f"Error emitting log update to user {username}: {e}")
            
        except Exception as e:
            self.logger.error(f"Error in _emit_log_content: {e}")
    
    def _read_and_parse_log_file(self, filepath: str, max_lines: Optional[int] = None) -> List[Dict]:
        """
        Read and parse log file into structured entries.
        
        Args:
            filepath: Path to log file
            max_lines: Maximum lines to read (None = use self.max_lines)
            
        Returns:
            List of parsed log entry dicts
        """
        lines_limit = max_lines if max_lines is not None else self.max_lines
        
        try:
            # Only truncate file if using default max_lines (live mode)
            if max_lines is None:
                self._truncate_log_file(filepath)
            
            # Read file and get last N lines
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            # Get last N lines only (optimize for initial load)
            lines = lines[-lines_limit:] if len(lines) > lines_limit else lines
            
            # Parse each line
            entries = []
            for line in lines:
                if line.strip():
                    parsed = self._parse_log_line(line)
                    entries.append(parsed)
            
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
            self.logger.error(f"Error truncating log file {filepath}: {e}")
    
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


# Global log emitter instance
log_emitter_obj: Optional[LogEmitter] = None


def initialize_log_emitter(socket_io, logs_dir: str, interval: float = 2.0):
    """
    Initialize and start the global log emitter.
    
    Args:
        socket_io: SocketIO instance
        logs_dir: Path to logs directory
        interval: Update interval in seconds
    """
    global log_emitter_obj
    
    if log_emitter_obj is not None:
        logger = get_logger("log.emitter")
        logger.warning("Log emitter already initialized")
        return
    
    log_emitter_obj = LogEmitter(socket_io, logs_dir, interval)
    log_emitter_obj.start()


def cleanup_log_emitter():
    """Stop and cleanup the global log emitter."""
    global log_emitter_obj
    
    if log_emitter_obj is not None:
        log_emitter_obj.stop()
        log_emitter_obj = None
