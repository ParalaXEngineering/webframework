"""
Settings Storage - Simple JSON persistence layer.

Handles reading/writing configuration with original structure:
{
    "category": {
        "friendly": "Category Label",
        "setting": {
            "friendly": "Setting Label",
            "type": "string|int|bool|select|multistring|...",
            "value": <value>,
            "options": [...],  # for select types
            "persistent": true/false  # optional
        }
    }
}
"""

import json
from typing import Any, Dict, Optional


class SettingNotFoundError(Exception):
    """Raised when a required setting is not found in the configuration."""
    pass


class SettingsStorage:
    """Simple JSON-based settings storage."""
    
    def __init__(self, config_path: str):
        """Initialize with config file path."""
        self.config_path = config_path
        self._settings: Optional[Dict[str, Any]] = None
    
    def load(self) -> Dict[str, Any]:
        """Load settings from JSON file."""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._settings = json.load(f)
        return self._settings if self._settings else {}
    
    def save(self, settings: Dict[str, Any]) -> None:
        """Save settings to JSON file."""
        self._settings = settings
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    
    def get(self, key: str) -> Any:
        """
        Get setting value by dot notation (category.setting).
        Returns None if not found.
        """
        if self._settings is None:
            self.load()
        
        parts = key.split('.')
        if len(parts) < 2:
            return None
        
        category, setting = parts[0], '.'.join(parts[1:])
        
        try:
            if self._settings:
                return self._settings[category][setting]['value']
        except (KeyError, TypeError):
            pass
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set setting value by dot notation (category.setting)."""
        if self._settings is None:
            self.load()
        
        parts = key.split('.')
        if len(parts) < 2:
            raise ValueError(f"Invalid key: {key}")
        
        category, setting = parts[0], '.'.join(parts[1:])
        
        if self._settings and category not in self._settings:
            raise KeyError(f"Category not found: {category}")
        if self._settings and setting not in self._settings[category]:
            raise KeyError(f"Setting not found: {setting}")
        
        if self._settings:
            self._settings[category][setting]['value'] = value
    
    def get_category(self, category: str) -> Dict[str, Any]:
        """Get all settings in a category (excluding 'friendly')."""
        if self._settings is None:
            self.load()
        
        if not self._settings or category not in self._settings:
            return {}
        
        return {k: v for k, v in self._settings[category].items() if k != 'friendly'}
    
    def list_categories(self) -> list:
        """Get list of category names."""
        if self._settings is None:
            self.load()
        return list(self._settings.keys()) if self._settings else []
    
    def get_all(self) -> Dict[str, Any]:
        """Get complete settings dictionary."""
        if self._settings is None:
            self.load()
        return self._settings if self._settings else {}
    
    def get_nested(self, *keys: str, default: Any = None, raise_on_missing: bool = False) -> Any:
        """
        Safely get a nested setting value.
        
        Args:
            *keys: Path to the setting (e.g., "updates", "address", "value")
            default: Default value if not found (only used if raise_on_missing=False)
            raise_on_missing: If True, raise SettingNotFoundError instead of returning default
            
        Returns:
            The setting value or default
            
        Raises:
            SettingNotFoundError: If setting not found and raise_on_missing=True
            
        Example:
            # Get updates.address.value with default
            addr = storage.get_nested("updates", "address", "value", default="")
            
            # Get with error on missing
            addr = storage.get_nested("updates", "address", "value", raise_on_missing=True)
        """
        if self._settings is None:
            self.load()
        
        if not self._settings:
            if raise_on_missing:
                raise SettingNotFoundError("Settings file is empty or not loaded")
            return default
        
        current = self._settings
        path_taken = []
        
        for key in keys:
            path_taken.append(key)
            if not isinstance(current, dict) or key not in current:
                if raise_on_missing:
                    path_str = " → ".join(path_taken)
                    available = list(current.keys()) if isinstance(current, dict) else []
                    raise SettingNotFoundError(
                        f"Setting not found: {path_str}\n"
                        f"Available keys at this level: {available}\n"
                        f"Please check your config.json file and ensure the setting exists."
                    )
                return default
            current = current[key]
        
        return current

