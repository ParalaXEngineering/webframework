try:
    from .. import access_manager
except ImportError:
    import access_manager

from typing import Optional, List, Dict, Any, ClassVar
from enum import Enum
from functools import wraps

from .core import DisplayerItems, DisplayerCategory, BSstyle, ResourceRegistry


class DisplayerItem:
    """Generic class to store the information about a display item. A display item is the atomic information used to display stuff on the screen."""

    # Define which attributes should be serialized to dict for template rendering
    _SERIALIZABLE_ATTRS: ClassVar[Dict[str, str]] = {
        'm_text': 'text',
        'm_level': 'level',
        'm_value': 'value',
        'm_style': 'style',
        'm_disabled': 'disabled',
        'm_data': 'data',
        'm_tooltips': 'tooltips',
        'm_header': 'header',
        'm_possibles': 'possibles',
        'm_parameters': 'parameters',
        'm_path': 'path',
        'm_icon': 'icon',
        'm_endpoint': 'endpoint',
        'm_focus': 'focus',
        'm_date': 'date',
        'm_itemId': 'itemId',
    }

    def __init__(self, itemType: DisplayerItems) -> None:
        """Constructor

        :param itemType: The type of item that this display is. Should be used by any child item
        :type itemType: DisplayerItems
        """
        self.m_type = itemType

    @classmethod
    def instantiate_test(cls):
        """
        Create a test instance of this DisplayerItem with sensible default data.
        
        Override this method in child classes to provide proper test data.
        Default implementation returns a minimal instance.
        
        :return: Test instance of this DisplayerItem
        :rtype: DisplayerItem
        
        Example override:
            @classmethod
            def instantiate_test(cls):
                return cls(
                    id="test_id",
                    text="Sample Text",
                    value="test_value",
                    choices=["Option A", "Option B"]
                )
        """
        # Default: try to instantiate with minimal parameters
        # Child classes should override this for proper test data
        return cls(DisplayerItems.TEXT)

    @classmethod
    def get_required_resources(cls) -> List[str]:
        """
        Return list of required resources (vendors) for this displayer item.
        Override in child classes to declare dependencies.
        
        Example:
            @classmethod
            def get_required_resources(cls):
                return ['datatables', 'sweetalert']
        
        :return: List of resource identifiers
        :rtype: list
        """
        return []

    def display(self, container: List[Dict[str, Any]], parent_id: Optional[str] = None) -> None:
        """
        Add this item to a container view.
        
        This method serializes the item's attributes and appends the resulting
        dictionary to the provided container list. The container will be rendered
        by Jinja2 templates.

        :param container: The container in which the display item should be appended. 
                         The items are added by order of adding in the code
        :type container: list
        :param parent_id: If we are in a form, each different form will have a parent id
        :type parent_id: str, optional
        """
        item = {"object": "item", "type": self.m_type.value}

        # Serialize all registered attributes that exist and are not None
        for attr_name, dict_key in self._SERIALIZABLE_ATTRS.items():
            if hasattr(self, attr_name):
                value = getattr(self, attr_name)
                if value is not None:
                    item[dict_key] = value

        # Handle special cases for IDs (m_ids takes precedence over m_id)
        if hasattr(self, "m_ids"):
            if parent_id:
                item["id"] = [f"{parent_id}.{id}" for id in self.m_ids]
            else:
                item["id"] = self.m_ids
        elif hasattr(self, "m_id"):
            if parent_id:
                item["id"] = f"{parent_id}.{self.m_id}"
            else:
                item["id"] = self.m_id

        container.append(item)
        return

    def setDisabled(self, disabled: bool = False) -> None:
        """Disable the current item. While the function is always present, it can yield to no result depending on the item

        :param disabled: Disable the item, defaults to False
        :type disabled: bool, optional
        """

        self.m_disabled = disabled
        return

    def setId(self, id: str = None) -> None:
        """Set an id to the current item. This way, the item can easily be replaced by something else with some javascript

        :param id: The id of the item, defaults to None
        :type id: str, optional

        """
        self.m_itemId = id
        return


@DisplayerCategory.DISPLAY
class DisplayerItemPlaceholder(DisplayerItem):
    """
    Specialized display item to set a placeholder with an id which can be filled later.
    
    Useful for creating dynamic content areas that can be updated via JavaScript.
    """

    def __init__(self, id: str, data: str = "") -> None:
        """
        Initialize a placeholder item.
        
        Args:
            id: Unique identifier for the placeholder
            data: Initial placeholder content (default: "")
            
        Example:
            >>> placeholder = DisplayerItemPlaceholder(id="dynamic_area", data="Loading...")
        """
        super().__init__(DisplayerItems.PLACEHOLDER)
        self.m_id = id
        self.m_data = data
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample placeholder."""
        return cls(id="test_placeholder", data="Initial placeholder data")


@DisplayerCategory.DISPLAY
class DisplayerItemAlert(DisplayerItem):
    """
    Specialized display item to display an alert with a Bootstrap style.
    
    Alerts are used to provide feedback messages to users with different
    color schemes based on the alert type (success, warning, danger, info).
    """

    def __init__(self, text: str, highlightType: BSstyle = BSstyle.SUCCESS) -> None:
        """
        Initialize an alert item.
        
        Args:
            text: The alert message text
            highlightType: The Bootstrap style for the alert (default: BSstyle.SUCCESS)
                          Determines the color scheme of the alert
            
        Example:
            >>> alert = DisplayerItemAlert(text="Operation completed!", highlightType=BSstyle.SUCCESS)
            >>> warning = DisplayerItemAlert(text="Please check your input", highlightType=BSstyle.WARNING)
        """
        super().__init__(DisplayerItems.ALERT)
        self.m_text = text
        self.m_style = highlightType.value

    def setText(self, text: str):
        """Update the alert text."""
        self.m_text = text
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample alert."""
        return cls(text="This is a test alert message", highlightType=BSstyle.WARNING)


