# ParalaX Web Framework - AI Agent Instructions

This document provides AI coding agents with essential knowledge to work effectively with the ParalaX Web Framework codebase. Focus on **non-obvious architectural patterns** and **critical workflows** that require understanding multiple files.

---

## 🏗️ Architecture Overview

### Framework vs Application Separation

**Critical Pattern**: This is a **framework** that applications integrate, NOT a standalone app.

**Proper Integration (Required Pattern)**:
```python
from flask import Flask
from src.main import setup_app
from src.modules import site_conf

# 1. Create Flask app
app = Flask(__name__, ...)

# 2. MUST create and set Site_conf BEFORE setup_app()
class MyAppConfig(site_conf.Site_conf):
    def __init__(self):
        super().__init__()
        self.add_sidebar_title("My App")
        self.add_sidebar_section("Features", "feature_bp.index", "bi-list", [])

site_conf.site_conf_obj = MyAppConfig()  # CRITICAL: Set BEFORE setup_app!

# 3. Initialize framework (auto-discovers blueprints, sets up scheduler, emitters)
socketio = setup_app(app)

# 4. Register custom blueprints
app.register_blueprint(my_custom_bp)

# 5. Run with SocketIO
socketio.run(app, host='0.0.0.0', port=5000)
```

**See**: `tests/manual_test_webapp.py` (lines 33-94) for complete working example.

---

## 🎨 Displayer System (Primary UI Pattern)

**Three-Tier Hierarchy** - Building pages requires understanding this structure:

### Tier 1: Displayer (Container)
```python
from src.modules.displayer import Displayer
disp = Displayer()
```

### Tier 2: Module (Logical Section)
```python
# Option A: Generic module (just a name)
disp.add_generic("My Feature")

# Option B: Module from class (auto-adds sidebar integration)
disp.add_module(MyThreadedActionClass)
```

### Tier 3: Layout (Content Organization)
```python
from src.modules.displayer import DisplayerLayout, Layouts

# VERTICAL layout uses Bootstrap 12-column grid
disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [8, 4]))  # 8+4=12 cols

# HORIZONTAL layout - side-by-side
disp.add_master_layout(DisplayerLayout(Layouts.HORIZONTAL, ["Left", "Right"]))

# TABLE layout - headers + rows
disp.add_master_layout(DisplayerLayout(Layouts.TABLE, ["Name", "Status", "Actions"]))

# TABS layout - tab navigation
disp.add_master_layout(DisplayerLayout(Layouts.TABS, ["Config", "Logs", "Debug"]))
```

### Tier 4: Items (UI Components)
```python
from src.modules.displayer import (
    DisplayerItemText, DisplayerItemButton, DisplayerItemInputText,
    DisplayerItemInputDropdown, DisplayerItemImage, TableMode
)

# Add to specific column (VERTICAL layouts)
disp.add_display_item(DisplayerItemText("Main content"), column=0)
disp.add_display_item(DisplayerItemButton("btn_save", "Save"), column=1)

# Add to specific section (HORIZONTAL/TABLE/TABS)
disp.add_display_item(DisplayerItemInputText("username", "Username"), column=0)
```

### TABLE Layout Modes

**NEW API (Recommended)**: Use `datatable_config` with `TableMode` enum

```python
# Simple HTML table (no JavaScript)
disp.add_master_layout(DisplayerLayout(
    Layouts.TABLE,
    columns=["Name", "Status", "Actions"]
    # No datatable_config = plain HTML
))

# Interactive DataTable (manual item population - flexible)
disp.add_master_layout(DisplayerLayout(
    Layouts.TABLE,
    columns=["Name", "Status", "Actions"],
    datatable_config={
        "table_id": "users",
        "mode": TableMode.INTERACTIVE,  # Use TableMode enum
        "searchable_columns": [0, 1]    # Enable search panes on Name, Status
    }
))

# Bulk Data DataTable (pre-loaded JSON - most efficient)
disp.add_master_layout(DisplayerLayout(
    Layouts.TABLE,
    columns=["Name", "Email", "Status"],
    datatable_config={
        "table_id": "bulk_users",
        "mode": TableMode.BULK_DATA,  # Efficient for large datasets
        "data": [
            {"Name": "Alice", "Email": "alice@ex.com", "Status": "Active"},
            {"Name": "Bob", "Email": "bob@ex.com", "Status": "Inactive"}
        ],
        "columns": [{"data": "Name"}, {"data": "Email"}, {"data": "Status"}],
        "searchable_columns": [0, 1]  # Optional: columns with search panes
    }
))

# Server-Side DataTable (AJAX endpoint)
disp.add_master_layout(DisplayerLayout(
    Layouts.TABLE,
    columns=["Name", "Email", "Status"],
    datatable_config={
        "table_id": "ajax_users",
        "mode": TableMode.SERVER_SIDE,
        "api_endpoint": "api.get_users",
        "refresh_interval": 3000,  # Auto-refresh every 3s
        "columns": [{"data": "Name"}, {"data": "Email"}, {"data": "Status"}]
    }
))
```

