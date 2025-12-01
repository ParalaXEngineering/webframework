"""Settings Storage: JSON persistence layer for configuration management."""

import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Constants for settings structure keys
FRIENDLY_KEY = "friendly"
VALUE_KEY = "value"
TYPE_KEY = "type"
OPTIONS_KEY = "options"
PERSISTENT_KEY = "persistent"


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
        """Load settings from JSON file. Creates default config if file doesn't exist."""
        if not os.path.exists(self.config_path):
            # Try to create default config for application paths
            # Framework tests will use in-memory empty config
            self._create_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning("Config file not readable at %s, using empty config", self.config_path)
            self._settings = {}
        
        return self._settings if self._settings else {}
    
    def _create_default_config(self) -> None:
        """Create a default config.json file with empty structure."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Create minimal default config (features will be merged by manager)
        default_config = {}
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
    
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
                return self._settings[category][setting][VALUE_KEY]
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
            self._settings[category][setting][VALUE_KEY] = value
    
    def get_category(self, category: str) -> Dict[str, Any]:
        """Get all settings in a category (excluding 'friendly')."""
        if self._settings is None:
            self.load()
        
        if not self._settings or category not in self._settings:
            return {}
        
        return {k: v for k, v in self._settings[category].items() if k != FRIENDLY_KEY}
    
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
                    logger.error(
                        "Setting not found: %s. Available: %s",
                        path_str, available
                    )
                    raise SettingNotFoundError(
                        f"Setting not found: {path_str}\n"
                        f"Available keys at this level: {available}\n"
                        f"Please check your config.json file and ensure the setting exists."
                    )
                return default
            current = current[key]
        
        return current

