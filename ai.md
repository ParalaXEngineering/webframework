# AI Development Notes - WebFramework

## Quick Start Reference

### Running the Demo
```bash
cd /Users/mremacle/Documents/ParalaX/dev.nosync/webframework
source .venv/bin/activate
FLASK_APP=demo.py flask run --port 5001
# Access at http://localhost:5001
```

### Running Tests
```bash
source .venv/bin/activate
pytest tests/ -v                    # All tests (191 tests)
pytest tests/core/ -v               # Core module tests (69 tests)
pytest tests/imports/ -v            # Import tests (26 tests)
pytest tests/pages/ -v              # Page/HTTP tests (8 tests)
pytest tests/ --collect-only        # See test discovery
```

**Test Status**: ✅ All 191 tests passing (as of refactoring 2024)

## Test Suite Architecture

### New Test Structure (191 tests)
```
tests/
├── core/                    # Core framework tests (69 tests)
│   ├── test_startup.py      # 6 tests - initialization
│   ├── test_core_modules.py # 11 tests - core classes
│   ├── test_displayer_unit.py # 52 tests - DisplayerItem unit tests
│   └── test_displayer_auto.py # 94 tests - Auto-discovery tests ⭐
│
├── imports/                 # Import system tests (26 tests)
│   ├── test_imports.py      # 6 tests - import mechanics
│   └── test_auto_imports.py # 20 tests - Auto-discovery of all modules ⭐
│
└── pages/                   # Page/route tests (8 tests)
    └── test_http_forms.py   # Form data transformation tests
```

### Auto-Discovery System ⭐

**NEW**: Tests automatically discover and test new code!

#### 1. DisplayerCategory Decorators (src/displayer.py)
```python
@DisplayerCategory.INPUT
class DisplayerItemNewWidget(DisplayerItem):
    def __init__(self, id: str, ...):
        super().__init__(DisplayerItems.NEWWIDGET)
        # This class is now AUTO-TESTED!
```

Categories: INPUT (25), DISPLAY (4), BUTTON (6), MEDIA (4)

#### 2. Module Auto-Discovery (tests/imports/test_auto_imports.py)
- Scans src/ directory automatically
- Tests all 17 modules
- New modules in src/ are automatically tested

#### 3. Auto-Generated Tests (tests/core/test_displayer_auto.py)
- 94 parametrized tests
- Tests every decorated DisplayerItem class
- Validates m_type, parameters, instantiation

**Benefits**: Add a class with decorator → automatic test coverage!

## Architecture Overview

### Core Components

1. **displayer.py** (src/displayer.py)
   - Main display system with 40+ DisplayerItem types
   - 4 layout types: VERTICAL, HORIZONTAL, TABLE, TABS
   - **NEW**: DisplayerCategory decorator system for auto-discovery
   - Key classes:
     - `Displayer`: Main container
     - `DisplayerLayout`: Layout manager (uses `m_column`, not `m_columns`)
     - `DisplayerItem`: Base class for all items
     - Various `DisplayerItem*` subclasses (all decorated)

2. **site_conf.py** (src/site_conf.py)
   - Base configuration class
   - Must be extended, not used directly
   - Provides sidebar/topbar configuration
   - Has `context_processor()` method for Flask template context

3. **access_manager.py** (src/access_manager.py)
   - Class name: `Access_manager` (NOT AccessManager)
   - Authorization/authentication system
   - Requires initialization with config

### Flask Integration Pattern

```python
# 1. Extend Site_conf
class DemoSiteConf(site_conf.Site_conf):
    def __init__(self):
        super().__init__()
        # Configure app details, sidebar, topbar
        
# 2. Initialize access manager (REQUIRED even if not using auth)
app_manager = access_manager.AccessManager()
app_manager.initialize(app, config_dict, demo_conf)

# 3. Register context processor (CRITICAL!)
@app.context_processor
def inject_template_vars():
    base_context = demo_conf.context_processor()
    return base_context

# 4. Use Blueprints with proper naming
demo_bp = Blueprint('demo', __name__)
# Routes use 'demo.route_name' format
```