@DisplayerCategory.DISPLAY
class DisplayerItemText(DisplayerItem):
    """
    Specialized display item to display a simple line of text.
    
    Basic text display component for showing static or dynamic text content.
    """

    def __init__(self, text: str) -> None:
        """
        Initialize a text display item.
        
        Args:
            text: The text content to display
            
        Example:
            >>> text_item = DisplayerItemText(text="Hello, World!")
        """
        super().__init__(DisplayerItems.TEXT)
        self.m_text = text
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample text."""
        return cls(text="Sample DisplayerItemText")

@DisplayerCategory.INPUT
class DisplayerItemHidden(DisplayerItem):
    """
    Specialized display item for a hidden form field.
    
    Hidden fields are not visible to the user but their values are submitted with forms.
    """

    def __init__(self, id: str, value: str = None) -> None:
        """
        Initialize a hidden input field.
        
        Args:
            id: Unique identifier for the hidden field
            value: The value to store in the hidden field (default: None)
            
        Example:
            >>> hidden = DisplayerItemHidden(id="user_id", value="12345")
        """
        super().__init__(DisplayerItems.INHIDDEN)
        self.m_value = value
        self.m_id = id
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample hidden field."""
        return cls(id="test_hidden", value="hidden_value")


@DisplayerCategory.BUTTON
class DisplayerItemIconLink(DisplayerItem):
    """Specialized display item to display a clickable icon link."""

    def __init__(
        self,
        id: str,
        text: str,
        icon: str,
        link: str = "",
        parameters: list = None,
        color: BSstyle = BSstyle.PRIMARY,
    ) -> None:
        """
        Initialize an icon link item.
        
        Args:
            id: Unique identifier for the icon link
            text: Tooltip or accessibility text for the icon
            icon: MDI icon name (without 'mdi-' prefix)
            link: Flask endpoint or URL (default: "")
                 Can be empty to display icon without link
            parameters: GET parameters to append to the link (default: None)
                       List of strings like ["param1=value1", "param2=value2"]
            color: Bootstrap style for icon color (default: BSstyle.PRIMARY)
            
        Example:
            >>> iconlink = DisplayerItemIconLink(
            ...     id="edit_icon",
            ...     text="Edit Item",
            ...     icon="pencil",
            ...     link="edit_page",
            ...     parameters=["item_id=42"],
            ...     color=BSstyle.WARNING
            ... )
        """
        super().__init__(DisplayerItems.ICONLINK)
        self.m_text = text
        self.m_id = id
        self.m_data = link
        self.m_icon = icon
        self.m_parameters = parameters
        self.m_style = color.value
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample icon link."""
        return cls(id="test_icon_link", text="View Details", icon="information", 
                   link="#details", parameters=["id=123", "action=view"], color=BSstyle.PRIMARY)
    
@DisplayerCategory.BUTTON
class DisplayerItemButtonLink(DisplayerItem):
    """Specialized display item to display a link icon"""

    def __init__(
        self,
        id: str,
        text: str,
        icon: str,
        link: str = "",
        parameters: list = None,
        color: BSstyle = BSstyle.PRIMARY,
    ) -> None:
        """
        Initialize a button link item.
        
        Args:
            id: Unique identifier for the button
            text: Button text content
            icon: MDI icon name (without 'mdi-' prefix)
            link: Flask endpoint or URL to link to
            parameters: GET parameters to append to the link (default: None)
            color: Bootstrap style for button color (default: BSstyle.PRIMARY)
            
        Example:
            >>> button = DisplayerItemButtonLink(
            ...     id="submit_btn",
            ...     text="Submit",
            ...     icon="check",
            ...     link="process_form",
            ...     parameters=["form_id=123"],
            ...     color=BSstyle.SUCCESS
            ... )
        """
        super().__init__(DisplayerItems.BUTTONLINK)
        self.m_text = text
        self.m_id = id
        self.m_data = link
        self.m_icon = icon
        self.m_parameters = parameters
        self.m_style = color.value
        return

    def display(self, container: list, parent_id: str = None) -> None:
        """Add button to container with icon and parameters."""
        super().display(container, parent_id)
        container[-1]["icon"] = self.m_icon
        container[-1]["parameters"] = self.m_parameters
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample button link."""
        return cls(id="test_button_link", text="Submit Form", icon="check", 
                   link="#action", parameters=["form_id=456"], color=BSstyle.SUCCESS)


@DisplayerCategory.BUTTON
class DisplayerItemButton(DisplayerItem):
    """Specialized display item to display a simple button."""

    def __init__(self, id: str, text: str, focus: bool = False) -> None:
        """
        Initialize a simple button item.
        
        Args:
            id: Unique identifier for the button
            text: Button label text
            focus: Whether the button should have focus on page load (default: False)
            
        Example:
            >>> button = DisplayerItemButton(id="confirm_btn", text="Confirm", focus=True)
        """
        super().__init__(DisplayerItems.BUTTON)
        self.m_text = text
        self.m_id = id
        self.m_focus = focus
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample button."""
        return cls(id="test_button", text="Click Me", focus=False)
    
@DisplayerCategory.BUTTON
class DisplayerItemModalButton(DisplayerItem):
    """Specialized display item to display a button that opens a modal dialog."""

    def __init__(self, text: str, link: str) -> None:
        """
        Initialize a modal trigger button.
        
        Args:
            text: Button label text
            link: Flask route that returns the modal content
            
        Example:
            >>> modal_btn = DisplayerItemModalButton(text="Show Details", link="modal_details")
        """
        super().__init__(DisplayerItems.MODALBUTTON)
        self.m_text = text
        self.m_path = link
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample modal button."""
        return cls(text="Open Modal", link="test_modal_route")
    
