# ParalaX Web Framework - AI Agent Guide

## Architecture Overview

**Git Submodule Pattern**: This framework is designed to be used as a Git submodule in website projects. The framework code lives in `submodules/framework/`, while user code lives in `website/`. This separation is critical - never mix framework code with website-specific code.

**Key Components**:
- **Displayer System** (`src/modules/displayer/`): Programmatic UI generator using layouts, items, and modules. All pages use Displayer to build interfaces dynamically rather than writing raw HTML.
- **Site Configuration** (`src/modules/site_conf.py`): Feature flags and navigation defined here. Use `enable_*()` methods to activate framework features (threads, auth, logging, etc.). Each website inherits from `Site_conf` to customize.
- **Thread Manager** (`src/modules/threaded/`): Background task execution with real-time progress tracking via SocketIO. All long-running operations use `Threaded_action` base class.
- **Authentication** (`src/modules/auth/`): Role-based permissions with user/group management. Permission checks happen at both route and module level.
- **Settings Engine** (`src/modules/settings/`): JSON-based configuration with optional sections that auto-merge when features are enabled (see `default_configs.py`).

**Data Flow**: Flask routes → Displayer builds UI → Jinja2 templates render → SocketIO updates state → Thread emitters push real-time updates to user-isolated rooms.

## Critical Developer Workflows

### Running the Framework
```powershell
# Always use the venv to avoid Python 3.6 issues
.venv\Scripts\activate
python main.py
```

### Testing
```bash
# Ordered execution: displayer tests generate HTML, then resource tests validate it
pytest tests/ -v

# Test structure:
# tests/unit/ - pure logic, no Flask
# tests/integration/ - full Flask app tests
# tests/conftest.py defines execution order
```

### Using Framework Manager
```bash
# Interactive mode for all tasks
python framework_manager.py

# Specific operations
python framework_manager.py vendors    # Update JS/CSS libraries
python framework_manager.py docs       # Build Sphinx docs
python framework_manager.py example --create  # Create example website
```

## Project-Specific Conventions

### Form Submission Pattern
**ALWAYS** use `util_post_to_json()` for form data parsing - direct `request.form.get()` will fail:
```python
from modules.utilities import util_post_to_json

@bp.route('/submit', methods=['POST'])
def submit():
    data_in = util_post_to_json(request.form.to_dict())
    my_data = data_in.get("module_id", {})  # Nested structure auto-parsed
```

### Displayer Pattern for Pages
Standard page structure (see `src/pages/threads.py` for reference):
```python
disp = Displayer()
disp.add_generic("Page Title")
disp.set_title("Browser Title")
disp.add_breadcrumb("Home", "endpoint.name", [])

# Add layouts and items
layout_id = disp.add_master_layout(DisplayerLayout(Layouts.HORIZONTAL, [8, 4]))
disp.add_display_item(DisplayerItemText("Content"), column=0)

return disp.display()  # Returns Flask render_template result
```

### Feature Flag System
Enable features in `website/site_conf.py` (NOT in framework code):
```python
class MySiteConf(Site_conf):
    def __init__(self):
        super().__init__()
        self.enable_threads(add_to_sidebar=True, add_to_topbar=True)
        self.enable_authentication()  # Auto-adds user management sections
        self.enable_log_viewer()
```

Features auto-register pages and merge config sections from `default_configs.py`.

### Configuration Access Pattern
Use `get_config_or_error()` for safe config access with automatic error pages:
```python
from modules.utilities import get_config_or_error
from modules.settings import SettingsManager

configs, error = get_config_or_error(
    get_settings_manager(),
    "section.key1.value",
    "section.key2.value"
)
if error:
    return error  # Auto-renders error.j2

value1 = configs["section.key1.value"]
```

### Working Directory Requirement
User's `main.py` **must** change to framework directory before `setup_app()`:
```python
framework_root = os.path.join(project_root, 'submodules', 'framework')
os.chdir(framework_root)  # Required for template discovery
socketio = setup_app(app)
```

### Site Configuration Order
Critical initialization sequence:
```python
# 1. Set site_conf BEFORE setup_app()
site_conf.site_conf_obj = MySiteConf()
site_conf.site_conf_app_path = framework_root

# 2. Setup app (registers framework pages based on feature flags)
socketio = setup_app(app)

# 3. Register user blueprints AFTER
app.register_blueprint(my_bp)
```

### Thread Isolation with SocketIO
Users are isolated in SocketIO rooms based on `session['user']`. Thread emitters only send updates to the thread owner's room. Guest users (GUEST) see shared state; logged-in users see only their threads.

### Threaded Actions
Background tasks inherit from `Threaded_action`:
```python
class MyAction(Threaded_action):
    m_default_name = "My Task"
    m_required_permission = "Module_Name"  # Maps to auth module
    
    def action(self):
        self.emit_console("Progress update")
        # Long-running work
```

Thread manager automatically handles lifecycle, logging, and cleanup.

## Integration Points

**Frontend Libraries**: All vendors in `webengine/assets/vendors/`. Updated via `framework_manager.py vendors`. CDN fallbacks configured in base templates.

**Logging**: Centralized factory at `src/modules/log/logger_factory.py`. Per-thread console output via `emit_console()`. Real-time viewer at `/logging/logs` when feature enabled.

**Authentication**: Permission checks via `@auth_manager.require_permission('Module', 'action')` decorator or `auth_manager.check_permission()` in code. Module-level permissions defined in `Action.m_required_permission`.

**Resource Loading**: Displayer items auto-register CSS/JS dependencies via `ResourceRegistry`. Templates inject only required resources per page.

**Testing**: Use fixtures from `tests/unit/conftest.py` (no Flask) or `tests/integration/conftest.py` (with Flask app). Test execution order enforced in root `conftest.py`.

## Critical Files

- `src/main.py`: App initialization, blueprint auto-discovery, feature flag processing
- `src/modules/site_conf.py`: Base configuration class with `enable_*()` methods
- `src/modules/displayer/__init__.py`: All UI components exported here
- `src/modules/utilities.py`: Form parsing, config access, breadcrumbs
- `src/modules/default_configs.py`: Optional config sections for features
- `framework_manager.py`: Unified CLI for vendors, docs, examples

## Common Pitfalls

1. **Never** use `request.form.get()` directly - always use `util_post_to_json()`
2. **Never** forget `os.chdir(framework_root)` before `setup_app()` in user's `main.py`
3. **Never** enable features after `setup_app()` - feature flags must be set first
4. **Always** use `.venv` on Windows to avoid Python 3.6 compatibility issues
5. **Always** check if manager objects are None before using (thread_manager_obj, scheduler_obj, auth_manager)
6. When creating website projects, structure must be: `website/pages/`, `website/modules/`, `submodules/framework/`

## Documentation

Build with: `python framework_manager.py docs` (auto-installs deps, validates docstrings, opens browser).
Located at: `docs/build/html/index.html`
