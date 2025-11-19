# Displayer System

## Purpose
Programmatic UI generation with layouts, items, breadcrumbs, and automatic resource registration. No raw HTML in routes.

## Core Components
- `src/modules/displayer/displayer.py` - Displayer main class
- `src/modules/displayer/layout.py` - DisplayerLayout (VERTICAL, HORIZONTAL, TABLE, TABS)
- `src/modules/displayer/items/*.py` - DisplayerItem subclasses (buttons, inputs, alerts, etc.)
- `src/modules/displayer/core.py` - ResourceRegistry, enums (Layouts, BSstyle, etc.)
- `src/modules/displayer/__init__.py` - Exports all items

## Critical Patterns

### Basic Page Structure (MANDATORY)
```python
from modules.displayer import (
    Displayer, DisplayerLayout, Layouts,
    DisplayerItemText, DisplayerItemButton, BSstyle
)
from modules.utilities import get_home_endpoint

@blueprint.route("/mypage")
def mypage():
    disp = Displayer()
    disp.add_generic("My Page Title")
    disp.set_title("My Page")  # Browser title
    disp.add_breadcrumb("Home", get_home_endpoint(), [])
    disp.add_breadcrumb("My Page", "mymodule.mypage", [])
    
    # Add layout (columns sum to 12)
    layout_id = disp.add_master_layout(DisplayerLayout(Layouts.HORIZONTAL, [8, 4]))
    
    # Add items to columns
    disp.add_display_item(DisplayerItemText("Content here"), column=0)
    disp.add_display_item(DisplayerItemButton("Action", "/action"), column=1)
    
    return disp.display()  # Returns HTML string
```

### Layouts
```python
# Horizontal (Bootstrap grid columns)
disp.add_master_layout(DisplayerLayout(Layouts.HORIZONTAL, [6, 6]))  # 2 equal cols

# Vertical (stacked)
disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))  # Full width

# Table (auto rows/cols from data)
disp.add_master_layout(DisplayerLayout(Layouts.TABLE, columns=3))

# Tabs (named tabs)
disp.add_master_layout(DisplayerLayout(Layouts.TABS, ["Tab1", "Tab2"]))

# Spacer (empty space)
disp.add_master_layout(DisplayerLayout(Layouts.SPACER, [12]))
```

### Common Items
```python
# Text/HTML
DisplayerItemText("<p>Content</p>")
DisplayerItemAlert("Warning message", BSstyle.WARNING)

# Buttons
DisplayerItemButton("btn_id", "Click Me", link="/action", color=BSstyle.PRIMARY)
DisplayerItemModalButton("btn_modal", "Open Modal", "modal_id")

# Inputs
DisplayerItemInputText("input_id", "Label", "default_value")
DisplayerItemInputSelect("select_id", "Label", ["opt1", "opt2"], "opt1")
DisplayerItemInputNumeric("num_id", "Label", 0, min_val=0, max_val=100)
DisplayerItemInputCheckbox("chk_id", "Label", ["Option 1", "Option 2"], [0])

# Images/Files
DisplayerItemImage("path/to/image.jpg", caption="Image caption")
DisplayerItemFile("file_id", "Download File", "/download/123")

# Advanced
DisplayerItemCard("Card Title", "Card content", footer="Footer text")
DisplayerItemProgressBar(50, color=BSstyle.SUCCESS)  # 50%
DisplayerItemConsole("console_id", ["Line 1", "Line 2"])
```

### Form Handling (MANDATORY with util_post_to_json)
```python
from modules.utilities import util_post_to_json

@blueprint.route("/submit", methods=["POST"])
def submit():
    data = util_post_to_json(request.form.to_dict())  # NOT request.form.get()
    # Access nested: data["category"]["field"]
    username = data.get("user", {}).get("name", "")
    return "OK"
```

### Breadcrumbs (Use get_home_endpoint)
```python
from modules.utilities import get_home_endpoint

# First breadcrumb always home
disp.add_breadcrumb("Home", get_home_endpoint(), [])

# Additional levels
disp.add_breadcrumb("Files", "filemanager.index", [])
disp.add_breadcrumb("Upload", "filemanager.upload", ["?folder=docs"])
```

### Resource Registration (Automatic)
```python
# Items auto-register resources
DisplayerItemCalendar(...)  # Auto-registers FullCalendar CSS/JS

# Manual registration (rare)
from modules.displayer.core import ResourceRegistry, DisplayerCategory
ResourceRegistry.add_resource(DisplayerCategory.CSS, "/path/to/custom.css")
ResourceRegistry.add_resource(DisplayerCategory.JS, "/path/to/custom.js")
```

## API Quick Reference
```python
class Displayer:
    def add_generic(title: str)
    def set_title(title: str)
    def add_breadcrumb(title: str, endpoint: str, params: List[str], style: str = None)
    def add_master_layout(layout: DisplayerLayout) -> int  # Returns layout_id
    def add_display_item(item: DisplayerItem, column: int = 0, layout_id: int = -1)
    def display() -> str  # Returns rendered HTML

class DisplayerLayout:
    def __init__(layout_type: Layouts, columns: List[Union[int, str]])

# Enums
class Layouts(Enum):
    VERTICAL, HORIZONTAL, TABLE, TABS, SPACER

class BSstyle(Enum):
    PRIMARY, SECONDARY, SUCCESS, DANGER, WARNING, INFO, LIGHT, DARK

class BSalign(Enum):
    LEFT, CENTER, RIGHT

# Item base class
class DisplayerItem:
    id: str
    type: DisplayerItems
    def display() -> str
```

## Common Pitfalls
1. **util_post_to_json MANDATORY** - Never use `request.form.get()` directly
2. **Column sum** - Horizontal columns must sum to 12 (Bootstrap grid)
3. **Breadcrumb home** - Use `get_home_endpoint()` not hardcoded "demo.index"
4. **Layout IDs** - Store layout_id from `add_master_layout()` if adding to multiple layouts
5. **display() call** - Must call `disp.display()` at end to render
6. **Item IDs** - Must be unique across page
7. **Resource duplication** - Don't manually add vendor resources; items auto-register
8. **HTML escaping** - DisplayerItemText escapes by default; use raw HTML carefully

## Integration Points
- **Jinja2**: Renders via `base_content.j2` template
- **Bootstrap**: Grid system (columns), styles (BSstyle enum)
- **ResourceRegistry**: Auto-includes CSS/JS in page head
- **Utilities**: Form parsing via `util_post_to_json()`
- **Auth**: Access denied pages rendered via Displayer

## Files
- `displayer.py` - Main Displayer class
- `layout.py` - DisplayerLayout (VERTICAL, HORIZONTAL, etc.)
- `items/*.py` - All DisplayerItem subclasses
- `core.py` - ResourceRegistry, enums (Layouts, BSstyle, DisplayerItems)
- `__init__.py` - Exports all items for clean imports
- `file_items.py` - File manager specific items (upload, display)