## Critical Gotchas & Fixes

### 1. Template Context Variables
**Problem**: Jinja2 errors about undefined variables (app, sidebarItems, etc.)
**Solution**: Always register context processor AND extend Site_conf properly.

### 2. Blueprint URL Building
**Problem**: `BuildError: Could not build url for endpoint 'index'`
**Solution**: All endpoints need blueprint prefix:
- Breadcrumbs: `"demo.index"` not `"index"`
- Form targets: `target="demo.inputs"` not `target="inputs"`
- Navigation: Always use `"demo.route_name"`

### 3. DisplayerItem Signatures (TRICKY!)

Different item types have different signatures - CHECK THE SOURCE!

**Text/Display Items** (most take 1-2 params):
```python
DisplayerItemText(text)
DisplayerItemAlert(text, style)
DisplayerItemTitle(text, level)
```

**Input Items** (vary widely):
```python
# File/Folder: Only 2 params!
DisplayerItemInputFile(id, text)  # NOT (id, text, value)
DisplayerItemInputFolder(id, text)  # NOT (id, text, value)

# String inputs: 3 params
DisplayerItemInputString(id, label, default_value)
DisplayerItemInputText(id, label, default_value)
DisplayerItemInputNumeric(id, label, default_value)

# Select: 4 params
DisplayerItemInputSelect(id, label, default, options_list)
DisplayerItemInputMultiSelect(id, label, default_list, options_list)
```

**Link Items**:
```python
DisplayerItemLink(id, text, url, params, style)
DisplayerItemIconLink(id, text, icon, url, params, style)
DisplayerItemDownload(id, text, url)  # NEVER use "#" as url!
```

**Button Items**:
```python
DisplayerItemButton(id, text, style, icon)
DisplayerItemButtonLink(id, text, icon, url, params, style)
```

### 4. Template Macro Arguments

**layouts.j2 macros** have strict argument counts:
```jinja2
display_horizontal_layout(columns, containers, align, spacing)  # 4 args
display_vertical_layout(columns, containers, align, spacing, height, background, user_id, style)  # 8 args
```

Don't pass extra params! The template itself reads from layout dict.

### 5. DisplayerLayout Spacing

```python
# Spacing can be int or str
DisplayerLayout(..., spacing=3)  # Converts to "py-3"
DisplayerLayout(..., spacing="py-3")  # Direct string
DisplayerLayout(...)  # Default spacing=0

# Template receives the processed string
```

### 6. URL Endpoints

**Never use `"#"` as a URL!** Flask's `url_for()` will try to build it and fail.
```python
# BAD:
DisplayerItemDownload("id", "Download", "#")

# GOOD:
DisplayerItemDownload("id", "Download", "/path/to/file")
# Or just remove the item if it's placeholder
```

## POST Data Transformation

### util_post_to_json() Behavior

**Does NOT convert types** - everything stays as strings:
```python
# Form data:
{"name": "John", "age": "25"}
# After util_post_to_json():
{"name": "John", "age": "25"}  # age is still string!
```

**Array pattern** - `listN` creates arrays:
```python
# Form data:
{"list1": "apple", "list2": "banana", "list3": "cherry"}
# After util_post_to_json():
{"list": ["apple", "banana", "cherry"]}
```

**Nested objects** - `parent__child` pattern:
```python
# Form data:
{"user__name": "John", "user__age": "25"}
# After util_post_to_json():
{"user": {"name": "John", "age": "25"}}
```

## Testing Strategy

### HTTP Testing Pattern
```python
# Good pattern for testing pages:
import requests
pages = {
    'Page Name': 'http://localhost:5001/route',
}
for name, url in pages.items():
    try:
        r = requests.get(url, timeout=2)
        status = '✅ OK' if r.status_code == 200 else f'❌ {r.status_code}'
    except Exception as e:
        status = f'❌ {str(e)[:40]}'
    print(f'{name:20} : {status}')
```