@DisplayerCategory.BUTTON
class DisplayerItemModalLink(DisplayerItem):
    """Specialized display item to display an icon link that opens a modal dialog."""

    def __init__(
        self,
        text: str,
        icon: str,
        link: str = "",
        color: BSstyle = BSstyle.PRIMARY,
    ) -> None:
        """
        Initialize a modal trigger icon link.
        
        Args:
            text: Tooltip text for the icon link
            icon: MDI icon name (without 'mdi-' prefix)
            link: Flask route that returns the modal content (default: "")
            color: Bootstrap style for the icon color (default: BSstyle.PRIMARY)
            
        Example:
            >>> modal_link = DisplayerItemModalLink(
            ...     text="View Details",
            ...     icon="information-outline",
            ...     link="modal_info",
            ...     color=BSstyle.INFO
            ... )
        """
        super().__init__(DisplayerItems.MODALLINK)
        self.m_text = text
        self.m_path = link
        self.m_icon = icon
        self.m_style = color.value
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample modal link."""
        return cls(text="Info", icon="information-outline", link="", color=BSstyle.INFO)


@DisplayerCategory.DISPLAY
class DisplayerItemBadge(DisplayerItem):
    """Specialized display item to display a badge with a color."""

    def __init__(self, text: str, highlightType: BSstyle = BSstyle.SUCCESS) -> None:
        """
        Initialize a badge item.
        
        Args:
            text: The badge text content
            highlightType: The Bootstrap style for the badge color (default: BSstyle.SUCCESS)
                          Determines the color scheme of the badge
                          
        Example:
            >>> badge = DisplayerItemBadge(text="New", highlightType=BSstyle.PRIMARY)
        """
        super().__init__(DisplayerItems.BADGE)
        self.m_text = text
        self.m_style = highlightType.value

    def setText(self, text: str):
        """Update the badge text."""
        self.m_text = text
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample badge."""
        return cls(text="Status: Active", highlightType=BSstyle.SUCCESS)


@DisplayerCategory.BUTTON
class DisplayerItemDownload(DisplayerItem):
    """Specialized display item to display a download button."""

    def __init__(self, id: str, text: str, link) -> None:
        """
        Initialize a download button.
        
        Args:
            id: Unique identifier for the button
            text: Button label text
            link: URL or path to the file to download
            
        Example:
            >>> download = DisplayerItemDownload(id="dl_report", text="Download Report", link="/files/report.pdf")
        """
        super().__init__(DisplayerItems.DOWNLOAD)
        self.m_text = text
        self.m_id = id
        self.m_data = link

        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample download button."""
        # Use test_disp.item_page Flask endpoint
        return cls(id="test_download", text="Download File", link="test_disp.item_page")


@DisplayerCategory.MEDIA
class DisplayerItemImage(DisplayerItem):
    """Specialized display item to display an image."""

    def __init__(self, height: str, link: str, endpoint: str = None, path: str = None) -> None:
        """
        Initialize an image item.
        
        Args:
            height: The height of the image (CSS value, e.g., "200px", "50%")
            link: URL to the image (can be full HTTP address or filename)
            endpoint: Endpoint name from site_conf for local files (default: None)
            path: Path relative to the endpoint for local files (default: None)
            
        Example:
            >>> # Remote image
            >>> img1 = DisplayerItemImage(height="300px", link="https://example.com/image.jpg")
            >>> # Local image
            >>> img2 = DisplayerItemImage(height="200px", link="logo.png", endpoint="static", path="images")
        """
        super().__init__(DisplayerItems.IMAGE)
        self.m_data = height
        self.m_value = link
        self.m_path = path
        self.m_endpoint = endpoint

        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample image."""
        return cls(height="200px", link="https://tse3.mm.bing.net/th/id/OIP.GGAs1O-ZmfBJGBCDcj0KpgHaDd?rs=1&pid=ImgDetMain", endpoint=None, path=None)

@DisplayerCategory.MEDIA
class DisplayerItemFile(DisplayerItem):
    """Specialized display item to display a file link with metadata."""

    def __init__(self, link: str, endpoint: str = None, path: str = None, text: str = None, creation_date: str = None) -> None:
        """
        Initialize a file item.
        
        Args:
            link: Filename or URL to the file
            endpoint: Endpoint name from site_conf for local files (default: None)
            path: Path relative to the endpoint for local files (default: None)
            text: Display text or description for the file (default: None)
            creation_date: File creation date string (default: None)
            
        Example:
            >>> file = DisplayerItemFile(
            ...     link="report.pdf",
            ...     endpoint="static",
            ...     path="documents",
            ...     text="Annual Report 2024",
            ...     creation_date="2024-01-15"
            ... )
        """
        super().__init__(DisplayerItems.FILE)
        self.m_text = text
        self.m_date = creation_date
        self.m_value = link
        self.m_path = path
        self.m_endpoint = endpoint
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample file."""
        return cls(link="test_document.pdf", endpoint="common", path="/files", 
                   text="Sample Document", creation_date="2024-01-15")
    
@DisplayerCategory.INPUT
class DisplayerItemInputBox(DisplayerItem):
    """Specialized display to display an input checkbox."""

    def __init__(self, id: str, text: str = None, value: bool = None) -> None:
        """
        Initialize a checkbox input.
        
        Args:
            id: Unique identifier for the checkbox
            text: Label text for the checkbox (default: None)
            value: Initial checked state (default: None)
            
        Example:
            >>> checkbox = DisplayerItemInputBox(id="agree_terms", text="I agree to terms", value=False)
        """
        super().__init__(DisplayerItems.INBOX)
        self.m_text = text
        self.m_value = value
        self.m_id = id
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample checkbox."""
        return cls(id="test_checkbox", text="Enable notifications", value=True)


