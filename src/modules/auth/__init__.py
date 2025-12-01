"""
Authentication and authorization module for ParalaX Web Framework.

This module provides:
- User authentication (password-based and passwordless)
- Permission management (CRUD + custom module actions)
- User preferences storage
- Group management
"""

from functools import wraps

from flask import session, redirect, url_for, render_template

from .auth_manager import AuthManager
from .auth_models import User
from .permission_registry import PermissionRegistry

__all__ = [
    'AuthManager', 'PermissionRegistry', 'User', 'auth_manager',
    'require_permission', 'require_admin', 'require_login'
]

# Constants
DEFAULT_ACTION = "view"
ADMIN_GROUP = "admin"
ROUTE_LOGIN = 'common.login'
SESSION_USER_KEY = 'user'

# Global auth_manager instance (initialized by main.py when auth is enabled)
auth_manager = None


def require_permission(module: str, action: str = DEFAULT_ACTION):
    """
    Decorator that checks permissions if auth is enabled, otherwise allows access.
    
    This is a convenience decorator that automatically handles the case where
    authentication is disabled. When auth is enabled, it delegates to the
    AuthManager's require_permission method.
    
    Args:
        module: Module name (e.g., "FileManager", "Scheduler")
        action: Action name (e.g., "view", "edit", "delete", "upload")
    
    Returns:
        Decorator function
    
    Example:
        ::
        
            from src.modules.auth import require_permission
            
            @demo_bp.route('/file-manager')
            @require_permission("FileManager", "view")
            def file_manager_page():
                return "File Manager Page"
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # If auth is disabled, allow access
            if auth_manager is None:
                return f(*args, **kwargs)
            
            # Auth is enabled - check permission
            current_user = session.get(SESSION_USER_KEY)
            if not current_user:
                return redirect(url_for(ROUTE_LOGIN))
            
            if not auth_manager.has_permission(current_user, module, action):
                # User is logged in but lacks permission - show access denied
                try:
                    from modules.displayer import (
                        Displayer, DisplayerLayout, Layouts, DisplayerItemAlert, BSstyle
                    )
                except ImportError:
                    from submodules.framework.src.modules.displayer import (
                        Displayer, DisplayerLayout, Layouts, DisplayerItemAlert, BSstyle
                    )
                disp = Displayer()
                disp.add_generic("Access Denied")
                disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
                disp.add_display_item(
                    DisplayerItemAlert(
                        f"<p>You don't have permission to access <strong>{module}</strong> "
                        f"with action <strong>{action}</strong>.</p>"
                        f"<p>Current user: <strong>{current_user}</strong></p>"
                        f"<p>Please contact an administrator to request access.</p>",
                        BSstyle.ERROR,
                        title="Access Denied",
                        icon="shield-alert"
                    ),
                    column=0
                )
                return render_template("base_content.j2", content=disp.display())
            
            # Permission granted - allow access
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_admin():
    """
    Decorator that requires admin group membership if auth is enabled.
    
    This is a convenience decorator that automatically handles the case where
    authentication is disabled. When auth is enabled, it checks for admin group.
    
    Returns:
        Decorator function
    
    Example:
        ::
        
            from src.modules.auth import require_admin
            
            @admin_bp.route('/admin-panel')
            @require_admin()
            def admin_panel():
                return "Admin Panel"
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # If auth is disabled, allow access
            if auth_manager is None:
                return f(*args, **kwargs)
            
            # Auth is enabled - check admin group
            current_user = session.get(SESSION_USER_KEY)
            if not current_user:
                return redirect(url_for(ROUTE_LOGIN))
            
            # Check if user is in admin group
            user_obj = auth_manager.get_user(current_user)
            if not user_obj or ADMIN_GROUP not in user_obj.groups:
                # User is logged in but not admin - show access denied
                try:
                    from modules.displayer import (
                        Displayer, DisplayerLayout, Layouts, DisplayerItemAlert, BSstyle
                    )
                except ImportError:
                    from submodules.framework.src.modules.displayer import (
                        Displayer, DisplayerLayout, Layouts, DisplayerItemAlert, BSstyle
                    )
                disp = Displayer()
                disp.add_generic("Access Denied")
                disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
                disp.add_display_item(
                    DisplayerItemAlert(
                        f"<p>This page requires admin privilege.</p>"
                        f"<p>Current user: <strong>{current_user}</strong></p>"
                        f"<p>Please contact an administrator to request access.</p>",
                        BSstyle.ERROR,
                        title="Admin access required",
                        icon="shield-alert"
                    ),
                    column=0
                )
                return render_template("base_content.j2", content=disp.display())
            
            # Admin access granted
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_login():
    """
    Decorator that requires any authenticated user (any group).
    
    This is a convenience decorator that checks if a user is logged in,
    regardless of their permissions or group membership.
    
    Returns:
        Decorator function
    
    Example:
        ::
        
            from src.modules.auth import require_login
            
            @bp.route('/profile')
            @require_login()
            def user_profile():
                return "User Profile Page"
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # If auth is disabled, allow access
            if auth_manager is None:
                return f(*args, **kwargs)
            
            # Auth is enabled - check if user is logged in
            current_user = session.get(SESSION_USER_KEY)
            if not current_user:
                return redirect(url_for(ROUTE_LOGIN))
            
            # User is logged in - allow access
            return f(*args, **kwargs)
        return decorated_function
    return decorator