### Debugging Flask Errors
```bash
# Check logs:
tail -100 /tmp/demo.log | grep -A20 "Exception"

# Find specific error:
tail -100 /tmp/demo.log | grep -B5 -A15 "route_name"
```

## Port Management

```bash
# Find what's using a port:
lsof -ti:5001

# Kill process on port:
lsof -ti:5001 | xargs kill -9

# Or kill by name:
pkill -f "flask run"
pkill -f "demo.py"
```

## Common Development Workflow

1. **Make changes** to demo.py or templates
2. **Restart server**: `pkill -f "flask run" && FLASK_APP=demo.py flask run --port 5001 > /tmp/demo.log 2>&1 &`
3. **Test pages**: Use the requests script above
4. **Check errors**: `tail -50 /tmp/demo.log`
5. **Iterate** until all pages return 200

## Documentation System

Built with Sphinx:
```bash
./build_docs.sh  # Build HTML docs
./setup_docs.sh  # Initialize Sphinx structure
```

Docs location: `docs/build/html/index.html`

## Project Structure Quick Ref

```
src/
  displayer.py       - Display system (1857 lines) ⭐ NOW WITH DECORATORS
  site_conf.py       - Base config class (Site_conf)
  access_manager.py  - Auth system (Access_manager class)
  utilities.py       - Utilities (util_post_to_json, etc.)
  common.py          - Common functions

templates/
  base.j2            - Main template
  base_content.j2    - Content wrapper with forms
  displayer/
    layouts.j2       - Layout rendering macros
    items.j2         - Item rendering macros

demo.py              - Demo Flask app (511 lines)

tests/               ⭐ REFACTORED STRUCTURE
  core/
    test_startup.py         - 6 tests
    test_core_modules.py    - 11 tests
    test_displayer_unit.py  - 52 tests (original unit tests)
    test_displayer_auto.py  - 94 tests (AUTO-DISCOVERY!)
  imports/
    test_imports.py         - 6 tests
    test_auto_imports.py    - 20 tests (AUTO-DISCOVERY!)
  pages/
    test_http_forms.py      - 8 tests
```

## Environment

- Python 3.13 in `.venv`
- Flask with Blueprints
- Jinja2 templates
- Port 5001 (5000 often in use on Mac)

## Testing Strategy

### Auto-Discovery Pattern
New code is automatically tested when you:
1. Add `@DisplayerCategory.INPUT` decorator to new DisplayerItem classes
2. Add new .py files to src/ directory

### Manual Testing Pattern
For complex features, add specific tests in:
- `tests/core/` for core framework features
- `tests/pages/` for route/page features

## Remember

- **Always extend Site_conf**, never use directly
- **Class name is Access_manager**, NOT AccessManager
- **Always initialize Access_manager**, even if not using auth
- **Always register context_processor**
- **Check DisplayerItem signatures** in displayer.py before use
- **Use blueprint prefixes** in all url_for() calls
- **Never use "#" as URL endpoint**
- **Layout attribute is m_column**, not m_columns
- **Layout m_type is string**, compare with `Layouts.VERTICAL.value`
- **util_post_to_json uses . separator**, not __
- **Test after every change** - Flask errors can cascade
- **Add decorators to new DisplayerItem classes** for auto-testing

## Recent Major Changes

### Test Suite Refactoring (2024)
- **Before**: 97 tests in flat structure
- **After**: 191 tests with auto-discovery
- **Added**: DisplayerCategory decorator system (40 classes decorated)
- **Added**: Auto-discovery import tests (17 modules)
- **Added**: Parametrized tests (94 auto-generated)
- **See**: TEST_REFACTORING_SUMMARY.md for full details

---
Last Updated: 2024 (Test Refactoring)
Status: 
  - ✅ All 191 tests passing
  - ✅ Demo application working (5/5 pages)
  - ✅ Documentation complete
  - ✅ Auto-discovery enabled
