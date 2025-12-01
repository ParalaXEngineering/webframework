# Refactoring: Migrate to AppContext Pattern

## Problem

Global state is scattered across 10+ modules:

```python
# In auth/__init__.py
auth_manager = None

# In site_conf.py
site_conf_obj = None
site_conf_app_path = None

# In settings/__init__.py
settings_manager = None

# In threaded/threaded_manager.py
thread_manager_obj = None

# In scheduler/__init__.py
scheduler_obj = None
scheduler_ltobj = None

# In socketio_manager.py
socketio_manager = SocketIOManager()

# In main.py
auth_manager = None  # Duplicate!
```

This causes:
- Hard to test (must mock globals)
- Import order nightmares
- Circular import issues (hence all the try/except ImportError)
- Dependency injection impossible
- State leaks between tests

## Solution: AppContext Singleton

Already created at `src/modules/app_context.py`. Now we need to migrate.

## Migration Plan

### Phase 1: Add Forwarding Properties (Non-Breaking)

Update each module to forward to `app_context` while keeping the global variable:

```python
# auth/__init__.py
from ..app_context import app_context as _ctx

# Keep for backward compatibility
auth_manager = None

def __getattr__(name):
    """Forward attribute access to app_context."""
    if name == 'auth_manager':
        return _ctx.auth_manager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

This lets old code keep working while new code uses `app_context`.

### Phase 2: Update main.py to Use AppContext

Replace:
```python
auth_manager_module.auth_manager = auth_manager_instance
globals()['auth_manager'] = auth_manager_instance
```

With:
```python
from .modules.app_context import app_context
app_context.auth_manager = auth_manager_instance
```

### Phase 3: Update Consumers Gradually

Replace scattered imports:
```python
# Old
from ..modules.auth import auth_manager
if auth_manager is not None:
    user = auth_manager.get_current_user()

# New
from ..modules.app_context import app_context
if app_context.auth_manager is not None:
    user = app_context.auth_manager.get_current_user()

# Or even better - use helper method
user = app_context.get_current_user()
```

### Phase 4: Remove Old Globals

Once all consumers are migrated, remove the module-level globals.

## Files to Update

### High Priority (main.py initialization)
- [x] `src/modules/app_context.py` - Created
- [ ] `src/main.py` - Use app_context for all manager assignments
- [ ] `src/modules/__init__.py` - Export app_context

### Module-Level Globals to Migrate
- [ ] `src/modules/auth/__init__.py` - `auth_manager`
- [ ] `src/modules/site_conf.py` - `site_conf_obj`, `site_conf_app_path`
- [ ] `src/modules/settings/__init__.py` - `settings_manager`
- [ ] `src/modules/threaded/threaded_manager.py` - `thread_manager_obj`
- [ ] `src/modules/scheduler/__init__.py` - `scheduler_obj`, `scheduler_ltobj`
- [ ] `src/modules/socketio_manager.py` - `socketio_manager`

### Consumers to Update
- [ ] `src/modules/displayer/displayer.py` - Uses auth_manager
- [ ] `src/modules/threaded/threaded_action.py` - Uses scheduler, threaded_manager
- [ ] `src/modules/threaded/thread_emitter.py` - Uses threaded_manager
- [ ] `src/pages/threads.py` - Uses threaded_manager
- [ ] `src/pages/settings.py` - Uses settings_manager
- [ ] `src/pages/user.py` - Uses auth_manager
- [ ] `src/pages/admin.py` - Uses auth_manager
- [ ] All other pages...

## Testing Strategy

### Unit Tests for AppContext

```python
# tests/unit/test_app_context.py
import pytest
from src.modules.app_context import AppContext, app_context


def test_app_context_reset():
    """Test that reset clears all managers."""
    ctx = AppContext()
    ctx.auth_manager = "mock"
    ctx.reset()
    assert ctx.auth_manager is None


def test_app_context_require_auth_raises_when_none():
    """Test that require_auth raises when auth not enabled."""
    ctx = AppContext()
    with pytest.raises(RuntimeError, match="Authentication is not enabled"):
        ctx.require_auth()


def test_feature_flags_cached():
    """Test that feature flags are cached."""
    # ...
```

### Integration Tests

```python
def test_app_context_initialized_after_setup(app):
    """Test that setup_app populates app_context."""
    from src.modules.app_context import app_context
    
    assert app_context.settings_manager is not None
    assert app_context.is_initialized  # Add this flag
```

## Backward Compatibility

For a transition period, keep the old globals but have them read from app_context:

```python
# In auth/__init__.py
import sys
from types import ModuleType

class _AuthModule(ModuleType):
    @property
    def auth_manager(self):
        from .app_context import app_context
        return app_context.auth_manager
    
    @auth_manager.setter
    def auth_manager(self, value):
        from .app_context import app_context
        app_context.auth_manager = value

sys.modules[__name__] = _AuthModule(__name__)
```

This is Python magic but ensures 100% backward compatibility.

## Estimated Effort

- Phase 1 (Forwarding): 2 hours
- Phase 2 (main.py update): 1 hour
- Phase 3 (Consumer migration): 4 hours
- Phase 4 (Cleanup): 1 hour
- Testing: 2 hours

**Total: ~10 hours**

## Benefits After Migration

1. **Testability**: Mock `app_context` once, all managers are mocked
2. **Explicit dependencies**: Functions can take `ctx: AppContext` parameter
3. **No circular imports**: Single source of truth
4. **Type safety**: IDE knows what's available
5. **Lazy initialization**: Managers don't need to exist at import time
