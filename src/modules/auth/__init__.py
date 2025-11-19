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
from .permission_registry import PermissionRegistry
from .auth_models import User

__all__ = ['AuthManager', 'PermissionRegistry', 'User', 'auth_manager', 'require_permission', 'require_admin']

# Global auth_manager instance (initialized by main.py when auth is enabled)
auth_manager = None


def require_permission(module: str, action: str = "view"):
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
            current_user = session.get('user')
            if not current_user:
                return redirect(url_for('common.login'))
            
            if not auth_manager.has_permission(current_user, module, action):
                # User is logged in but lacks permission - show access denied
                from src.modules import displayer
                disp = displayer.Displayer()
                disp.add_generic("Access Denied")
                disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
                disp.add_display_item(
                    displayer.DisplayerItemAlert(
                        f"<h4><i class='bi bi-shield-x'></i> Access Denied</h4>"
                        f"<p>You don't have permission to access <strong>{module}</strong> with action <strong>{action}</strong>.</p>"
                        f"<p>Current user: <strong>{current_user}</strong></p>"
                        f"<p>Please contact an administrator to request access.</p>",
                        displayer.BSstyle.ERROR
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
            current_user = session.get('user')
            if not current_user:
                return redirect(url_for('common.login'))
            
            if not auth_manager.is_admin(current_user):
                # User is logged in but not admin - show access denied
                from src.modules import displayer
                disp = displayer.Displayer()
                disp.add_generic("Access Denied")
                disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
                disp.add_display_item(
                    displayer.DisplayerItemAlert(
                        f"<h4><i class='bi bi-shield-x'></i> Admin Access Required</h4>"
                        f"<p>This page requires administrator privileges.</p>"
                        f"<p>Current user: <strong>{current_user}</strong></p>"
                        f"<p>Please contact an administrator if you need access.</p>",
                        displayer.BSstyle.ERROR
                    ),
                    column=0
                )
                return render_template("base_content.j2", content=disp.display())
            
            # Admin access granted
            return f(*args, **kwargs)
        return decorated_function
    return decorator
