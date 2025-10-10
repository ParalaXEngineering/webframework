"""
Core components for the Displayer system.

This module contains:
- ResourceRegistry: Dynamic resource loading system
- DisplayerCategory: Category decorator for auto-discovery
- Enums: Layout types, item types, styles, and alignment options
"""

from enum import Enum


# ============================================================================
# Resource Dependency System for Dynamic Loading
# ============================================================================

class ResourceRegistry:
    """
    Global registry for tracking which CSS/JS resources are needed by displayer items.
    This allows dynamic loading of only the required assets.
    
    Example:
        >>> ResourceRegistry.require('datatables', 'filepond')
        >>> css_files = ResourceRegistry.get_required_css()
        >>> js_files = ResourceRegistry.get_required_js()
    """
    
    _required_css = set()
    _required_js = set()
    _required_vendors = set()
    
    # Define available resources
    RESOURCES = {
        'jquery': {
            'js': ['vendors/jquery/jquery.min.js']
        },
        'datatables': {
            'css': ['vendors/datatables.net/datatables.min.css'],
            'js': ['vendors/datatables.net/datatables.min.js', 'js/datatables-init.js']
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
        'fullcalendar': {
            'js': ['vendors/fullcalendar/fullcalendar.min.js']
        },
        'apexcharts': {
            'js_cdn': ['https://cdn.jsdelivr.net/npm/apexcharts']
        }
    }
    
    @classmethod
    def require(cls, *resource_names):
        """
        Mark resources as required. Can be called by displayer items or layouts.
        
        Args:
            *resource_names: Variable number of resource names to require
            
        Example:
            >>> ResourceRegistry.require('datatables', 'sweetalert')
        """
        for name in resource_names:
            if name in cls.RESOURCES:
                cls._required_vendors.add(name)
    
    @classmethod
    def get_required_css(cls):
        """
        Get list of all required CSS files.
        
        Returns:
            list: CSS file paths needed by registered resources
        """
        css_files = []
        for vendor in cls._required_vendors:
            if vendor in cls.RESOURCES and 'css' in cls.RESOURCES[vendor]:
                css_files.extend(cls.RESOURCES[vendor]['css'])
        return list(set(css_files))
    
    @classmethod
    def get_required_js(cls):
        """
        Get list of all required JS files.
        
        Returns:
            list: JS file paths needed by registered resources
        """
        js_files = []
        for vendor in cls._required_vendors:
            if vendor in cls.RESOURCES and 'js' in cls.RESOURCES[vendor]:
                js_files.extend(cls.RESOURCES[vendor]['js'])
        return list(set(js_files))
    
    @classmethod
    def get_required_js_cdn(cls):
        """
        Get list of all required CDN JS files.
        
        Returns:
            list: CDN URLs for JS resources
        """
        js_cdn = []
        for vendor in cls._required_vendors:
            if vendor in cls.RESOURCES and 'js_cdn' in cls.RESOURCES[vendor]:
                js_cdn.extend(cls.RESOURCES[vendor]['js_cdn'])
        return list(set(js_cdn))
    
    @classmethod
    def reset(cls):
        """
        Reset all required resources. Useful for testing or new page renders.
        """
        cls._required_css.clear()
        cls._required_js.clear()
        cls._required_vendors.clear()


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
    """Available layout types for organizing displayer items."""
    VERTICAL = "VERT"
    HORIZONTAL = "HORIZ"
    TABLE = "TABLE"
    SPACER = "SPACER"
    TABS = "TABS"


class TableMode(Enum):
    """
    DataTable rendering modes for TABLE layouts.
    
    - SIMPLE: Plain HTML table without DataTables JavaScript
    - INTERACTIVE: DataTables with manual row population via DisplayerItems
    - BULK_DATA: DataTables with pre-loaded JSON data (most efficient for large datasets)
    - SERVER_SIDE: DataTables with AJAX endpoint for server-side data loading
    """
    SIMPLE = "simple"
    INTERACTIVE = "interactive"
    BULK_DATA = "bulk_data"
    SERVER_SIDE = "server_side"


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
    INSTRINGICON = "INSTRINGICON"
    INMULTITEXT = "INMULTITEXT"
    INFILE = "INFILE"
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
    INIMAGE = "INIMAGE"
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
    ALERTBOX = "ALERTBOX"
    DYNAMICCONTENT = "DYNAMICCONTENT"
    BUTTONGROUP = "BUTTONGROUP"
    ICONTEXT = "ICONTEXT"
    ACTIONBUTTONS = "ACTIONBUTTONS"


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
