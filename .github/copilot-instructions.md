````instructions
# ParalaX Web Framework - AI Agent Instructions

## Architecture
**Submodule pattern**: Framework in `submodules/framework/`, website code in `website/`. Never mix layers.

```
website/
├── main.py           # Entry point
├── site_conf.py      # extends Site_conf, enables features
├── config.json       # Runtime settings
├── pages/            # Flask Blueprints
└── modules/          # Custom logic
submodules/framework/ # This codebase (git submodule)
```

## Core Systems
| System | Location | Purpose |
|--------|----------|---------|
| Displayer | `src/modules/displayer/` | Programmatic UI (never raw HTML) |
| Auth | `src/modules/auth/` | RBAC decorators + permission registry |
| Settings | `src/modules/settings/` | JSON config with auto-merge |
| Threaded | `src/modules/threaded/` | Background tasks with SocketIO progress |
| i18n | `src/modules/i18n/` | TranslatableString pattern |

## Critical Patterns

### 1. NO Custom HTML (STRICT RULE)
**NEVER write raw HTML in routes.** Always use DisplayerItems.
```python
# ❌ WRONG - Raw HTML
return "<h1>Title</h1><p>Content</p>"

# ✅ CORRECT - DisplayerItems
disp.add_display_item(DisplayerItemText("<h1>Title</h1>"), column=0)
```

### 2. Form Handling (MANDATORY)
```python
from src.modules.utilities import util_post_to_json
data = util_post_to_json(request.form.to_dict())  # NOT request.form.get()
```

### 3. Page Structure (Recommended Pattern)
```python
from src.modules.displayer import Displayer, DisplayerLayout, Layouts, DisplayerItemText

disp = Displayer()
disp.add_generic("Page Title", display=False)  # display=False hides generic module title
disp.set_title("Page Title")                   # Sets browser/page title
layout_id = disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [8, 4]))
disp.add_display_item(DisplayerItemText("Content"), column=0)
return render_template("base_content.j2", content=disp.display())
```

### 4. Module Pattern (for permission-controlled pages)
```python
from src.modules.action import Action

class MyModule(Action):
    m_default_name = "MyFeature"
    m_required_permission = "AdminTools"  # Optional: defaults to module name
    m_required_action = "execute"         # 'view', 'edit', 'execute'
    
    def start(self):
        # User context auto-injected: _current_user, _user_permissions, _is_guest
        if self.has_permission('execute'):
            # Module logic here
            pass

# In route:
disp.add_module(MyModule, display=False)  # Automatic permission checking
```

### 3. Initialization Order (STRICT)
```python
# In main.py - ORDER MATTERS
os.chdir(framework_root)                    # 1. Change to framework dir
site_conf.site_conf_obj = MySiteConf()      # 2. Set site config BEFORE setup
socketio = setup_app(app)                   # 3. Initialize framework
app.register_blueprint(my_bp)               # 4. Register blueprints AFTER
```

### 4. Feature Flags (in website/site_conf.py)
```python
class MySiteConf(Site_conf):
    def __init__(self):
        super().__init__()
        self.enable_authentication(add_to_sidebar=True)
        self.enable_threads(add_to_sidebar=True)
        self.enable_settings()
        self.enable_file_manager()
        self.enable_plugin("tracker")  # Load plugin from submodules/
```

### 5. Auth Decorator (NEVER implement your own)
```python
from src.modules.auth import require_permission

@bp.route('/page')
@require_permission("ModuleName", "view")  # or "edit", "execute"
def page():
    ...
```

### 6. Safe Config Access
```python
from src.modules.utilities import get_config_or_error
configs, error = get_config_or_error(settings_mgr, "path.key.value")
if error: return error  # Auto-renders error page
```

### 7. Threaded Actions
```python
from src.modules.threaded.threaded_action import Threaded_action

class MyTask(Threaded_action):
    m_default_name = "Task Name"
    m_required_permission = "Module_Name"
    
    def action(self):
        for i in range(100):
            if not self.m_running: return  # Check abort flag
            self.m_running_state = i       # Update progress
            self.console_write(f"Step {i}")
```

### 8. i18n Messages
```python
# In website/i18n/messages.py
from src.modules.i18n.messages import *  # Import ALL framework messages
TEXT_MY_LABEL = TranslatableString("My Label")  # Add custom

# Usage
from website.i18n.messages import TEXT_MY_LABEL, TEXT_SETTINGS  # Both work
```

## Layout Types (CRITICAL: Names are inverted!)
| Layout | Effect | columns= |
|--------|--------|----------|
| `VERTICAL` | Side-by-side columns | Bootstrap widths `[8, 4]` |
| `HORIZONTAL` | Stacked vertically | `[12]` for full width |
| `TABLE` | Data table | Header strings `["Name", "Actions"]` |
| `TABS` | Tabbed interface | Tab labels |

## DisplayerItems (NO custom HTML - STRICT)
Text, Alert, Button, ActionButtons, InputString, InputSelect, InputNumber, InputTextArea, InputCheckbox, InputFile, Table, Card, Badge, Icon, Image, Link, Console, Graph, GridEditor

## App Context Access
```python
from src.modules.app_context import app_context
auth = app_context.auth_manager
settings = app_context.settings_manager
threads = app_context.thread_manager
```

## SocketIO Rooms
- Users isolated by `user_{username}_{session_id}`
- Threads emit to owner's room only via `emit_to_user()`
- GUEST users share a room

## Common Pitfalls
1. ❌ `request.form.get()` → ✅ `util_post_to_json()`
2. ❌ Feature flags after `setup_app()` → ✅ Before
3. ❌ Custom `@require_permission` → ✅ Use framework's
4. ❌ Raw HTML strings → ✅ DisplayerItems only
5. ❌ Bare `logging.getLogger()` → ✅ `from src.modules.log.logger_factory import get_logger`
6. ❌ VERTICAL for stacking → ✅ HORIZONTAL (names inverted!)

## Testing
- **Structure**: tests/unit/ (pure logic), tests/integration/ (Flask), tests/frontend/ (Playwright E2E)
- **Prerequisites**: `pip install -e .[dev]` then `playwright install`
- **Frontend**: Requires Manual_Webapp running on port 5001
- **Commands**:
  - `pytest tests/ -v` (all tests)
  - `pytest tests/unit/ -v` (unit only, no Flask)
  - `pytest tests/frontend/ -v` (E2E, requires server)
  - `pytest -m startup` (marked tests)
- **Test Ordering**: Custom hook enforces displayer → resource_loading
- **Human Mode**: Set `HUMAN_MODE=True` in tests/frontend/conftest.py for visible browser

## Commands
```bash
python main.py                        # Run website
pytest tests/ -v                      # Test
python framework_manager.py docs      # Build docs
python framework_manager.py vendors   # Update JS/CSS libs
```

## Reference Documentation
For comprehensive API documentation and advanced patterns, see `.github/reference/`:
- `displayer.md` - All DisplayerItems, layouts, forms
- `auth.md` - Permission registry, security patterns
- `threaded.md` - Process execution, logging, SocketIO
- `utilities.md`, `settings.md`, `file_manager.md`, etc.

**When to read**: Implementing new features, troubleshooting edge cases, needing complete API coverage.
````
