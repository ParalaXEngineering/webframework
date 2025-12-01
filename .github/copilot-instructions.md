# ParalaX Web Framework

## Architecture
**Submodule pattern**: Framework in `submodules/framework/`, user code in `website/`. Never mix.

**Core systems**:
- `displayer/`: Programmatic UI via layouts+items (not raw HTML)
- `site_conf.py`: Feature flags via `enable_*()`, auto-registers pages/nav
- `threaded/`: Background tasks via `Threaded_action`, SocketIO progress
- `auth/`: RBAC, decorator+module-level checks
- `settings/`: JSON config, optional sections auto-merge via `default_configs.py`

**Flow**: Route→Displayer→Jinja2→SocketIO→Thread emitters (user-isolated rooms)

## Critical Patterns

### Form Handling (MANDATORY)
```python
from modules.utilities import util_post_to_json
data = util_post_to_json(request.form.to_dict())  # NOT request.form.get()
```

### Page Structure
```python
disp = Displayer()
disp.add_generic("Title")
layout = disp.add_master_layout(DisplayerLayout(Layouts.HORIZONTAL, [8,4]))
disp.add_display_item(DisplayerItemText("x"), column=0)
return disp.display()
```

### Initialization Order (STRICT)
```python
# 1. BEFORE setup_app()
site_conf.site_conf_obj = MySiteConf()
site_conf.site_conf_app_path = framework_root
os.chdir(framework_root)  # Required for templates

# 2. Setup
socketio = setup_app(app)

# 3. AFTER setup_app()
app.register_blueprint(my_bp)
```

### Feature Flags (in website/site_conf.py)
```python
class MySiteConf(Site_conf):
    def __init__(self):
        super().__init__()
        self.enable_threads(add_to_sidebar=True)  # Auto-registers /threads page
        self.enable_authentication()  # Auto-adds user mgmt sections
```

### Safe Config Access
```python
from modules.utilities import get_config_or_error
configs, error = get_config_or_error(mgr, "path.key1.value", "path.key2.value")
if error: return error  # Auto-renders error page
```

### Threaded Actions
```python
class MyAction(Threaded_action):
    m_default_name = "Task"
    m_required_permission = "Module_Name"
    def action(self):
        self.emit_console("msg")  # Real-time to user's SocketIO room
```

### Home Page Navigation (IMPORTANT)
Override the default home endpoint in your website's `site_conf.py`:
```python
class MySiteConf(Site_conf):
    def __init__(self):
        super().__init__()
        self.app_details("My App", "1.0", "home", 
                        home_endpoint="my_module.home")  # Custom home page
```
Default is `framework_index` (the built-in empty home page).

## Key Files
- `src/main.py`: Initialization, feature→page mapping
- `src/modules/site_conf.py`: `enable_*()` methods
- `src/modules/displayer/__init__.py`: All UI exports
- `src/modules/utilities.py`: `util_post_to_json()`, `get_config_or_error()`
- `src/modules/default_configs.py`: Optional config sections

## Workflows
```bash
.venv\Scripts\activate; python main.py  # Run (use venv for py3.7+)
pytest tests/ -v  # Test (ordered: displayer→resource→others)
python framework_manager.py vendors|docs|example  # Utilities
```

## Pitfalls
1. `util_post_to_json()` mandatory (not `request.form.get()`)
2. `os.chdir(framework_root)` before `setup_app()`
3. Feature flags before `setup_app()`
4. Check managers for None: `thread_manager_obj`, `scheduler_obj`, `auth_manager`
5. Website structure: `website/{pages,modules}/`, `submodules/framework/`

## SocketIO
- Users in rooms by `session['user']`
- Thread emitters→owner's room only
- GUEST=shared, logged-in=isolated

## Auth (FRAMEWORK-PROVIDED)
**NEVER** implement your own `require_permission` decorator. Use the framework's:

```python
from src.modules.auth import require_permission

@bp.route('/my-page')
@require_permission("Module_Name", "view")
def my_page():
    return "Protected page"
```

