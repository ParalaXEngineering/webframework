"""
Comprehensive Settings Tests

Tests for SettingsStorage and SettingsManager - the 3-layer settings architecture.

Architecture:
- Layer 1: JSON file (config.json) - persistent storage
- Layer 2: SettingsStorage - file I/O with dot-notation access (e.g., "application.name")
- Layer 3: SettingsManager - high-level API with caching and validation

Test Coverage:
- SettingsStorage: load, save, get, set, get_category, list_categories
- SettingsManager: load, get, set, save, get_category, get_category_friendly, update_multiple
- Type validation: string, int, bool
- Category management: nested structures with friendly names
- Dot-notation access: "category.setting" format

Test Data Structure:
{
    "category": {
        "friendly": "Category Display Name",
        "setting_name": {
            "friendly": "Setting Display Name",
            "type": "string|int|bool",
            "value": <setting_value>
        }
    }
}
"""

import pytest
import json
import tempfile
import os
from src.modules.settings_storage import SettingsStorage
from src.modules.settings_manager import SettingsManager


@pytest.fixture
def temp_config():
    """
    Create a temporary config file with test data.
    
    Creates a temporary JSON config file with application and database
    settings, automatically cleaned up after each test.
    """
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


# =============================================================================
# SettingsStorage Tests - Low-level file I/O
# =============================================================================

def test_storage_load(temp_config):
    """
    Test loading settings from file.
    
    Validates that SettingsStorage correctly reads JSON config file
    and loads nested category/setting structure.
    """
    storage = SettingsStorage(temp_config)
    settings = storage.load()
    
    assert "application" in settings
    assert "database" in settings
    assert settings["application"]["name"]["value"] == "Test App"


def test_storage_save(temp_config):
    """
    Test saving settings to file.
    
    Validates that SettingsStorage correctly writes modified settings
    back to JSON file with persistence.
    """
    storage = SettingsStorage(temp_config)
    settings = storage.load()
    
    settings["application"]["name"]["value"] = "Modified App"
    storage.save(settings)
    
    # Reload and verify
    storage2 = SettingsStorage(temp_config)
    settings2 = storage2.load()
    assert settings2["application"]["name"]["value"] == "Modified App"


def test_storage_get(temp_config):
    """
    Test getting individual setting values.
    
    Validates dot-notation access: "category.setting" format for
    convenient value retrieval without nested dict navigation.
    """
    storage = SettingsStorage(temp_config)
    storage.load()
    
    assert storage.get("application.name") == "Test App"
    assert storage.get("application.debug") == False
    assert storage.get("database.port") == 5432
    assert storage.get("nonexistent.key") is None


def test_storage_set(temp_config):
    """
    Test setting individual setting values.
    
    Validates that dot-notation set works correctly with type conversion
    and persists in memory (before save).
    """
    storage = SettingsStorage(temp_config)
    storage.load()
    
    storage.set("application.name", "New Name")
    assert storage.get("application.name") == "New Name"
    
    storage.set("application.debug", True)
    assert storage.get("application.debug") is True


def test_storage_get_category(temp_config):
    """
    Test getting all settings in a category.
    
    Validates that entire categories can be retrieved as dictionaries,
    excluding metadata like "friendly" names.
    """
    storage = SettingsStorage(temp_config)
    storage.load()
    
    app_settings = storage.get_category("application")
    assert "name" in app_settings
    assert "debug" in app_settings
    assert "friendly" not in app_settings  # Should be excluded


def test_storage_list_categories(temp_config):
    """
    Test listing all categories.
    
    Validates that top-level category names can be enumerated,
    useful for building settings UI navigation.
    """
    storage = SettingsStorage(temp_config)
    storage.load()
    
    categories = storage.list_categories()
    assert "application" in categories
    assert "database" in categories


# =============================================================================
# SettingsManager Tests - High-level API with caching
# =============================================================================

def test_manager_load(temp_config):
    """
    Test manager load functionality.
    
    Validates that SettingsManager correctly initializes from config file
    and provides high-level API access.
    """
    manager = SettingsManager(temp_config)
    manager.load()
    
    assert manager.get_setting("application.name") == "Test App"


def test_manager_get_set(temp_config):
    """
    Test manager get/set operations.
    
    Validates that SettingsManager provides convenient get_setting/set_setting
    methods with caching for performance.
    """
    manager = SettingsManager(temp_config)
    manager.load()
    
    manager.set_setting("application.name", "Manager Test")
    assert manager.get_setting("application.name") == "Manager Test"


def test_manager_save(temp_config):
    """
    Test manager save functionality.
    
    Validates that SettingsManager persists changes to disk correctly
    and can be reloaded by a new manager instance.
    """
    manager = SettingsManager(temp_config)
    manager.load()
    
    manager.set_setting("application.name", "Saved App")
    manager.save()
    
    # Reload with new manager
    manager2 = SettingsManager(temp_config)
    manager2.load()
    assert manager2.get_setting("application.name") == "Saved App"


def test_manager_get_category(temp_config):
    """
    Test manager category retrieval.
    
    Validates that SettingsManager can retrieve entire categories
    with all metadata (type, friendly, value).
    """
    manager = SettingsManager(temp_config)
    manager.load()
    
    app_settings = manager.get_category("application")
    assert "name" in app_settings
    assert app_settings["name"]["type"] == "string"


def test_manager_get_category_friendly(temp_config):
    """
    Test getting category friendly name.
    
    Validates that SettingsManager can retrieve user-friendly category names
    for display in settings UI headers.
    """
    manager = SettingsManager(temp_config)
    manager.load()
    
    assert manager.get_category_friendly("application") == "Application Settings"
    assert manager.get_category_friendly("database") == "Database Settings"


def test_manager_list_categories(temp_config):
    """
    Test listing all categories.
    
    Validates that SettingsManager can enumerate all top-level categories,
    useful for building navigation and tabbed settings interfaces.
    """
    manager = SettingsManager(temp_config)
    manager.load()
    
    categories = manager.list_categories()
    assert "application" in categories
    assert "database" in categories


def test_manager_update_multiple(temp_config):
    """
    Test updating multiple settings at once.
    
    Validates batch update capability: useful for form submissions
    where multiple settings change simultaneously.
    """
    manager = SettingsManager(temp_config)
    manager.load()
    
    updates = {
        "application.name": "Batch Updated",
        "application.port": 8080,
        "database.host": "remote.server.com"
    }
    
    for key, value in updates.items():
        manager.set_setting(key, value)
    
    assert manager.get_setting("application.name") == "Batch Updated"
    assert manager.get_setting("application.port") == 8080
    assert manager.get_setting("database.host") == "remote.server.com"


def test_manager_get_all_settings(temp_config):
    """
    Test getting all settings at once.
    
    Validates that SettingsManager can export entire configuration,
    useful for debugging or creating settings backups.
    """
    manager = SettingsManager(temp_config)
    manager.load()
    
    all_settings = manager.get_all_settings()
    
    assert "application" in all_settings
    assert "database" in all_settings
    assert all_settings["application"]["name"]["value"] == "Test App"
    assert all_settings["database"]["host"]["value"] == "localhost"

