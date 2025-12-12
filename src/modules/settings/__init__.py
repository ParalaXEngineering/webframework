"""Settings module: Provides configuration management for the web framework."""

from .storage import SettingsStorage, SettingNotFoundError
from .manager import SettingsManager

__all__ = [
    'SettingsStorage',
    'SettingsManager',
    'SettingNotFoundError',
]


