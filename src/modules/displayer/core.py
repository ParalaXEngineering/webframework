"""
Core components for the Displayer system.

This module contains:
- ResourceRegistry: Dynamic resource loading system (request-scoped)
- DisplayerCategory: Category decorator for auto-discovery
- Enums: Layout types, item types, styles, and alignment options
"""

from enum import Enum
from typing import Set, Dict, List


# ============================================================================
# Resource Dependency System for Dynamic Loading
# ============================================================================

class ResourceRegistry:
    """
    Request-scoped registry for tracking which CSS/JS resources are needed by displayer items.
    Uses Flask's g object for request-scoped storage to avoid conflicts between concurrent requests.
    Falls back to class-level storage when outside Flask context (e.g., tests).
    
    Example:
        >>> ResourceRegistry.require('datatables', 'filepond')
        >>> css_files = ResourceRegistry.get_required_css()
        >>> js_files = ResourceRegistry.get_required_js()
    """
    
    # Class-level storage for backward compatibility (used outside Flask context)
    _required_css: Set[str] = set()
    _required_js: Set[str] = set()
    _required_vendors: Set[str] = set()
    
    # Define available resources
    RESOURCES: Dict[str, Dict[str, List[str]]] = {
        'jquery': {
            'js': ['vendors/jquery/jquery.min.js']
        },
        'datatables': {
            'css': ['vendors/datatables.net/datatables.min.css'],
            'js': ['vendors/datatables.net/datatables.min.js', 'js/datatables-init.js']
        },
        'rowreorder': {
            'css_cdn': ['https://cdn.datatables.net/rowreorder/1.4.1/css/rowReorder.dataTables.min.css'],
            'js_cdn': ['https://cdn.datatables.net/rowreorder/1.4.1/js/dataTables.rowReorder.min.js']
        },
        'gridstack': {
            'css': ['vendors/gridstack/gridstack.min.css', 'css/gridstack-bootstrap.css'],
            'js': ['vendors/gridstack/gridstack-all.min.js']
        },
        'sweetalert': {
            'css': ['vendors/sweetalert/sweetalert2.min.css'],
            'js': ['vendors/sweetalert/sweetalert2.min.js']
        },
        'filepond': {
            'css': [
                'vendors/filepond/filepond.min.css',
                'vendors/filepond-plugin-image-preview/filepond-plugin-image-preview.min.css'
            ],
            'js': [
                'vendors/filepond/filepond.min.js',
                'vendors/filepond-plugin-image-preview/filepond-plugin-image-preview.min.js',
                'vendors/filepond-plugin-file-validate-type/filepond-plugin-file-validate-type.min.js',
                'js/filepond-init.js'
            ]
        },
        'tinymce': {
            'js': ['vendors/tinymce/tinymce.min.js', 'js/tinymce-init.js']
        },
        'tracker_admin': {
            'js_custom': ['/common/assets/tracker_js/?filename=tracker_admin.js']
        },
        'fullcalendar': {
            'js': ['vendors/fullcalendar/fullcalendar.min.js']
        },
        'apexcharts': {
            'js_cdn': ['https://cdn.jsdelivr.net/npm/apexcharts']
        },
        'highlightjs': {
            'css': ['vendors/highlightjs/styles/atom-one-dark.min.css'],
            'js': ['vendors/highlightjs/highlight.min.js']
        }
    }
    
    @classmethod
    def _get_registry(cls) -> set:
        """Get the request-scoped registry, or fallback to class-level."""
        try:
            from flask import g
            if not hasattr(g, '_resource_registry'):
                g._resource_registry = set()
            return g._resource_registry
        except (ImportError, RuntimeError):
            # Outside Flask context (e.g., tests) - use class-level
            return cls._required_vendors
    
    @classmethod
    def require(cls, *resource_names):
        """
        Mark resources as required. Can be called by displayer items or layouts.
        
        Args:
            *resource_names: Variable number of resource names to require
            
        Example:
            >>> ResourceRegistry.require('datatables', 'sweetalert')
        """
        registry = cls._get_registry()
        for name in resource_names:
            if name in cls.RESOURCES:
                registry.add(name)
    
    @classmethod
    def get_required_css(cls):
        """
        Get list of all required CSS files for this request.
        
        Returns:
            list: CSS file paths needed by registered resources
        """
        registry = cls._get_registry()
        css_files = []
        for vendor in registry:
            if vendor in cls.RESOURCES and 'css' in cls.RESOURCES[vendor]:
                css_files.extend(cls.RESOURCES[vendor]['css'])
        return list(set(css_files))
    
    @classmethod
    def get_required_js(cls):
        """
        Get list of all required JS files for this request.
        
        Returns:
            list: JS file paths needed by registered resources
        """
        registry = cls._get_registry()
        js_files = []
        for vendor in registry:
            if vendor in cls.RESOURCES:
                if 'js' in cls.RESOURCES[vendor]:
                    js_files.extend(cls.RESOURCES[vendor]['js'])
                if 'js_custom' in cls.RESOURCES[vendor]:
                    js_files.extend(cls.RESOURCES[vendor]['js_custom'])
        return list(set(js_files))
    
    @classmethod
    def get_required_js_cdn(cls):
        """
        Get list of all required CDN JS files for this request.
        
        Returns:
            list: CDN URLs for JS resources
        """
        registry = cls._get_registry()
        js_cdn = []
        for vendor in registry:
            if vendor in cls.RESOURCES and 'js_cdn' in cls.RESOURCES[vendor]:
                js_cdn.extend(cls.RESOURCES[vendor]['js_cdn'])
        return list(set(js_cdn))
    
    @classmethod
    def get_required_css_cdn(cls):
        """ for this request.
        
        Returns:
            list: CDN URLs for CSS resources
        """
        registry = cls._get_registry()
        css_cdn = []
        for vendor in registry:
            if vendor in cls.RESOURCES and 'css_cdn' in cls.RESOURCES[vendor]:
                css_cdn.extend(cls.RESOURCES[vendor]['css_cdn'])
        return list(set(css_cdn))
    
    @classmethod
    def reset(cls):
        """
        Reset request-scoped resources.
        For backward compatibility and testing.
        """
        try:
            from flask import g
            if hasattr(g, '_resource_registry'):
                g._resource_registry = set()
        except (ImportError, RuntimeError):
            # Outside Flask context - reset class-level
            cls._required_vendors = set()


