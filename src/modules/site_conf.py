"""Module for site configuration and UI customization.

Provides the Site_conf class for managing application settings, sidebar navigation,
topbar UI, and feature flags for the ParalaX framework.
"""
import logging
import os
from typing import Optional

from . import scheduler

from .log.logger_factory import get_logger

from .i18n.messages import (
    TEXT_SECTION_SYSTEM,
    TEXT_SECTION_USER_MANAGEMENT,
    TEXT_SECTION_ACCOUNT,
    TEXT_SECTION_ADMIN,
    TEXT_SECTION_MONITORING,
    TEXT_SECTION_TOOLS,
    TEXT_SECTION_DEPLOYMENT,
    TEXT_MY_PROFILE_SIDEBAR,
    TEXT_FRAMEWORK_PREFERENCES,
    TEXT_USERS,
    TEXT_PERMISSIONS,
    TEXT_GROUPS_SIDEBAR,
    TEXT_THREAD_MONITOR_SIDEBAR,
    TEXT_LOG_VIEWER_SIDEBAR,
    TEXT_BUG_TRACKER_SIDEBAR,
    TEXT_SETTINGS_SIDEBAR,
    TEXT_UPDATER_SIDEBAR,
    TEXT_PACKAGER_SIDEBAR,
    TEXT_FILE_MANAGER_SIDEBAR,
    TEXT_TOOLTIP_MANAGER_SIDEBAR,
    TEXT_DEFAULT_INDEX_MESSAGE,
)

logger = get_logger("site_conf")

# Module-level globals for application configuration
site_conf_obj: Optional["Site_conf"] = None
site_conf_app_path: Optional[str] = None

# Sidebar endpoints (technical identifiers - domain-specific)
ENDPOINT_USER = "user"
ENDPOINT_ADMIN = "admin"
ENDPOINT_MONITORING = "monitoring"
ENDPOINT_TOOLS = "tools"
ENDPOINT_DEPLOYMENT = "deployment"

# Sidebar attribute keys (technical identifiers - domain-specific)
ATTR_NAME = "name"
ATTR_ENDPOINT = "endpoint"
ATTR_IS_TITLE = "isTitle"
ATTR_SUBMENU = "submenu"
ATTR_ICON = "icon"

# Icons (MDI format - domain-specific)
ICON_ACCOUNT_CIRCLE = "account-circle"
ICON_SHIELD_LOCK = "shield-lock"
ICON_MONITOR_DASHBOARD = "monitor-dashboard"
ICON_TOOLBOX = "toolbox"
ICON_PACKAGE_VARIANT = "package-variant"
ICON_COG_SYNC = "cog-sync"

# Default values (domain-specific)
DEFAULT_PORT = 5000
DEFAULT_VERSION = "0.0.0.1"
DEFAULT_APP_NAME = "Default"
DEFAULT_ICON = "home"
DEFAULT_FOOTER = "2024 &copy;ESD"
DEFAULT_HOME_ENDPOINT = "framework_index"

