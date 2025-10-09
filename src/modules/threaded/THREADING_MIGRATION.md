# Threading System Migration Guide

## Overview

The threading system has been **refactored and enhanced** with new capabilities for console output, logging, and better monitoring. This guide explains the changes and how to migrate existing code.

---

## What Changed?

### 1. **New Package Structure**

The threading modules have been moved to a dedicated package:

**Old Structure:**
```
src/modules/
  ├── threaded_action.py
  └── threaded_manager.py
```

**New Structure:**
```
src/modules/threaded/
  ├── __init__.py
  ├── threaded_action.py
  └── threaded_manager.py
```

### 2. **New Console & Logging Features**

The `Threaded_action` class now includes:
- **Console output capture** - Write messages to thread-specific console
- **Structured logging** - Separate log entries with timestamps
- **Auto-capture of process output** - Process stdout/stderr automatically added to console

### 3. **Enhanced Thread Monitoring UI**

The threads page (`/threads/`) now features:
- Statistics dashboard
- Tabbed interface for each thread (Console / Logs / Process Output)
- Detailed thread view with real-time updates
- Progress bars and status indicators

---

## Breaking Changes & Migration

### Import Statements

**Before:**
```python
from src.modules.threaded_action import Threaded_action
from src.modules.threaded_manager import Threaded_manager
```

**After:**
```python
from src.modules.threaded.threaded_action import Threaded_action
from src.modules.threaded.threaded_manager import Threaded_manager

# Or use the package import
from src.modules.threaded import Threaded_action, Threaded_manager
```

---

## New Features You Should Use

### 1. **Console Writing**

Instead of only using `self.m_logger`, you can now write to a thread-specific console:

```python
class MyThread(Threaded_action):
    def action(self):
        # Write to console (visible in web UI)
        self.console_write("Starting operation", "INFO")
        self.console_write("Warning: something might fail", "WARNING")
        self.console_write("Critical error occurred", "ERROR")
        
        # Raw output (no timestamp/level)
        self.console_write_raw("Raw console output")
```

**Benefits:**
- Messages appear in web UI under "Console Output" tab
- Users can monitor progress in real-time
- Separate from file logs

### 2. **Structured Logging**

Log entries are now stored separately for better organization:

```python
class MyThread(Threaded_action):
    def action(self):
        # These appear in the "Logs" tab
        self.log_write("Operation started", "INFO")
        self.log_write("Configuration loaded", "INFO")
        self.log_write("Connection timeout", "WARNING")
```

**Difference from Console:**
- Logs are structured (timestamp, level, message as separate fields)
- Displayed in a table format in web UI
- Better for filtering and searching

### 3. **Auto-Captured Process Output**

Process stdout/stderr are now automatically captured to console:

```python
class MyThread(Threaded_action):
    def action(self):
        # Process output automatically appears in console
        self.process_exec(["python", "script.py"], ".")
        self.process_wait()
        
        # No need to manually read and log output
        # It's already in self.console_get_output()
```

---

## Migrating SSH-Based Child Classes

If you have classes that extend `Threaded_action` for SSH operations (like in the attached examples), here's what to do:

### Example: SSH Connection Class

**Your Current Code (from `threaded_action.py` in website):**
```python
class Threaded_action(threaded_action.Threaded_action):
    def __init__(self):
        super().__init__()
        self.m_ssh = None
        
    def connect(self):
        self.m_ssh = ssh_dfdig.connect(self.m_logger, client, program)
        return self.m_ssh is not None
    
    def command_exec(self, command, ssh=None):
        # SSH command execution
        ...
```

**Migration Steps:**

1. **Update imports** (as shown above)

2. **Add console logging to your methods:**
```python
def connect(self, timeout=0, interval=1):
    """Connect in ssh to the current target"""
    client = scheduler.scheduler_obj.m_target
    
    # NEW: Log connection attempt
    self.console_write(f"Connecting to {client}...", "INFO")
    
    self.m_ssh = self.connect_target(client, timeout, interval)
    
    if not self.m_ssh:
        # NEW: Log failure
        self.console_write(f"Connection to {client} failed", "ERROR")
        return False
    else:
        # NEW: Log success
        self.console_write(f"Connected to {client}", "INFO")
        return True
```

