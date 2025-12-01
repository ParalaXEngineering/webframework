# Refactoring: Split main.py into Initialization Modules

## Problem

`main.py` is a 750+ line monster that handles too many responsibilities:
- Flask app configuration
- Blueprint discovery and registration
- Auth manager initialization
- Settings manager initialization  
- File manager initialization
- Scheduler initialization (real-time + long-term)
- Thread manager initialization
- Log emitter initialization
- Thread emitter initialization
- SocketIO handlers (connect, disconnect, events)
- Context processors (5 of them)
- Error handlers
- CSRF token generation
- Route definitions

This violates Single Responsibility Principle and makes the code hard to test and maintain.

## Proposed Solution

Create an `initialization/` package with focused modules:

```
src/
├── main.py                    # Slim orchestrator only
└── initialization/
    ├── __init__.py
    ├── flask_config.py        # Flask app configuration
    ├── blueprints.py          # Blueprint discovery and registration
    ├── managers.py            # Auth, Settings, FileManager init
    ├── schedulers.py          # Scheduler and ThreadManager init
    ├── emitters.py            # Log and Thread emitters
    ├── socketio_handlers.py   # SocketIO event handlers
    ├── context_processors.py  # All context processors
    └── error_handlers.py      # Error handling routes
```

## Implementation Plan

### Phase 1: Extract Context Processors

Create `initialization/context_processors.py`:

```python
"""Context processors for template injection."""
from typing import Any, Dict
from flask import session, request
from ..modules.app_context import app_context


def register_context_processors(app) -> None:
    """Register all context processors with the Flask app."""
    app.context_processor(inject_bar)
    app.context_processor(inject_endpoint)
    app.context_processor(inject_csrf_token)
    app.context_processor(inject_resources)
    app.context_processor(inject_user_theme)


def inject_bar() -> Dict[str, Any]:
    """Inject sidebar and topbar items."""
    # Move existing inject_bar logic here
    ...


def inject_endpoint() -> Dict[str, Any]:
    """Inject request endpoint and page info."""
    ...


def inject_csrf_token() -> Dict[str, Any]:
    """Generate and inject CSRF token."""
    ...


def inject_resources() -> Dict[str, Any]:
    """Inject required CSS/JS resources."""
    ...


def inject_user_theme() -> Dict[str, Any]:
    """Inject user's theme preference."""
    ...
```

### Phase 2: Extract Manager Initialization

Create `initialization/managers.py`:

```python
"""Manager initialization for auth, settings, file management."""
from typing import TYPE_CHECKING
from ..modules.app_context import app_context

if TYPE_CHECKING:
    from flask import Flask


def initialize_auth_manager(app_path: str, site_config) -> None:
    """Initialize authentication manager if enabled."""
    if not site_config.m_enable_authentication:
        app_context.auth_manager = None
        return
    
    from ..modules.auth.auth_manager import AuthManager
    # ... initialization logic


def initialize_settings_manager(config_path: str, site_config) -> None:
    """Initialize settings manager (always enabled)."""
    from ..modules.settings import SettingsManager
    # ... initialization logic


def initialize_file_manager(settings_manager, site_config) -> None:
    """Initialize file manager if enabled."""
    if not site_config.m_enable_file_manager:
        return
    # ... initialization logic
```

### Phase 3: Extract Scheduler Initialization

Create `initialization/schedulers.py`:

```python
"""Scheduler and thread manager initialization."""
from ..modules.app_context import app_context


def initialize_schedulers(app_path: str, site_config, socketio) -> None:
    """Initialize all schedulers based on feature flags."""
    if site_config.m_enable_scheduler:
        _init_realtime_scheduler(app_path, socketio)
    
    if site_config.m_enable_long_term_scheduler:
        _init_longterm_scheduler()
    
    if site_config.m_enable_threads:
        _init_thread_manager()


def _init_realtime_scheduler(app_path: str, socketio) -> None:
    """Initialize real-time scheduler."""
    ...


def _init_longterm_scheduler() -> None:
    """Initialize long-term scheduler."""
    ...


def _init_thread_manager() -> None:
    """Initialize thread manager."""
    ...
```

### Phase 4: Slim main.py

After extraction, `main.py` becomes:

```python
"""ParalaX Web Framework - Main application entry point."""
from flask import Flask
from .initialization import (
    configure_flask,
    register_blueprints,
    initialize_managers,
    initialize_schedulers,
    initialize_emitters,
    register_socketio_handlers,
    register_context_processors,
    register_error_handlers,
)
from .modules.app_context import app_context


def setup_app(app: Flask):
    """Setup Flask app with all framework components."""
    # 1. Configure Flask
    socketio = configure_flask(app)
    
    # 2. Determine paths
    app_path = _get_app_path()
    app_context.app_path = app_path
    
    # 3. Load site configuration
    site_config = _load_site_config(app_path)
    app_context.site_conf = site_config
    
    # 4. Initialize managers
    initialize_managers(app_path, site_config)
    
    # 5. Register blueprints
    register_blueprints(app, app_path, site_config)
    
    # 6. Initialize schedulers
    initialize_schedulers(app_path, site_config, socketio)
    
    # 7. Initialize emitters
    initialize_emitters(app_path, site_config, socketio)
    
    # 8. Register handlers
    register_socketio_handlers(socketio, site_config)
    register_context_processors(app)
    register_error_handlers(app)
    
    return socketio
```

## Migration Strategy

1. **Create initialization package** with empty modules
2. **Extract one module at a time**, starting with context_processors (lowest risk)
3. **Run tests after each extraction** to ensure nothing breaks
4. **Update imports** in any code that directly accessed main.py internals
5. **Update copilot-instructions.md** with new architecture

## Testing Considerations

- Each initialization module should be independently testable
- Mock `app_context` for unit tests
- Integration tests should verify the full `setup_app()` flow

## Estimated Effort

- Phase 1 (Context Processors): 1 hour
- Phase 2 (Managers): 2 hours
- Phase 3 (Schedulers): 1 hour
- Phase 4 (Slim main.py): 1 hour
- Testing & Fixes: 2 hours

**Total: ~7 hours**

## Risks

- Circular imports during transition (mitigate with TYPE_CHECKING)
- Missing imports in extracted modules (mitigate with thorough testing)
- Breaking existing webapps that import from main.py (mitigate with backward-compat aliases)
