"""
Application Context - Centralized dependency container for the ParalaX framework.

This module replaces scattered global state with a single, testable container.
All framework components are accessible through the AppContext singleton.

Usage:
    from src.modules.app_context import app_context
    
    # Access components
    auth = app_context.auth_manager
    settings = app_context.settings_manager
    threads = app_context.thread_manager
    
    # In tests, you can reset or mock:
    app_context.reset()
    app_context.auth_manager = MockAuthManager()
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, Any, Dict

if TYPE_CHECKING:
    from .auth.auth_manager import AuthManager
    from .settings.manager import SettingsManager
    from .threaded.threaded_manager import Threaded_manager
    from .scheduler.scheduler import Scheduler
    from .socketio_manager import SocketIOManager
    from .site_conf import Site_conf
    from .tooltip_manager.manager import TooltipManager
    from .help_manager import HelpManager
    from flask_socketio import SocketIO


@dataclass
class AppContext:
    """
    Centralized container for all framework components.
    
    Replaces module-level globals with a single, injectable context.
    This makes testing easier and dependencies explicit.
    
    Attributes:
        auth_manager: Authentication and authorization manager
        settings_manager: Configuration settings manager
        thread_manager: Background thread manager
        scheduler: Real-time scheduler instance
        scheduler_lt: Long-term scheduler instance
        socketio: Flask-SocketIO instance
        socketio_manager: Multi-user SocketIO room manager
        site_conf: Site configuration instance
        app_path: Base path for the application
        is_initialized: Whether the context has been fully initialized
    """
    
    # Core managers - None until initialized
    auth_manager: Optional["AuthManager"] = None
    settings_manager: Optional["SettingsManager"] = None
    thread_manager: Optional["Threaded_manager"] = None
    scheduler: Optional["Scheduler"] = None
    scheduler_lt: Optional["Scheduler"] = None
    socketio: Optional["SocketIO"] = None
    socketio_manager: Optional["SocketIOManager"] = None
    site_conf: Optional["Site_conf"] = None
    tooltip_manager: Optional["TooltipManager"] = None
    help_manager: Optional["HelpManager"] = None
    
    # Plugin instances (for accessing assets, etc.)
    plugins: Dict[str, Any] = field(default_factory=dict)
    
    # Paths
    app_path: Optional[str] = None
    framework_path: Optional[str] = None
    
    # State
    is_initialized: bool = False
    
    # Feature flags cache (derived from site_conf)
    _feature_flags: dict = field(default_factory=dict)
    
    def reset(self) -> None:
        """
        Reset all components to None.
        
        Useful for testing to ensure clean state between tests.
        """
        self.auth_manager = None
        self.settings_manager = None
        self.thread_manager = None
        self.scheduler = None
        self.scheduler_lt = None
        self.socketio = None
        self.socketio_manager = None
        self.site_conf = None
        self.tooltip_manager = None
        self.plugins.clear()
        self.app_path = None
        self.framework_path = None
        self.is_initialized = False
        self._feature_flags.clear()
    
    def is_feature_enabled(self, feature: str) -> bool:
        """
        Check if a feature is enabled.
        
        Args:
            feature: Feature name (e.g., 'authentication', 'threads', 'scheduler')
            
        Returns:
            True if the feature is enabled
        """
        if self.site_conf is None:
            return False
        
        # Cache feature flags for performance
        if feature not in self._feature_flags:
            attr_name = f"m_enable_{feature}"
            self._feature_flags[feature] = getattr(self.site_conf, attr_name, False)
        
        return self._feature_flags[feature]
    
    def require_auth(self) -> "AuthManager":
        """
        Get auth_manager or raise if not available.
        
        Returns:
            AuthManager instance
            
        Raises:
            RuntimeError: If auth is not enabled or not initialized
        """
        if self.auth_manager is None:
            raise RuntimeError(
                "Authentication is not enabled. "
                "Call site_conf.enable_authentication() before setup_app()."
            )
        return self.auth_manager
    
    def require_threads(self) -> "Threaded_manager":
        """
        Get thread_manager or raise if not available.
        
        Returns:
            Threaded_manager instance
            
        Raises:
            RuntimeError: If threads are not enabled or not initialized
        """
        if self.thread_manager is None:
            raise RuntimeError(
                "Thread manager is not enabled. "
                "Call site_conf.enable_threads() before setup_app()."
            )
        return self.thread_manager
    
    def require_settings(self) -> "SettingsManager":
        """
        Get settings_manager or raise if not available.
        
        Returns:
            SettingsManager instance
            
        Raises:
            RuntimeError: If settings manager is not initialized
        """
        if self.settings_manager is None:
            raise RuntimeError(
                "Settings manager is not initialized. "
                "This should not happen - settings are always enabled."
            )
        return self.settings_manager
    
    def get_current_user(self) -> Optional[str]:
        """
        Get the current logged-in user from session.
        
        Returns:
            Username string or None if not logged in
        """
        try:
            from flask import session
            return session.get('user')
        except RuntimeError:
            # No request context
            return None
    
    def has_permission(self, module: str, action: str = 'view') -> bool:
        """
        Check if current user has permission for a module action.
        
        Args:
            module: Module name
            action: Action name (default: 'view')
            
        Returns:
            True if user has permission, or if auth is disabled
        """
        if self.auth_manager is None:
            return True  # Auth disabled = allow all
        
        user = self.get_current_user()
        if not user:
            return False
        
        return self.auth_manager.has_permission(user, module, action)


# Global singleton instance
app_context = AppContext()


def get_context() -> AppContext:
    """
    Get the global application context.
    
    This function exists for explicit dependency injection in tests:
    
        def my_function(ctx: AppContext = None):
            ctx = ctx or get_context()
            # use ctx.auth_manager, ctx.settings_manager, etc.
    
    Returns:
        The global AppContext instance
    """
    return app_context