3. **Update command execution to log output:**
```python
def command_read_line_callback(self, lines: list):
    """Called for each line received from target"""
    
    # Keep your existing logic
    self.m_command_results_history += lines
    
    # NEW: Also write to console
    for line in lines:
        self.console_write_raw(line)
    
    # Your existing modal emit logic
    scheduler.scheduler_obj.emit_modal("terminal", text)
```

### Example: MCU Programming Module

**Your Current Code (from `MCU_program.py`):**
```python
class MCU_program(threaded_action.Threaded_action):
    def action(self):
        # Upload file
        self.upload(file_path, "/tmp/update.tar.gz", ssh)
        
        # Execute command
        self.command_exec(command, ssh=ssh)
        
        # Wait and parse results
        while self.m_command_running:
            infos = self.read_and_parse_data()
            # Process infos...
```

**After Migration:**
```python
from website import threaded_action  # Your SSH extension

class MCU_program(threaded_action.Threaded_action):
    def action(self):
        # NEW: Console logging for user visibility
        self.console_write("Starting MCU programming", "INFO")
        
        # Upload file
        self.console_write(f"Uploading {self.m_file}", "INFO")
        self.upload(file_path, "/tmp/update.tar.gz", ssh)
        
        # Execute command
        self.console_write("Executing flash command", "INFO")
        self.command_exec(command, ssh=ssh)
        
        # Wait and parse results
        self.console_write("Monitoring flash progress...", "INFO")
        while self.m_command_running:
            infos = self.read_and_parse_data()
            for info in infos:
                # NEW: Log parsed information
                if "Target" in info:
                    self.console_write(f"Flashing target: {info['Target']}", "INFO")
                elif "Remaining" in info:
                    self.console_write(f"Bytes remaining: {info['Remaining']}", "DEBUG")
        
        self.console_write("MCU programming complete", "INFO")
```

---

## Thread Monitoring UI

### Accessing Thread Details

Users can now:
1. View all threads at `/threads/`
2. Click "Details" on any thread
3. See tabbed interface with:
   - **Console Output**: Real-time console messages
   - **Logs**: Structured log entries in table format
   - **Process Output**: Output from local processes

### API Endpoints

New API endpoints for custom integrations:

```python
# Get all threads
GET /threads/api/threads
# Returns: {"threads": {...}, "stats": {...}}

# Get console data for specific thread
GET /threads/api/thread/<thread_name>/console
# Returns: {"console_output": [...], "logs": [...], "process_output": [...]}

# Get logs for specific thread
GET /threads/api/thread/<thread_name>/logs
# Returns: {"logs": [...]}
```

---

## Compatibility Notes

### ✅ Backward Compatible

- Existing `self.m_logger` usage still works
- Process execution (`process_exec`, `process_wait`) unchanged
- Thread lifecycle (`start()`, `delete()`) unchanged
- `command_close()` method preserved for SSH classes

### ⚠️ Requires Attention

- **Import paths** must be updated
- Child classes should add **console logging** for better UX
- SSH-based classes can benefit from **logging connection status**

---

## Testing

New test suite at `tests/test_threading.py` covers:
- Thread lifecycle (create, start, stop, delete)
- Console output (write, read, clear)
- Logging (write, read, structure)
- Process communication
- Thread manager operations
- Error handling
- Multi-threading

Run tests:
```bash
pytest tests/test_threading.py -v
```

---

## Summary Checklist

For each file that uses threading:

- [ ] Update import statements
- [ ] Add `console_write()` calls for user-visible operations
- [ ] Add `log_write()` for important events
- [ ] Test with new thread monitoring UI
- [ ] Verify error messages appear in UI
- [ ] Check console output is readable

---

## Benefits of Migration

1. **Better UX**: Users see real-time progress and logs in web UI
2. **Easier Debugging**: Console and logs separate from file logs
3. **Cleaner Code**: Structured logging vs. string concatenation
4. **Thread Safety**: Enhanced locking in thread manager
5. **Monitoring**: Statistics and status dashboard

---

## Questions?

If you encounter issues during migration:
1. Check that imports are correct
2. Verify `thread_manager_obj` is initialized
3. Check console browser for JS errors
4. Review test suite for examples

---

**Last Updated:** {{ current_date }}
**Framework Version:** 2.0 (Enhanced Threading)
