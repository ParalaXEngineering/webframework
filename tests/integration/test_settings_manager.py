"""
Integration tests for settings_manager module.

Tests the SettingsManager class with actual SettingsStorage integration.
"""

import pytest
import tempfile
from pathlib import Path
from src.modules.settings_manager import SettingsManager


class TestSettingsManager:
    """Test suite for SettingsManager class."""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file path for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
        Path(config_path).unlink()
        
        yield config_path
        
        Path(config_path).unlink(missing_ok=True)
        backup_dir = Path(config_path).parent / "backups"
        if backup_dir.exists():
            for backup in backup_dir.glob("*.json"):
                backup.unlink()
            backup_dir.rmdir()
    
    @pytest.fixture
    def manager(self, temp_config_file):
        """Create a SettingsManager instance for testing."""
        return SettingsManager(temp_config_file, create_backup=False)
    
    # Basic Operations
    
    def test_manager_load_creates_file(self, temp_config_file):
        """Test that manager loads and creates file with defaults."""
        manager = SettingsManager(temp_config_file)
        settings = manager.load()
        
        assert Path(temp_config_file).exists()
        assert isinstance(settings, dict)
        assert "application" in settings
        assert "logging" in settings
    
    def test_manager_get_setting(self, manager):
        """Test getting individual settings."""
        manager.load()
        
        app_name = manager.get_setting("application.name")
        assert app_name == "ParalaX Web Framework"
        
        port = manager.get_setting("network.port")
        assert port == 5001
        
        # Test default value
        unknown = manager.get_setting("nonexistent.key", "default_value")
        assert unknown == "default_value"
    
    def test_manager_set_setting(self, manager):
        """Test setting individual settings."""
        manager.load()
        
        # Set a value
        success = manager.set_setting("application.name", "Test App")
        assert success
        
        # Verify it was set
        value = manager.get_setting("application.name")
        assert value == "Test App"
        
        # Reload and verify persistence
        manager.load()
        value = manager.get_setting("application.name")
        assert value == "Test App"
    
    def test_manager_update_multiple(self, manager):
        """Test updating multiple settings atomically."""
        manager.load()
        
        updates = {
            "application.name": "Batch Update Test",
            "network.port": 8080,
            "logging.level": "ERROR"
        }
        
        success = manager.update_multiple(updates)
        assert success
        
        # Verify all updates
        assert manager.get_setting("application.name") == "Batch Update Test"
        assert manager.get_setting("network.port") == 8080
        assert manager.get_setting("logging.level") == "ERROR"
    
    # Category Operations
    
    def test_manager_get_category(self, manager):
        """Test getting entire category."""
        manager.load()
        
        app_settings = manager.get_category("application")
        assert isinstance(app_settings, dict)
        assert "name" in app_settings
        assert "version" in app_settings
        assert "debug" in app_settings
    
    def test_manager_update_category(self, manager):
        """Test updating entire category."""
        manager.load()
        
        new_app_settings = {
            "name": "Category Test",
            "version": "2.0.0",
            "debug": True
        }
        
        success = manager.update_category("application", new_app_settings)
        assert success
        
        # Verify category was updated
        app_settings = manager.get_category("application")
        assert app_settings["name"] == "Category Test"
        assert app_settings["version"] == "2.0.0"
        assert app_settings["debug"] is True
    
    def test_manager_list_categories(self, manager):
        """Test listing all categories."""
        manager.load()
        
        categories = manager.list_categories()
        assert isinstance(categories, list)
        assert "application" in categories
        assert "logging" in categories
        assert "network" in categories
        assert "authentication" in categories
        assert "interface" in categories
        assert "paths" in categories
    
    def test_manager_reset_category_to_defaults(self, manager):
        """Test resetting a category to defaults."""
        manager.load()
        
        # Modify a category
        manager.set_setting("application.name", "Modified")
        assert manager.get_setting("application.name") == "Modified"
        
        # Reset to defaults
        success = manager.reset_category_to_defaults("application")
        assert success
        
        # Verify it's back to default
        assert manager.get_setting("application.name") == "ParalaX Web Framework"
    
    # Import/Export
    
    def test_manager_export_settings(self, manager, temp_config_file):
        """Test exporting settings."""
        manager.load()
        
        # Export without file
        exported = manager.export_settings()
        assert isinstance(exported, dict)
        assert "application" in exported
        
        # Export to file
        export_path = str(Path(temp_config_file).parent / "exported.json")
        exported = manager.export_settings(export_path)
        assert Path(export_path).exists()
        
        # Cleanup
        Path(export_path).unlink()
    
    def test_manager_import_settings_replace(self, manager, temp_config_file):
        """Test importing settings (replace mode)."""
        manager.load()
        
        # Modify settings
        manager.set_setting("application.name", "Before Import")
        
        # Create export
        export_path = str(Path(temp_config_file).parent / "import_test.json")
        manager.export_settings(export_path)
        
        # Modify again
        manager.set_setting("application.name", "After Export")
        assert manager.get_setting("application.name") == "After Export"
        
        # Import (replace)
        success = manager.import_settings(export_path, merge=False)
        assert success
        
        # Should be back to exported value
        assert manager.get_setting("application.name") == "Before Import"
        
        # Cleanup
        Path(export_path).unlink()
    
    def test_manager_import_settings_merge(self, manager, temp_config_file):
        """Test importing settings (merge mode)."""
        manager.load()
        
        # Set initial values
        manager.set_setting("application.name", "Original Name")
        manager.set_setting("network.port", 9999)
        
        # Export current settings first
        export_path = str(Path(temp_config_file).parent / "merge_test.json")
        manager.export_settings(export_path)
        
        # Modify the export file to only change application.name
        # while keeping other settings like port
        import json
        with open(export_path, 'r') as f:
            merge_data = json.load(f)
        
        # Only change application.name in the export
        merge_data['application']['name'] = 'Merged Name'
        
        with open(export_path, 'w') as f:
            json.dump(merge_data, f, indent=2)
        
        # Import with merge
        success = manager.import_settings(export_path, merge=True)
        assert success
        
        # application.name should be updated
        assert manager.get_setting("application.name") == "Merged Name"
        # network.port should remain unchanged (was 9999, merge file also has 9999)
        assert manager.get_setting("network.port") == 9999
        
        # Cleanup
        Path(export_path).unlink()
    
    # Validation
    
    def test_manager_validate_settings(self, manager):
        """Test settings validation."""
        manager.load()
        
        valid, error = manager.validate_settings()
        assert valid is True
        assert error is None
    
    def test_manager_validation_fails_invalid_type(self, manager):
        """Test validation catches invalid types."""
        manager.load()
        
        # Try to set invalid type (port should be integer)
        success = manager.set_setting("network.port", "not_a_number", validate=True)
        assert success is False
        
        # Port should still be the default
        assert manager.get_setting("network.port") == 5001
    
    # Utility Methods
    
    def test_manager_get_setting_info(self, manager):
        """Test getting setting information."""
        manager.load()
        
        info = manager.get_setting_info("application.name")
        assert info['key'] == "application.name"
        assert info['current_value'] == "ParalaX Web Framework"
        assert info['default_value'] == "ParalaX Web Framework"
        assert info['type'] == 'str'
    
    def test_manager_search_settings(self, manager):
        """Test searching settings."""
        manager.load()
        
        # Search by key
        results = manager.search_settings("port")
        assert len(results) > 0
        assert any(r['path'] == 'network.port' for r in results)
        
        # Search by value
        results = manager.search_settings("ParalaX")
        assert len(results) > 0
        assert any(r['match_type'] == 'value' for r in results)
    
    def test_manager_get_modified_settings(self, manager):
        """Test getting modified settings."""
        manager.load()
        
        # Initially, nothing should be modified
        modified = manager.get_modified_settings()
        assert len(modified) == 0
        
        # Modify a setting
        manager.set_setting("application.name", "Modified App")
        
        # Should now show as modified
        modified = manager.get_modified_settings()
        assert "application.name" in modified
        assert modified["application.name"]["current"] == "Modified App"
        assert modified["application.name"]["default"] == "ParalaX Web Framework"
    
    def test_manager_delete_setting(self, manager):
        """Test deleting a setting."""
        manager.load()
        
        # Add a custom (non-required) setting
        manager.set_setting("custom.feature_flag", True)
        assert manager.get_setting("custom.feature_flag") is True
        
        # Delete it
        success = manager.delete_setting("custom.feature_flag")
        assert success
        
        # Should be gone
        assert manager.get_setting("custom.feature_flag") is None
    
    def test_manager_reset_to_defaults(self, manager):
        """Test resetting all settings to defaults."""
        manager.load()
        
        # Modify multiple settings
        manager.set_setting("application.name", "Modified")
        manager.set_setting("network.port", 9999)
        
        # Reset all
        success = manager.reset_to_defaults()
        assert success
        
        # Reload and verify defaults
        manager.load()
        assert manager.get_setting("application.name") == "ParalaX Web Framework"
        assert manager.get_setting("network.port") == 5001