@DisplayerCategory.MEDIA
class DisplayerItemGraph(DisplayerItem):
    """Specialized display to display a graph using ApexCharts."""

    def __init__(self, id: str, text: str = None, x: list = [], y: list = [], data_type="date") -> None:
        """
        Initialize a graph item.
        
        Args:
            id: Unique identifier for the graph element
            text: Optional title or description text (default: None)
            x: List of x-axis values (default: [])
            y: List of y-axis data values (default: [])
            data_type: Data type for x-axis, e.g., "date", "numeric", "category" (default: "date")
                      See ApexCharts documentation for available types
                      
        Example:
            >>> graph = DisplayerItemGraph(
            ...     id="sales_chart",
            ...     text="Monthly Sales",
            ...     x=["2024-01", "2024-02", "2024-03"],
            ...     y=[100, 150, 120],
            ...     data_type="date"
            ... )
        """
        super().__init__(DisplayerItems.GRAPH)
        self.m_text = text
        self.m_id = id

        self.m_graphx = x
        self.m_graphy = y
        self.m_datatype = data_type
        return

    @classmethod
    def get_required_resources(cls) -> list:
        """Graph requires ApexCharts library."""
        return ['apexcharts']

    def display(self, container: list, parent_id: str = None) -> None:
        """Add graph to container with chart configuration."""
        super().display(container, parent_id)
        container[-1]["id"] = self.m_id.replace(" ", "_")
        container[-1]["graph_x"] = self.m_graphx
        container[-1]["graph_y"] = self.m_graphy
        container[-1]["graph_type"] = self.m_datatype
        container[-1]["id"] = container[-1]["id"].replace(".", "")  # Forbidden in javascript variables
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample graph."""
        # y should be dict of series name -> list of values matching x length
        return cls(id="test_graph", text="Sample Graph", 
                   x=[1640995200000, 1641081600000, 1641168000000],  # Unix timestamps for date type
                   y={"Series1": [10, 25, 15], "Series2": [15, 30, 20]}, 
                   data_type="date")


@DisplayerCategory.INPUT
class DisplayerItemInputFileExplorer(DisplayerItem):
    """Specialized display to display an input file explorer with multiple file categories."""

    def __init__(
        self,
        id: str,
        text: str = None,
        files: list = [],
        title: list = [],
        icons: list = [],
        classes: list = [],
        hiddens: list = [],
    ) -> None:
        """
        Initialize a file explorer input.
        
        Args:
            id: Unique identifier for the file explorer element
            text: Optional accompanying text or label (default: None)
            files: List of file lists for each category (default: [])
                  Each element is a list of files for one category
            title: List of titles for each file category (default: [])
            icons: List of MDI icon names for each category (default: [])
                  Icon names without 'mdi-' prefix
            classes: List of Bootstrap style classes for each category (default: [])
                    e.g., "primary", "success", "danger"
            hiddens: List of boolean values indicating if category is collapsible (default: [])
                    True means the category has a collapse button
                    
        Example:
            >>> explorer = DisplayerItemInputFileExplorer(
            ...     id="file_manager",
            ...     text="Upload Files",
            ...     files=[["doc1.pdf", "doc2.docx"], ["img1.jpg"]],
            ...     title=["Documents", "Images"],
            ...     icons=["file-document", "file-image"],
            ...     classes=["primary", "success"],
            ...     hiddens=[False, True]
            ... )
        """
        super().__init__(DisplayerItems.INFILEEXPLORER)
        self.m_text = text
        self.m_id = id

        self.m_explorerFiles = files
        self.m_explorerTitles = title
        self.m_explorerIcons = icons
        self.m_explorerClasses = classes
        self.m_explorerHiddens = hiddens
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample file explorer."""
        return cls(id="test_fileexplorer", text="File Explorer", 
                   files=[["file1.txt", "file2.pdf"], ["image1.png"]],
                   title=["Documents", "Images"],
                   icons=["file-document", "file-image"],
                   classes=["primary", "success"],
                   hiddens=[False, True])

    def display(self, container: list, parent_id: str = None) -> None:
        """Add file explorer to container with all category configurations."""
        super().display(container, parent_id)
        container[-1]["explorer_files"] = self.m_explorerFiles
        container[-1]["explorer_titles"] = self.m_explorerTitles
        container[-1]["explorer_icons"] = self.m_explorerIcons
        container[-1]["explorer_classes"] = self.m_explorerClasses
        container[-1]["explorer_hiddens"] = self.m_explorerHiddens
        return

@DisplayerCategory.INPUT
class DisplayerItemInputCascaded(DisplayerItem):
    """Specialized display to have multiple select choices where each level depends on the previous one."""

    def __init__(self, ids: list, text: str = None, value: list = None, choices: list = [], level: int = -1) -> None:
        """
        Initialize a cascaded select input.
        
        Args:
            ids: List of unique identifiers for each cascade level
            text: Optional label text (default: None)
            value: Current selected values for each level (default: None)
                  List with one value per cascade level
            choices: Possible choices for each cascade level (default: [])
                    Nested structure where each level's choices depend on parent selection
            level: Specific level to display, or -1 to display all levels (default: -1)
                  If value exceeds available levels, it's clamped to max level
                  
        Example:
            >>> cascaded = DisplayerItemInputCascaded(
            ...     ids=["country", "state", "city"],
            ...     text="Select Location",
            ...     value=["USA", "California", "San Francisco"],
            ...     choices={
            ...         "USA": {
            ...             "California": ["San Francisco", "Los Angeles"],
            ...             "Texas": ["Houston", "Dallas"]
            ...         },
            ...         "Canada": {
            ...             "Ontario": ["Toronto", "Ottawa"]
            ...         }
            ...     },
            ...     level=-1
            ... )
        """
        super().__init__(DisplayerItems.INCASCADED)
        self.m_text = text
        self.m_value = value
        self.m_ids = ids
        for items in choices:
            if isinstance(items, list):
                items.sort()
        self.m_data = choices
        if level > len(choices):
            level = len(choices)
        self.m_level = level
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample cascaded select."""
        # Cascaded needs nested dict structure where each key contains the next level's dict
        return cls(ids=["level1", "level2", "level3"], text="Cascaded Selection",
                   value=["category1", "subcategory2", "item3"],
                   choices={
                       "category1": {
                           "subcategory1": {"item1": {}, "item2": {}},
                           "subcategory2": {"item3": {}, "item4": {}}
                       },
                       "category2": {
                           "subcategory3": {"item5": {}, "item6": {}}
                       }
                   },
                   level=-1)

@DisplayerCategory.INPUT
class DisplayerItemInputSelect(DisplayerItem):
    """Specialized display to display an input select box."""

    def __init__(self, id: str, text: str = None, value: bool = None, choices: list = [], tooltips: list = []) -> None:
        """
        Initialize a select dropdown input.
        
        Args:
            id: Unique identifier for the select element
            text: Optional label text (default: None)
            value: Currently selected value (default: None)
            choices: List of selectable options (default: [])
                    Automatically sorted alphabetically
            tooltips: List of tooltip texts for each choice (default: [])
                     Must match length of choices for proper pairing
                     
        Example:
            >>> select = DisplayerItemInputSelect(
            ...     id="priority",
            ...     text="Select Priority",
            ...     value="medium",
            ...     choices=["low", "medium", "high"],
            ...     tooltips=["Low priority", "Medium priority", "High priority"]
            ... )
        """
        super().__init__(DisplayerItems.SELECT)
        self.m_text = text
        self.m_value = value
        self.m_id = id
        
        # Ensure choices and tooltips have the same length before zipping
        if isinstance(choices, list) and isinstance(tooltips, list):
            if len(choices) == len(tooltips) and len(choices) > 0:
                combined = list(zip(choices, tooltips))
                combined.sort(key=lambda pair: pair[0])
                # Unzip safely
                choices, tooltips = map(list, zip(*combined))
            elif len(choices) > 0:
                choices.sort()
        
        self.m_data = choices
        self.m_tooltips = tooltips
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample select."""
        return cls(id="test_select", text="Choose an option", value="option2",
                   choices=["option1", "option2", "option3"], 
                   tooltips=["First option", "Second option", "Third option"])


