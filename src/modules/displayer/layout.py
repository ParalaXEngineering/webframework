"""
Layout system for organizing displayer items.

This module contains the DisplayerLayout class which defines how items
are arranged on the page (vertical, horizontal, table, tabs, spacer).
"""

from typing import Optional, List, Dict, Any

from .core import Layouts, BSalign, BSstyle, MAZERStyles, ResourceRegistry


class DisplayerLayout:
    """
    Class to store information about a layout.
    
    Layouts define how displayer items are organized on the page.
    Supported layout types:
    - VERTICAL: Stack items vertically in columns
    - HORIZONTAL: Arrange items horizontally
    - TABLE: Display items in a table with headers
    - TABS: Show items in tabbed interface
    - SPACER: Add empty space between items
    
    Example:
        >>> layout = DisplayerLayout(
        ...     layoutType=Layouts.HORIZONTAL,
        ...     columns=[6, 6],  # Two equal columns
        ...     alignment=[BSalign.L, BSalign.R]
        ... )
    """

    def __init__(
        self,
        layoutType: Layouts,
        columns: Optional[List[Any]] = None,
        subtitle: Optional[str] = None,
        alignment: Optional[BSalign] = None,
        spacing: Any = 0,
        height: int = 0,
        background: Optional[BSstyle] = None,
        responsive: Optional[Dict[str, Any]] = None,
        userid: Optional[str] = None,
        style: Optional[MAZERStyles] = None
    ) -> None:
        """
        Initialize a layout.

        Args:
            layoutType: The layout type (Layouts enum)
            columns: Column sizes (int list). Sum should not exceed 12. For TABLE/TABS, these are header labels.
            subtitle: Optional subtitle for the layout
            alignment: Alignment for each column (BSalign list)
            spacing: Bootstrap spacing format {property}{sides}-{size}, or int for py-{size}
            height: Height value for the layout (default line height)
            background: Background color/style (BSstyle enum)
            responsive: DataTables configuration dict for responsive tables.
                Format: {"tableName": {"type": "simple/advanced", "columns": [...]}}
            userid: Custom ID for form analysis
            style: Custom style override (MAZERStyles enum)
            
        Example:
            >>> # Simple horizontal layout
            >>> layout = DisplayerLayout(
            ...     layoutType=Layouts.HORIZONTAL,
            ...     columns=[8, 4],
            ...     alignment=[BSalign.L, BSalign.R],
            ...     spacing=3,
            ...     background=BSstyle.LIGHT
            ... )
            
            >>> # Responsive table layout
            >>> layout = DisplayerLayout(
            ...     layoutType=Layouts.TABLE,
            ...     columns=["Name", "Email", "Status"],
            ...     responsive={"userTable": {"type": "advanced", "columns": [0, 1, 2]}}
            ... )
        """
        self.m_type = layoutType.value
        self.m_column = columns if columns is not None else []
        self.m_subtitle = subtitle
        self.m_alignement = alignment
        self.m_height = height
        self.m_background = background
        self.m_responsive = responsive
        self.m_userid = userid
        self.m_style = style
        
        # Instance-specific layout metadata storage (replaces class variable g_all_layout)
        self.m_all_layout = {}
        
        # Convert integer spacing to py-{spacing} format
        if isinstance(spacing, int):
            if spacing <= 5:
                self.m_spacing = f"py-{spacing}"
            else:
                self.m_spacing = "py-5"
        else:
            self.m_spacing = spacing 

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

        # Table and Tabs layouts have special structure
        if self.m_type == Layouts.TABLE.value or self.m_type == Layouts.TABS.value:
            current_layout["header"] = self.m_column
            
            # Handle responsive tables with DataTables
            if isinstance(self.m_responsive, dict):
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