- **Route-level**: `@require_permission('Module', 'action')` (framework decorator, auto-handles auth disabled)
- **Class-level**: `m_required_permission = "Module_Name"` (for Threaded_action subclasses)
- **Inline checks**: `auth_manager.has_permission(user, module, action)` (business logic within routes)

The framework's `require_permission` decorator automatically:
- Works when auth is disabled (allows access)
- Works when auth is enabled (checks permissions)
- Shows proper access denied pages
- Handles redirects to login

## Internationalization (i18n) - SOLUTION C PATTERN

**Architecture**: Website extends framework messages via star import.

### Setup (One-Time per Website)
```bash
mkdir -p website/i18n
touch website/i18n/{__init__.py,messages.py,messages.pyi}
touch website/py.typed
```

### 1. website/i18n/__init__.py
```python
from .messages import *
__all__ = ['messages']
```

### 2. website/i18n/messages.py
```python
"""Website-specific translatable messages."""

# Import ALL framework messages (~800+ constants)
from src.modules.i18n.messages import *  # noqa: F403

# Add your custom translatable strings below
TEXT_MY_DASHBOARD = TranslatableString("Dashboard")  # noqa: F405
TEXT_ANALYTICS = TranslatableString("Analytics")  # noqa: F405
MSG_CUSTOM_SUCCESS = TranslatableString("Success!")  # noqa: F405
ERROR_MY_VALIDATION = TranslatableString("Validation failed")  # noqa: F405
```

### 3. website/i18n/messages.pyi (for VSCode)
```python
# Type stub - keep in sync with messages.py
from src.modules.i18n.messages import *

TEXT_MY_DASHBOARD: str
TEXT_ANALYTICS: str
MSG_CUSTOM_SUCCESS: str
ERROR_MY_VALIDATION: str
```

### 4. Usage in Pages (Single Import)
```python
# Import from website.i18n.messages gets BOTH framework and custom
from website.i18n.messages import (
    TEXT_SETTINGS,        # Framework string
    MSG_SETTINGS_SAVED,   # Framework string  
    TEXT_MY_DASHBOARD,    # Your custom string
    MSG_CUSTOM_SUCCESS    # Your custom string
)

@bp.route('/dashboard')
def dashboard():
    disp = Displayer()
    disp.add_generic(TEXT_MY_DASHBOARD)      # Custom
    disp.add_breadcrumb(TEXT_SETTINGS, "/")  # Framework
    flash(MSG_CUSTOM_SUCCESS, "success")     # Custom
```

### Message Naming Conventions
- `TEXT_*` - Labels, headings, navigation
- `MSG_*` - Success/info messages
- `ERROR_*` - Error messages
- `BUTTON_*` - Button labels
- `TOOLTIP_*` - Tooltips
- `LABEL_*` - Form labels
- `TABLE_HEADER_*` - Table columns

### Translation Workflow
```bash
# After adding new strings
python framework_manager.py babel extract  # Scan code for strings
python framework_manager.py babel update   # Update .po files
# Edit translations/fr/LC_MESSAGES/messages.po
python framework_manager.py babel compile  # Generate .mo files
# Restart app
```

### IMPORTANT: Never Hardcode User-Facing Strings
❌ **Bad**: `disp.add_generic("Dashboard")`  
✅ **Good**: `disp.add_generic(TEXT_MY_DASHBOARD)`

❌ **Bad**: `flash("Settings saved!", "success")`  
✅ **Good**: `flash(MSG_SETTINGS_SAVED, "success")`

### VSCode Setup (.vscode/settings.json)
```json
{
    "python.analysis.extraPaths": [
        "${workspaceFolder}/your_webapp",
        "${workspaceFolder}/src",
        "${workspaceFolder}"
    ]
}
```
Replace `your_webapp` with actual webapp folder. Order matters (webapp before framework)!

### Reference
- Framework messages: `src/modules/i18n/messages.py` (~800+ constants)
- Full docs: `docs/source/i18n.rst`
- Example: `Manual_Webapp/website/i18n/messages.py`

## Resources
- Auto-registered by Displayer items via `ResourceRegistry`
- Vendors: `webengine/assets/vendors/` (update: `framework_manager.py vendors`)
- Docs: `python framework_manager.py docs` → `docs/build/html/`