@DisplayerCategory.INPUT
class DisplayerItemInputMultiSelect(DisplayerItem):
    """Specialized display to display a multiple select with a possibility to add them on the fly."""

    def __init__(self, id: str, text: str = None, value: bool = None, choices: list = []) -> None:
        """
        Initialize a multi-select input.
        
        Args:
            id: Unique identifier for the multi-select element
            text: Optional label text (default: None)
            value: Currently selected values (default: None)
            choices: List of selectable options (default: [])
                    Automatically sorted alphabetically
                    Allows adding new options dynamically
                    
        Example:
            >>> multiselect = DisplayerItemInputMultiSelect(
            ...     id="tags",
            ...     text="Select Tags",
            ...     value=["tag1", "tag3"],
            ...     choices=["tag1", "tag2", "tag3", "tag4"]
            ... )
        """
        super().__init__(DisplayerItems.INMULTISELECT)
        choices.sort()
        self.m_text = text
        self.m_value = value
        self.m_id = id
        self.m_data = choices
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample multi-select."""
        return cls(id="test_multiselect", text="Select multiple items", 
                   value=["item2", "item3"], choices=["item1", "item2", "item3", "item4"])


@DisplayerCategory.INPUT
class DisplayerItemInputMapping(DisplayerItem):
    """Specialized display to display a mapping with a possibility to add them on the fly."""

    def __init__(self, id: str, text: str = None, value: bool = None, choices: list = []) -> None:
        """
        Initialize a mapping input for key-value pairs.
        
        Args:
            id: Unique identifier for the mapping element
            text: Optional label text (default: None)
            value: Current mapping dictionary (default: None)
                  Keys map to lists of selected choices
            choices: List of available options to map (default: [])
                    Automatically sorted alphabetically
                    
        Example:
            >>> mapping = DisplayerItemInputMapping(
            ...     id="category_mapping",
            ...     text="Map Items to Categories",
            ...     value={"Category A": ["item1", "item2"], "Category B": ["item3"]},
            ...     choices=["item1", "item2", "item3", "item4"]
            ... )
        """
        super().__init__(DisplayerItems.INMAPPING)
        choices.sort()
        self.m_text = text
        self.m_value = value
        self.m_id = id
        self.m_data = choices
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample mapping."""
        return cls(id="test_mapping", text="Key-Value Mapping", 
                   value={"Section A": ["option1", "option2"], "Section B": ["option3"]}, 
                   choices=["option1", "option2", "option3"])


@DisplayerCategory.INPUT
class DisplayerItemInputListSelect(DisplayerItem):
    """Specialized display to display a set of list select."""

    def __init__(self, id: str, text: str = None, value: bool = None, choices: list = []) -> None:
        """
        Initialize a list select input.
        
        Args:
            id: Unique identifier for the list select element
            text: Optional label text (default: None)
            value: Currently selected items from the lists (default: None)
            choices: List of available options (default: [])
                    Automatically sorted alphabetically
                    
        Example:
            >>> listselect = DisplayerItemInputListSelect(
            ...     id="item_list",
            ...     text="Select Items",
            ...     value=["item2", "item4"],
            ...     choices=["item1", "item2", "item3", "item4"]
            ... )
        """
        super().__init__(DisplayerItems.INLISTSELECT)
        choices.sort()
        self.m_text = text
        self.m_value = value
        self.m_id = id
        self.m_data = choices
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample list select."""
        return cls(id="test_listselect", text="Select from lists", 
                   value=["list1_item2", "list2_item1"], 
                   choices=["list1_item1", "list1_item2", "list2_item1", "list2_item2"])


@DisplayerCategory.INPUT
class DisplayerItemInputTextSelect(DisplayerItem):
    """Specialized display to display a mapping for a text and a selection for the user."""

    def __init__(self, id: str, text: str = None, value: str = None, choices: list = []) -> None:
        """
        Initialize a text-select input combining text fields with selections.
        
        Args:
            id: Unique identifier for the element
            text: Optional label text (default: None)
            value: Current value as list of [text, selection] pairs (default: None)
                  Each pair combines a text input with a dropdown choice
            choices: List of available options for the select portion (default: [])
                    Automatically sorted alphabetically
                    
        Example:
            >>> textselect = DisplayerItemInputTextSelect(
            ...     id="config_pairs",
            ...     text="Configuration",
            ...     value=[["Setting 1", "high"], ["Setting 2", "medium"]],
            ...     choices=["low", "medium", "high"]
            ... )
        """
        super().__init__(DisplayerItems.INTEXTSELECT)
        choices.sort()
        self.m_text = text
        self.m_value = value
        self.m_id = id
        self.m_data = choices
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample text-select pairs (list of [text, select])."""
        return cls(id="test_textselect", text="Text and Selection",
                   value=[["First text", "option2"], ["Second text", "option1"]],
                   choices=["option1", "option2", "option3"])


