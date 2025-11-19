# Log System

## Purpose
Unified logging with rotating file handlers and console output. Thread-safe logger creation with standardized formatting.

## Core Components
- `src/modules/log/logger_factory.py` - get_logger() factory function
- `logs/` - Log file directory (auto-created)

## Critical Patterns

### Get Logger (MANDATORY)
```python
from modules.log.logger_factory import get_logger

# In module/class
logger = get_logger("my_module")
logger.info("Application started")
logger.debug("Detailed debug info")
logger.warning("Something unexpected")
logger.error("Operation failed")
```

### Exception Logging
```python
try:
    risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)  # Includes traceback
```

### HTML Exception Formatting
```python
from modules.log.logger_factory import format_exception_html

try:
    operation()
except Exception as e:
    # Single-line HTML for web display
    html_error = format_exception_html(e, include_traceback=True)
    logger.error(html_error)
    # Returns: "Error message<br>Traceback line 1<br>Traceback line 2..."
```

### Custom Logger Config
```python
# Override defaults (rare)
logger = get_logger(
    "custom_module",
    level=logging.INFO,        # Default: DEBUG
    max_bytes=5_000_000,       # Default: 1MB
    backup_count=10            # Default: 5 backups
)
```

## API Quick Reference
```python
def get_logger(
    name: str,
    level: int = logging.DEBUG,
    max_bytes: int = 1_000_000,
    backup_count: int = 5
) -> logging.Logger

def format_exception_html(
    exc: Exception,
    include_traceback: bool = True
) -> str

# Logger methods (standard logging module)
logger.debug(msg, *args, **kwargs)
logger.info(msg, *args, **kwargs)
logger.warning(msg, *args, **kwargs)
logger.error(msg, *args, **kwargs, exc_info=False)
logger.critical(msg, *args, **kwargs)
```

## Common Pitfalls
1. **Duplicate handlers** - get_logger() checks for existing handlers; safe to call multiple times
2. **Thread safety** - Uses `_logger_lock` for handler creation; safe in multi-threaded apps
3. **Log directory** - Auto-created at `logs/` relative to working directory
4. **File rotation** - Size-based (default 1MB), not time-based
5. **Propagation** - Set to False to prevent duplicate logs from ancestor loggers
6. **exc_info** - Must pass `exc_info=True` to include traceback in error logs
7. **Format string** - Uses standard format: `%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - %(message)s`
8. **Console output** - Always enabled; both file and console handlers attached

## Integration Points
- **Threaded**: Each Threaded_action has `self.m_logger` for thread-specific logging
- **Auth**: AuthManager logs user operations (login, permission changes)
- **FileManager**: Logs uploads, deletes, integrity checks
- **Scheduler**: Logs emission errors, thread polling
- **SocketIO**: Logs connection events, room management

## Files
- `logger_factory.py` - get_logger() and format_exception_html()
- `logs/*.log` - Rotating log files (one per logger name)
- `logs/*.log.1`, `*.log.2`, etc. - Rotated backups (up to backup_count)
