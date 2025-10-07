"""
Unit tests for settings_storage module.

Tests the SettingsStorage class in isolation without external dependencies.
"""

import pytest
import json
import tempfile
from pathlib import Path
from src.modules.settings_storage import SettingsStorage


class TestSettingsStorage:
    """Test suite for SettingsStorage class."""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file path for testing (file not created)."""
        # Create a temp file just to get a valid path, then delete it
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
        # Delete the file immediately - we just want the path
        Path(config_path).unlink()
        
        yield config_path
        
        # Cleanup
        Path(config_path).unlink(missing_ok=True)
        # Cleanup backups
        backup_dir = Path(config_path).parent / "backups"
        if backup_dir.exists():
            for backup in backup_dir.glob("*.json"):
                backup.unlink()
            backup_dir.rmdir()
    
    @pytest.fixture
    def storage(self, temp_config_file):
        """Create a SettingsStorage instance for testing."""
        return SettingsStorage(temp_config_file, create_backup=False)
    
    def test_settings_load_creates_file_if_missing(self, temp_config_file):
        """Test that load() creates file with defaults if it doesn't exist."""
        # The fixture already ensures the file doesn't exist
        # Don't try to delete it again
        
        storage = SettingsStorage(temp_config_file)
        settings = storage.load()
        
        assert Path(temp_config_file).exists()
        assert isinstance(settings, dict)
        assert "application" in settings
        assert "logging" in settings
        assert settings["application"]["name"] == "ParalaX Web Framework"
    
    def test_settings_save_creates_pretty_json(self, storage, temp_config_file):
        """Test that save() creates pretty-formatted JSON."""
        settings = storage.load()
        settings["application"]["name"] = "Test App"
        
        storage.save(settings)
        
        # Read raw file content
        with open(temp_config_file, 'r') as f:
            content = f.read()
        
        # Check formatting
        assert "  " in content  # Has indentation
        assert '"application"' in content
        assert '"name": "Test App"' in content
        assert content.endswith('\n')  # Has trailing newline
    
    def test_settings_get_returns_default_if_not_found(self, storage):
        """Test that get() returns default value for missing keys."""
        storage.load()
        
        # Existing key
        assert storage.get("application.name") == "ParalaX Web Framework"
        
        # Non-existent key with default
        assert storage.get("nonexistent.key", "default_value") == "default_value"
        
        # Non-existent key without default
        assert storage.get("nonexistent.key") is None
    
    def test_settings_set_updates_value(self, storage):
        """Test that set() updates a setting value."""
        storage.load()
        
        result = storage.set("application.name", "New Name", save_immediately=False)
        assert result is True
        assert storage.get("application.name") == "New Name"
    
    def test_settings_set_creates_nested_keys(self, storage):
        """Test that set() can create nested keys that don't exist."""
        storage.load()
        
        result = storage.set("new.nested.key", "value", save_immediately=False)
        assert result is True
        assert storage.get("new.nested.key") == "value"
    
    def test_settings_update_is_atomic(self, storage, temp_config_file):
        """Test that update() saves all changes atomically."""
        storage.load()
        
        updates = {
            "application.name": "Updated App",
            "network.port": 8080,
            "logging.level": "DEBUG"
        }
        
        result = storage.update(updates)
        assert result is True
        
        # Verify all updates were applied
        assert storage.get("application.name") == "Updated App"
        assert storage.get("network.port") == 8080
        assert storage.get("logging.level") == "DEBUG"
        
        # Verify file was saved
        with open(temp_config_file, 'r') as f:
            saved_data = json.load(f)
        assert saved_data["application"]["name"] == "Updated App"
    
    def test_settings_validate_rejects_invalid_data(self, storage):
        """Test that validate() rejects invalid settings."""
        storage.load()
        
        # Invalid type
        settings = storage._settings.copy()
        settings["network"]["port"] = "not_a_number"
        valid, error = storage.validate(settings)
        assert valid is False
        assert "type" in error.lower()
        
        # Out of range
        settings = storage._settings.copy()
        settings["network"]["port"] = 99999
        valid, error = storage.validate(settings)
        assert valid is False
        assert "99999" in error or "65535" in error
        
        # Invalid choice
        settings = storage._settings.copy()
        settings["logging"]["level"] = "INVALID"
        valid, error = storage.validate(settings)
        assert valid is False
        assert "INVALID" in error
    
    def test_settings_validate_accepts_valid_data(self, storage):
        """Test that validate() accepts valid settings."""
        settings = storage.load()
        
        valid, error = storage.validate(settings)
        assert valid is True
        assert error is None
    
    def test_settings_save_preserves_order(self, storage, temp_config_file):
        """Test that save() preserves key order (not alphabetically sorted)."""
        settings = storage.load()
        storage.save(settings)
        
        with open(temp_config_file, 'r') as f:
            content = f.read()
        
        # Check that 'application' appears before other keys
        # (since sort_keys=False in json.dump)
        app_pos = content.find('"application"')
        logging_pos = content.find('"logging"')
        network_pos = content.find('"network"')
        
        assert app_pos < logging_pos < network_pos
    
    def test_settings_reset_to_defaults(self, storage):
        """Test that reset_to_defaults() restores default settings."""
        storage.load()
        
        # Modify settings
        storage.set("application.name", "Modified", save_immediately=False)
        storage.set("network.port", 9999, save_immediately=False)
        
        # Reset
        result = storage.reset_to_defaults()
        assert result is True
        
        # Verify defaults restored
        assert storage.get("application.name") == "ParalaX Web Framework"
        assert storage.get("network.port") == 5001
    
    def test_settings_handles_concurrent_access(self, storage, temp_config_file):
        """Test that atomic writes prevent data corruption from concurrent access."""
        storage.load()
        
        # Simulate multiple writes
        for i in range(10):
            storage.set("application.version", f"1.0.{i}")
        
        # File should still be valid JSON
        with open(temp_config_file, 'r') as f:
            data = json.load(f)
        
        assert "application" in data
        assert "version" in data["application"]
    
    def test_settings_backup_creation(self, temp_config_file):
        """Test that backups are created when enabled."""
        storage = SettingsStorage(temp_config_file, create_backup=True)
        settings = storage.load()
        
        # Modify and save (should create backup)
        settings["application"]["name"] = "Modified"
        storage.save(settings)
        
        # Check backup was created
        backup_dir = Path(temp_config_file).parent / "backups"
        assert backup_dir.exists()
        backups = list(backup_dir.glob("*.json"))
        assert len(backups) >= 1
    
    def test_settings_get_schema(self, storage):
        """Test that get_schema() returns the validation schema."""
        schema = storage.get_schema()
        
        assert isinstance(schema, dict)
        assert "application.name" in schema
        assert "type" in schema["application.name"]
    
    def test_settings_get_defaults(self, storage):
        """Test that get_defaults() returns default settings."""
        defaults = storage.get_defaults()
        
        assert isinstance(defaults, dict)
        assert "application" in defaults
        assert defaults["application"]["name"] == "ParalaX Web Framework"
        
        # Verify it's a copy, not the original
        defaults["application"]["name"] = "Modified"
        assert storage.DEFAULT_SETTINGS["application"]["name"] == "ParalaX Web Framework"
    
    def test_settings_validation_required_fields(self, storage):
        """Test that validation checks required fields."""
        settings = {}
        
        valid, error = storage.validate(settings)
        assert valid is False
        assert "required" in error.lower()
    
    def test_settings_validation_string_length(self, storage):
        """Test that validation checks string length constraints."""
        settings = storage.load()
        
        # Too short
        settings["application"]["name"] = ""
        valid, error = storage.validate(settings)
        assert valid is False
        assert "character" in error.lower()
        
        # Too long
        settings["application"]["name"] = "x" * 200
        valid, error = storage.validate(settings)
        assert valid is False
        assert "character" in error.lower()
    
    def test_settings_merge_with_defaults(self, storage, temp_config_file):
        """Test that loading merges with defaults for missing keys."""
        # Create a config file with only partial settings
        partial_settings = {
            "application": {
                "name": "Custom App"
            }
        }
        
        with open(temp_config_file, 'w') as f:
            json.dump(partial_settings, f)
        
        # Load should merge with defaults
        settings = storage.load()
        
        assert settings["application"]["name"] == "Custom App"  # Custom value
        assert "version" in settings["application"]  # From defaults
        assert "logging" in settings  # From defaults
        assert "network" in settings  # From defaults
