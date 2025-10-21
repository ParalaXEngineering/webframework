"""
Settings Manager - Business logic layer for settings management.

Simple wrapper around SettingsStorage with convenience methods.
"""

from typing import Any, Dict, List, Optional
from .storage import SettingsStorage, SettingNotFoundError


class SettingsManager:
    """Manages application settings with business logic."""
    
    def __init__(self, config_path: str):
        """Initialize manager with config file path."""
        self.storage = SettingsStorage(config_path)
        self._settings: Optional[Dict[str, Any]] = None
    
    def load(self) -> None:
        """Load settings from storage."""
        self._settings = self.storage.load()
    
    def save(self) -> None:
        """Save current settings to storage."""
        if self._settings is not None:
            self.storage.save(self._settings)
    
    def get_setting(self, key: str) -> Any:
        """Get setting value by key (category.setting)."""
        return self.storage.get(key)
    
    def set_setting(self, key: str, value: Any) -> None:
        """Set setting value by key (category.setting)."""
        self.storage.set(key, value)
    
    def get_category(self, category: str) -> Dict[str, Any]:
        """Get all settings in a category."""
        return self.storage.get_category(category)
    
    def get_category_friendly(self, category: str) -> str:
        """Get friendly name for a category."""
        if self._settings is None:
            self.load()
        if self._settings:
            return self._settings.get(category, {}).get('friendly', category)
        return category
    
    def list_categories(self) -> List[str]:
        """Get list of all categories."""
        return self.storage.list_categories()
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings."""
        return self.storage.get_all()
    
    def update_multiple(self, updates: Dict[str, Any]) -> None:
        """
        Update multiple settings at once.
        
        Args:
            updates: Dict with keys in dot notation and values to set
        """
        for key, value in updates.items():
            self.set_setting(key, value)
    
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
            addr = manager.get_nested("updates", "address", "value", default="")
            
            # Get with error on missing  
            addr = manager.get_nested("updates", "address", "value", raise_on_missing=True)
        """
        return self.storage.get_nested(*keys, default=default, raise_on_missing=raise_on_missing)

