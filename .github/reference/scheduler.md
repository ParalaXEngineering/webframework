# Scheduler System

## Purpose
Periodic task polling and SocketIO message emission to web clients. Queues messages, groups by user, emits to isolated rooms. Main loop for UI updates.

## Core Components
- `src/modules/scheduler/scheduler.py` - Scheduler main loop, emit methods
- `src/modules/scheduler/message_queue.py` - MessageQueue, MessageType enum
- `src/modules/scheduler/emitter.py` - MessageEmitter (SocketIO wrapper)

## Critical Patterns

### Emit from Thread (MANDATORY)
```python
from modules.threaded import Threaded_action

class MyTask(Threaded_action):
    def action(self):
        # Status update (progress bar)
        self.m_scheduler.emit_status(
            category="task",
            string="Processing files",
            status=50,  # 0-100%, 101 = error
            supplement="File 5/10"
        )
        
        # Popup notification
        from modules.scheduler.scheduler import logLevel
        self.m_scheduler.emit_popup(logLevel.success, "Task complete!")
        
        # Result output
        self.m_scheduler.emit_result("success", "<p>Operation successful</p>")
```

### Status Updates (Progress)
```python
# Basic status
scheduler_obj.emit_status("category", "Loading...", status=0)

# With progress
scheduler_obj.emit_status("category", "Processing", status=50, supplement="Item 5/10")

# Error state
scheduler_obj.emit_status("category", "Failed", status=101)

# Updatable status (use status_id)
scheduler_obj.emit_status(
    category="upload",
    string="Uploading files",
    status=25,
    status_id="upload_progress"  # Same ID updates existing line
)
```

### Popups
```python
from modules.scheduler.scheduler import logLevel

scheduler_obj.emit_popup(logLevel.success, "File uploaded successfully")
scheduler_obj.emit_popup(logLevel.info, "Starting backup...")
scheduler_obj.emit_popup(logLevel.warning, "Disk space low")
scheduler_obj.emit_popup(logLevel.error, "Connection failed")
```

### Button Updates
```python
# Change button content
scheduler_obj.emit_button("btn_id", "mdi-check", "Complete", style="success")

# Enable/disable
scheduler_obj.disable_button("btn_submit")
scheduler_obj.enable_button("btn_submit")
```

### Form Reload
```python
# Reload form elements (after data change)
scheduler_obj.emit_reload([
    {"id": "form_field_1", "content": "<input value='new_value'>"},
    {"id": "form_field_2", "content": "<select>...</select>"}
])
```

### Modal Update
```python
scheduler_obj.emit_modal("modal_id", "<div>New modal content</div>")
```

## API Quick Reference
```python
class Scheduler:
    # Status/Progress
    def emit_status(category: str, string: str, status: int = 0, 
                   supplement: str = "", status_id: Optional[str] = None)
    
    # Notifications
    def emit_popup(level: logLevel, string: str)
    def emit_result(category: str, content: str)  # Bootstrap category
    
    # UI Updates
    def emit_button(id: str, icon: str, text: str, style: str = "primary")
    def disable_button(id: str)
    def enable_button(id: str)
    def emit_modal(id: str, content: str)
    def emit_reload(content: list)  # [{"id": "...", "content": "..."}]
    
    # Lifecycle
    def start()  # Starts main loop (blocking)

class logLevel(Enum):
    success = 0  # Green
    info = 1     # Blue
    warning = 2  # Orange
    error = 3    # Red
    empty = 4    # Neutral

# Global singleton
from modules.scheduler import scheduler_obj
```

## Common Pitfalls
1. **User isolation** - Emits auto-route to user's room via `_get_current_username()` from thread context
2. **Blocking loop** - `start()` is blocking; run in background thread (framework handles this)
3. **Queue limit** - Modals limited to last 5 to prevent memory issues
4. **Status ID** - Use `status_id` to update existing line, not create new one
5. **HTML escaping** - Content can include HTML; escape user input to prevent XSS
6. **Thread context** - Called FROM Threaded_action.action(), not from routes
7. **Bootstrap styles** - Use "success", "danger", "warning", "info", "primary", etc.
8. **Icon format** - Use MDI icons (e.g., "mdi-check", "mdi-alert")

## Integration Points
- **SocketIO**: Uses socketio_manager for user-isolated emission
- **Threaded**: Accessed via `self.m_scheduler` in Threaded_action
- **MessageQueue**: Queues messages by type and username
- **MessageEmitter**: Batches and emits messages to SocketIO rooms
- **ThreadManager**: Polls thread info (progress, state) for UI updates

## Files
- `scheduler.py` - Main Scheduler class, emit methods, main loop
- `message_queue.py` - MessageQueue, MessageType, QueuedMessage dataclass
- `emitter.py` - MessageEmitter for SocketIO emission
- `__init__.py` - Exports, `scheduler_obj` global
