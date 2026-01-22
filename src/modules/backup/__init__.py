"""
Framework Backup Module

Handles backup and restore of framework-specific components:
- File Manager (database + HashFS storage)
- Tooltip Manager (database)
- Configuration files
"""

from .file_manager_backup import (
    get_file_manager_info,
    backup_file_manager,
    restore_file_manager,
    calculate_file_manager_size,
    count_uploaded_files,
)

from .tooltip_backup import (
    get_tooltip_manager_info,
    backup_tooltip_manager,
    restore_tooltip_manager,
)

from .config_backup import (
    backup_config,
    restore_config,
)

__all__ = [
    # File Manager
    "get_file_manager_info",
    "backup_file_manager",
    "restore_file_manager",
    "calculate_file_manager_size",
    "count_uploaded_files",
    # Tooltip Manager
    "get_tooltip_manager_info",
    "backup_tooltip_manager",
    "restore_tooltip_manager",
    # Config
    "backup_config",
    "restore_config",
]
