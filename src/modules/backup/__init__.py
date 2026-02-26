"""
Backup modules for framework components.

Provides backup and restore functionality for:
- File Manager (database + uploaded files)
- Tooltip Manager (database)
- Configuration (config.json)
"""

from . import file_manager_backup
from . import tooltip_backup
from . import config_backup

__all__ = [
    'file_manager_backup',
    'tooltip_backup',
    'config_backup',
]