@DisplayerCategory.INPUT
class DisplayerItemInputSelectText(DisplayerItem):
    """Specialized display to display a mapping for a selection followed by a text input."""

    def __init__(self, id: str, text: str = None, value: str = None, choices: list = []) -> None:
        """
        Initialize a select-text input combining selection with text.
        
        Args:
            id: Unique identifier for the element
            text: Optional label text (default: None)
            value: Current value as list of [selection, text] pairs (default: None)
                  Each pair combines a dropdown choice with a text input
            choices: List of available options for the select portion (default: [])
                    Automatically sorted alphabetically
                    
        Example:
            >>> selecttext = DisplayerItemInputSelectText(
            ...     id="reason_notes",
            ...     text="Select Reason and Add Notes",
            ...     value=[["technical", "Server was down"], ["user_error", "Wrong password"]],
            ...     choices=["technical", "user_error", "planned"]
            ... )
        """
        super().__init__(DisplayerItems.INSELECTTEXT)
        choices.sort()
        self.m_text = text
        self.m_value = value
        self.m_id = id
        self.m_data = choices
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample select-text pairs (list of [select, text])."""
        return cls(id="test_selecttext", text="Select and describe", 
                   value=[["option2", "Description for option 2"], ["option1", "Another description"]],
                   choices=["option1", "option2", "option3"])


@DisplayerCategory.INPUT
class DisplayerItemInputDualTextSelect(DisplayerItem):
    """Specialized display to display a mapping for two text inputs followed by a selection."""

    def __init__(self, id: str, text: str = None, value: str = None, choices: list = []) -> None:
        """
        Initialize a dual text-select input.
        
        Args:
            id: Unique identifier for the element
            text: Optional label text (default: None)
            value: Current value as list of [text1, text2, selection] triplets (default: None)
                  Each triplet combines two text inputs with a dropdown choice
            choices: List of available options for the select portion (default: [])
                    Automatically sorted alphabetically
                    
        Example:
            >>> dualtextselect = DisplayerItemInputDualTextSelect(
            ...     id="metric_config",
            ...     text="Configure Metrics",
            ...     value=[["CPU", "90", "critical"], ["RAM", "80", "warning"]],
            ...     choices=["info", "warning", "critical"]
            ... )
        """
        super().__init__(DisplayerItems.INDUALTEXTSELECT)
        choices.sort()
        self.m_text = text
        self.m_value = value
        self.m_id = id
        self.m_data = choices
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample dual text-select (list of [text1, text2, select])."""
        return cls(id="test_dualtextselect", text="Dual text with select", 
                   value=[["First text", "Second text", "choice2"], ["Another first", "Another second", "choice1"]],
                   choices=["choice1", "choice2", "choice3"])


@DisplayerCategory.INPUT
class DisplayerItemInputDualSelectText(DisplayerItem):
    """Specialized display to display a mapping for two selections followed by a text input."""

    def __init__(self, id: str, text: str = None, value: str = None, choices: list = []) -> None:
        """
        Initialize a dual select-text input.
        
        Args:
            id: Unique identifier for the element
            text: Optional label text (default: None)
            value: Current value as list of [select1, select2, text] triplets (default: None)
                  Each triplet combines two dropdown choices with a text input
            choices: List of available options for both select portions (default: [])
                    Automatically sorted alphabetically
                    
        Example:
            >>> dualselecttext = DisplayerItemInputDualSelectText(
            ...     id="rule_config",
            ...     text="Define Rules",
            ...     value=[["condition1", "action1", "Comment"], ["condition2", "action2", "Note"]],
            ...     choices=["condition1", "condition2", "action1", "action2"]
            ... )
        """
        super().__init__(DisplayerItems.INDUALSELECTTEXT)
        choices.sort()
        self.m_text = text
        self.m_value = value
        self.m_id = id
        self.m_data = choices
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample dual select-text (list of [select1, select2, text])."""
        return cls(id="test_dualselecttext", text="Dual select with text", 
                   value=[["opt1", "opt2", "Combined result"], ["opt2", "opt3", "Another combination"]],
                   choices=["opt1", "opt2", "opt3"])


@DisplayerCategory.INPUT
class DisplayerItemInputTextText(DisplayerItem):
    """Specialized display to display a mapping with two text inputs."""

    def __init__(self, id: str, text: str = None, value: str = None) -> None:
        """
        Initialize a text-text input pair.
        
        Args:
            id: Unique identifier for the element
            text: Optional label text (default: None)
            value: Current value as list of [text1, text2] pairs (default: None)
                  Each pair combines two related text inputs
                  
        Example:
            >>> texttext = DisplayerItemInputTextText(
            ...     id="key_value_pairs",
            ...     text="Configuration",
            ...     value=[["hostname", "server1.example.com"], ["port", "8080"]]
            ... )
        """
        super().__init__(DisplayerItems.INTEXTTEXT)
        self.m_text = text
        self.m_value = value
        self.m_id = id
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample text-text pairs (list of [text1, text2])."""
        return cls(id="test_texttext", text="Two text fields", 
                   value=[["First field", "Second field"], ["Another first", "Another second"]])