# ============================================================================
# Displayer Item Category System for Auto-Discovery Testing
# ============================================================================

class DisplayerCategory:
    """
    Category decorator for DisplayerItem classes to enable auto-discovery in tests.
    
    Usage:
        >>> @DisplayerCategory.INPUT
        >>> class DisplayerItemInputString(DisplayerItem):
        ...     pass
    
    Categories:
        - INPUT: Input form elements (text, number, date, select, etc.)
        - DISPLAY: Display-only elements (text, alert, badge, etc.)
        - BUTTON: Interactive buttons and links
        - LAYOUT: Layout-related items
        - MEDIA: Images, files, graphs, calendars
        - ADVANCED: Complex composite items
    """
    
    _registry = {
        'input': [],
        'display': [],
        'button': [],
        'layout': [],
        'media': [],
        'advanced': []
    }
    
    @classmethod
    def _register(cls, category, item_class):
        """
        Register a class in a category.
        
        Args:
            category: The category name
            item_class: The class to register
            
        Returns:
            The item class (for decorator chaining)
        """
        if category not in cls._registry:
            cls._registry[category] = []
        if item_class not in cls._registry[category]:
            cls._registry[category].append(item_class)
        return item_class
    
    @classmethod
    def get_all(cls, category=None):
        """
        Get all registered classes, optionally filtered by category.
        
        Args:
            category: Optional category filter
            
        Returns:
            dict or list: All categories or classes in specific category
        """
        if category:
            return cls._registry.get(category, [])
        return cls._registry
    
    # Decorator methods
    @classmethod
    def INPUT(cls, item_class):
        """Mark class as an input item."""
        item_class._displayer_category = 'input'
        return cls._register('input', item_class)
    
    @classmethod
    def DISPLAY(cls, item_class):
        """Mark class as a display item."""
        item_class._displayer_category = 'display'
        return cls._register('display', item_class)
    
    @classmethod
    def BUTTON(cls, item_class):
        """Mark class as a button/link item."""
        item_class._displayer_category = 'button'
        return cls._register('button', item_class)
    
    @classmethod
    def LAYOUT(cls, item_class):
        """Mark class as a layout item."""
        item_class._displayer_category = 'layout'
        return cls._register('layout', item_class)
    
    @classmethod
    def MEDIA(cls, item_class):
        """Mark class as a media item (image, file, graph, calendar)."""
        item_class._displayer_category = 'media'
        return cls._register('media', item_class)
    
    @classmethod
    def ADVANCED(cls, item_class):
        """Mark class as an advanced/composite item."""
        item_class._displayer_category = 'advanced'
        return cls._register('advanced', item_class)


# ============================================================================
# Enums
# ============================================================================

