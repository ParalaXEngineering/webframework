"""
Settings Storage Module

Handles persistent storage and retrieval of application settings.
Provides clean API for settings operations with validation and atomic writes.
"""

import json
import logging
from typing import Any, Optional, Dict
from pathlib import Path
import shutil
from datetime import datetime

logger = logging.getLogger(__name__)


class SettingsStorage:
    """
    Manages application settings with file-based persistence.
    
    Features:
    - JSON file storage with pretty formatting
    - Atomic writes (temp file + rename)
    - Schema validation
    - Default values
    - Type conversion
    - Backup on write
    
    Example:
        >>> storage = SettingsStorage("config.json")
        >>> settings = storage.load()
        >>> settings['application']['name'] = "MyApp"
        >>> storage.save(settings)
    """
    
    # Default settings schema
    DEFAULT_SETTINGS = {
        "application": {
            "name": "ParalaX Web Framework",
            "version": "1.0.0",
            "debug": False,
            "description": "Web framework for industrial applications"
        },
        "logging": {
            "level": "INFO",
            "max_file_size_mb": 10,
            "backup_count": 5,
            "log_to_file": True,
            "log_to_console": True
        },
        "network": {
            "host": "0.0.0.0",
            "port": 5001,
            "ssl_enabled": False,
            "ssl_cert_path": "",
            "ssl_key_path": ""
        },
        "authentication": {
            "enabled": True,
            "session_timeout_minutes": 30,
            "max_login_attempts": 3,
            "require_strong_passwords": False
        },
        "interface": {
            "theme": "light",
            "language": "en",
            "items_per_page": 25,
            "show_sidebar": True
        },
        "paths": {
            "upload_directory": "./uploads",
            "backup_directory": "./backups",
            "temp_directory": "./temp"
        }
    }
    
    # Schema for validation
    SCHEMA = {
        "application.name": {"type": str, "required": True, "min_length": 1, "max_length": 100},
        "application.version": {"type": str, "required": True, "pattern": r"^\d+\.\d+\.\d+$"},
        "application.debug": {"type": bool, "required": True},
        "logging.level": {"type": str, "required": True, "choices": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]},
        "logging.max_file_size_mb": {"type": int, "required": True, "min": 1, "max": 1000},
        "logging.backup_count": {"type": int, "required": True, "min": 0, "max": 100},
        "network.host": {"type": str, "required": True},
        "network.port": {"type": int, "required": True, "min": 1, "max": 65535},
        "network.ssl_enabled": {"type": bool, "required": True},
        "authentication.enabled": {"type": bool, "required": True},
        "authentication.session_timeout_minutes": {"type": int, "required": True, "min": 1, "max": 1440},
        "authentication.max_login_attempts": {"type": int, "required": True, "min": 1, "max": 10},
        "interface.theme": {"type": str, "required": True, "choices": ["light", "dark"]},
        "interface.items_per_page": {"type": int, "required": True, "min": 10, "max": 100},
    }
    
    def __init__(self, config_path: str, create_backup: bool = True):
        """
        Initialize settings storage.
        
        Args:
            config_path: Path to the JSON configuration file
            create_backup: Whether to create backups before saving
        """
        self.config_path = Path(config_path)
        self.create_backup = create_backup
        self._settings: Optional[Dict] = None
        
        # Ensure parent directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
    
    def load(self, create_if_missing: bool = True) -> Dict[str, Any]:
        """
        Load settings from file with defaults.
        
        Args:
            create_if_missing: If True, create file with defaults if it doesn't exist
            
        Returns:
            Dictionary containing all settings
            
        Raises:
            FileNotFoundError: If file doesn't exist and create_if_missing is False
            json.JSONDecodeError: If file contains invalid JSON
        """
        if not self.config_path.exists():
            if create_if_missing:
                logger.info(f"Config file not found at {self.config_path}, creating with defaults")
                self._settings = self._deep_copy_dict(self.DEFAULT_SETTINGS)
                self.save(self._settings)
                return self._settings
            else:
                raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
            
            # Merge with defaults to ensure all keys exist
            self._settings = self._merge_with_defaults(loaded_settings)
            logger.debug(f"Settings loaded from {self.config_path}")
            return self._settings
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            raise
    
    def save(self, settings: Dict[str, Any], validate: bool = True) -> bool:
        """
        Save settings with pretty formatting and validation.
        
        Args:
            settings: Settings dictionary to save
            validate: Whether to validate before saving
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate if requested
            if validate:
                valid, error = self.validate(settings)
                if not valid:
                    logger.error(f"Validation failed: {error}")
                    return False
            
            # Create backup if enabled
            if self.create_backup and self.config_path.exists():
                self._create_backup()
            
            # Write to temporary file first (atomic write)
            temp_path = self.config_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(
                    settings,
                    f,
                    indent=2,           # Pretty formatting
                    sort_keys=False,    # Preserve order
                    ensure_ascii=False  # Support unicode
                )
                f.write('\n')  # Add trailing newline
            
            # Atomic rename
            shutil.move(str(temp_path), str(self.config_path))
            
            # Update cached settings
            self._settings = settings
            
            logger.info(f"Settings saved to {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            # Clean up temp file if it exists
            if temp_path.exists():
                temp_path.unlink()
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a single setting value using dot notation.
        
        Args:
            key: Setting key in dot notation (e.g., "application.name")
            default: Default value if key not found
            
        Returns:
            Setting value or default
            
        Example:
            >>> storage.get("application.name")
            "ParalaX Web Framework"
            >>> storage.get("nonexistent.key", "default")
            "default"
        """
        if self._settings is None:
            self.load()
        
        keys = key.split('.')
        value = self._settings
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any, save_immediately: bool = True) -> bool:
        """
        Set a single setting value using dot notation.
        
        Args:
            key: Setting key in dot notation
            value: Value to set
            save_immediately: If True, save to file immediately
            
        Returns:
            True if successful, False otherwise
            
        Example:
            >>> storage.set("application.name", "My App")
            True
        """
        if self._settings is None:
            self.load()
        
        keys = key.split('.')
        current = self._settings
        
        try:
            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            # Set the value
            current[keys[-1]] = value
            
            # Save if requested
            if save_immediately:
                return self.save(self._settings)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to set {key}={value}: {e}")
            return False
    
    def update(self, updates: Dict[str, Any], save_immediately: bool = True) -> bool:
        """
        Update multiple settings atomically.
        
        Args:
            updates: Dictionary of key-value pairs to update (supports dot notation)
            save_immediately: If True, save to file immediately
            
        Returns:
            True if all updates successful, False otherwise
            
        Example:
            >>> storage.update({
            ...     "application.name": "New Name",
            ...     "network.port": 8080
            ... })
            True
        """
        if self._settings is None:
            self.load()
        
        try:
            # Apply all updates
            for key, value in updates.items():
                self.set(key, value, save_immediately=False)
            
            # Save once after all updates
            if save_immediately:
                return self.save(self._settings)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update settings: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """
        Reset all settings to default values.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self._settings = self._deep_copy_dict(self.DEFAULT_SETTINGS)
            return self.save(self._settings)
        except Exception as e:
            logger.error(f"Failed to reset settings: {e}")
            return False
    
    def validate(self, settings: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate settings against schema.
        
        Args:
            settings: Settings dictionary to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            for key, rules in self.SCHEMA.items():
                value = self._get_nested_value(settings, key)
                
                # Check required
                if rules.get("required", False) and value is None:
                    return False, f"Required setting '{key}' is missing"
                
                if value is None:
                    continue
                
                # Check type
                expected_type = rules.get("type")
                if expected_type and not isinstance(value, expected_type):
                    return False, f"Setting '{key}' must be of type {expected_type.__name__}, got {type(value).__name__}"
                
                # Check choices
                choices = rules.get("choices")
                if choices and value not in choices:
                    return False, f"Setting '{key}' must be one of {choices}, got '{value}'"
                
                # Check numeric ranges
                if isinstance(value, (int, float)):
                    min_val = rules.get("min")
                    max_val = rules.get("max")
                    if min_val is not None and value < min_val:
                        return False, f"Setting '{key}' must be >= {min_val}, got {value}"
                    if max_val is not None and value > max_val:
                        return False, f"Setting '{key}' must be <= {max_val}, got {value}"
                
                # Check string length
                if isinstance(value, str):
                    min_len = rules.get("min_length")
                    max_len = rules.get("max_length")
                    if min_len is not None and len(value) < min_len:
                        return False, f"Setting '{key}' must be at least {min_len} characters"
                    if max_len is not None and len(value) > max_len:
                        return False, f"Setting '{key}' must be at most {max_len} characters"
            
            return True, None
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_schema(self) -> Dict[str, Dict]:
        """Get the validation schema."""
        return self.SCHEMA.copy()
    
    def get_defaults(self) -> Dict[str, Any]:
        """Get the default settings."""
        return self._deep_copy_dict(self.DEFAULT_SETTINGS)
    
    def _create_backup(self) -> None:
        """Create a backup of the current config file."""
        try:
            backup_dir = self.config_path.parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"{self.config_path.stem}_{timestamp}.json"
            
            shutil.copy2(self.config_path, backup_path)
            logger.debug(f"Backup created: {backup_path}")
            
            # Keep only last 10 backups
            self._cleanup_old_backups(backup_dir, keep=10)
            
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")
    
    def _cleanup_old_backups(self, backup_dir: Path, keep: int = 10) -> None:
        """Remove old backup files, keeping only the most recent ones."""
        try:
            backups = sorted(backup_dir.glob(f"{self.config_path.stem}_*.json"))
            if len(backups) > keep:
                for old_backup in backups[:-keep]:
                    old_backup.unlink()
                    logger.debug(f"Removed old backup: {old_backup}")
        except Exception as e:
            logger.warning(f"Failed to cleanup old backups: {e}")
    
    def _merge_with_defaults(self, settings: Dict) -> Dict:
        """Merge loaded settings with defaults to ensure all keys exist."""
        result = self._deep_copy_dict(self.DEFAULT_SETTINGS)
        self._deep_merge(result, settings)
        return result
    
    def _deep_merge(self, base: Dict, updates: Dict) -> None:
        """Recursively merge updates into base dictionary."""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _deep_copy_dict(self, d: Dict) -> Dict:
        """Create a deep copy of a dictionary."""
        import copy
        return copy.deepcopy(d)
    
    def _get_nested_value(self, d: Dict, key: str) -> Any:
        """Get nested value using dot notation."""
        keys = key.split('.')
        value = d
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return None
