"""
Settings Manager Module

Business logic layer for settings management.
Provides high-level operations for settings with category-based organization.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from .settings_storage import SettingsStorage

logger = logging.getLogger(__name__)


class SettingsManager:
    """
    Business logic layer for settings management.
    
    Provides high-level operations like category management, validation,
    export/import, and settings utilities.
    """
    
    def __init__(self, config_path: str, create_backup: bool = True):
        """
        Initialize settings manager.
        
        Args:
            config_path: Path to config file
            create_backup: Whether to create backups on save
        """
        self.storage = SettingsStorage(config_path, create_backup=create_backup)
        self._settings = None
        
    def load(self) -> Dict[str, Any]:
        """
        Load settings from storage.
        
        Returns:
            Dictionary containing all settings
        """
        self._settings = self.storage.load()
        return self._settings
    
    def save(self) -> bool:
        """
        Save current settings to storage.
        
        Returns:
            True if successful, False otherwise
        """
        if self._settings is None:
            logger.warning("No settings loaded, nothing to save")
            return False
        return self.storage.save(self._settings)
    
    # Category Management
    
    def get_category(self, category: str) -> Optional[Dict[str, Any]]:
        """
        Get all settings for a specific category.
        
        Args:
            category: Category name (e.g., 'application', 'logging')
            
        Returns:
            Dictionary of category settings or None if not found
        """
        if self._settings is None:
            self.load()
        return self._settings.get(category)
    
    def update_category(self, category: str, settings: Dict[str, Any], validate: bool = True) -> bool:
        """
        Update all settings in a category.
        
        Args:
            category: Category name
            settings: New settings for the category
            validate: Whether to validate before updating
            
        Returns:
            True if successful, False otherwise
        """
        if self._settings is None:
            self.load()
        
        # Create a copy to validate
        test_settings = self._settings.copy()
        test_settings[category] = settings
        
        # Validate if requested
        if validate:
            valid, error = self.storage.validate(test_settings)
            if not valid:
                logger.error(f"Validation failed for category '{category}': {error}")
                return False
        
        # Update the category
        self._settings[category] = settings
        return self.save()
    
    def list_categories(self) -> List[str]:
        """
        Get list of all setting categories.
        
        Returns:
            List of category names
        """
        if self._settings is None:
            self.load()
        return list(self._settings.keys())
    
    # Individual Setting Operations
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a single setting value using dot notation.
        
        Args:
            key: Setting key in dot notation (e.g., 'application.name')
            default: Default value if not found
            
        Returns:
            Setting value or default
        """
        if self._settings is None:
            self.load()
        return self.storage.get(key, default)
    
    def set_setting(self, key: str, value: Any, validate: bool = True, save_immediately: bool = True) -> bool:
        """
        Set a single setting value using dot notation.
        
        Args:
            key: Setting key in dot notation
            value: Value to set
            validate: Whether to validate before setting
            save_immediately: Whether to save immediately after setting
            
        Returns:
            True if successful, False otherwise
        """
        if self._settings is None:
            self.load()
        
        # Use storage's set method (which validates internally if needed)
        success = self.storage.set(key, value, save_immediately=False)
        if not success:
            return False
        
        # Validate the entire settings structure if requested
        if validate:
            valid, error = self.storage.validate(self.storage._settings)
            if not valid:
                logger.error(f"Validation failed for key '{key}': {error}")
                # Reload to revert the change
                self.load()
                return False
        
        # Update our cache
        self._settings = self.storage._settings
        
        # Save if requested
        if save_immediately:
            return self.save()
        return True
    
    def delete_setting(self, key: str, save_immediately: bool = True) -> bool:
        """
        Delete a setting using dot notation.
        
        Args:
            key: Setting key in dot notation
            save_immediately: Whether to save immediately after deletion
            
        Returns:
            True if successful, False otherwise
        """
        if self._settings is None:
            self.load()
        
        parts = key.split('.')
        current = self._settings
        
        try:
            # Navigate to parent
            for part in parts[:-1]:
                current = current[part]
            
            # Delete the final key
            if parts[-1] in current:
                del current[parts[-1]]
                
                if save_immediately:
                    return self.save()
                return True
            else:
                logger.warning(f"Key '{key}' not found")
                return False
                
        except (KeyError, TypeError) as e:
            logger.error(f"Error deleting key '{key}': {e}")
            return False
    
    # Batch Operations
    
    def update_multiple(self, updates: Dict[str, Any], validate: bool = True) -> bool:
        """
        Update multiple settings atomically.
        
        Args:
            updates: Dictionary of key-value pairs to update (supports dot notation)
            validate: Whether to validate after all updates
            
        Returns:
            True if successful, False otherwise
        """
        if self._settings is None:
            self.load()
        
        # Use storage's update method
        success = self.storage.update(updates, save_immediately=False)
        if not success:
            return False
        
        # Validate if requested
        if validate:
            valid, error = self.storage.validate(self.storage._settings)
            if not valid:
                logger.error(f"Validation failed after batch update: {error}")
                # Reload to revert changes
                self.load()
                return False
        
        # Update our cache
        self._settings = self.storage._settings
        
        # Save
        return self.save()
    
    # Import/Export
    
    def export_settings(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Export current settings.
        
        Args:
            output_path: Optional path to save exported settings
            
        Returns:
            Dictionary of all settings
        """
        if self._settings is None:
            self.load()
        
        if output_path:
            export_storage = SettingsStorage(output_path, create_backup=False)
            export_storage.save(self._settings)
            logger.info(f"Settings exported to {output_path}")
        
        return self._settings.copy()
    
    def import_settings(self, input_path: str, merge: bool = False, validate: bool = True) -> bool:
        """
        Import settings from file.
        
        Args:
            input_path: Path to settings file to import
            merge: If True, merge with existing settings; if False, replace all
            validate: Whether to validate imported settings
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import_storage = SettingsStorage(input_path, create_backup=False)
            imported_settings = import_storage.load()
            
            if validate:
                valid, error = self.storage.validate(imported_settings)
                if not valid:
                    logger.error(f"Imported settings validation failed: {error}")
                    return False
            
            if merge:
                # Load current settings if not loaded
                if self._settings is None:
                    self.load()
                # Merge imported settings into current
                self._deep_merge(self._settings, imported_settings)
            else:
                # Replace all settings
                self._settings = imported_settings
            
            # Save the imported settings
            success = self.save()
            if success:
                # Reload to ensure cache is in sync
                self.load()
            return success
            
        except Exception as e:
            logger.error(f"Error importing settings from {input_path}: {e}")
            return False
    
    def _deep_merge(self, target: Dict, source: Dict) -> None:
        """
        Deep merge source dict into target dict (modifies target in place).
        
        Args:
            target: Target dictionary to merge into
            source: Source dictionary to merge from
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    # Validation and Defaults
    
    def validate_settings(self) -> Tuple[bool, Optional[str]]:
        """
        Validate current settings against schema.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if self._settings is None:
            self.load()
        return self.storage.validate(self._settings)
    
    def reset_to_defaults(self) -> bool:
        """
        Reset all settings to default values.
        
        Returns:
            True if successful, False otherwise
        """
        return self.storage.reset_to_defaults()
    
    def reset_category_to_defaults(self, category: str) -> bool:
        """
        Reset a specific category to default values.
        
        Args:
            category: Category name to reset
            
        Returns:
            True if successful, False otherwise
        """
        if self._settings is None:
            self.load()
        
        defaults = self.storage.get_defaults()
        if category not in defaults:
            logger.error(f"Unknown category: {category}")
            return False
        
        self._settings[category] = defaults[category].copy()
        return self.save()
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get the settings schema.
        
        Returns:
            Dictionary containing schema definition
        """
        return self.storage.get_schema()
    
    def get_defaults(self) -> Dict[str, Any]:
        """
        Get default settings.
        
        Returns:
            Dictionary containing default settings
        """
        return self.storage.get_defaults()
    
    # Utility Methods
    
    def get_setting_info(self, key: str) -> Dict[str, Any]:
        """
        Get information about a specific setting.
        
        Args:
            key: Setting key in dot notation
            
        Returns:
            Dictionary with setting info (value, type, default, schema)
        """
        if self._settings is None:
            self.load()
        
        current_value = self.storage.get(key)
        defaults = self.storage.get_defaults()
        default_value = self._get_nested_value(defaults, key)
        
        # Try to find schema info
        schema = self.storage.get_schema()
        schema_info = self._get_nested_value(schema, key)
        
        return {
            'key': key,
            'current_value': current_value,
            'default_value': default_value,
            'schema': schema_info,
            'type': type(current_value).__name__ if current_value is not None else 'None'
        }
    
    def _get_nested_value(self, data: Dict, key: str) -> Any:
        """
        Get nested value from dictionary using dot notation.
        
        Args:
            data: Dictionary to search in
            key: Key in dot notation
            
        Returns:
            Value or None if not found
        """
        parts = key.split('.')
        current = data
        try:
            for part in parts:
                current = current[part]
            return current
        except (KeyError, TypeError):
            return None
    
    def search_settings(self, search_term: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
        Search for settings by key or value.
        
        Args:
            search_term: Term to search for
            case_sensitive: Whether search should be case-sensitive
            
        Returns:
            List of matching settings with their paths and values
        """
        if self._settings is None:
            self.load()
        
        results = []
        search_lower = search_term if case_sensitive else search_term.lower()
        
        def search_recursive(obj: Any, path: str = "") -> None:
            """Recursively search through settings."""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    key_match = search_lower in (key if case_sensitive else key.lower())
                    
                    if key_match:
                        results.append({
                            'path': current_path,
                            'value': value,
                            'match_type': 'key'
                        })
                    
                    if isinstance(value, (str, int, float, bool)):
                        value_str = str(value)
                        value_match = search_lower in (value_str if case_sensitive else value_str.lower())
                        if value_match and not key_match:
                            results.append({
                                'path': current_path,
                                'value': value,
                                'match_type': 'value'
                            })
                    
                    search_recursive(value, current_path)
        
        search_recursive(self._settings)
        return results
    
    def get_modified_settings(self) -> Dict[str, Any]:
        """
        Get settings that differ from defaults.
        
        Returns:
            Dictionary of modified settings with their paths
        """
        if self._settings is None:
            self.load()
        
        defaults = self.storage.get_defaults()
        modified = {}
        
        def compare_recursive(current: Any, default: Any, path: str = "") -> None:
            """Recursively compare current and default settings."""
            if isinstance(current, dict) and isinstance(default, dict):
                for key in current.keys():
                    current_path = f"{path}.{key}" if path else key
                    if key in default:
                        if current[key] != default[key]:
                            if isinstance(current[key], dict):
                                compare_recursive(current[key], default[key], current_path)
                            else:
                                modified[current_path] = {
                                    'current': current[key],
                                    'default': default[key]
                                }
                    else:
                        # New key not in defaults
                        modified[current_path] = {
                            'current': current[key],
                            'default': None
                        }
        
        compare_recursive(self._settings, defaults)
        return modified