@DisplayerCategory.INPUT
class DisplayerItemInputListText(DisplayerItem):
    """Specialized display to display a list of input text fields."""

    def __init__(self, id: str, text: str = None, value: dict = None) -> None:
        """
        Initialize a list text input.
        
        Args:
            id: Unique identifier for the element
            text: Optional label text (default: None)
            value: Current value as dictionary mapping item keys to text values (default: None)
                  Each key-value pair creates a separate text input
                  
        Example:
            >>> listtext = DisplayerItemInputListText(
            ...     id="settings",
            ...     text="Application Settings",
            ...     value={"api_key": "abc123", "timeout": "30", "retries": "3"}
            ... )
        """
        super().__init__(DisplayerItems.INLISTTEXT)
        self.m_text = text
        self.m_value = value
        self.m_id = id
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample list of texts."""
        return cls(id="test_listtext", text="List of text inputs", 
                   value={"item1": "Text 1", "item2": "Text 2", "item3": "Text 3"})


@DisplayerCategory.INPUT
class DisplayerItemInputNumeric(DisplayerItem):
    """Specialized display to display an input number field."""

    def __init__(self, id: str, text: str = None, value: float = None, focus: bool = False) -> None:
        """
        Initialize a numeric input.
        
        Args:
            id: Unique identifier for the input element
            text: Optional label text (default: None)
            value: Initial numeric value (default: None)
            focus: Whether the input should have focus on page load (default: False)
            
        Example:
            >>> numeric = DisplayerItemInputNumeric(
            ...     id="quantity",
            ...     text="Enter Quantity",
            ...     value=100.5,
            ...     focus=True
            ... )
        """
        super().__init__(DisplayerItems.INNUM)
        self.m_text = text
        self.m_value = value
        self.m_id = id
        self.m_focus = focus
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample numeric input."""
        return cls(id="test_numeric", text="Enter a number", value=42.5, focus=False)


@DisplayerCategory.INPUT
class DisplayerItemInputDate(DisplayerItem):
    """Specialized display to display an input date.
    Date shall be in format YYYY-MM-DD or YYYY-MM-DDT000:00 if the minute and hour is also needed."""

    def __init__(self, id: str, text: str = None, value: str = None) -> None:
        """
        Initialize a date input.
        
        Args:
            id: Unique identifier for the input element
            text: Optional label text (default: None)
            value: Initial date value in format YYYY-MM-DD or YYYY-MM-DDTHH:MM (default: None)
                  
        Example:
            >>> date = DisplayerItemInputDate(
            ...     id="start_date",
            ...     text="Select Start Date",
            ...     value="2024-01-15"
            ... )
            >>> datetime = DisplayerItemInputDate(
            ...     id="appointment",
            ...     text="Appointment Time",
            ...     value="2024-01-15T14:30"
            ... )
        """
        super().__init__(DisplayerItems.INDATE)
        self.m_text = text
        self.m_value = value
        self.m_id = id
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample date input."""
        return cls(id="test_date", text="Select a date", value="2024-01-15")


@DisplayerCategory.INPUT
class DisplayerItemInputText(DisplayerItem):
    """Specialized display to display a multi-line text area input."""

    def __init__(self, id: str, text: str = None, value: str = None) -> None:
        """
        Initialize a text area input.
        
        Args:
            id: Unique identifier for the textarea element
            text: Optional label text (default: None)
            value: Initial text content (default: None)
                  Supports multi-line text input
                  
        Example:
            >>> textarea = DisplayerItemInputText(
            ...     id="description",
            ...     text="Enter Description",
            ...     value="This is a multi-line\\ntext area input"
            ... )
        """
        super().__init__(DisplayerItems.INTEXT)
        self.m_text = text
        self.m_value = value
        self.m_id = id
        return
    
    @classmethod
    def get_required_resources(cls) -> list:
        """Text input requires TinyMCE library for rich text editing."""
        return ['tinymce']
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample text input."""
        return cls(id="test_text", text="Enter text", value="Sample text value")
    
@DisplayerCategory.INPUT
class DisplayerItemInputTextJS(DisplayerItem):
    """Specialized display to display an input text with a JS function execution on change."""

    def __init__(self, id: str, text: str = None, value: str = None, js: str = None, focus = False) -> None:
        """
        Initialize a text input with JavaScript onChange handler.
        
        Args:
            id: Unique identifier for the input element
            text: Optional label text (default: None)
            value: Initial text value (default: None)
            js: JavaScript code to execute on change event (default: None)
               Code has access to 'this' referring to the input element
            focus: Whether the input should have focus on page load (default: False)
            
        Example:
            >>> textjs = DisplayerItemInputTextJS(
            ...     id="uppercase_input",
            ...     text="Auto Uppercase",
            ...     value="hello",
            ...     js="this.value = this.value.toUpperCase();",
            ...     focus=True
            ... )
        """
        super().__init__(DisplayerItems.INTEXTJS)
        self.m_text = text
        self.m_value = value
        self.m_id = id
        self.m_data = js
        self.m_focus = focus
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample text-JS input."""
        # JS function to capitalize input
        js_code = "this.value = this.value.toUpperCase();"
        return cls(id="test_textjs", text="Text with JS (auto-capitalize)", value="type here", 
                   js=js_code, focus=False)
    
@DisplayerCategory.INPUT
class DisplayerItemInputString(DisplayerItem):
    """
    Specialized display item for a text string input field.
    
    Standard single-line text input for collecting string data from users.
    """

    def __init__(self, id: str, text: str = None, value: str = None, focus: bool = False) -> None:
        """
        Initialize a string input field.
        
        Args:
            id: Unique identifier for the input field
            text: Label text displayed above the input (default: None)
            value: Pre-filled value in the input field (default: None)
            focus: Whether this field should receive focus on page load (default: False)
            
        Example:
            >>> name_input = DisplayerItemInputString(
            ...     id="user_name",
            ...     text="Enter your name",
            ...     value="John Doe",
            ...     focus=True
            ... )
        """
        super().__init__(DisplayerItems.INSTRING)
        self.m_text = text
        self.m_value = value
        self.m_id = id
        self.m_focus = focus
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample string input."""
        return cls(id="test_string", text="Enter a string", value="Sample string", focus=False)
    
