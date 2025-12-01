"""
File Manager Package - Comprehensive file management with versioning and tagging.

This package provides:
- Content-addressable storage with deduplication (HashFS)
- File versioning with group IDs
- Tag-based organization
- Integrity verification
- Database-backed metadata

Main exports:
- FileManager: Main manager class
- FileGroup, FileVersion, FileTag: Database models
- ContentAddressableStorage: Storage backend
"""

from .manager import FileManager
from .models import Base, FileGroup, FileVersion, FileTag, THUMB_DIR, THUMB_SIZE_SMALL, THUMB_SIZE_MEDIUM, THUMB_SUFFIX
from .storage import ContentAddressableStorage

__all__ = [
    'FileManager',
    'FileGroup',
    'FileVersion',
    'FileTag',
    'ContentAddressableStorage',
    'Base',
    'THUMB_DIR',
    'THUMB_SIZE_SMALL',
    'THUMB_SIZE_MEDIUM',
    'THUMB_SUFFIX'
]
