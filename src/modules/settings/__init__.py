"""Settings module: Provides configuration management for the web framework."""

from .storage import SettingsStorage, SettingNotFoundError
from .manager import SettingsManager

__all__ = [
    'SettingsStorage',
    'SettingsManager',
    'SettingNotFoundError',
    'settings_manager',  # Global singleton instance
]

# Global settings manager instance (initialized by framework at startup)
settings_manager = None


