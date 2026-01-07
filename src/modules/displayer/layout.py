"""
Layout system for organizing displayer items.

This module contains the DisplayerLayout class which defines how items
are arranged on the page (vertical, horizontal, table, tabs, spacer).
"""

import warnings
from typing import Any, Dict, List, Optional, Union

from .core import BSalign, BSstyle, Layouts, MAZERStyles, ResourceRegistry, TableMode
from ..i18n.messages import (
    ERROR_BOTH_RESPONSIVE_AND_DATATABLE,
    ERROR_GRID_CONFIG_ITEMS_NOT_LIST,
    ERROR_GRID_CONFIG_NO_ITEMS,
    ERROR_GRID_CONFIG_NOT_DICT,
    ERROR_GRID_ITEM_EXCEEDS_BOUNDS,
    ERROR_GRID_ITEM_INVALID_WIDTH,
    ERROR_GRID_ITEM_INVALID_X,
    ERROR_GRID_ITEM_MISSING_KEY,
    ERROR_GRID_ITEM_NOT_DICT,
    ERROR_GRID_LAYOUT_REQUIRES_CONFIG,
    WARNING_RESPONSIVE_DEPRECATED,
)


class DisplayerLayout:
    """
    Class to store information about a layout.
    
    Layouts define how displayer items are organized on the page.
    
    Supported layout types:
    
    - VERTICAL: Items in columns flow naturally (wrap if small, stack if large).
                Multiple items in same column appear left-to-right if they fit.
    - HORIZONTAL: Items always stack vertically, one per row (forced block display).
                  Each item takes full column width, appearing one below the other.
    - TABLE: Display items in a table with headers
    - TABS: Show items in tabbed interface
    - SPACER: Add empty space between items
    
    Example:
        >>> # VERTICAL: Items flow naturally in columns
        >>> layout = DisplayerLayout(
        ...     layoutType=Layouts.VERTICAL,
        ...     columns=[6, 6],  # Two equal columns
        ...     alignment=[BSalign.L, BSalign.R]
        ... )
        >>> # Small items (like badges) will appear left-to-right
        >>> 
        >>> # HORIZONTAL: Items forced to stack vertically
        >>> layout = DisplayerLayout(
        ...     layoutType=Layouts.HORIZONTAL,
        ...     columns=[12],  # Single column with full width
        ...     alignment=[BSalign.L]
        ... )
        >>> # Each item gets its own row, stacked vertically
    """

    def __init__(
        self,
        layoutType: Layouts,
        columns: Optional[List[Any]] = None,
        subtitle: Optional[str] = None,
        alignment: Optional[Union[BSalign, List[BSalign]]] = None,
        spacing: Any = 0,
        height: int = 0,
        background: Optional[BSstyle] = None,
        responsive: Optional[Dict[str, Any]] = None,
        datatable_config: Optional[Dict[str, Any]] = None,
        grid_config: Optional[Dict[str, Any]] = None,
        userid: Optional[str] = None,
        style: Optional[MAZERStyles] = None,
        reorder_callback: Optional[str] = None
    ) -> None:
        """
        Initialize a layout.

        Args:
            layoutType: The layout type (Layouts enum)
            columns: Column sizes (int list). 
                - For VERTICAL/HORIZONTAL: Bootstrap column widths (1-12). Sum should not exceed 12.
                - For HORIZONTAL: Use single value like [12] for full width, [8] for centered column, etc.
                - For TABLE/TABS: These are header labels (strings).
            subtitle: Optional subtitle for the layout
            alignment: Alignment for each column (BSalign list or single BSalign)
            spacing: Bootstrap spacing format {property}{sides}-{size}, or int for py-{size}
            height: Height value for the layout (default line height)
            background: Background color/style (BSstyle enum)
            responsive: DEPRECATED - Use datatable_config instead
            datatable_config: DataTable configuration dict.
                Format: {"table_id": "myTable", "mode": TableMode.BULK_DATA, "data": [...], ...}
            grid_config: GRID layout configuration (GridStack JSON).
                Format: {"version": "1.0", "columns": 12, "items": [{"field_id": "example1", "x": 0, "y": 0, "w": 6, "h": 1}, ...]}
            userid: Custom ID for form analysis
            style: Custom style override (MAZERStyles enum)
            reorder_callback: URL endpoint for saving row order (used with TableMode.REORDERABLE)
            
        Example:
            >>> # VERTICAL layout: side-by-side columns
            >>> layout = DisplayerLayout(
            ...     layoutType=Layouts.VERTICAL,
            ...     columns=[8, 4],
            ...     alignment=[BSalign.L, BSalign.R],
            ...     spacing=3,
            ...     background=BSstyle.LIGHT
            ... )
            
            >>> # HORIZONTAL layout: stacked items in single column
            >>> layout = DisplayerLayout(
            ...     layoutType=Layouts.HORIZONTAL,
            ...     columns=[12],  # Full width
            ...     alignment=[BSalign.C],  # Center aligned
            ...     spacing=2
            ... )
            
            >>> # New DataTable API
            >>> layout = DisplayerLayout(
            ...     layoutType=Layouts.TABLE,
            ...     columns=["Name", "Email", "Status"],
            ...     datatable_config={
            ...         "table_id": "users",
            ...         "mode": TableMode.BULK_DATA,
            ...         "data": [{"Name": "Alice", "Email": "a@ex.com", "Status": "Active"}],
            ...         "searchable_columns": [0, 1]
            ...     }
            ... )
        """
        self.m_type = layoutType.value
        self.m_column = columns if columns is not None else []
        self.m_subtitle = subtitle
        # Normalize alignment to always be a list for consistent handling
        if alignment is None:
            self.m_alignement = None
        elif isinstance(alignment, list):
            self.m_alignement = alignment
        else:
            self.m_alignement = [alignment]
        self.m_height = height
        self.m_background = background
        self.m_userid = userid
        self.m_style = style
        self.m_grid_config = grid_config
        self.m_reorder_callback = reorder_callback
        
        # Instance-specific layout metadata storage (replaces class variable g_all_layout)
        self.m_all_layout = {}
        
        # For GRID layouts, validate config
        # Note: GridStack is NOT required for rendering GRID layouts (uses CSS Grid)
        # GridStack is only needed for the editor itself
        if layoutType == Layouts.GRID:
            if grid_config is None:
                raise ValueError(str(ERROR_GRID_LAYOUT_REQUIRES_CONFIG))
            self._validate_grid_config(grid_config)
        
        # Handle backward compatibility: responsive -> datatable_config
        if responsive is not None and datatable_config is not None:
            raise ValueError(str(ERROR_BOTH_RESPONSIVE_AND_DATATABLE))
        
        if responsive is not None:
            warnings.warn(
                str(WARNING_RESPONSIVE_DEPRECATED),
                DeprecationWarning,
                stacklevel=2
            )
            # Keep old format as-is for backward compatibility
            self.m_datatable_config = None
            self.m_responsive = responsive
        elif datatable_config is not None:
            self.m_datatable_config = datatable_config
            self.m_responsive = None
        else:
            self.m_datatable_config = None
            self.m_responsive = None
        
        # Convert integer spacing to py-{spacing} format
        if isinstance(spacing, int):
            if spacing <= 5:
                self.m_spacing = f"py-{spacing}"
            else:
                self.m_spacing = "py-5"
        else:
            self.m_spacing = spacing
    
    def _validate_grid_config(self, config: Dict[str, Any]) -> None:
        """
        Validate GRID layout configuration.
        
        Args:
            config: The configuration dictionary to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        if not isinstance(config, dict):
            raise ValueError(str(ERROR_GRID_CONFIG_NOT_DICT))
        
        if "items" not in config:
            raise ValueError(str(ERROR_GRID_CONFIG_NO_ITEMS))
        
        if not isinstance(config["items"], list):
            raise ValueError(str(ERROR_GRID_CONFIG_ITEMS_NOT_LIST))
        
        # Validate each item
        for idx, item in enumerate(config["items"]):
            if not isinstance(item, dict):
                raise ValueError(ERROR_GRID_ITEM_NOT_DICT.format(idx=idx))
            
            required_keys = ["field_id", "x", "y", "w", "h"]
            for key in required_keys:
                if key not in item:
                    raise ValueError(ERROR_GRID_ITEM_MISSING_KEY.format(idx=idx, key=key))
            
            # Validate grid constraints (Bootstrap 12-column)
            if item["w"] < 1 or item["w"] > 12:
                raise ValueError(ERROR_GRID_ITEM_INVALID_WIDTH.format(idx=idx))
            
            if item["x"] < 0 or item["x"] >= 12:
                raise ValueError(ERROR_GRID_ITEM_INVALID_X.format(idx=idx))
            
            if item["x"] + item["w"] > 12:
                raise ValueError(ERROR_GRID_ITEM_EXCEEDS_BOUNDS.format(idx=idx))
    
    def _convert_old_responsive_format(self, responsive: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert old 'responsive' format to new 'datatable_config' format.
        
        Args:
            responsive: Old format like {"table1": {"type": "advanced", "columns": [0,1], ...}}
        
        Returns:
            New format compatible with datatable_config
        """
        # Get the first (and typically only) table config
        table_id = list(responsive.keys())[0]
        old_config = responsive[table_id]
        
        # Map old 'type' to new TableMode
        type_map = {
            "basic": TableMode.INTERACTIVE.value,
            "advanced": TableMode.BULK_DATA.value,
            "ajax": TableMode.SERVER_SIDE.value,
            "simple": TableMode.SIMPLE.value
        }
        
        old_type = old_config.get("type", "interactive")
        new_mode = type_map.get(old_type, TableMode.INTERACTIVE.value)
        
        # Build new config
        new_config = {
            "table_id": table_id,
            "mode": new_mode
        }
        
        # Copy over other settings with renamed keys
        if "columns" in old_config:
            new_config["searchable_columns"] = old_config["columns"]
        if "ajax_columns" in old_config:
            new_config["columns"] = old_config["ajax_columns"]
        if "data" in old_config:
            new_config["data"] = old_config["data"]
        if "api" in old_config:
            new_config["api_endpoint"] = old_config["api"]
        
        return new_config

    def display(self, container: List[Dict[str, Any]], id: int) -> None:
        """
        Add this layout to a container view.
        
        This method generates the layout dictionary structure that will be
        rendered by the Jinja2 templates.

        Args:
            container: The container list to append this layout to
            id: The layout ID
            
        Returns:
            None (modifies container in place)
            
        Example:
            >>> layouts = []
            >>> layout = DisplayerLayout(Layouts.HORIZONTAL, columns=[6, 6])
            >>> layout.display(layouts, id=1)
            >>> print(layouts[0]['type'])  # 'HORIZ'
        """
        current_layout = {
            "object": "layout",
            "type": self.m_type,
            "id": id,
            "subtitle": self.m_subtitle,
            "background": self.m_background.value if self.m_background else None
        }

        # GRID layout has special structure
        if self.m_type == Layouts.GRID.value:
            current_layout["grid_config"] = self.m_grid_config
            current_layout["user_id"] = self.m_userid
            # Create containers for each field_id
            containers = {}
            if self.m_grid_config:
                for item in self.m_grid_config.get("items", []):
                    containers[item["field_id"]] = []
            current_layout["containers"] = containers
            container.append(current_layout)
            return

        # Table and Tabs layouts have special structure
        if self.m_type == Layouts.TABLE.value or self.m_type == Layouts.TABS.value:
            current_layout["header"] = self.m_column
            
            # Handle DataTables configuration (new or old format)
            config_to_use = self.m_datatable_config if self.m_datatable_config else None
            
            # Also support old m_responsive format for backward compatibility
            if config_to_use is None and isinstance(self.m_responsive, dict):
                # Register DataTables resource when table has responsive enabled
                ResourceRegistry.require('datatables')
                
                # Set responsive table ID
                current_layout["responsive"] = list(self.m_responsive.keys())[0]
                responsive_info = self.m_responsive[current_layout["responsive"]]
                
                # Set responsive type (basic or advanced with searchpanes)
                if "type" in responsive_info:
                    current_layout["responsive_type"] = responsive_info["type"]
                else:
                    current_layout["responsive_type"] = "basic"

                # Update instance responsive table information       
                if "responsive_addon" not in self.m_all_layout:
                    self.m_all_layout["responsive_addon"] = {}

                for table_id, responsive_info in self.m_responsive.items():
                    # Prepare the entry for this table
                    table_dict = {}
                    for key, value in responsive_info.items():
                        if key != "type":
                            table_dict[key] = value
                    table_dict["type"] = responsive_info.get("type", "basic")
                    # Append/update this table's addon
                    self.m_all_layout["responsive_addon"][table_id] = table_dict
            
            elif config_to_use is not None:
                # New datatable_config format
                ResourceRegistry.require('datatables')
                
                # Require RowReorder extension if mode is REORDERABLE
                mode = config_to_use.get("mode", TableMode.INTERACTIVE.value)
                if hasattr(mode, 'value'):
                    mode = mode.value
                if mode == TableMode.REORDERABLE.value or mode == 'reorderable':
                    ResourceRegistry.require('rowreorder')
                
                table_id = config_to_use.get("table_id", "table")
                
                # Extract value if it's an enum
                if hasattr(mode, 'value'):
                    mode = mode.value
                
                # Set layout properties for template
                current_layout["responsive"] = table_id
                current_layout["responsive_type"] = mode
                
                # Build addon configuration for JavaScript initialization
                if "responsive_addon" not in self.m_all_layout:
                    self.m_all_layout["responsive_addon"] = {}
                
                table_dict = {
                    "type": mode,  # Keep "type" key for template compatibility
                }
                
                # Copy configuration fields
                if "data" in config_to_use:
                    table_dict["data"] = config_to_use["data"]
                if "columns" in config_to_use:
                    table_dict["ajax_columns"] = config_to_use["columns"]
                else:
                    # If columns not provided, generate from table headers
                    # This is required for DataTables initialization
                    table_dict["ajax_columns"] = [{"data": col} for col in self.m_column]
                    
                if "searchable_columns" in config_to_use:
                    table_dict["columns"] = config_to_use["searchable_columns"]
                if "api_endpoint" in config_to_use:
                    table_dict["api"] = config_to_use["api_endpoint"]
                if "api_params" in config_to_use:
                    table_dict["api_params"] = config_to_use["api_params"]
                if "refresh_interval" in config_to_use:
                    table_dict["refresh_interval"] = config_to_use["refresh_interval"]
                if "order" in config_to_use:
                    table_dict["order"] = config_to_use["order"]
                if "pageLength" in config_to_use:
                    table_dict["pageLength"] = config_to_use["pageLength"]
                
                self.m_all_layout["responsive_addon"][table_id] = table_dict
            
            # Add reorder callback if provided (for REORDERABLE mode)
            if self.m_reorder_callback:
                current_layout["reorder_callback"] = self.m_reorder_callback

            # For TABS, lines is a single row of cells (one per tab)
            if self.m_type == Layouts.TABS.value:
                current_layout["lines"] = [[[] for _ in range(len(self.m_column))]]
            else:
                current_layout["lines"] = None

            current_layout["user_id"] = self.m_userid
    
        else:
            # Standard layouts (VERTICAL, HORIZONTAL, SPACER)
            # Check column size and create containers
            column_size = 0
            col_nb = 0
            containers = []
            alignments = []
            
            for col in self.m_column:
                column_size += col
                containers.append([])
                
                # Set alignment for each column
                if not self.m_alignement or col_nb >= len(self.m_alignement):
                    alignments.append(BSalign.L.value)
                else:
                    alignments.append(self.m_alignement[col_nb].value)
                col_nb += 1

            # Validate column size (Bootstrap 12-column grid)
            if column_size > 12 or column_size == 0:
                current_layout["columns"] = []
                current_layout["containers"] = []
            else:
                current_layout["columns"] = self.m_column
                current_layout["containers"] = containers
                
            current_layout["align"] = alignments
            current_layout["spacing"] = self.m_spacing
            current_layout["user_id"] = self.m_userid
            current_layout["style"] = self.m_style.value if self.m_style else None

        container.append(current_layout)
