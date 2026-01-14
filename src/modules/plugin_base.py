"""
Plugin Base - Abstract base class for ParalaX framework plugins.

Plugins allow extending the framework with additional functionality
that can be enabled per-site via site_conf.enable_plugin().

Usage:
    from src.modules.plugin_base import PluginBase
    
    class MyPlugin(PluginBase):
        name = "my_plugin"
        
        def validate_dependencies(self, site_conf):
            if not site_conf.m_enable_authentication:
                raise RuntimeError("MyPlugin requires authentication")
        
        def on_register(self, app, app_context, plugin_config):
            # Register blueprints, sidebar items, etc.
            pass
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from flask import Flask, Blueprint
    from .app_context import AppContext
    from .site_conf import Site_conf


class PluginBase(ABC):
    """
    Abstract base class for framework plugins.
    
    Plugins are discovered from the submodules folder and enabled
    via site_conf.enable_plugin(name). They can:
    - Register Flask blueprints
    - Add sidebar/topbar items
    - Initialize services
    - Provide templates and static assets
    
    Attributes:
        name: Unique plugin identifier (e.g., "tracker")
    """
    
    name: str = ""
    """Unique plugin identifier, must match the submodule folder name."""
    
    @abstractmethod
    def validate_dependencies(self, site_conf: "Site_conf") -> None:
        """
        Validate that required framework features are enabled.
        
        Called before on_register(). Should raise RuntimeError with a
        descriptive message if dependencies are not met.
        
        Args:
            site_conf: The site configuration instance
            
        Raises:
            RuntimeError: If required features are not enabled
        """
        pass
    
    @abstractmethod
    def on_register(
        self, 
        app: "Flask", 
        app_context: "AppContext", 
        plugin_config: Dict[str, Any]
    ) -> None:
        """
        Register the plugin with the Flask application.
        
        Called during setup_app() for each enabled plugin. This method should:
        - Register all Flask blueprints
        - Add sidebar items via site_conf
        - Initialize any plugin-specific services
        - Configure database connections if needed
        
        Args:
            app: The Flask application instance
            app_context: The framework's app context (for accessing managers)
            plugin_config: Plugin-specific configuration from config.json
        """
        pass
    
    def get_blueprints(self) -> List["Blueprint"]:
        """
        Return list of Flask blueprints to register.
        
        Override this if you want to expose blueprints separately from
        on_register(). Default implementation returns empty list.
        
        Returns:
            List of Flask Blueprint instances
        """
        return []
    
    def get_templates_path(self) -> Optional[str]:
        """
        Return absolute path to plugin templates directory.
        
        Override if the plugin provides custom Jinja2 templates.
        
        Returns:
            Absolute path to templates directory, or None
        """
        return None
    
    def get_assets_path(self) -> Optional[str]:
        """
        Return absolute path to plugin static assets directory.
        
        Override if the plugin provides custom CSS/JS/images.
        
        Returns:
            Absolute path to assets directory, or None
        """
        return None
    
    def build_sidebar(self, site_conf: "Site_conf") -> None:
        """
        Add plugin items to the sidebar.
        
        Called after on_register() if the plugin is enabled.
        Override to add navigation items.
        
        Args:
            site_conf: The site configuration instance
        """
        pass