class Layouts(Enum):
    """
    Available layout types for organizing displayer items.
    
    - VERTICAL: Bootstrap grid layout with columns. Items flow naturally within columns.
                Small items (badges, buttons) appear left-to-right if they fit,
                larger items stack vertically. Standard Bootstrap behavior.
                Example: [6, 6] creates two columns side by side.
                
    - HORIZONTAL: Single column where each item is forced to take full width.
                  Items always stack vertically, one per row, regardless of size.
                  Each item wrapped in block-level div (mb-2 spacing).
                  Example: [12] creates full-width stacked items.
                  
    - TABLE: Tabular layout with rows and columns, headers at the top.
             Supports DataTables for interactive features.
             
    - TABS: Tabbed interface for organizing content in separate tabs.
    
    - SPACER: Empty vertical space for visual separation between sections.
    
    - GRID: Custom grid layout designed by the user via visual editor.
            Uses GridStack.js for drag-and-drop layout configuration.
            JSON configuration maps field IDs to grid positions.
    """
    VERTICAL = "VERT"
    HORIZONTAL = "HORIZ"
    TABLE = "TABLE"
    SPACER = "SPACER"
    TABS = "TABS"
    GRID = "GRID"


class TableMode(Enum):
    """
    DataTable rendering modes for TABLE layouts.
    
    - SIMPLE: Plain HTML table without DataTables JavaScript
    - INTERACTIVE: DataTables with manual row population via DisplayerItems
    - BULK_DATA: DataTables with pre-loaded JSON data (most efficient for large datasets)
    - SERVER_SIDE: DataTables with AJAX endpoint for server-side data loading
    - REORDERABLE: DataTables with RowReorder extension for drag-and-drop row reordering
    """
    SIMPLE = "simple"
    INTERACTIVE = "interactive"
    BULK_DATA = "bulk_data"
    SERVER_SIDE = "server_side"
    REORDERABLE = "reorderable"


class DisplayerItems(Enum):
    """Registry of all available displayer item types."""
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    FILE = "FILE"
    BADGE = "BADGE"
    SEPARATOR = "SEPARATOR"
    INDATE = "INDATE"
    INBOX = "INBOX"
    INNUM = "INNUM"
    INHIDDEN = "INHIDDEN"
    INTEXT = "INTEXT"
    INTEXTJS = "INTEXTJS"
    INSTRING = "INSTRING"
    INPASSWORD = "INPASSWORD"
    INSTRINGICON = "INSTRINGICON"
    INMULTITEXT = "INMULTITEXT"
    INMULTIINT = "INMULTIINT"
    INMULTIFLOAT = "INMULTIFLOAT"
    INMULTICHECK = "INMULTICHECK"
    INMULTIDATE = "INMULTIDATE"
    INCHOICE = "INCHOICE"
    INMULTICHOICE = "INMULTICHOICE"
    INFOLDER = "INFOLDER"
    INCASCADED = "INCASCADED"
    INFILEEXPLORER = "INFILEEXPLORER"
    INMULTISELECT = "INMULTISELECT"
    INMAPPING = "INMAPPING"
    INTEXTSELECT = "INTEXTSELECT"
    INSELECTTEXT = "INSELECTTEXT"
    INDUALSELECTTEXT = "INDUALSELECTTEXT"
    INDUALTEXTSELECT = "INDUALTEXTSELECT"
    INTEXTTEXT = "INTEXTTEXT"
    INLISTTEXT = "INLISTTEXT"
    INLISTSELECT = "INLISTSELECT"
    BUTTON = "BUTTON"
    MODALBUTTON = "MODALBUTTON"
    MODALLINK = "MODALLINK"
    ALERT = "ALERT"
    SELECT = "SELECT"
    GRAPH = "GRAPH"
    DOWNLOAD = "DOWNLOAD"
    ICONLINK = "ICONLINK"
    BUTTONLINK = "BUTTONLINK"
    PLACEHOLDER = "PLACEHOLDER"
    CALENDAR = "CALENDAR"
    CARD = "CARD"
    DYNAMICCONTENT = "DYNAMICCONTENT"
    BUTTONGROUP = "BUTTONGROUP"
    ICONTEXT = "ICONTEXT"
    ACTIONBUTTONS = "ACTIONBUTTONS"
    CONSOLE = "CONSOLE"
    CODE = "CODE"
    PROGRESSBAR = "PROGRESSBAR"
    GRIDEDITOR = "GRIDEDITOR"
    FILEUPLOAD = "FILEUPLOAD"
    FILEDISPLAY = "FILEDISPLAY"
    TREE = "TREE"


class BSstyle(Enum):
    """Bootstrap color/style options."""
    PRIMARY = "primary"
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    ERROR = "danger"
    DARK = "dark"
    LIGHT = "light-secondary"
    SECONDARY = "secondary"
    ULTRALIGHT = "body"
    NONE = "none"


class BSalign(Enum):
    """Bootstrap alignment options."""
    L = "start"
    R = "end"
    C = "center"


class MAZERStyles(Enum):
    """MAZER template style options."""
    CARD = "rounded-3"
    HEADER = ""
    BODY = ""