**OLD API (Deprecated, will be removed in v2.0)**: `responsive` parameter

```python
# Still works but shows deprecation warning
disp.add_master_layout(DisplayerLayout(
    Layouts.TABLE,
    columns=["Name", "Status"],
    responsive={
        "table1": {
            "type": "advanced",  # OLD: "basic", "advanced", "ajax"
            "columns": [0, 1],
            "ajax_columns": [{"data": "Name"}, {"data": "Status"}],
            "data": [...]
        }
    }
))
```

**TableMode Enum Values**:
- `TableMode.SIMPLE` - Plain HTML table (no DataTables JS)
- `TableMode.INTERACTIVE` - DataTables with manual row population (flexible)
- `TableMode.BULK_DATA` - DataTables with pre-loaded data (efficient for 100s-1000s of rows)
- `TableMode.SERVER_SIDE` - DataTables with AJAX endpoint (for dynamic data)

### Complete Page Example
```python
@my_bp.route('/my-page', methods=['GET', 'POST'])
def my_page():
    disp = Displayer()
    disp.add_generic("My Page")
    disp.set_title("My Feature")
    disp.add_breadcrumb("Home", "route.index", [])
    
    # Create 8-4 column layout
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [8, 4]))
    
    # Add items to columns
    disp.add_display_item(DisplayerItemText("Main content area"), column=0)
    disp.add_display_item(
        DisplayerItemButton("btn_action", "Execute", BSstyle.PRIMARY),
        column=1
    )
    
    # Handle form submission
    if request.method == 'POST':
        from src.modules import utilities
        data_in = utilities.util_post_to_json(request.form.to_dict())
        
        # Forms are namespaced by module name
        if "My Page" in data_in:
            module_data = data_in["My Page"]
            if "btn_action" in module_data:
                # Handle button click
                pass
    
    return render_template("base_content.j2", content=disp.display())
```

**See**: `tests/demo_pages.py` (lines 1-370) for 7 complete working examples.

---

## 🔄 Real-Time Communication

### Three Emitter Systems (All Auto-Initialized in setup_app)

**1. Scheduler Emitter** (`src/modules/scheduler/scheduler.py`)
- **Purpose**: Progress updates, popups, status messages from background tasks
- **Usage in Threaded Actions**:
```python
from src.modules import scheduler

class MyAction(Threaded_action):
    def action(self):
        # Update progress (0-100 = progress, 101 = error, 102 = info)
        scheduler.scheduler_obj.emit_status(
            self.get_name(),
            "Processing file...",
            status=50,
            supplement="50/100 complete"
        )
        
        # Show popup
        scheduler.scheduler_obj.emit_popup("Success!", "Task completed")
        
        # Reload a div by ID
        scheduler.scheduler_obj.emit_reload("results_div", new_html_content)
```

**2. Thread Emitter** (`src/modules/threaded/thread_emitter.py`)
- **Purpose**: Real-time thread status/console updates every 0.5s
- **Auto-collects**: Running threads, progress, console output, errors
- **No manual usage required** - monitors `threaded_manager.thread_manager_obj` automatically

**3. Log Emitter** (`src/modules/log/log_emitter.py`)
- **Purpose**: Live log file updates every 2.0s
- **Auto-monitors**: `logs/` directory for all `.log` files
- **No manual usage required** - background daemon thread

---

## 🧵 Threading System

### Creating Background Tasks

**Base Pattern**:
```python
from src.modules.threaded import Threaded_action

class MyBackgroundTask(Threaded_action):
    m_default_name = "My Task"  # REQUIRED: Module identifier
    
    def action(self):
        """Override this method - runs in background thread"""
        self.console_write("Starting task...", "INFO")
        
        # Update progress
        self.m_running_state = 50  # 0-100 percentage
        
        # Long-running work
        result = self.do_work()
        
        # Report completion
        from src.modules import scheduler
        scheduler.scheduler_obj.emit_status(
            self.get_name(),
            "Task completed",
            status=100
        )
        
        self.console_write("Task finished", "INFO")
```

