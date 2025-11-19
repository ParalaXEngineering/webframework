# Settings System

## Purpose
JSON-based configuration management with nested settings, optional section merging, and user overrides. Auto-merges feature configs when enabled in site_conf.

## Core Components
- `src/modules/settings/manager.py` - SettingsManager business logic
- `src/modules/settings/storage.py` - SettingsStorage JSON I/O
- `src/modules/settings/__init__.py` - Module exports
- `src/modules/default_configs.py` - Optional feature configs (FEATURE_CONFIGS)
- `website/settings/config.json` - Main config file

## Critical Patterns

### Safe Config Access (MANDATORY)
```python
from modules.utilities import get_config_or_error

# Single value
source, error = get_config_or_error(settings_mgr, "updates.source.value")
if error:
    return error  # Auto-renders error page via Displayer

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
user = configs["updates.user.value"]
```

### Direct Access (Use Sparingly)
```python
# Get single setting
value = settings_mgr.get_setting("file_storage.max_file_size_mb")

# Get category
file_config = settings_mgr.get_category("file_storage")

# Set setting
settings_mgr.set_setting("file_storage.max_file_size_mb", 100)
settings_mgr.save()
```

### Nested Access
```python
# Safe nested get
addr = settings_mgr.get_nested("updates", "address", "value", default="")

# Raise error on missing
addr = settings_mgr.get_nested("updates", "address", "value", raise_on_missing=True)
```

### Optional Config Merging (Site_conf)
```python
# In site_conf.py
class MySiteConf(Site_conf):
    def __init__(self):
        super().__init__()
        self.enable_file_manager()  # Auto-merges FILE_STORAGE_CONFIG
        self.enable_threads()       # Auto-merges FRAMEWORK_UI_CONFIG
        self.enable_updater()       # Auto-merges UPDATES_CONFIG
```

## API Quick Reference
```python
class SettingsManager:
    def __init__(config_path: str)
    
    # Load/Save
    def load() -> None
    def save() -> None
    
    # Access
    def get_setting(key: str) -> Any  # "category.setting"
    def set_setting(key: str, value: Any)
    def get_category(category: str) -> Dict[str, Any]
    def get_nested(*keys: str, default: Any = None, raise_on_missing: bool = False) -> Any
    
    # Metadata
    def set_setting_metadata(key: str, metadata_key: str, metadata_value: Any)
    def get_category_friendly(category: str) -> str
    def list_categories() -> List[str]
    
    # Bulk operations
    def update_multiple(updates: Dict[str, Any])
    def get_all_settings() -> Dict[str, Any]
    
    # User overrides
    def get_overridable_settings() -> Dict[str, Any]
    
    # Auto-merge
    def merge_optional_configs(site_conf_obj)

# Config structure
{
    "category_name": {
        "friendly": "Display Name",
        "setting_key": {
            "type": "string|int|bool|select|array|path",
            "friendly": "Setting Label",
            "value": "actual_value",
            "persistent": true,
            "overridable_by_user": false,
            "options": ["opt1", "opt2"]  # For select type
        }
    }
}
```

## Common Pitfalls
1. **Dot notation** - Use `"category.setting"` not `"category", "setting"`
2. **save() required** - Changes only in memory until `save()` called
3. **Missing keys** - Use `get_config_or_error()` not direct access (prevents KeyError crashes)
4. **Type consistency** - Config types (string, int, bool) must match usage
5. **Friendly names** - Use `get_category_friendly()` for display, not raw category name
6. **Optional sections** - Call `merge_optional_configs()` AFTER loading config, BEFORE using it
7. **User overrides** - Set `overridable_by_user: true` for settings users can customize
8. **Default configs** - Defined in `default_configs.py` as `FEATURE_CONFIGS` dict

## Integration Points
- **Site_conf**: Calls `merge_optional_configs()` to add feature sections
- **File Manager**: Reads `file_storage.*` settings for validation/limits
- **Utilities**: `get_config_or_error()` helper prevents crashes
- **Auth**: User preferences stored separately (not in main config.json)
- **Default_configs**: `FEATURE_CONFIGS` mapping feature flags to config sections

## Files
- `manager.py` - SettingsManager with business logic
- `storage.py` - SettingsStorage with JSON I/O, nested key parsing
- `default_configs.py` - FEATURE_CONFIGS dict (framework_ui, file_manager, etc.)
- `website/settings/config.json` - Main config file (JSON)
- `website/settings/.file_metadata.db` - File manager metadata (SQLite, not settings)
