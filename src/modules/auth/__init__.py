"""
Authentication and authorization module for ParalaX Web Framework.

This module provides:
- User authentication (password-based and passwordless)
- Permission management (CRUD + custom module actions)
- User preferences storage
- Group management
"""

from .auth_manager import AuthManager
from .permission_registry import PermissionRegistry
from .auth_models import User

__all__ = ['AuthManager', 'PermissionRegistry', 'User']