### Starting Threads from Routes
```python
from src.modules.threaded import threaded_manager

@my_bp.route('/start-task', methods=['POST'])
def start_task():
    # Create and start thread
    task = MyBackgroundTask()
    task.start()
    
    # Or get existing thread by name
    existing = threaded_manager.thread_manager_obj.get_thread("My Task")
    
    return jsonify({"status": "started"})
```

### Thread Lifecycle
- **`m_running`**: `True` while thread executing
- **`m_running_state`**: Progress (-1 = running no %, 0-100 = percentage)
- **`m_error`**: String error message if exception occurred
- **`m_background`**: If `True`, thread persists after completion
- **Auto-cleanup**: Non-background threads auto-delete 0.5s after completion

**See**: `src/modules/threaded/threaded_action.py` (lines 1-500) for full API.

---

## 📦 Resource Auto-Loading System

**Critical Pattern**: CSS/JS dependencies are **automatically loaded** - don't manually add `<script>` tags!

### How It Works
1. **Items declare resources**:
```python
class DisplayerItemCustom(DisplayerItemBase):
    def get_required_resources(self):
        return {
            'css': ['/static/custom.css'],
            'js': ['/static/custom.js']
        }
```

2. **ResourceRegistry prevents duplicates** (`src/modules/displayer/core.py`)
3. **Context processor injects** into templates (`src/main.py` lines 140-150)

### For Custom Components
```python
from src.modules.displayer import ResourceRegistry

# In your route
ResourceRegistry.register_css('/static/my-feature.css')
ResourceRegistry.register_js('/static/my-feature.js')
```

Resources automatically appear in `<head>` - **no manual template editing required**.

---

## 📝 Form Handling Pattern

**Critical**: Forms are **module-namespaced** to prevent ID collisions.

### Form Data Structure
```python
# POST data structure:
{
    "Module Name": {          # Module's m_default_name or add_generic() name
        "button_id": "value",
        "input_name": "user_value"
    }
}
```

### Handling POST Requests
```python
from src.modules import utilities

if request.method == 'POST':
    # Convert Flask form to nested dict
    data_in = utilities.util_post_to_json(request.form.to_dict())
    
    # Access module-scoped data
    if "My Feature" in data_in:
        module_data = data_in["My Feature"]
        
        # Check specific button/input
        if "btn_submit" in module_data:
            user_input = module_data.get("input_username", "")
            # Process...
```

**Why**: Multiple modules can have buttons with same ID without conflicts.

**See**: `tests/demo_pages.py` (search for `util_post_to_json`) for 5+ working examples.

---

## 🔧 Critical Workflows

### Testing
```bash
# Run all tests (144/145 passing)
pytest tests/ -v

# Run specific test file
pytest tests/test_displayer.py -v

# Run tests with markers
pytest -m core -v

# With coverage (if pytest-cov installed)
pytest tests/ --cov=src --cov-report=term-missing
```

**Configuration**: `pytest.ini` defines markers, paths, output format.

### Running the Test Application
```bash
# Activate virtual environment first (REQUIRED)
.\.venv\Scripts\python.exe tests\manual_test_webapp.py

# Or use VS Code debugger (F5) - see .vscode/launch.json
```

**Debugging**: VS Code launch.json configured for `tests/manual_test_webapp.py` with Flask debug mode.

### Building Documentation
```bash
cd docs
.\make.bat html

# Output: docs/build/html/index.html
```

**Sphinx Configuration**: `docs/source/conf.py` - autodoc enabled.

### Installing as Development Package
```bash
# From repository root
pip install -e .

# With development dependencies
pip install -e ".[dev]"

# With documentation dependencies
pip install -e ".[docs]"
```

---

## 🔗 Integration Points

### 1. Blueprint Auto-Discovery
**Where**: `src/main.py` lines 102-134

**Discovers from**:
- `src/pages/` - Framework pages (status, threads, etc.)
- `website/pages/` - Application pages (if exists)

**Naming convention**: `*_bp.py` files with blueprint variable named `*_bp`

### 2. Context Processors
**Injected into ALL templates** (`src/main.py` lines 136-155):
- `inject_bar()`: `m_sidebar`, `m_topbar` from Site_conf
- `inject_endpoint()`: Current route for nav highlighting
- `inject_resources()`: CSS/JS from ResourceRegistry

### 3. Global Singletons
**Module-level shared instances**:
```python
from src.modules import scheduler
scheduler.scheduler_obj  # Scheduler instance

from src.modules.threaded import threaded_manager
threaded_manager.thread_manager_obj  # Thread registry

from src.modules.threaded import thread_emitter
thread_emitter.thread_emitter_obj  # Thread status broadcaster

from src.modules.log import log_emitter
log_emitter.log_emitter_obj  # Log file monitor
```

