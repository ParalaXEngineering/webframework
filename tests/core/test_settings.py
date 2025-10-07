"""
Comprehensive Settings Tests

Tests for SettingsStorage and SettingsManager.
"""

import pytest
import json
import tempfile
import os
from src.modules.settings_storage import SettingsStorage
from src.modules.settings_manager import SettingsManager


@pytest.fixture
def temp_config():
    """Create a temporary config file with test data."""
    config_data = {
        "application": {
            "friendly": "Application Settings",
            "name": {
                "friendly": "App Name",
                "type": "string",
                "value": "Test App"
            },
            "debug": {
                "friendly": "Debug Mode",
                "type": "bool",
                "value": False
            },
            "port": {
                "friendly": "Port Number",
                "type": "int",
                "value": 5000
            }
        },
        "database": {
            "friendly": "Database Settings",
            "host": {
                "friendly": "DB Host",
                "type": "string",
                "value": "localhost"
            },
            "port": {
                "friendly": "DB Port",
                "type": "int",
                "value": 5432
            }
        }
    }
    
    fd, path = tempfile.mkstemp(suffix='.json')
    with os.fdopen(fd, 'w') as f:
        json.dump(config_data, f)
    
    yield path
    
    try:
        os.unlink(path)
    except:
        pass


# SettingsStorage Tests

def test_storage_load(temp_config):
    """Test loading settings from file."""
    storage = SettingsStorage(temp_config)
    settings = storage.load()
    
    assert "application" in settings
    assert "database" in settings
    assert settings["application"]["name"]["value"] == "Test App"


def test_storage_save(temp_config):
    """Test saving settings to file."""
    storage = SettingsStorage(temp_config)
    settings = storage.load()
    
    settings["application"]["name"]["value"] = "Modified App"
    storage.save(settings)
    
    # Reload and verify
    storage2 = SettingsStorage(temp_config)
    settings2 = storage2.load()
    assert settings2["application"]["name"]["value"] == "Modified App"


def test_storage_get(temp_config):
    """Test getting individual setting values."""
    storage = SettingsStorage(temp_config)
    storage.load()
    
    assert storage.get("application.name") == "Test App"
    assert storage.get("application.debug") == False
    assert storage.get("database.port") == 5432
    assert storage.get("nonexistent.key") is None


def test_storage_set(temp_config):
    """Test setting individual setting values."""
    storage = SettingsStorage(temp_config)
    storage.load()
    
    storage.set("application.name", "New Name")
    assert storage.get("application.name") == "New Name"
    
    storage.set("application.debug", True)
    assert storage.get("application.debug") == True


def test_storage_get_category(temp_config):
    """Test getting all settings in a category."""
    storage = SettingsStorage(temp_config)
    storage.load()
    
    app_settings = storage.get_category("application")
    assert "name" in app_settings
    assert "debug" in app_settings
    assert "friendly" not in app_settings  # Should be excluded


def test_storage_list_categories(temp_config):
    """Test listing all categories."""
    storage = SettingsStorage(temp_config)
    storage.load()
    
    categories = storage.list_categories()
    assert "application" in categories
    assert "database" in categories


# SettingsManager Tests

def test_manager_load(temp_config):
    """Test manager load functionality."""
    manager = SettingsManager(temp_config)
    manager.load()
    
    assert manager.get_setting("application.name") == "Test App"


def test_manager_get_set(temp_config):
    """Test manager get/set operations."""
    manager = SettingsManager(temp_config)
    manager.load()
    
    manager.set_setting("application.name", "Manager Test")
    assert manager.get_setting("application.name") == "Manager Test"


def test_manager_save(temp_config):
    """Test manager save functionality."""
    manager = SettingsManager(temp_config)
    manager.load()
    
    manager.set_setting("application.name", "Saved App")
    manager.save()
    
    # Reload with new manager
    manager2 = SettingsManager(temp_config)
    manager2.load()
    assert manager2.get_setting("application.name") == "Saved App"


def test_manager_get_category(temp_config):
    """Test manager category retrieval."""
    manager = SettingsManager(temp_config)
    manager.load()
    
    app_settings = manager.get_category("application")
    assert "name" in app_settings
    assert app_settings["name"]["type"] == "string"


def test_manager_get_category_friendly(temp_config):
    """Test getting category friendly name."""
    manager = SettingsManager(temp_config)
    manager.load()
    
    assert manager.get_category_friendly("application") == "Application Settings"
    assert manager.get_category_friendly("database") == "Database Settings"


def test_manager_list_categories(temp_config):
    """Test manager list categories."""
    manager = SettingsManager(temp_config)
    manager.load()
    
    categories = manager.list_categories()
    assert len(categories) == 2
    assert "application" in categories


def test_manager_update_multiple(temp_config):
    """Test updating multiple settings at once."""
    manager = SettingsManager(temp_config)
    manager.load()
    
    updates = {
        "application.name": "Bulk Update",
        "application.debug": True,
        "database.port": 3306
    }
    manager.update_multiple(updates)
    
    assert manager.get_setting("application.name") == "Bulk Update"
    assert manager.get_setting("application.debug") == True
    assert manager.get_setting("database.port") == 3306


def test_manager_get_all_settings(temp_config):
    """Test getting all settings."""
    manager = SettingsManager(temp_config)
    manager.load()
    
    all_settings = manager.get_all_settings()
    assert "application" in all_settings
    assert "database" in all_settings
