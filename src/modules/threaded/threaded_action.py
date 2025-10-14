"""
Threaded Action - Base class for long-running threaded operations.

This module provides a base class for executing long-term actions with:
- Thread lifecycle management
- Console output capture (process and custom)
- Logging integration
- Progress tracking
- Communication with local processes
"""

import threading
import time
import copy
import subprocess
import traceback
from collections import deque
from typing import Optional, List, Dict, Any


try:
    from . import threaded_manager
    from .. import scheduler
    from ..logger_factory import get_logger
except ImportError:
    import threaded_manager
    import scheduler
    from logger_factory import get_logger


class Threaded_action:
    """Base class to execute long term action with console and logging support.
    
    It registers itself on the thread manager and handles the creation and 
    destruction of the python thread. Moreover, it provides:
    - Helper functions to communicate with the host (Windows, Linux, macOS)
    - Console output management for displaying in web UI
    - Logging capabilities specific to each thread
    - Process communication and monitoring
    """

    m_scheduler = None
    """Link to the scheduler object"""

    m_default_name = "Default name"
    """The default name of the module"""

    m_type = "threaded_action"
    """The type of the module"""

    m_error = None
    """A possible error that can be appended to the module for display option"""
    
    m_required_permission = None
    """The permission module name required to access this module (e.g., 'Demo_Threading'). None means no permission check."""
    
    m_required_action = 'view'
    """The action required to access this module (e.g., 'view', 'execute', 'edit'). Default is 'view'."""
    
    # User context - set by framework when module is loaded
    _current_user = None
    _user_permissions = []
    _is_guest = False
    _is_readonly = True
    
    def __init__(self):       
        """Constructor - Initializes thread, console, logging, and process management"""
        self.m_name = None

        # Thread management
        self.m_thread_action = None
        self.m_thread_command = None
        self.m_thread_process_stdout = None
        self.m_thread_process_stderr = None

        # Running state
        self.m_running = False
        self.m_running_state = -1  # -1 indicates a task running without percentage info

        # Process management
        self.m_process = None
        self.m_process_running = False
        self.m_process_results = []
        self.m_stderr = None
        self.m_stdout = None
        self.m_process_input = []

        # Console management - NEW FEATURE
        self._console_lock = threading.Lock()
        self._console_output = deque(maxlen=1000)  # Last 1000 lines
        self._console_logs = deque(maxlen=500)     # Last 500 log entries
        
        # Background flag
        self.m_background = False

        # User preferences - NEW FEATURE
        self.m_user_prefs = {}  # Injected by route handler

        # Logger initialization
        self.m_logger = None
        self._init_logger()

        # Register the thread
        threaded_manager.thread_manager_obj.add_thread(self)

        self.m_scheduler = scheduler.scheduler_obj

    def _init_logger(self):
        """Initialize logger with custom handler for console capture"""
        self.m_logger = get_logger("threaded_action")
        self.m_logger.info(f"Threaded action '{self.get_name()}' initialized")

    def __del__(self):
        """Destructor"""
        if self.m_logger:
            self.m_logger.info(f"Threaded action '{self.get_name()}' destroyed")

    # ============================================================================
    # USER CONTEXT API - NEW FUNCTIONALITY
    # ============================================================================
    
    def get_current_user(self) -> Optional[str]:
        """
        Get the current logged-in username.
        
        Returns:
            Username or None if not set
        """
        return self._current_user
    
    def get_user_permissions(self) -> List[str]:
        """
        Get all permissions the current user has for this module.
        
        Returns:
            List of permission actions (e.g., ['view', 'edit', 'execute'])
        """
        return self._user_permissions.copy() if self._user_permissions else []
    
    def is_guest_user(self) -> bool:
        """
        Check if the current user is a guest.
        
        Returns:
            True if user is GUEST
        """
        return self._is_guest
    
    def is_readonly_mode(self) -> bool:
        """
        Check if the module is in read-only mode for the current user.
        
        A module is read-only if the user doesn't have write/edit/execute permissions.
        
        Returns:
            True if read-only (user can only view)
        """
        return self._is_readonly
    
    def has_permission(self, action: str) -> bool:
        """
        Check if the current user has a specific permission for this module.
        
        Args:
            action: Permission to check (e.g., 'write', 'edit', 'execute')
        
        Returns:
            True if user has the permission
        """
        return action in self._user_permissions if self._user_permissions else False

    # ============================================================================
    # CONSOLE MANAGEMENT - NEW FUNCTIONALITY
    # ============================================================================

    def console_write(self, message: str, level: str = "INFO"):
        """Write a message to the thread's console output.
        
        This is the main method for modules to write to their own console.
        Messages are stored and can be retrieved for display in the web UI.
        
        Args:
            message: The message to write
            level: Log level (INFO, WARNING, ERROR, DEBUG)
        """
        with self._console_lock:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            formatted_msg = f"[{timestamp}] [{level}] {message}"
            self._console_output.append(formatted_msg)
            
            # Also log it
            if level == "ERROR":
                self.m_logger.error(message)
            elif level == "WARNING":
                self.m_logger.warning(message)
            elif level == "DEBUG":
                self.m_logger.debug(message)
            else:
                self.m_logger.info(message)

    def console_write_raw(self, message: str):
        """Write raw message to console without timestamp or level.
        
        Args:
            message: The raw message to write
        """
        with self._console_lock:
            self._console_output.append(message)

    def console_get_output(self, lines: Optional[int] = None) -> List[str]:
        """Get console output lines.
        
        Args:
            lines: Number of lines to retrieve (None = all)
            
        Returns:
            List of console output lines
        """
        with self._console_lock:
            if lines is None:
                return list(self._console_output)
            else:
                return list(self._console_output)[-lines:]

    def console_clear(self):
        """Clear the console output"""
        with self._console_lock:
            self._console_output.clear()

    def log_write(self, message: str, level: str = "INFO"):
        """Write a log entry (separate from console output).
        
        This stores logs separately for the "logs" tab in the UI.
        
        Args:
            message: The log message
            level: Log level (INFO, WARNING, ERROR, DEBUG)
        """
        with self._console_lock:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_entry = {
                "timestamp": timestamp,
                "level": level,
                "message": message
            }
            self._console_logs.append(log_entry)

    # ============================================================================
    # USER PREFERENCES - NEW FUNCTIONALITY
    # ============================================================================

    def get_user_pref(self, key: str, default=None):
        """Access user preference for this module.
        
        User preferences are stored per-user and per-module, allowing modules
        to remember user-specific settings like serial ports, timeouts, etc.
        
        Args:
            key: Preference key to retrieve
            default: Default value if key not found
            
        Returns:
            The preference value or default
            
        Example:
            port = self.get_user_pref("default_serial_port", "COM1")
            timeout = self.get_user_pref("timeout", 60)
        """
        module_prefs = self.m_user_prefs.get("module_settings", {}).get(self.m_default_name, {})
        return module_prefs.get(key, default)

    def log_get_entries(self, lines: Optional[int] = None) -> List[Dict[str, str]]:
        """Get log entries.
        
        Args:
            lines: Number of entries to retrieve (None = all)
            
        Returns:
            List of log entry dictionaries
        """
        with self._console_lock:
            if lines is None:
                return list(self._console_logs)
            else:
                return list(self._console_logs)[-lines:]

    def log_clear(self):
        """Clear the log entries"""
        with self._console_lock:
            self._console_logs.clear()

    def get_console_data(self) -> Dict[str, Any]:
        """Get all console and log data for display.
        
        Returns:
            Dictionary with console output, logs, and other display data
        """
        return {
            "console_output": self.console_get_output(),
            "logs": self.log_get_entries(),
            "process_output": self.process_format_results() if self.m_process else [],
            "running": self.m_running,
            "progress": self.m_running_state,
            "error": self.m_error
        }

    # ============================================================================
    # THREAD MANAGEMENT
    # ============================================================================

    def get_name(self) -> str:
        """Return the name of the instance.
        
        Returns:
            The name of the instance
        """
        if self.m_name:
            return self.m_name
        return self.m_default_name

    def change_name(self, name: str):
        """Change the name of the instance.
        
        Args:
            name: The new name
        """
        self.m_name = name
        self.console_write(f"Thread renamed to: {name}", "INFO")

    def delete(self):
        """Delete the thread and unregister it from the thread manager"""
        self.console_write("Thread deletion requested", "WARNING")
        self.m_running = False
        threaded_manager.thread_manager_obj.del_thread(self)

    # ============================================================================
    # PROCESS MANAGEMENT
    # ============================================================================

    def process_exec(self, command: list, source_folder: str, shell=True, inputs=None):
        """Execute a local process command (non-blocking).
        
        This function returns immediately. Use process_wait() to wait for completion.
        
        Args:
            command: The command to execute
            source_folder: The relative path of execution
            shell: The shell argument of subprocess
            inputs: A list with detection of specific string and how to react
        """
        self.console_write(f"Executing process: {' '.join(command)}", "INFO")
        
        try:
            self.m_process = subprocess.Popen(
                command,
                cwd=source_folder,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                universal_newlines=True,
                shell=shell,
            )
            self.m_process_running = True

            # Start reading threads
            self.m_thread_process_stdout = threading.Thread(
                target=self.process_read_stdout, daemon=True
            )
            self.m_thread_process_stdout.start()
            
            self.m_thread_process_stderr = threading.Thread(
                target=self.process_read_stderr, daemon=True
            )
            self.m_thread_process_stderr.start()
            
            self.console_write(f"Process started (PID: {self.m_process.pid})", "INFO")
        except Exception as e:
            self.console_write(f"Failed to start process: {e}", "ERROR")
            self.m_logger.error(f"Process execution failed: {e}")

    def process_close(self):
        """Kill and close the local process"""
        if self.m_process:
            self.console_write(f"Killing process (PID: {self.m_process.pid})", "WARNING")
            self.m_process.kill()
            self.m_process = None
            self.m_process_running = False

    def process_format_results(self) -> list:
        """Format the results of the process, and reset them.
        
        By default, the formatting does nothing and just returns the raw data.
        
        Returns:
            The result of the last executed (or executing) process
        """
        result = copy.copy(self.m_process_results)
        self.m_process_results = []
        return result

    def process_delete_results(self):
        """Delete the results of the process"""
        self.m_process_results = []

    def process_read_stderr(self):
        """Read thread for the error output of the currently executing local process"""
        while self.m_process and self.m_process.poll() is None:
            try:
                line = self.m_process.stderr.readline()
                if line:
                    self.m_process_results.append(line)
                    self.console_write_raw(f"[STDERR] {line.strip()}")
            except Exception as e:
                self.console_write(f"Error reading stderr: {e}", "ERROR")
                self.m_process_running = False
            time.sleep(0.1)

        # Process is done, read any remaining lines
        try:
            lines = self.m_process.stderr.readlines()
            for line in lines:
                self.m_process_results.append(line)
                self.console_write_raw(f"[STDERR] {line.strip()}")
            self.m_process_running = False
        except Exception:
            self.m_process_running = False
        return

    def process_read_stdout(self):
        """Read thread for the standard output of the currently executing local process"""
        while self.m_process_running and self.m_process.poll() is None:
            try:
                line = self.m_process.stdout.readline()
                if line:
                    if self.m_process_input:
                        if self.m_process_input[0] in line:
                            self.m_process.communicate(input=self.m_process_input[1])
                    self.m_process_results.append(line)
                    self.console_write_raw(f"[STDOUT] {line.strip()}")
            except Exception as e:
                self.console_write(f"Error reading stdout: {e}", "ERROR")
                self.m_process_running = False
            time.sleep(0.1)

        # Process is done, read any remaining lines
        try:
            lines = self.m_process.stdout.readlines()
            for line in lines:
                self.m_process_results.append(line)
                self.console_write_raw(f"[STDOUT] {line.strip()}")
            self.m_process_running = False
        except Exception:
            self.m_process_running = False
        return

    def process_wait(self, timeout: Optional[float] = None):
        """Wait for the currently executing local process to finish.
        
        Args:
            timeout: Maximum time to wait in seconds (None = wait forever)
        """
        start_time = time.time()
        while True:
            time.sleep(0.3)
            if not self.m_process_running:
                self.console_write("Process completed", "INFO")
                return
            if timeout and (time.time() - start_time) >= timeout:
                self.console_write(f"Process wait timeout after {timeout}s", "WARNING")
                return

    def process_read_results(self):
        """Read the raw results of the last executed (executing) process, and delete them"""
        result = copy.copy(self.m_process_results)
        self.m_process_results = []
        return result

    # ============================================================================
    # COMPATIBILITY METHODS (for SSH-based child classes)
    # ============================================================================

    def command_close(self):
        """For compatibility with SSH-based implementations"""
        return

    # ============================================================================
    # THREAD EXECUTION
    # ============================================================================

    def action(self):
        """Main function of this thread - Override this in child classes"""
        self.console_write("Default action - override this method", "WARNING")
        return

    def thread_process(self):
        """Thread function wrapper with error handling"""
        self.m_running = True
        self.console_write(f"Thread '{self.get_name()}' started", "INFO")
        
        try:
            self.action()
            self.console_write(f"Thread '{self.get_name()}' completed successfully", "INFO")
        except Exception as e:
            traceback_str = traceback.format_exc()
            self.console_write(f"Thread failed: {e}", "ERROR")
            self.m_logger.warning(f"Thread '{self.get_name()}' failed: {e}")
            self.m_logger.info(f"Traceback: {traceback_str}")
            self.m_error = str(e)
            
        self.m_running = False
        if not self.m_background:
            # Small delay to allow reading threads to finish
            time.sleep(0.5)
            self.delete()
        return

    def start(self):
        """Start the thread"""
        self.console_write(f"Starting thread '{self.get_name()}'", "INFO")
        self.m_thread_action = threading.Thread(target=self.thread_process, daemon=True)
        self.m_thread_action.start()
        return

    def wait_finished(self):
        """Wait for the thread to finish"""
        if self.m_thread_action:
            self.m_thread_action.join()
        return