**Initialization**: All created in `setup_app()` (lines 165-184).

### 4. Template System
**Base templates** (`templates/`):
- `base.j2` - HTML skeleton with sidebar/topbar
- `base_content.j2` - Standard page wrapper (use for displayer pages)
- `base_content_reloader.j2` - Auto-reload wrapper (for live data)

**Displayer templates** (`templates/displayer/`):
- `layouts.j2` - Jinja2 macros for rendering layouts
- `items.j2` - Jinja2 macros for rendering 40+ item types

**Usage**: `return render_template("base_content.j2", content=disp.display())`

---

## ⚠️ Common Pitfalls

### 1. Site_conf Timing
**WRONG**:
```python
socketio = setup_app(app)
site_conf.site_conf_obj = MyConfig()  # TOO LATE!
```

**CORRECT**:
```python
site_conf.site_conf_obj = MyConfig()  # BEFORE setup_app!
socketio = setup_app(app)
```

### 2. Layout Column Math
**WRONG**:
```python
DisplayerLayout(Layouts.VERTICAL, [6, 8])  # 6+8=14 (invalid!)
```

**CORRECT**:
```python
DisplayerLayout(Layouts.VERTICAL, [6, 6])   # 6+6=12 ✓
DisplayerLayout(Layouts.VERTICAL, [8, 4])   # 8+4=12 ✓
DisplayerLayout(Layouts.VERTICAL, [12])     # Full width ✓
```

### 3. Form Data Access
**WRONG**:
```python
button_value = request.form['btn_submit']  # KeyError if not found!
```

**CORRECT**:
```python
data_in = utilities.util_post_to_json(request.form.to_dict())
if "Module Name" in data_in:
    if "btn_submit" in data_in["Module Name"]:
        # Safe access
```

### 4. Thread Progress Values
**Special values** for `m_running_state`:
- `-1` = Running without percentage info
- `0-99` = Progress percentage
- `100` = Success (scheduler marks complete)
- `101` = Error (scheduler shows error state)
- `102` = Info message

### 5. Virtual Environment
**ALWAYS activate `.venv` before running**:
```bash
# Windows
.\.venv\Scripts\Activate.ps1

# Then run tests/scripts
python tests\manual_test_webapp.py
```

**Python 3.6 errors?** You're not using the venv - check your interpreter!

---

## 📚 Key Files Reference

| File | Purpose | Lines to Study |
|------|---------|----------------|
| `src/main.py` | Framework initialization, `setup_app()` | 62-270 |
| `src/modules/displayer/displayer.py` | Main Displayer class | 1-300 |
| `src/modules/displayer/items.py` | 40+ DisplayerItem types | 1-1000 |
| `src/modules/threaded/threaded_action.py` | Thread base class | 56-450 |
| `src/modules/scheduler/scheduler.py` | Scheduler + emit methods | 141-270 |
| `src/modules/site_conf.py` | Site configuration base | 1-426 |
| `tests/manual_test_webapp.py` | Complete integration example | 33-94 |
| `tests/demo_pages.py` | 7 working displayer examples | 1-370 |
| `tests/conftest.py` | Pytest fixtures | 1-100 |

---

## 🎯 Quick Decision Tree

**Adding a new page?**
→ Create route, build Displayer hierarchy, render to `base_content.j2`

**Need background processing?**
→ Create `Threaded_action` subclass, use `emit_status()` for progress

**Need real-time updates?**
→ Scheduler emitter (manual), thread emitter (auto), or log emitter (auto)

**Adding custom CSS/JS?**
→ Use `ResourceRegistry.register_css/js()` - auto-injects

**Form not submitting correctly?**
→ Use `util_post_to_json()` and check module namespace

**Import errors?**
→ Activate `.venv` first, ensure `pip install -e .` ran

**Tests failing?**
→ Check pytest output, ensure Flask app fixture configured

---

## 💡 Pro Tips

1. **Study working examples**: `tests/demo_pages.py` has 7 complete patterns
2. **Use VS Code debugger**: F5 launches test app with breakpoints
3. **Check logs**: `logs/` directory has detailed runtime info
4. **Console output**: Threads auto-capture `console_write()` for debugging
5. **Resource conflicts**: ResourceRegistry prevents duplicate CSS/JS loads
6. **Module naming**: `m_default_name` must match form namespace exactly
7. **Bootstrap grid**: Layout columns must sum to 12 (Mazer theme uses Bootstrap 5)

---

**Last Updated**: 2025 (Framework AI branch - active development)
