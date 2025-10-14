"""
Main Displayer class for constructing page displays.

This module contains the Displayer class which orchestrates the creation
of modules, layouts, and items for rendering web pages.
"""

from typing import Optional, Dict, List, Any
import logging

logger = logging.getLogger(__name__)

try:
    # Import the module, not the object, so we get the updated value
    from ..auth import auth_manager as auth_manager_module
except ImportError:
    from auth import auth_manager as auth_manager_module

try:
    from flask import session
except ImportError:
    # For testing without Flask
    session = None

from .core import ResourceRegistry, Layouts
from .layout import DisplayerLayout


class Displayer:
    """
    Main displayer class to construct the information displayed on the screen.

    The displayer is constituted of several modules (each module is a single form and card), 
    which are themselves created with layouts that can be stacked on top of another
    (for instance vertical layouts, horizontal ones, etc...). In each layout, there is one 
    or more display items that hold the information displayed.

    The modules, layouts and items are always displayed in the order in which they have been 
    added to the displayer.
    
    Example:
        >>> disp = Displayer()
        >>> disp.add_generic("MyModule")
        >>> layout_id = disp.add_master_layout(DisplayerLayout(Layouts.HORIZONTAL, columns=[6, 6]))
        >>> disp.add_display_item(DisplayerItemText("Hello"), column=0)
        >>> data = disp.display()
    """

    def __init__(self) -> None:
        """Initialize a new Displayer instance."""
        # Reset resource registry for this new page render
        ResourceRegistry.reset()
        
        self.m_modules: Dict[str, Dict[str, Any]] = {}
        self.m_modals: List[Dict[str, Any]] = []
        self.g_next_layout: int = 0
        self.m_all_layout: Dict[str, Any] = {}
        self.m_breadcrumbs: Dict[str, str] = {}
        self.m_title: Optional[str] = None
        self.m_active_module: Optional[str] = None
        self.m_last_layout: Optional[DisplayerLayout] = None

    def add_module(self, module: Any, name_override: Optional[str] = None, display: bool = True) -> None:
        """
        Prepare a new module for displaying. An optional ID can be assigned to this module.
        The module is then set to active, which means that everything will be added on it.
        
        This method now automatically checks permissions if the module has m_required_permission set.
        If permission check fails, the module is marked as access_denied and will display an 
        access denied message instead of the regular content.

        Args:
            module: A module object with m_default_name, m_type, and optionally m_error
            name_override: An optional name overriding, instead of the default name
            display: Display the title
        """
        # Safely get m_default_name, or use "Generic" if it doesn't exist
        default_name = getattr(module, 'm_default_name', 'Generic')

        error_module = None
        if hasattr(module, "m_error"):
            error_module = module.m_error

        # Check permissions automatically
        access_denied = False
        denied_reason = None
        user_permissions = []
        current_username = None
        is_guest = False
        
        required_permission = getattr(module, 'm_required_permission', None)
        required_action = getattr(module, 'm_required_action', 'view')
        
        # Get the current auth_manager instance from the module (not the import-time value)
        auth_manager = auth_manager_module.auth_manager
        
        logger.info(f"[Displayer] Module: {default_name}, required_permission={required_permission}, required_action={required_action}")
        logger.info(f"[Displayer] auth_manager={auth_manager}, session available={session is not None}")
        
        # If no explicit permission is set, use the module name as permission
        # This ensures GUEST users can't access modules unless explicitly granted
        if not required_permission:
            required_permission = default_name
            logger.info(f"[Displayer] No explicit permission, defaulting to module name: {required_permission}")
        
        if auth_manager is not None and session is not None:
            logger.info(f"[Displayer] Auth system is available, checking permissions...")
            current_username = session.get('username')
            logger.info(f"[Displayer] Checking permissions for user: {current_username}, module: {required_permission}, action: {required_action}")
            
            if not current_username:
                access_denied = True
                denied_reason = "You must be logged in to access this module."
            else:
                # Check if user is GUEST (for informational purposes)
                is_guest = current_username.upper() == 'GUEST'
                
                # Check permissions - GUEST is treated like any other user
                has_perm = auth_manager.has_permission(current_username, required_permission, required_action)
                logger.info(f"[Displayer] Permission check result: {has_perm} for {current_username} on {required_permission}.{required_action}")
                
                if not has_perm:
                    access_denied = True
                    denied_reason = f"You need '{required_action}' permission for '{required_permission}' module."
                else:
                    # Get all user permissions for this module
                    user_permissions = auth_manager.get_user_permissions(current_username, required_permission)
        else:
            logger.warning(f"[Displayer] Auth system NOT available! auth_manager={auth_manager is not None}, session={session is not None}")
            logger.warning(f"[Displayer] Module '{default_name}' will be displayed WITHOUT permission checks!")
        
        # Inject user context into the module instance
        if hasattr(module, '_current_user'):
            module._current_user = current_username
        if hasattr(module, '_user_permissions'):
            module._user_permissions = user_permissions
        if hasattr(module, '_is_guest'):
            module._is_guest = is_guest
        if hasattr(module, '_is_readonly'):
            module._is_readonly = not ('write' in user_permissions or 'edit' in user_permissions or 'execute' in user_permissions) if user_permissions else True
        
        self.m_modules[default_name] = {
            "id": default_name,
            "type": module.m_type,
            "display": display,
            "error": error_module,
            "access_denied": access_denied,
            "denied_reason": denied_reason,
            "required_permission": required_permission,
            "required_action": required_action,
            "user_permissions": user_permissions,
            "current_user": current_username,
            "is_guest": is_guest,
            "is_readonly": not ('write' in user_permissions or 'edit' in user_permissions or 'execute' in user_permissions) if user_permissions else True
        }
        if name_override:
            self.m_modules[default_name]["name_override"] = name_override

        self.m_active_module = default_name

    def add_generic(self, name: str, display: bool = True) -> None:
        """
        Prepare a generic item for displaying.

        Args:
            name: The item name
            display: Display the title
        """
        self.m_modules[name] = {"id": name, "type": None, "display": display}
        self.m_active_module = name

    def switch_module(self, name: str) -> None:
        """
        Switch the current module to the given one, if it exists.

        Args:
            name: The name of the module to switch to
        """
        if name in self.m_modules:
            self.m_active_module = name

    def set_title(self, title: str) -> None:
        """
        Set the page title.
        
        Args:
            title: The title string
        """
        self.m_title = title
    
    def add_breadcrumb(
            self, 
            name: str,
            url: str,
            parameters: List[str],
            style: Optional[str] = None
    ) -> None:
        """
        Add a new item in the breadcrumbs menu.
        
        Args:
            name: The name displayed for the current link in the breadcrumbs
            url: The url endpoint (in the format used by url_for in jinja)
            parameters: The list of parameters for the get link
            style: Optional style override
        """
        self.m_breadcrumbs[name] = {"url": url, "parameters": parameters, "style": style}

    def find_layout(
        self, 
        searchable_layout: Optional[List[Dict]] = None, 
        layout_id: int = -1
    ) -> Optional[Dict[str, Any]]:
        """
        Find a layout recursively by its ID.

        Args:
            searchable_layout: A list of items that can contain layouts. 
                             If None, searches in active module's layouts.
            layout_id: The layout ID to search for. Returns None if -1.

        Returns:
            The found layout dictionary if found, None otherwise.
            
        Example:
            >>> layout = displayer.find_layout(layout_id=5)
            >>> if layout:
            ...     print(layout['type'])
        """
        # Handle default value and invalid ID
        if layout_id == -1:
            return None
            
        if searchable_layout is None:
            if not self.m_active_module or "layouts" not in self.m_modules[self.m_active_module]:
                return None
            searchable_layout = self.m_modules[self.m_active_module]["layouts"]

        for potential_layout in searchable_layout:
            if not isinstance(potential_layout, dict) or potential_layout.get("object") != "layout":
                continue
                
            # Found the layout
            if potential_layout.get("id") == layout_id:
                return potential_layout
            
            # Search recursively in children
            found = self._search_layout_children(potential_layout, layout_id)
            if found is not None:
                return found

        return None
    
    def _search_layout_children(
        self, 
        layout: Dict[str, Any], 
        layout_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Search for a layout ID within a layout's children.
        
        Args:
            layout: The parent layout to search in
            layout_id: The layout ID to find
            
        Returns:
            The found layout or None
        """
        # Search in containers (VERTICAL/HORIZONTAL layouts)
        if containers := layout.get("containers"):
            for container in containers:
                if found := self.find_layout(container, layout_id):
                    return found
        
        # Search in lines (TABLE/TABS layouts)
        if lines := layout.get("lines"):
            for line in lines:
                for column in line:
                    if found := self.find_layout(column, layout_id):
                        return found
        
        return None

    def add_display_item(
        self,
        item,
        column: int = 0,
        layout_id: int = -1,
        disabled: bool = False,
        id: int = None,
        line: int = -1,
    ) -> bool:
        """
        Add a new display item.

        Args:
            item: The DisplayerItem to add
            column: The column of the layout in which it will be added
            layout_id: The layout id of the parent layout (-1 for last one added)
            disabled: Whether the item should be disabled
            id: If set, the whole item will have an id for JavaScript updates
            line: If set, the line in the layout is forced. Some layouts don't have 
                  the notion of lines. If line == -2, a new line will only be created 
                  if no other line already exists

        Returns:
            True if success, False if the given information is not correct
        """
        # Register required resources for this item
        if hasattr(item, "get_required_resources"):
            resources = item.get_required_resources()
            if resources:
                ResourceRegistry.require(*resources)

        # Check that there is at least a module and a layout
        if not self.m_active_module or "layouts" not in self.m_modules[self.m_active_module]:
            return False

        # Try to find the layout
        if layout_id == -1:
            layout_id = self.g_next_layout - 1

        layout = self.find_layout(layout_id=layout_id)
        if layout is None:
            return False

        if layout["type"] == Layouts.VERTICAL.value:
            # Check that there are enough columns
            if column >= len(layout["containers"]):
                return False

        elif layout["type"] == Layouts.TABLE.value or layout["type"] == Layouts.TABS.value:
            # Do we have at least a line?
            if not layout["lines"]:
                layout["lines"] = [[[] for _ in range(len(layout["header"]))]]

            # For TABS, only one row is allowed
            if layout["type"] == Layouts.TABS.value:
                line = 0
            else:
                if line == -1:
                    # Check if we need to create a new line
                    if layout["lines"][-1][column]:
                        layout["lines"].append([[] for _ in range(len(layout["header"]))])
                elif line == -2:
                    # Check if we need to create a new line
                    if layout["lines"][-1][column] and len(layout["lines"][-1][column]) == 0:
                        layout["lines"].append([[] for _ in range(len(layout["header"]))])
                    line = -1
                else:
                    if len(layout["lines"]) <= line:
                        for i in range(len(layout["lines"]), line + 1):
                            layout["lines"].append([[] for _ in range(len(layout["header"]))])

        if disabled:
            item.setDisabled(True)

        if id:
            item.setId(id)

        # Add the display item
        if layout["type"] == Layouts.VERTICAL.value:
            item.display(layout["containers"][column], self.m_modules[self.m_active_module]["id"])
        elif layout["type"] == Layouts.TABLE.value:
            item.display(
                layout["lines"][line][column],
                self.m_modules[self.m_active_module]["id"],
            )
        elif layout["type"] == Layouts.TABS.value:
            # Always line 0 for tabs
            item.display(
                layout["lines"][0][column],
                self.m_modules[self.m_active_module]["id"],
            )

        return True
    
    def add_modal(self, id: str, modal: str, header: str = "") -> None:
        """
        Add a modal dialog.
        
        Args:
            id: Unique identifier for the modal
            modal: Modal content object with display() method
            header: Optional header text
        """
        self.m_modals.append({"id": id, "content": modal.display(), "header": header})

    def add_slave_layout(
        self,
        layout: DisplayerLayout,
        column: int = 0,
        layout_id: int = -1,
        line: int = -1,
    ) -> int:
        """
        Add a child layout inside a master layout.
        
        Args:
            layout: The DisplayerLayout to add
            column: The column to add the layout in
            layout_id: The parent layout ID (-1 for last created layout)
            line: The line number for TABLE layouts (-1 for auto)
        
        Returns:
            The new layout ID, or -1 if failed
        """
        if layout_id == -1:
            layout_id = self.g_next_layout - 1

        master_layout = self.find_layout(layout_id=layout_id)
        if master_layout is None:
            return -1

        if layout.m_type == Layouts.VERTICAL.value:
            # Check that there are enough columns
            if "header" in master_layout and column >= len(master_layout["header"]):
                return -1 
            if "containers" in master_layout and column >= len(master_layout["containers"]):
                return -1
            
        # Add the display item
        if layout.m_type == Layouts.VERTICAL.value:
            if "lines" in master_layout:
                # Do we have at least a line?
                if not master_layout["lines"]:
                    master_layout["lines"] = [[[] for _ in range(len(master_layout["header"]))]]

                if line == -1:
                    # Check if we need to create a new line
                    if master_layout["lines"][-1][column]:
                        master_layout["lines"].append([[] for _ in range(len(master_layout["header"]))])
                elif line == -2:
                    # Check if we need to create a new line
                    if master_layout["lines"][-1][column] and len(master_layout["lines"][-1][column]) == 0:
                        master_layout["lines"].append([[] for _ in range(len(master_layout["header"]))])
                    line = -1
                else:
                    if len(master_layout["lines"]) <= line:
                        for i in range(len(master_layout["lines"]), line + 1):
                            master_layout["lines"].append([[] for _ in range(len(master_layout["header"]))])
                layout.display(master_layout["lines"][line][column], self.g_next_layout)
            else:
                layout.display(master_layout["containers"][column], self.g_next_layout)
            self.g_next_layout += 1

            # Setup the all layout variable (merge responsive_addon to preserve all tables)
            for item in layout.m_all_layout:
                if item == "responsive_addon" and item in self.m_all_layout:
                    # Merge responsive_addon dictionaries instead of overwriting
                    self.m_all_layout[item].update(layout.m_all_layout[item])
                else:
                    self.m_all_layout[item] = layout.m_all_layout[item]

            return self.g_next_layout - 1
        elif master_layout["type"] == Layouts.TABS.value:
            # Only one row for tabs
            layout.display(master_layout["lines"][0][column], self.g_next_layout)
            self.g_next_layout += 1
            # Merge responsive_addon to preserve all tables
            for item in layout.m_all_layout:
                if item == "responsive_addon" and item in self.m_all_layout:
                    # Merge responsive_addon dictionaries instead of overwriting
                    self.m_all_layout[item].update(layout.m_all_layout[item])
                else:
                    self.m_all_layout[item] = layout.m_all_layout[item]
            return self.g_next_layout - 1

    def add_master_layout(self, layout: DisplayerLayout) -> int:
        """
        Add a top-level layout to the active module.
        
        Args:
            layout: The DisplayerLayout to add
            
        Returns:
            The layout ID
        """
        if "layouts" not in self.m_modules[self.m_active_module]:
            self.m_modules[self.m_active_module]["layouts"] = []

        self.m_last_layout = layout
        layout.display(self.m_modules[self.m_active_module]["layouts"], self.g_next_layout)
        self.g_next_layout += 1

        # Setup the all layout variable (merge responsive_addon to preserve all tables)
        for item in layout.m_all_layout:
            if item == "responsive_addon" and item in self.m_all_layout:
                # Merge responsive_addon dictionaries instead of overwriting
                self.m_all_layout[item].update(layout.m_all_layout[item])
            else:
                self.m_all_layout[item] = layout.m_all_layout[item]

        return self.g_next_layout - 1

    def duplicate_master_layout(self) -> Optional[int]:
        """
        Add a new layout, identical to the previous one.
        
        Returns:
            The new layout ID, or None if no previous layout exists
        """
        if self.m_last_layout:
            self.m_last_layout.display(self.m_modules[self.m_active_module]["layouts"], self.g_next_layout)
            self.g_next_layout += 1
            return self.g_next_layout - 1

        return None

    def display(self, bypass_auth: bool = False) -> Dict[str, Any]:
        """
        Return the information to pass to the template.

        Args:
            bypass_auth: If True, skip authorization checks

        Returns:
            Dictionary needed for the template to display
        """
        serve_modules = {}
        serve_modules["modals"] = self.m_modals
        serve_modules["all_layout"] = self.m_all_layout
        if self.m_breadcrumbs:
            serve_modules["breadcrumbs"] = self.m_breadcrumbs
        serve_modules["title"] = self.m_title
        
        # Include required resources so they're available in template context
        serve_modules["required_css"] = ResourceRegistry.get_required_css()
        serve_modules["required_js"] = ResourceRegistry.get_required_js()
        serve_modules["required_cdn"] = ResourceRegistry.get_required_js_cdn()

        for module in self.m_modules:  
            # Authorization is now handled in add_module(), so we just check the flag
            # No need to call authorize_module again here
            if not bypass_auth:
                # Skip modules that were denied access during add_module
                if self.m_modules[module].get('access_denied', False):
                    # Still add it so the template can show the access denied message
                    serve_modules[module] = self.m_modules[module]
                else:
                    serve_modules[module] = self.m_modules[module]
            else: 
                serve_modules[module] = self.m_modules[module]

        return serve_modules

    def set_default_layout(self, id: int) -> None:
        """
        Impose the default layout back to a given one so that for any future item added, 
        if layout is not specified, the layout id will be this one.

        Args:
            id: A new layout id
        """
        self.g_next_layout = id