class Site_conf:
    """Provides a set of function to configure the website"""
    
    def __init__(self):
        """Initialize site configuration with default values."""
        self.m_globals = {
            "on_target": False,
            "PORT": DEFAULT_PORT,
            "version": DEFAULT_VERSION
        }

        self.m_app = {"name": DEFAULT_APP_NAME, "version": "0", "icon": DEFAULT_ICON, "footer": DEFAULT_FOOTER}
        """App information"""

        self.m_include_tar_gz_dirs = []

        self.m_index = str(TEXT_DEFAULT_INDEX_MESSAGE)
        
        self.m_home_endpoint = DEFAULT_HOME_ENDPOINT
        """Default home page endpoint - can be overridden by website modules"""

        self.m_sidebar = []
        """Sidebar content"""

        self.m_topbar = {"display": False, "left": [], "center": [], "right": [], "login": False}
        """Topbar content"""

        self.m_javascripts = []
        """Custom javascripts"""

        self.m_scheduler_lt_functions = []
        """Functions that can be registered in the long term scheduler. Should be an array of arrays which are [func, period]"""

        self.m_enable_easter_eggs = False
        """Enable easter eggs (Konami code, pixel mode, death screen, etc.)"""
        
        # Feature flags - all disabled by default (opt-in)
        self.m_enable_authentication = False
        """Enable authentication system and login/logout pages"""
        
        self.m_enable_threads = False
        """Enable thread monitoring and background task management"""
        
        self.m_enable_scheduler = False
        """Enable real-time scheduler for SocketIO updates"""
        
        self.m_enable_long_term_scheduler = False
        """Enable long-term scheduler for periodic tasks"""
        
        self.m_enable_log_viewer = False
        """Enable log viewing page"""
        
        self.m_enable_admin_panel = False
        """Enable admin panel page"""
        
        self.m_enable_bug_tracker = False
        """Enable bug tracker page"""
        
        self.m_enable_settings = False
        """Enable settings page"""
        
        self.m_enable_updater = False
        """Enable updater page"""
        
        self.m_enable_packager = False
        """Enable packager page"""
        
        self.m_enable_file_manager = False
        """Enable file manager system"""
        
        self.m_file_manager_admin = False
        """Enable file manager admin interface"""
        
        self.m_enable_tooltip_manager = False
        """Enable tooltip manager system"""
        
        self.m_enable_help = False
        """Enable help system with markdown documentation"""
        
        # Plugin system
        self.m_enabled_plugins: list[str] = []
        """List of enabled plugin names (e.g., ['tracker'])"""

    def enable_plugin(self, name: str) -> None:
        """Enable a plugin by name.
        
        Plugins are loaded from submodules/{name}/web/ and must implement PluginBase.
        The plugin will be registered during setup_app().
        
        :param name: Plugin name (must match submodule folder name)
        :type name: str
        
        Example:
            self.enable_plugin("tracker")  # Loads from submodules/tracker/web/
        """
        if name not in self.m_enabled_plugins:
            self.m_enabled_plugins.append(name)
            logger.debug("Plugin '%s' enabled", name)

    def _ensure_system_title(self):
        """Helper to ensure 'System' title exists in sidebar."""
        has_system_title = any(
            item.get(ATTR_NAME) == str(TEXT_SECTION_SYSTEM) and item.get(ATTR_IS_TITLE) 
            for item in self.m_sidebar
        )
        
        if not has_system_title:
            self.add_sidebar_title(str(TEXT_SECTION_SYSTEM))

    def enable_authentication(self, add_to_sidebar: bool = True):
        """Enable authentication system and automatically add login/logout functionality.
        
        :param add_to_sidebar: If True, adds user management section to sidebar, defaults to True
        :type add_to_sidebar: bool, optional
        """
        self.m_enable_authentication = True
        self.use_login()  # Set topbar login flag
        
        if add_to_sidebar:
            # Add User Management section
            self.add_sidebar_title(str(TEXT_SECTION_USER_MANAGEMENT))
            self.add_sidebar_section(str(TEXT_SECTION_ACCOUNT), ICON_ACCOUNT_CIRCLE, ENDPOINT_USER)
            self.add_sidebar_submenu(str(TEXT_MY_PROFILE_SIDEBAR), "user_profile.profile", endpoint=ENDPOINT_USER)
            self.add_sidebar_submenu(str(TEXT_FRAMEWORK_PREFERENCES), "user_profile.framework_preferences", endpoint=ENDPOINT_USER)
            
            # Add Admin section
            self.add_sidebar_section(str(TEXT_SECTION_ADMIN), ICON_SHIELD_LOCK, ENDPOINT_ADMIN)
            self.add_sidebar_submenu(str(TEXT_USERS), "admin_auth.manage_users", endpoint=ENDPOINT_ADMIN)
            self.add_sidebar_submenu(str(TEXT_PERMISSIONS), "admin_auth.manage_permissions", endpoint=ENDPOINT_ADMIN)
            self.add_sidebar_submenu(str(TEXT_GROUPS_SIDEBAR), "admin_auth.manage_groups", endpoint=ENDPOINT_ADMIN)
    
    def enable_threads(self, add_to_sidebar: bool = True, add_to_topbar: Optional[bool] = None, topbar_icon: Optional[str] = None, topbar_area: Optional[str] = None):
        """Enable thread monitoring and background task management.
        
        Settings can be configured globally in config.json under framework_ui category.
        Users can override these settings in their preferences.
        
        :param add_to_sidebar: If True, adds threads page to sidebar, defaults to True
        :type add_to_sidebar: bool, optional
        :param add_to_topbar: If True, adds thread status indicator to topbar, defaults to reading from settings
        :type add_to_topbar: bool, optional
        :param topbar_icon: Icon for the thread status indicator in topbar, defaults to reading from settings
        :type topbar_icon: str, optional
        :param topbar_area: Area of topbar for thread status ("left", "center", "right"), defaults to reading from settings
        :type topbar_area: str, optional
        """
        self.m_enable_threads = True
        if add_to_sidebar:
            self._ensure_system_title()
            # Check if Monitoring section exists, create if not
            has_monitoring = any(
                item.get(ATTR_ENDPOINT) == ENDPOINT_MONITORING for item in self.m_sidebar
            )
            if not has_monitoring:
                self.add_sidebar_section(str(TEXT_SECTION_MONITORING), ICON_MONITOR_DASHBOARD, ENDPOINT_MONITORING)
            self.add_sidebar_submenu(str(TEXT_THREAD_MONITOR_SIDEBAR), "threads.threads", endpoint=ENDPOINT_MONITORING)
        
        # Read from settings if parameters not explicitly provided
        if add_to_topbar is None:
            add_to_topbar = self._get_framework_setting("thread_status_enabled", True)
        
        if add_to_topbar:
            # Get settings with defaults
            final_icon: str = topbar_icon if topbar_icon is not None else str(self._get_framework_setting("thread_status_icon", ICON_COG_SYNC))
            final_area: str = topbar_area if topbar_area is not None else str(self._get_framework_setting("thread_status_position", "right"))
            
            self.add_topbar_thread_info(final_icon, final_area)
    
    def enable_scheduler(self):
        """Enable real-time scheduler for SocketIO updates."""
        self.m_enable_scheduler = True
    
    def enable_long_term_scheduler(self):
        """Enable long-term scheduler for periodic tasks."""
        self.m_enable_long_term_scheduler = True
    
    def enable_log_viewer(self, add_to_sidebar: bool = True):
        """Enable log viewing page.
        
        :param add_to_sidebar: If True, adds logs page to sidebar, defaults to True
        :type add_to_sidebar: bool, optional
        """
        self.m_enable_log_viewer = True
        if add_to_sidebar:
            self._ensure_system_title()
            # Check if Tools section exists, create if not
            has_tools = any(
                item.get(ATTR_ENDPOINT) == ENDPOINT_TOOLS for item in self.m_sidebar
            )
            if not has_tools:
                self.add_sidebar_section(str(TEXT_SECTION_TOOLS), ICON_TOOLBOX, ENDPOINT_TOOLS)
            self.add_sidebar_submenu(str(TEXT_LOG_VIEWER_SIDEBAR), "logging.logs", endpoint=ENDPOINT_TOOLS)
            self.add_sidebar_submenu("Logger Configuration", "logging.config", endpoint=ENDPOINT_TOOLS)
    
    def enable_bug_tracker(self, add_to_sidebar: bool = True):
        """Enable bug tracker page.
        
        :param add_to_sidebar: If True, adds bug tracker to sidebar, defaults to True
        :type add_to_sidebar: bool, optional
        """
        self.m_enable_bug_tracker = True
        if add_to_sidebar:
            self._ensure_system_title()
            # Check if Tools section exists, create if not
            has_tools = any(
                item.get(ATTR_ENDPOINT) == ENDPOINT_TOOLS for item in self.m_sidebar
            )
            if not has_tools:
                self.add_sidebar_section(str(TEXT_SECTION_TOOLS), ICON_TOOLBOX, ENDPOINT_TOOLS)
            self.add_sidebar_submenu(str(TEXT_BUG_TRACKER_SIDEBAR), "bug.bugtracker", endpoint=ENDPOINT_TOOLS)
    
    def enable_settings(self, add_to_sidebar: bool = True):
        """Enable settings page.
        
        :param add_to_sidebar: If True, adds settings to sidebar, defaults to True
        :type add_to_sidebar: bool, optional
        """
        self.m_enable_settings = True
        if add_to_sidebar:
            self._ensure_system_title()
            # Check if Tools section exists, create if not
            has_tools = any(
                item.get(ATTR_ENDPOINT) == ENDPOINT_TOOLS for item in self.m_sidebar
            )
            if not has_tools:
                self.add_sidebar_section(str(TEXT_SECTION_TOOLS), ICON_TOOLBOX, ENDPOINT_TOOLS)
            self.add_sidebar_submenu(str(TEXT_SETTINGS_SIDEBAR), "settings.index", endpoint=ENDPOINT_TOOLS)
    
    def enable_updater(self, add_to_sidebar: bool = True):
        """Enable updater page.
        
        :param add_to_sidebar: If True, adds updater to sidebar, defaults to True
        :type add_to_sidebar: bool, optional
        """
        self.m_enable_updater = True
        if add_to_sidebar:
            self._ensure_system_title()
            # Check if Deployment section exists, create if not
            has_deployment = any(
                item.get(ATTR_ENDPOINT) == ENDPOINT_DEPLOYMENT for item in self.m_sidebar
            )
            if not has_deployment:
                self.add_sidebar_section(str(TEXT_SECTION_DEPLOYMENT), ICON_PACKAGE_VARIANT, ENDPOINT_DEPLOYMENT)
            self.add_sidebar_submenu(str(TEXT_UPDATER_SIDEBAR), "updater.update", endpoint=ENDPOINT_DEPLOYMENT)
    
    def enable_packager(self, add_to_sidebar: bool = True):
        """Enable packager page.
        
        :param add_to_sidebar: If True, adds packager to sidebar, defaults to True
        :type add_to_sidebar: bool, optional
        """
        self.m_enable_packager = True
        if add_to_sidebar:
            self._ensure_system_title()
            # Check if Deployment section exists, create if not
            has_deployment = any(
                item.get(ATTR_ENDPOINT) == ENDPOINT_DEPLOYMENT for item in self.m_sidebar
            )
            if not has_deployment:
                self.add_sidebar_section(str(TEXT_SECTION_DEPLOYMENT), ICON_PACKAGE_VARIANT, ENDPOINT_DEPLOYMENT)
            self.add_sidebar_submenu(str(TEXT_PACKAGER_SIDEBAR), "packager.packager", endpoint=ENDPOINT_DEPLOYMENT)
    
    def enable_file_manager(self, add_to_sidebar: bool = False, enable_admin_page: bool = True):
        """Enable file upload/download management system.
        
        :param add_to_sidebar: If True, adds file manager admin page to sidebar, defaults to False
        :type add_to_sidebar: bool, optional
        :param enable_admin_page: If True, creates admin interface for file browsing (requires auth), defaults to True
        :type enable_admin_page: bool, optional
        """
        self.m_enable_file_manager = True
        self.m_file_manager_admin = enable_admin_page
        
        if add_to_sidebar and enable_admin_page:
            self._ensure_system_title()
            # Check if Tools section exists, create if not
            has_tools = any(
                item.get(ATTR_ENDPOINT) == ENDPOINT_TOOLS for item in self.m_sidebar
            )
            if not has_tools:
                self.add_sidebar_section(str(TEXT_SECTION_TOOLS), ICON_TOOLBOX, ENDPOINT_TOOLS)
            self.add_sidebar_submenu(str(TEXT_FILE_MANAGER_SIDEBAR), "file_manager_admin.index", endpoint=ENDPOINT_TOOLS)
    
    def enable_tooltip_manager(self, add_to_sidebar: bool = True):
        """Enable tooltip manager system.
        
        :param add_to_sidebar: If True, adds tooltip manager to sidebar under System Tools, defaults to True
        :type add_to_sidebar: bool, optional
        """
        self.m_enable_tooltip_manager = True
        if add_to_sidebar:
            self._ensure_system_title()
            # Check if Tools section exists, create if not
            has_tools = any(
                item.get(ATTR_ENDPOINT) == ENDPOINT_TOOLS for item in self.m_sidebar
            )
            if not has_tools:
                self.add_sidebar_section(str(TEXT_SECTION_TOOLS), ICON_TOOLBOX, ENDPOINT_TOOLS)
            self.add_sidebar_submenu(str(TEXT_TOOLTIP_MANAGER_SIDEBAR), "framework_tooltips.index", endpoint=ENDPOINT_TOOLS)
    
    def enable_help(self, add_to_sidebar: bool = True, add_admin_to_sidebar: bool = True):
        """Enable the help system.
        
        The help system provides:
        - Public help pages rendered from markdown files in website/help/
        - Plugin-contributed help content
        - Admin interface to enable/disable help sections
        
        :param add_to_sidebar: If True, adds Help link to sidebar under Tools, defaults to True
        :type add_to_sidebar: bool, optional
        :param add_admin_to_sidebar: If True, adds Help Config link to admin sidebar, defaults to True  
        :type add_admin_to_sidebar: bool, optional
        """
        self.m_enable_help = True
        
        if add_to_sidebar:
            self._ensure_system_title()
            # Check if Tools section exists, create if not
            has_tools = any(
                item.get(ATTR_ENDPOINT) == ENDPOINT_TOOLS for item in self.m_sidebar
            )
            if not has_tools:
                self.add_sidebar_section(str(TEXT_SECTION_TOOLS), ICON_TOOLBOX, ENDPOINT_TOOLS)
            self.add_sidebar_submenu("Help Center", "help.index", endpoint=ENDPOINT_TOOLS)
        
        if add_admin_to_sidebar and self.m_enable_authentication:
            # Add help admin to Admin section
            self.add_sidebar_submenu("Help Configuration", "help.admin", endpoint=ENDPOINT_ADMIN)
    
    def enable_all_features(self, add_to_sidebar: bool = True, add_to_topbar: bool = True):
        """Enable all framework features (useful for demos and testing).
        
        :param add_to_sidebar: If True, adds all pages to sidebar, defaults to True
        :type add_to_sidebar: bool, optional
        :param add_to_topbar: If True, adds topbar elements where applicable (e.g., thread status), defaults to True
        :type add_to_topbar: bool, optional
        """
        # Enable features - authentication adds its own section
        self.enable_authentication(add_to_sidebar)
        
        # Enable framework system features
        self.enable_scheduler()
        self.enable_long_term_scheduler()
        self.enable_threads(add_to_sidebar, add_to_topbar=add_to_topbar)
        self.enable_log_viewer(add_to_sidebar)
        self.enable_bug_tracker(add_to_sidebar)
        self.enable_settings(add_to_sidebar)
        self.enable_updater(add_to_sidebar)
        self.enable_packager(add_to_sidebar)
        self.enable_help(add_to_sidebar)

    
    def configure_easter_eggs(self) -> bool:
        """Configure whether easter eggs are enabled. Can be overridden by child classes.
        
        :return: True to enable easter eggs, False to disable
        :rtype: bool
        """
        return self.m_enable_easter_eggs
    
    def register_scheduler_lt_functions(self):
        """
        Register all the functions that are set in the m_scheduler_lt_functions, which must be populated by the child class
        """
        from .app_context import app_context
        if app_context.scheduler_lt:
            for func in self.m_scheduler_lt_functions:
                app_context.scheduler_lt.register_function(func[0], func[1])

    def add_sidebar_title(self, title: str):
        """Add a sidebar title, which can logically seperate several parts of the sidebar

        :param title: The title to add
        :type title: str
        """
        # Check if not already there
        if any(item.get(ATTR_NAME) == title for item in self.m_sidebar):
            return

        self.m_sidebar.append({ATTR_NAME: title, ATTR_IS_TITLE: True})

    def add_sidebar_section(self, section: str, icon: str, endpoint: str):
        """Add a section to the sidebar. Sections are not clickable and are meant to host a submenu

        :param section: The section
        :type section: str
        :param icon: The section icon, from the mdi icon pack.
        :type icon: str
        :param endpoint: The endpoint address of the section.
        :type endpoint: str
        """
        if any(item.get(ATTR_NAME) == section for item in self.m_sidebar):
            return

        self.m_sidebar.append(
            {
                ATTR_NAME: section,
                ATTR_ENDPOINT: endpoint,
                ATTR_ICON: "mdi-" + icon,
                "cat": "",
                ATTR_SUBMENU: [],
            }
        )

    def add_sidebar_page(self, name: str, icon: str, url: str):
        """Add a page to the sidebar

        :param name: The name of the page
        :type name: str
        :param icon: The page icon, from the mdi icon pack.
        :type icon: str
        :param url: The url of the page
        :type url: str
        """
        if any(item.get(ATTR_NAME) == name for item in self.m_sidebar):
            return

        self.m_sidebar.append(
            {
                ATTR_NAME: name,
                ATTR_ENDPOINT: url,
                "url": url,
                ATTR_ICON: "mdi-" + icon,
                "cat": "",
            }
        )

    def add_sidebar_subsubmenu(self, name: str, url: str, submenu: str, parameter: Optional[str] = None, endpoint: Optional[str] = None):
        """
        Add a sub-sub-menu item to the sidebar navigation.
        
        Args:
            name: Display name of the menu item
            url: URL or route for the menu item
            submenu: Parent submenu name
            parameter: Optional parameter to pass to the route
            endpoint: Optional endpoint name (defaults to first part of url)
        """
        url_endpoint = url.split(".")[0]
        if not endpoint:
            endpoint = url_endpoint
        for i in range(0, len(self.m_sidebar)):
            if "submenu" in self.m_sidebar[i]:
                if "subsubmenu" in self.m_sidebar[i]["submenu"]:
                    for j in range(0, len(self.m_sidebar[i]["submenu"]["subsubmenu"])):
                        if self.m_sidebar[i]["submenu"][submenu]["subsubmenu"][j]["name"] == name:
                            return

            if (
                "endpoint" in self.m_sidebar[i]
                and self.m_sidebar[i]["endpoint"] == endpoint
            ):
                for j in range(0, len(self.m_sidebar[i]["submenu"])):
                    if self.m_sidebar[i]["submenu"][j]["name"] == submenu:
                        if "subsubmenu" not in self.m_sidebar[i]["submenu"][j]:
                            self.m_sidebar[i]["submenu"][j]["subsubmenu"] = []

                        self.m_sidebar[i]["submenu"][j]["subsubmenu"].append(
                            {"name": name, "url": url, "cat": ""}
                        )

                        if parameter:
                            self.m_sidebar[i]["submenu"][j]["subsubmenu"][-1]["param"] = parameter

    def add_sidebar_submenu(
        self, name: str, url: str, parameter: Optional[str] = None, endpoint: Optional[str] = None
    ):
        """Add a submenu to the sidebar. It uses the url in order to extract the section. The url must be in the form endpoint.page

        :param name: The name of the submenu
        :type name: str
        :param url: The url of the submenu
        :type url: str
        :param parameter: Optional parameters for the page, that is the part of the GET url (e.g: topic=help), defaults to None
        :type parameter: str, optional
        :param endpoint: Optional endpoint override, instead of using the one in the url., defaults to None
        :type endpoint: str, optional
        """
        url_endpoint = url.split(".")[0]
        if not endpoint:
            endpoint = url_endpoint
        
        # Find the section by endpoint
        section = next(
            (item for item in self.m_sidebar 
             if ATTR_ENDPOINT in item and item[ATTR_ENDPOINT] == endpoint),
            None
        )
        
        if not section:
            return
        
        # Check if submenu already exists
        if ATTR_SUBMENU in section:
            if any(item.get(ATTR_NAME) == name and item.get("url") == url 
                   for item in section[ATTR_SUBMENU]):
                return
        
        section[ATTR_SUBMENU].append(
            {ATTR_NAME: name, "url": url, "cat": ""}
        )

        if parameter:
            section[ATTR_SUBMENU][-1]["param"] = parameter

    def add_topbar_textfield(self, id: str, icon: str, text: str, area: str, link: Optional[str] = None, color: str = "primary"
    ):
        """Add a new button to the topbar

        :param id: The id (of the div) of the button
        :type id: str
        :param icon: The icon, from the mdi library
        :type icon: str
        :param text: The text of the button
        :type text: str
        :param area: The area of the topbar where the button lives (left, center or right)
        :type area: str
        :param link: Optional link where the button will point, defaults to None
        :type link: str, optional
        """
        self.m_topbar["display"] = True
        if area in self.m_topbar:
            if any(item["id"] == id for item in self.m_topbar[area]):
                return

            self.m_topbar[area].append(
                {
                    "type": "field",
                    "icon": icon,
                    "text": text,
                    "id": id,
                    "color": color,
                    "link": link,
                }
            )

    def add_topbar_button(
        self, id: str, icon: str, text: str, area: str, link: Optional[str] = None
    ):
        """Add a new button to the topbar

        :param id: The id (of the div) of the button
        :type id: str
        :param icon: The icon, from the mdi library
        :type icon: str
        :param text: The text of the button
        :type text: str
        :param area: The area of the topbar where the button lives (left, center or right)
        :type area: str
        :param link: Optional link where the button will point, defaults to None
        :type link: str, optional
        """
        self.m_topbar["display"] = True
        if area in self.m_topbar:
            if any(item["id"] == id for item in self.m_topbar[area]):
                return

            self.m_topbar[area].append(
                {
                    "type": "button",
                    "icon": icon,
                    "text": text,
                    "id": id,
                    "color": "secondary",
                    "link": link,
                }
            )

    def add_topbar_thread_info(self, icon: str, area: str):
        """Add a zone where the thread are displayed. It can be skinned with an icon

        :param icon: The skin icon, mdi format
        :type icon: str
        :param area: The zone (center, left, right) where the status lives in the topbar
        :type area: str
        """
        self.m_topbar["display"] = True
        if area in self.m_topbar:
            if any(item["id"] == "thread" for item in self.m_topbar[area]):
                return

            self.m_topbar[area].append(
                {"type": "thread", "icon": icon, "color": "secondary", "id": "thread"}
            )

    def add_topbar_modal(
        self,
        id: str,
        icon: str,
        text: str,
        area: str,
        modal_text: str,
        modal_title: str,
        modal_footer: str,
        color: str,
    ):
        """Add a new button to the topbar that will display a modal information.

        Modal text content can be modified later on with the scheduler, or with the *update_topbar_modal* function

        :param id: The id (of the div) of the button
        :type id: str
        :param icon: The icon, from the mdi library
        :type icon: str
        :param text: The text of the button
        :type text: str
        :param area: The area of the topbar where the button lives (left, center or right)
        :type area: str
        :param modal_text: The content of the modal
        :type modal_text: str
        :param modal_title: _description_
        :type modal_title: str
        :param modal_footer: The title of the modal
        :type modal_footer: str
        :param color:  The footer of the modal
        :type color: str
        """

        self.m_topbar["display"] = True
        if area in self.m_topbar:
            if any(item["id"] == id for item in self.m_topbar[area]):
                return

            self.m_topbar[area].append(
                {
                    "type": "modal",
                    "icon": icon,
                    "text": text,
                    "id": id,
                    "modal_text": modal_text,
                    "modal_title": modal_title,
                    "modal_footer": modal_footer,
                    "color": color,
                }
            )

    def update_topbar_button(
        self,
        id: str,
        icon: str,
        text: str,
        area: str,
        color: str = "secondary",
        link: Optional[str] = None,
    ):
        """Update a new button to the topbar, works also for modals

        :param id: The id (of the div) of the button
        :type id: str
        :param icon: The icon, from the mdi library
        :type icon: str
        :param text: The text of the button
        :type text: str
        :param area: The area of the topbar where the button lives (left, center or right)
        :type area: str
        :param color: The color of the button, defaults to "secondary"
        :type color: str, optional
        :param link: Optionnal link, href on the button, defaults to None
        :type link: str, optional
        """

        self.m_topbar["display"] = True
        if area in self.m_topbar:
            item = next((item for item in self.m_topbar[area] if item["id"] == id), None)
            if item:
                item["icon"] = icon
                item["text"] = text
                item["color"] = color
                item["link"] = link

    def update_topbar_modal(self, id: str, text: str, area: str):
        """Update the content text of a modal

        :param id: The id (of the div) of the button
        :type id: str
        :param text: The text of the button
        :type text: str
        :param area: The area of the topbar where the button lives (left, center or right)
        :type area: str
        """
        self.m_topbar["display"] = True
        if area in self.m_topbar:
            item = next((item for item in self.m_topbar[area] if item["id"] == id), None)
            if item:
                item["modal_text"] = text

    def add_javascript(self, script: str):
        """Add a new script to load on the page

        :param script: A string with the path to the string, from assets/js
        :type script: str
        """
        self.m_javascripts.append(script)

    def use_login(self):
        """Indicate that this website uses login"""
        self.m_topbar["login"] = True
        # Login functionality is now always available through auth_manager
        return
    
    def _get_framework_setting(self, key: str, default=None, username: Optional[str] = None):
        """
        Get a framework setting with user override support.
        
        Resolution order:
        1. User override (if username provided and override exists)
        2. Global config.json setting
        3. Provided default value
        
        :param key: Setting key (e.g., "thread_status_position")
        :type key: str
        :param default: Default value if not found
        :param username: Username to check for overrides (optional)
        :return: Setting value
        """
        try:
            # Try to get user override first
            if username:
                try:
                    from .app_context import app_context
                    if app_context.auth_manager:
                        override = app_context.auth_manager.get_user_framework_override(
                            username, f"framework_ui.{key}"
                        )
                        if override is not None:
                            return override
                except Exception:
                    pass  # Fall through to global setting
            
            # Try to get from global settings
            try:
                from .settings import SettingsManager
                
                # Use the app path set by the framework
                if site_conf_app_path:
                    config_path = os.path.join(site_conf_app_path, "website", "config.json")
                else:
                    config_path = os.path.join(os.getcwd(), "website", "config.json")
                
                manager = SettingsManager(config_path)
                manager.load()
                value = manager.get_setting(f"framework_ui.{key}")
                if value is not None:
                    return value
            except Exception:
                pass  # Fall through to default
            
        except Exception:
            pass
        
        return default

    def app_details(self, name: str, version: str, icon: str, footer: Optional[str] = None, index: Optional[str] = None, home_endpoint: Optional[str] = None):
        """Set the application details

        :param name: The name of the application
        :type name: str
        :param version: The version of the application
        :type version: str
        :param icon: The icon of the application, in mdi format
        :type icon: str
        :param footer: Optional footer text
        :type footer: str, optional
        :param index: Optional index page content
        :type index: str, optional
        :param home_endpoint: Optional home endpoint (e.g., 'my_module.home') to override the default
        :type home_endpoint: str, optional
        """
        self.m_app["name"] = name
        self.m_app["icon"] = icon
        self.m_app["version"] = version
        if footer:
            self.m_app["footer"] = footer

        if index:
            self.m_index = index
        
        if home_endpoint:
            self.m_home_endpoint = home_endpoint

    def add_tar_gz(self, list_tar_gz: list):
        """
        Add directories to include in tar.gz distribution.
        
        Args:
            list_tar_gz: List of directory paths to include
        """
        if self.m_app["name"] == "OuFNis_DFDIG":
            self.m_include_tar_gz_dirs = list_tar_gz

    def context_processor(self):
        """
        Function that is called before rendering any page.
        
        Should be overwritten by the child object to provide custom context variables.
        
        Returns:
            Dictionary of context variables to inject into templates
        """
        return {
            "enable_easter_eggs": self.configure_easter_eggs(),
            "enable_bug_tracker": self.m_enable_bug_tracker
        }

    def socketio_event(self, event, data):
        """
        Function called to respond to SocketIO events.
        
        Should be overwritten by the child object to handle custom events.
        
        Args:
            event: Event name
            data: Event data payload
        """
        return

    def create_distribuate(self):
        """
        Function to create the distributable package on this platform.
        
        Should be overwritten by the child object to implement distribution logic.
        
        Returns:
            True if successful, False otherwise
            
        Raises:
            Exception: If not implemented by child class
        """
        raise Exception("Distribuate creation not handled by this website")
    
    def get_statics(self, app_path) -> dict:
        """
        Function to get static file directories that must be registered by the application.
        
        Should be overwritten to provide custom static directories (e.g., for images).
        
        Note: The returned paths should exist. For user avatars, ensure a 'users/' 
        subdirectory exists under the images path with at least a default.jpg file.
        
        Args:
            app_path: Base path of the application
            
        Returns:
            Dictionary mapping static route names to directory paths
        """
        logger.debug("App path: %s", app_path)
        return {"images": os.path.join(app_path, "website", "assets", "images"), 
                "js": os.path.join(app_path, "website", "assets", "js")}
