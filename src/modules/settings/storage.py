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
