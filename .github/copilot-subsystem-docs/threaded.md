# Threaded System

## Purpose
Background task execution with console output capture, progress tracking, SocketIO emission, and user isolation. Thread safety for multi-user environments.

## Core Components
- `src/modules/threaded/threaded_action.py` - Threaded_action base class
- `src/modules/threaded/threaded_manager.py` - ThreadManager (registry, lifecycle)
- `src/modules/threaded/__init__.py` - Exports, global thread_manager_obj

## Critical Patterns

### Basic Thread Implementation (MANDATORY)
```python
from modules.threaded import Threaded_action

class MyTask(Threaded_action):
    m_default_name = "My Background Task"
    m_required_permission = "MyModule"  # Module name for auth check
    m_required_action = "execute"       # Action type (default: "view")
    
    def action(self):
        """Override this - runs in background thread"""
        self.console_write("Starting task...", "INFO")
        
        for i in range(100):
            if not self.m_running:  # Check for cancellation
                self.console_write("Task cancelled", "WARNING")
                return
            
            # Progress update
            self.m_running_state = i  # -1 = indeterminate, 0-100 = percentage
            self.console_write(f"Progress: {i}%", "INFO")
            time.sleep(0.1)
        
        self.console_write("Task complete!", "INFO")
        self.m_running_state = 100

# Usage in route
thread = MyTask()
thread.start()  # Returns immediately, runs in background
```

### Console Output (Real-time to User)
```python
def action(self):
    # Standard console write
    self.console_write("Message", "INFO")  # INFO, WARNING, ERROR, DEBUG
    
    # Raw output (no timestamp)
    self.console_write_raw("Raw data\n")
    
    # Read console
    output = self.console_get_output(lines=50)  # Last 50 lines, or None for all
    
    # Clear console
    self.console_clear()
```

### Log Output (Separate from Console)
```python
def action(self):
    # Write log entry
    self.log_write("Important event", "INFO")
    
    # Read logs
    logs = self.log_get_entries(lines=100)
    # Returns: [{"timestamp": "...", "level": "INFO", "message": "..."}, ...]
    
    # Clear logs
    self.log_clear()
```

### Process Execution (Subprocess)
```python
def action(self):
    # Non-blocking process start
    self.process_exec(
        command=["python", "script.py"],
        source_folder="/path/to/dir",
        shell=True
    )
    
    # Wait for completion (optional timeout)
    self.process_wait(timeout=60)
    
    # Read output (stdout/stderr captured)
    results = self.process_format_results()
    
    # Or read raw results
    raw = self.process_read_results()
    
    # Kill process
    self.process_close()
```

### User Context (Multi-user Isolation)
```python
def action(self):
    # Get current user (captured from session at start())
    user = self.get_current_user()  # "admin", "user1", etc.
    
    # Check permissions
    if self.has_permission("write"):
        self.console_write("User has write access", "INFO")
    
    # Get all permissions
    perms = self.get_user_permissions()  # ["view", "edit", "execute"]
    
    # Check if guest
    if self.is_guest_user():
        self.console_write("Running as guest", "WARNING")
    
    # Check read-only mode
    if self.is_readonly_mode():
        self.console_write("Read-only access", "INFO")
```

### User Preferences
```python
def action(self):
    # Get module-specific preference
    port = self.get_user_pref("default_serial_port", "COM1")
    timeout = self.get_user_pref("timeout", 60)
    
    self.console_write(f"Using port {port} with timeout {timeout}s", "INFO")
```

### Thread Management
```python
# In route handler
from modules.threaded import thread_manager_obj

# Get thread by name
threads = thread_manager_obj.get_threads_by_name("My Task")

# Get all running threads
all_threads = thread_manager_obj.m_running_threads

# Delete thread (stops it)
thread.delete()  # Auto-unregisters and force-stops
```

## API Quick Reference
```python
class Threaded_action:
    # Class attributes (override these)
    m_default_name = "Default name"
    m_required_permission = None  # Module name or None
    m_required_action = "view"    # Action type
    
    # Instance attributes
    m_running: bool               # Is thread running?
    m_running_state: int          # Progress (-1 = indeterminate, 0-100 = %)
    m_error: Optional[str]        # Error message if failed
    m_background: bool            # Keep after completion?
    username: Optional[str]       # User who started thread
    
    # Console
    def console_write(message: str, level: str = "INFO")
    def console_write_raw(message: str)
    def console_get_output(lines: Optional[int] = None) -> List[str]
    def console_clear()
    
    # Logs
    def log_write(message: str, level: str = "INFO")
    def log_get_entries(lines: Optional[int] = None) -> List[Dict]
    def log_clear()
    
    # Process
    def process_exec(command: list, source_folder: str, shell=True, inputs=None)
    def process_wait(timeout: Optional[float] = None)
    def process_close()
    def process_format_results() -> list
    
    # User context
    def get_current_user() -> Optional[str]
    def get_user_permissions() -> List[str]
    def has_permission(action: str) -> bool
    def is_guest_user() -> bool
    def is_readonly_mode() -> bool
    def get_user_pref(key: str, default=None)
    
    # Lifecycle
    def start()  # Start thread (returns immediately)
    def delete()  # Stop and unregister
    def is_running() -> bool
    def get_progress() -> int
    def get_error() -> Optional[str]
    
    # Override this
    def action()  # Main thread function
```

## Common Pitfalls
1. **Check m_running** - Threads should periodically check `self.m_running` for cancellation
2. **User context** - Set at `start()` from session; not available in `__init__()`
3. **SocketIO emission** - Use scheduler, not direct socketio calls (handled by framework)
4. **Progress updates** - Set `m_running_state` for UI progress bar
5. **Error handling** - Set `self.m_error` on failure; framework displays it
6. **Background flag** - Set `m_background=True` to keep thread after completion
7. **Console vs logs** - Console for real-time output, logs for structured events
8. **Process blocking** - `process_exec()` is non-blocking; use `process_wait()` to wait
9. **Thread safety** - Console has `_console_lock`; use it for custom shared data
10. **Auto-registration** - Thread registers itself in `__init__`; no manual registration needed

## Integration Points
- **ThreadManager**: Auto-registration on init, lifecycle management
- **SocketIO**: User-isolated rooms via `username` and `user_session_id`
- **Scheduler**: Polls threads, emits progress updates to web UI
- **Auth**: Permission checks via `m_required_permission` and `m_required_action`
- **Logger**: `self.m_logger` for file logging (separate from console)

## Files
- `threaded_action.py` - Base class with console, process, user context
- `threaded_manager.py` - ThreadManager singleton (registry)
- `__init__.py` - Exports, `thread_manager_obj` global
