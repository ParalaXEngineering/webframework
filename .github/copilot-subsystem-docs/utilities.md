# Utilities Module

## Purpose
Helper functions for form parsing, config access, formatting, and common operations. Essential for safe form handling and config retrieval.

## Core Components
- `src/modules/utilities.py` - All utility functions

## Critical Patterns

### Form Data Parsing (MANDATORY)
```python
from modules.utilities import util_post_to_json

@blueprint.route("/submit", methods=["POST"])
def submit():
    # ALWAYS use this for form data
    data = util_post_to_json(request.form.to_dict())
    
    # Access nested data
    username = data.get("user", {}).get("name", "")
    settings = data.get("config", {}).get("database", {})
    
    # NEVER use request.form.get() directly
```

### Safe Config Access (MANDATORY)
```python
from modules.utilities import get_config_or_error

# Single value
source, error = get_config_or_error(settings_mgr, "updates.source.value")
if error:
    return error  # Auto-renders error page

# Multiple values
configs, error = get_config_or_error(
    settings_mgr,
    "updates.address.value",
    "updates.user.value",
    "updates.password.value"
)
if error:
    return error
address = configs["updates.address.value"]
```

### Home Endpoint (MANDATORY for Breadcrumbs)
```python
from modules.utilities import get_home_endpoint

# In every page
disp.add_breadcrumb("Home", get_home_endpoint(), [])
# Returns site_conf_obj.m_home_endpoint or "framework_index"
```

### File Size Formatting
```python
from modules.utilities import util_format_file_size

size_str = util_format_file_size(1536)  # "1.5 KB"
size_str = util_format_file_size(1048576)  # "1.0 MB"
```

### Date Formatting
```python
from modules.utilities import util_format_date

date_str = util_format_date("2024-11-19T10:30:00Z")  # "Nov 19, 2024 10:30 AM"
```

### Number Extraction
```python
from modules.utilities import utils_remove_letter

temp = utils_remove_letter("-55°C")  # Returns: -55
value = utils_remove_letter("Speed: 120 km/h")  # Returns: 120
```

### Dictionary Drilling
```python
from modules.utilities import util_drill_dict

# Get ultimate value from nested dict
data = {"a": {"b": {"c": "value"}}}
result = util_drill_dict(data)  # Returns: "value"
```

### List to HTML
```python
from modules.utilities import util_list_to_html

html = util_list_to_html(["Item 1", "Item 2", "Item 3"])
# Returns: "<ul><li>Item 1</li><li>Item 2</li><li>Item 3</li></ul>"
```

## API Quick Reference
```python
# Form handling
def util_post_to_json(data: dict) -> dict

# Config access
def get_config_or_error(settings_manager, *config_paths) -> tuple

# Navigation
def get_home_endpoint() -> str
def get_breadcrumbs() -> List[dict]
def update_breadcrumbs(disp, level, title, endpoint, params=None, style=None)

# Formatting
def util_format_file_size(size_bytes: int) -> str
def util_format_date(iso_date: str) -> str
def utils_remove_letter(text: str) -> int

# Data manipulation
def util_drill_dict(input: dict) -> str
def util_list_to_html(input_list: List) -> str
```

## Common Pitfalls
1. **util_post_to_json MANDATORY** - Framework requires this for nested form data
2. **get_config_or_error** - Returns tuple (value, error); MUST check error
3. **Home endpoint** - Never hardcode "demo.index"; use get_home_endpoint()
4. **Form structure** - HTML names like "user.name" become `{"user": {"name": "..."}}`
5. **Multichoice** - Checkboxes with "_" separator (e.g., "options_choice1" → `{"options": ["choice1"]}`)
6. **Error rendering** - get_config_or_error returns pre-rendered error page (Displayer dict)
7. **File size units** - Returns human-readable (KB, MB, GB) not bytes
8. **Date format** - Assumes ISO 8601 format input

## Integration Points
- **Displayer**: Form data flows through util_post_to_json before route logic
- **Settings**: get_config_or_error wraps SettingsManager for safe access
- **Site_conf**: get_home_endpoint reads m_home_endpoint from site_conf_obj
- **Auth**: Breadcrumbs stored in session['breadcrumbs']

## Files
- `utilities.py` - All utility functions (single file, 974 lines)
