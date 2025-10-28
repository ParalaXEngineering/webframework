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
Framework pages use a **configurable home endpoint** instead of hardcoded `demo.index`:
```python
from modules.utilities import get_home_endpoint
disp.add_breadcrumb("Home", get_home_endpoint(), [])
```
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

## Auth
- Decorator: `@auth_manager.require_permission('Module', 'action')`
- Class attr: `m_required_permission = "Module_Name"`
- Inline: `auth_manager.check_permission(user, module, action)`

## Resources
- Auto-registered by Displayer items via `ResourceRegistry`
- Vendors: `webengine/assets/vendors/` (update: `framework_manager.py vendors`)
- Docs: `python framework_manager.py docs` → `docs/build/html/`
