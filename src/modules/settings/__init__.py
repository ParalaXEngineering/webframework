"""
Settings Module

Provides configuration management for the web framework.
Handles storage, retrieval, and management of application settings.
"""

try:
    from .storage import SettingsStorage, SettingNotFoundError
    from .manager import SettingsManager
except ImportError:
    # Fallback for direct execution
    from storage import SettingsStorage, SettingNotFoundError
    from manager import SettingsManager

__all__ = [
    'SettingsStorage',
    'SettingsManager',
    'SettingNotFoundError',
]