@DisplayerCategory.INPUT
class DisplayerItemInputStringIcon(DisplayerItem):
    """Specialized display to display an input string that also displays an associated MDI icon if valid."""

    def __init__(self, id: str, text: str = None, value: str = None) -> None:
        """
        Initialize a string input with icon preview.
        
        Args:
            id: Unique identifier for the input element
            text: Optional label text (default: None)
            value: Initial value, typically an MDI icon name (default: None)
                  Icon will be displayed if value is a valid MDI icon name
                  
        Example:
            >>> stringicon = DisplayerItemInputStringIcon(
            ...     id="icon_selector",
            ...     text="Choose Icon",
            ...     value="star-outline"
            ... )
        """
        super().__init__(DisplayerItems.INSTRINGICON)
        self.m_text = text
        self.m_value = value
        self.m_id = id
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample string-icon input."""
        return cls(id="test_stringicon", text="Icon String", value="star-outline")


@DisplayerCategory.INPUT
class DisplayerItemInputMultiText(DisplayerItem):
    """Specialized display to display a multi-line text list input."""

    def __init__(self, id: str, text: str = None, value: str = None) -> None:
        """
        Initialize a multi-text input.
        
        Args:
            id: Unique identifier for the input element
            text: Optional label text (default: None)
            value: Initial value as list of text lines (default: None)
                  Each element in the list represents a separate line of text
                  
        Example:
            >>> multitext = DisplayerItemInputMultiText(
            ...     id="todo_list",
            ...     text="Task List",
            ...     value=["Buy groceries", "Call dentist", "Finish report"]
            ... )
        """
        super().__init__(DisplayerItems.INMULTITEXT)
        self.m_text = text
        self.m_value = value
        self.m_id = id
        return
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample multi-line text input."""
        return cls(id="test_multitext", text="Enter multiple lines", 
                   value=["Line 1", "Line 2", "Line 3"])


@DisplayerCategory.INPUT
class DisplayerItemInputFolder(DisplayerItem):
    """Specialized display to display a folder selection input."""

    def __init__(self, id: str, text: str = None) -> None:
        """
        Initialize a folder input.
        
        Args:
            id: Unique identifier for the input element
            text: Optional label text (default: None)
            
        Example:
            >>> folder = DisplayerItemInputFolder(
            ...     id="upload_folder",
            ...     text="Select Upload Folder"
            ... )
        """
        super().__init__(DisplayerItems.INFOLDER)
        self.m_text = text
        self.m_id = id
        return
    
    @classmethod
    def get_required_resources(cls) -> list:
        """Folder input requires FilePond library."""
        return ['filepond']
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample folder input."""
        return cls(id="test_folder", text="Select Folder")

@DisplayerCategory.INPUT
class DisplayerItemInputFile(DisplayerItem):
    """Specialized display to display a file upload input."""

    def __init__(self, id: str, text: str = None) -> None:
        """
        Initialize a file input.
        
        Args:
            id: Unique identifier for the input element
            text: Optional label text (default: None)
            
        Example:
            >>> file = DisplayerItemInputFile(
            ...     id="document_upload",
            ...     text="Upload Document"
            ... )
        """
        super().__init__(DisplayerItems.INFILE)
        self.m_text = text
        self.m_id = id
        return
    
    @classmethod
    def get_required_resources(cls) -> list:
        """File input requires FilePond library."""
        return ['filepond']
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample file input."""
        return cls(id="test_file", text="Select File")
    
@DisplayerCategory.INPUT
class DisplayerItemInputImage(DisplayerItem):
    """Specialized display to display an image upload input box."""

    def __init__(self, id: str, text: str = None) -> None:
        """
        Initialize an image input.
        
        Args:
            id: Unique identifier for the input element
            text: Optional label text (default: None)
            
        Example:
            >>> image = DisplayerItemInputImage(
            ...     id="profile_picture",
            ...     text="Upload Profile Picture"
            ... )
        """
        super().__init__(DisplayerItems.INIMAGE)
        self.m_text = text
        self.m_id = id
        return
    
    @classmethod
    def get_required_resources(cls) -> list:
        """Image input requires FilePond library."""
        return ['filepond']
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample image input."""
        return cls(id="test_image", text="Select Image")

@DisplayerCategory.MEDIA
class DisplayerItemCalendar(DisplayerItem):
    """Specialized display to display a full size calendar using FullCalendar library."""

    def __init__(self, id: str, view: str = "dayGridMonth", events: dict = {}) -> None:
        """
        Initialize a calendar display.
        
        Args:
            id: Unique identifier for the calendar element
            view: FullCalendar view mode (default: "dayGridMonth")
                 Options include: "dayGridMonth", "timeGridWeek", "timeGridDay", "listWeek"
            events: Events to display in FullCalendar format (default: {})
                   Dictionary with event data following FullCalendar's event object structure
                   
        Example:
            >>> calendar = DisplayerItemCalendar(
            ...     id="schedule",
            ...     view="timeGridWeek",
            ...     events={
            ...         "events": [
            ...             {"title": "Meeting", "start": "2024-01-15T10:00:00", "end": "2024-01-15T11:00:00"},
            ...             {"title": "Lunch", "start": "2024-01-15T12:00:00"}
            ...         ]
            ...     }
            ... )
        """
        super().__init__(DisplayerItems.CALENDAR)
        self.m_value = view
        self.m_id = id
        self.m_data = events
        return
    
    @classmethod
    def get_required_resources(cls) -> list:
        """Calendar requires FullCalendar library."""
        return ['fullcalendar']
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample calendar."""
        return cls(id="test_calendar", view="dayGridMonth", 
                   events=[
                       {"title": "Event 1", "start": "2024-01-15"},
                       {"title": "Event 2", "start": "2024-01-20", "end": "2024-01-22"}
                   ])
