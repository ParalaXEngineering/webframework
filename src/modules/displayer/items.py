from typing import Optional, List, Dict, Any, ClassVar, Union

from .core import DisplayerItems, DisplayerCategory, BSstyle


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
        'm_id': 'id',
        'm_css_class': 'css_class',
        'm_width': 'width',
        'm_icon_style': 'icon_style',
    }

    def __init__(self, itemType: DisplayerItems) -> None:
        """Constructor

        :param itemType: The type of item that this display is. Should be used by any child item
        :type itemType: DisplayerItems
        """
        self.m_type = itemType

    @classmethod
    def instantiate_test(cls):
        """Create a test instance of this DisplayerItem with sensible default data.

        Override this method in child classes to provide proper test data.
        Default implementation returns a minimal instance.

        Returns:
            Test instance of this DisplayerItem

        Example override::

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
        """Return list of required resources (vendors) for this displayer item.
        
        Override in child classes to declare dependencies.

        Returns:
            List of resource identifiers

        Example::

            @classmethod
            def get_required_resources(cls):
                return ['datatables', 'sweetalert']
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
            m_ids = getattr(self, "m_ids")
            if parent_id:
                item["id"] = [f"{parent_id}.{id}" for id in m_ids]  # type: ignore[assignment]
            else:
                item["id"] = m_ids  # type: ignore[assignment]
        elif hasattr(self, "m_id"):
            m_id = getattr(self, "m_id")
            if parent_id:
                item["id"] = f"{parent_id}.{m_id}"
            else:
                item["id"] = m_id

        container.append(item)
        return

    def setDisabled(self, disabled: bool = False) -> None:
        """Disable the current item. While the function is always present, it can yield to no result depending on the item

        :param disabled: Disable the item, defaults to False
        :type disabled: bool, optional
        """

        self.m_disabled = disabled
        return

    def setId(self, id: Optional[str] = None) -> None:
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
        """Create test instance with sample placeholder.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(id="test_placeholder", data="Initial placeholder data")


@DisplayerCategory.DISPLAY
class DisplayerItemAlert(DisplayerItem):
    """
    Flexible Bootstrap alert with icon, optional title, and dismissible support.

    Supports two visual styles:
    - fancy_header=True: Two-part alert with colored header bar and badge (legacy style)
    - fancy_header=False: Standard Bootstrap alert (default, recommended)

    Alerts are used to provide feedback messages to users with different
    color schemes based on the alert type (success, warning, danger, info).
    """

    def __init__(
        self, 
        text: str, 
        highlightType: BSstyle = BSstyle.SUCCESS, 
        title: Optional[str] = None, 
        icon: Optional[str] = None,
        id: Optional[str] = None,
        dismissible: bool = False,
        fancy_header: bool = False
    ) -> None:
        """
        Initialize an alert item.

        Args:
            text: The alert message text (HTML supported)
            highlightType: The Bootstrap style for the alert (default: BSstyle.SUCCESS)
                          Determines the color scheme of the alert
            title: Optional title/header for the alert
                  - fancy_header=True: appears as badge/label in header bar
                  - fancy_header=False: appears as bold text before content
            icon: Optional MDI icon name (with or without "mdi-" prefix)
                 Examples: "information", "check-circle", "alert-octagon", "alert"
                 Default: "alert-circle"
            id: Optional unique identifier for the alert (required if dismissible=True)
            dismissible: If True, adds close button (requires id parameter)
            fancy_header: If True, uses two-part layout with colored header bar (legacy style)
                         If False, uses standard Bootstrap alert (default, recommended)

        Example:
            >>> # Standard alert (recommended)
            >>> alert = DisplayerItemAlert(
            ...     text="Operation completed!", 
            ...     highlightType=BSstyle.SUCCESS,
            ...     icon="check-circle"
            ... )
            >>> 
            >>> # Dismissible alert
            >>> warning = DisplayerItemAlert(
            ...     id="warn1",
            ...     text="Please check your input", 
            ...     highlightType=BSstyle.WARNING, 
            ...     title="Warning", 
            ...     icon="alert-octagon",
            ...     dismissible=True
            ... )
            >>> 
            >>> # Fancy header style (legacy)
            >>> info = DisplayerItemAlert(
            ...     text="Important information",
            ...     highlightType=BSstyle.INFO,
            ...     title="Notice",
            ...     icon="information",
            ...     fancy_header=True
            ... )
        """
        super().__init__(DisplayerItems.ALERT)
        self.m_text = text
        self.m_style = highlightType.value if isinstance(highlightType, BSstyle) else highlightType
        self.m_header = title
        self.m_icon = icon if icon is not None else "alert-circle"
        self.m_itemId = id
        self.m_disabled = dismissible
        self.m_fancy_header = fancy_header
        
        # Validation: dismissible alerts require an ID
        if dismissible and not id:
            raise ValueError("Dismissible alerts require an 'id' parameter")

    def setText(self, text: str):
        """Update the alert text.
        
        Args:
            text: The new text content to set.
        """
        self.m_text = text
        return

    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample alert.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(
            text="This is a test alert message", 
            highlightType=BSstyle.WARNING, 
            title="Test Alert", 
            icon="alert-octagon",
            id="test_alert",
            dismissible=False
        )


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
        """Create test instance with sample text.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(text="Sample DisplayerItemText")


@DisplayerCategory.DISPLAY
class DisplayerItemSeparator(DisplayerItem):
    """
    Specialized display item to display a visual separator/divider line.

    Renders a Bootstrap horizontal rule to visually separate content sections.
    """

    def __init__(self) -> None:
        """
        Initialize a separator item.

        Example:
            >>> separator = DisplayerItemSeparator()
        """
        super().__init__(DisplayerItems.SEPARATOR)

    @classmethod
    def instantiate_test(cls):
        """Create test instance of separator.
        
        Returns:
            Instance of the class with test data.
        """
        return cls()


@DisplayerCategory.INPUT
class DisplayerItemHidden(DisplayerItem):
    """
    Specialized display item for a hidden form field.

    Hidden fields are not visible to the user but their values are submitted with forms.
    """

    def __init__(self, id: str, value: Optional[str] = None) -> None:
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
        """Create test instance with sample hidden field.
        
        Returns:
            Instance of the class with test data.
        """
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
        parameters: Optional[list] = None,
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
        """Create test instance with sample icon link.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(id="test_icon_link", text="View Details", icon="information",
                   link="#details", parameters=["id=123", "action=view"], color=BSstyle.PRIMARY)

@DisplayerCategory.BUTTON
class DisplayerItemButton(DisplayerItem):
    """Specialized display item to display a button with optional link and icon support.
    
    This unified button class supports both regular buttons and link buttons,
    providing a consistent interface for all button types. It supports:
    - Regular buttons (no link)
    - Link buttons (with navigation)
    - Icons with flexible layout styles
    - Colors/styles
    - Tooltips
    - Focus control
    """

    class IconStyle:
        """Icon layout styles for buttons."""
        LEFT = "left"              # Icon left of text, same size as text
        TOP = "top"                # Icon above text, larger size
        ICON_ONLY = "icon_only"    # Only icon, no text

    def __init__(
        self,
        id: str,
        text: str,
        icon: Optional[str] = None,
        link: Optional[str] = None,
        parameters: Optional[list] = None,
        color: Optional[BSstyle] = None,
        tooltip: Optional[str] = None,
        focus: bool = False,
        icon_style: Optional[str] = None,
    ) -> None:
        """
        Initialize a unified button item supporting both regular and link buttons.

        Args:
            id: Unique identifier for the button
            text: Button label text (can be empty for icon-only buttons)
            icon: Optional MDI icon name (without 'mdi-' prefix)
            link: Optional Flask endpoint or URL. If None, creates a regular button (default: None)
            parameters: GET parameters to append to the link as a list (default: None)
            color: Optional Bootstrap style for button color (default: None for default styling)
            tooltip: Optional tooltip text to display on hover (default: None)
            focus: Whether the button should have focus on page load (default: False)
            icon_style: Layout style for icon. Options: "left" (inline, same size),
                       "top" (stacked, larger), "icon_only" (icon only).
                       Defaults to "left". (default: None)

        Example:
            >>> # Link button with icon on the left
            >>> button = DisplayerItemButton(
            ...     id="submit_btn",
            ...     text="Submit",
            ...     icon="check",
            ...     link="process_form",
            ...     color=displayer.BSstyle.SUCCESS,
            ...     tooltip="Submit the form"
            ... )
            
            >>> # Button with icon on top
            >>> button = DisplayerItemButton(
            ...     id="action_btn",
            ...     text="Action",
            ...     icon="star",
            ...     color=displayer.BSstyle.PRIMARY,
            ...     icon_style="top"
            ... )
            
            >>> # Icon-only button
            >>> button = DisplayerItemButton(
            ...     id="delete_btn",
            ...     text="Delete",
            ...     icon="trash",
            ...     color=displayer.BSstyle.ERROR,
            ...     icon_style="icon_only"
            ... )
        """
        # Determine button type based on link parameter
        if link is not None:
            button_type = DisplayerItems.BUTTONLINK
        else:
            button_type = DisplayerItems.BUTTON
            
        super().__init__(button_type)
        
        self.m_text = text
        self.m_id = id
        self.m_icon = icon
        self.m_focus = focus
        self.m_tooltips = tooltip
        
        # Link-specific attributes
        self.m_data = link  # Only set if it's a link button
        self.m_parameters = parameters
        
        # Handle color styling
        if color is not None:
            self.m_style = color.value
        else:
            self.m_style = None
        
        # Icon style - default to LEFT (icon beside text)
        if icon_style is None:
            self.m_icon_style = self.IconStyle.LEFT
        else:
            self.m_icon_style = icon_style

    def display(self, container: list, parent_id: Optional[str] = None) -> None:
        """Add button to container with icon and optional link/parameters.
        
        Args:
            container: The container element to display in.
            parent_id: The parent element ID.
        """
        super().display(container, parent_id)
        
        # Add icon if present
        if self.m_icon:
            container[-1]["icon"] = self.m_icon
            container[-1]["icon_style"] = self.m_icon_style
        
        # Add parameters if this is a link button
        if self.m_parameters is not None:
            container[-1]["parameters"] = self.m_parameters
            
        return

    @classmethod
    def instantiate_test(cls):
        """Create test instances with various button configurations.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(
            id="test_button",
            text="Click Me",
            icon="check-circle",
            focus=False,
            tooltip="This is a unified test button",
            color=None,
            icon_style=cls.IconStyle.LEFT
        )

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
        """Create test instance with sample modal button.
        
        Returns:
            Instance of the class with test data.
        """
        # Note: Modal buttons require a Flask route that returns modal content
        # For demo purposes, this shows the structure - in real usage, provide a proper endpoint
        return cls(text="Open Modal (requires endpoint)", link="#")

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
        """Create test instance with sample modal link.
        
        Returns:
            Instance of the class with test data.
        """
        # Note: Modal links require a Flask route that returns modal content
        # For demo purposes, this shows the structure - in real usage, provide a proper endpoint
        return cls(text="Info (requires endpoint)", icon="information-outline", link="#", color=BSstyle.INFO)


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
        """Update the badge text.
        
        Args:
            text: The new text content to set.
        """
        self.m_text = text
        return

    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample badge.
        
        Returns:
            Instance of the class with test data.
        """
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
        """Create test instance with sample download button.
        
        Returns:
            Instance of the class with test data.
        """
        # Use a simple example - in real usage, provide a proper Flask endpoint
        return cls(id="test_download", text="Download File", link="#")


@DisplayerCategory.MEDIA
class DisplayerItemImage(DisplayerItem):
    """Specialized display item to display an image."""

    def __init__(self, height: str, link: str, endpoint: Optional[str] = None, path: Optional[str] = None, css_class: Optional[str] = None, width: Optional[str] = None) -> None:
        """
        Initialize an image item.

        Args:
            height: The height of the image (CSS value, e.g., "200px", "50%")
            link: URL to the image (can be full HTTP address or filename)
            endpoint: Endpoint name from site_conf for local files (default: None)
            path: Path relative to the endpoint for local files (default: None)
            css_class: Additional CSS classes to apply (e.g., "rounded-circle", "img-thumbnail")
            width: The width of the image (CSS value, e.g., "200px", "50%"). If not set, uses auto

        Example:
            >>> # Remote image
            >>> img1 = DisplayerItemImage(height="300px", link="https://example.com/image.jpg")
            >>> # Local image
            >>> img2 = DisplayerItemImage(height="200px", link="logo.png", endpoint="static", path="images")
            >>> # Rounded circular avatar
            >>> img3 = DisplayerItemImage(height="200px", width="200px", link="avatar.jpg", css_class="rounded-circle")
        """
        super().__init__(DisplayerItems.IMAGE)
        self.m_data = height
        self.m_value = link
        self.m_path = path
        self.m_endpoint = endpoint
        self.m_css_class = css_class
        self.m_width = width

        return

    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample image.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(height="200px", link="https://tse3.mm.bing.net/th/id/OIP.GGAs1O-ZmfBJGBCDcj0KpgHaDd?rs=1&pid=ImgDetMain")

@DisplayerCategory.MEDIA
class DisplayerItemFile(DisplayerItem):
    """Specialized display item to display a file link with metadata."""

    def __init__(self, link: str, endpoint: Optional[str] = None, path: Optional[str] = None, text: Optional[str] = None, creation_date: Optional[str] = None) -> None:
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
        """Create test instance with sample file.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(link="test_document.pdf", endpoint="common", path="/files",
                   text="Sample Document", creation_date="2024-01-15")

@DisplayerCategory.INPUT
class DisplayerItemInputBox(DisplayerItem):
    """Specialized display to display an input checkbox."""

    def __init__(self, id: str, text: Optional[str] = None, value: Optional[bool] = None) -> None:
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
        """Create test instance with sample checkbox.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(id="test_checkbox", text="Enable notifications", value=True)


@DisplayerCategory.MEDIA
class DisplayerItemGraph(DisplayerItem):
    """Specialized display to display a graph using ApexCharts."""

    def __init__(self, id: str, text: Optional[str] = None, x: Optional[Union[list, dict]] = None, y: Optional[Union[list, dict]] = None, data_type="date") -> None:
        """
        Initialize a graph item.

        Args:
            id: Unique identifier for the graph element
            text: Optional title or description text (default: None)
            x: List of x-axis values (default: [])
            y: List of y-axis data values or dict of series (default: [])
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

        self.m_graphx = x if x is not None else []
        self.m_graphy = y if y is not None else []
        self.m_datatype = data_type
        return

    @classmethod
    def get_required_resources(cls) -> list:
        """Graph requires ApexCharts library.
        
        Returns:
            List of required resource paths.
        """
        return ['apexcharts']

    def display(self, container: list, parent_id: Optional[str] = None) -> None:
        """Add graph to container with chart configuration.
        
        Args:
            container: The container element to display in.
            parent_id: The parent element ID.
        """
        super().display(container, parent_id)
        container[-1]["id"] = self.m_id.replace(" ", "_")
        container[-1]["graph_x"] = self.m_graphx
        container[-1]["graph_y"] = self.m_graphy
        container[-1]["graph_type"] = self.m_datatype
        container[-1]["id"] = container[-1]["id"].replace(".", "")  # Forbidden in javascript variables
        return

    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample graph.
        
        Returns:
            Instance of the class with test data.
        """
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
        text: Optional[str] = None,
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
        """Create test instance with sample file explorer.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(id="test_fileexplorer", text="File Explorer",
                   files=[["file1.txt", "file2.pdf"], ["image1.png"]],
                   title=["Documents", "Images"],
                   icons=["file-document", "file-image"],
                   classes=["primary", "success"],
                   hiddens=[False, True])

    def display(self, container: list, parent_id: Optional[str] = None) -> None:
        """Add file explorer to container with all category configurations.
        
        Args:
            container: The container element to display in.
            parent_id: The parent element ID.
        """
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

    def __init__(self, ids: list, text: Optional[str] = None, value: Optional[list] = None, choices: Optional[Union[list, dict]] = None, level: int = -1) -> None:
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
        if choices is None:
            choices = []
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
        """Create test instance with sample cascaded select.
        
        Returns:
            Instance of the class with test data.
        """
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

    def __init__(self, id: str, text: Optional[str] = None, value: Optional[str] = None, choices: list = [], tooltips: list = []) -> None:
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
        """Create test instance with sample select.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(id="test_select", text="Choose an option", value="option2",
                   choices=["option1", "option2", "option3"],
                   tooltips=["First option", "Second option", "Third option"])


@DisplayerCategory.INPUT
class DisplayerItemInputMultiSelect(DisplayerItem):
    """Specialized display to display a multiple select with a possibility to add them on the fly."""

    def __init__(self, id: str, text: Optional[str] = None, value: Optional[list] = None, choices: list = []) -> None:
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
        """Create test instance with sample multi-select.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(id="test_multiselect", text="Select multiple items",
                   value=["item2", "item3"], choices=["item1", "item2", "item3", "item4"])


@DisplayerCategory.INPUT
class DisplayerItemInputMapping(DisplayerItem):
    """Specialized display to display a mapping with a possibility to add them on the fly."""

    def __init__(self, id: str, text: Optional[str] = None, value: Optional[dict] = None, choices: list = []) -> None:
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
        """Create test instance with sample mapping.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(id="test_mapping", text="Key-Value Mapping",
                   value={"Section A": ["option1", "option2"], "Section B": ["option3"]},
                   choices=["option1", "option2", "option3"])


@DisplayerCategory.INPUT
class DisplayerItemInputListSelect(DisplayerItem):
    """Specialized display to display a set of list select."""

    def __init__(self, id: str, text: Optional[str] = None, value: Optional[list] = None, choices: list = []) -> None:
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
        """Create test instance with sample list select.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(id="test_listselect", text="Select from lists",
                   value=["list1_item2", "list2_item1"],
                   choices=["list1_item1", "list1_item2", "list2_item1", "list2_item2"])


@DisplayerCategory.INPUT
class DisplayerItemInputTextSelect(DisplayerItem):
    """Specialized display to display a mapping for a text and a selection for the user."""

    def __init__(self, id: str, text: Optional[str] = None, value: Optional[list] = None, choices: list = []) -> None:
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
        """Create test instance with sample text-select pairs (list of [text, select]).
        
        Returns:
            Instance of the class with test data.
        """
        return cls(id="test_textselect", text="Text and Selection",
                   value=[["First text", "option2"], ["Second text", "option1"]],
                   choices=["option1", "option2", "option3"])


@DisplayerCategory.INPUT
class DisplayerItemInputSelectText(DisplayerItem):
    """Specialized display to display a mapping for a selection followed by a text input."""

    def __init__(self, id: str, text: Optional[str] = None, value: Optional[list] = None, choices: list = []) -> None:
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
        """Create test instance with sample select-text pairs (list of [select, text]).
        
        Returns:
            Instance of the class with test data.
        """
        return cls(id="test_selecttext", text="Select and describe",
                   value=[["option2", "Description for option 2"], ["option1", "Another description"]],
                   choices=["option1", "option2", "option3"])


@DisplayerCategory.INPUT
class DisplayerItemInputDualTextSelect(DisplayerItem):
    """Specialized display to display a mapping for two text inputs followed by a selection."""

    def __init__(self, id: str, text: Optional[str] = None, value: Optional[list] = None, choices: list = []) -> None:
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
        """Create test instance with sample dual text-select (list of [text1, text2, select]).
        
        Returns:
            Instance of the class with test data.
        """
        return cls(id="test_dualtextselect", text="Dual text with select",
                   value=[["First text", "Second text", "choice2"], ["Another first", "Another second", "choice1"]],
                   choices=["choice1", "choice2", "choice3"])


@DisplayerCategory.INPUT
class DisplayerItemInputDualSelectText(DisplayerItem):
    """Specialized display to display a mapping for two selections followed by a text input."""

    def __init__(self, id: str, text: Optional[str] = None, value: Optional[list] = None, choices: list = []) -> None:
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
        """Create test instance with sample dual select-text (list of [select1, select2, text]).
        
        Returns:
            Instance of the class with test data.
        """
        return cls(id="test_dualselecttext", text="Dual select with text",
                   value=[["opt1", "opt2", "Combined result"], ["opt2", "opt3", "Another combination"]],
                   choices=["opt1", "opt2", "opt3"])


@DisplayerCategory.INPUT
class DisplayerItemInputTextText(DisplayerItem):
    """Specialized display to display a mapping with two text inputs."""

    def __init__(self, id: str, text: Optional[str] = None, value: Optional[list] = None) -> None:
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
        """Create test instance with sample text-text pairs (list of [text1, text2]).
        
        Returns:
            Instance of the class with test data.
        """
        return cls(id="test_texttext", text="Two text fields",
                   value=[["First field", "Second field"], ["Another first", "Another second"]])


@DisplayerCategory.INPUT
class DisplayerItemInputListText(DisplayerItem):
    """Specialized display to display a list of input text fields."""

    def __init__(self, id: str, text: Optional[str] = None, value: Optional[dict] = None) -> None:
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
        """Create test instance with sample list of texts.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(id="test_listtext", text="List of text inputs",
                   value={"item1": "Text 1", "item2": "Text 2", "item3": "Text 3"})


@DisplayerCategory.INPUT
class DisplayerItemInputNumeric(DisplayerItem):
    """Specialized display to display an input number field."""

    def __init__(self, id: str, text: Optional[str] = None, value: Optional[float] = None, focus: bool = False) -> None:
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
        """Create test instance with sample numeric input.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(id="test_numeric", text="Enter a number", value=42.5, focus=False)


@DisplayerCategory.INPUT
class DisplayerItemInputDate(DisplayerItem):
    """Specialized display to display an input date.
    Date shall be in format YYYY-MM-DD or YYYY-MM-DDT000:00 if the minute and hour is also needed."""

    def __init__(self, id: str, text: Optional[str] = None, value: Optional[str] = None) -> None:
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
        """Create test instance with sample date input.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(id="test_date", text="Select a date", value="2024-01-15")


@DisplayerCategory.INPUT
class DisplayerItemInputText(DisplayerItem):
    """Specialized display to display a multi-line text area input."""

    def __init__(self, id: str, text: Optional[str] = None, value: Optional[str] = None) -> None:
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
        """Text input requires TinyMCE library for rich text editing.
        
        Returns:
            List of required resource paths.
        """
        return ['tinymce']

    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample text input.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(id="test_text", text="Enter text", value="Sample text value")

@DisplayerCategory.INPUT
class DisplayerItemInputTextJS(DisplayerItem):
    """Specialized display to display an input text with a JS function execution on change."""

    def __init__(self, id: str, text: Optional[str] = None, value: Optional[str] = None, js: Optional[str] = None, focus = False) -> None:
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
        """Create test instance with sample text-JS input.
        
        Returns:
            Instance of the class with test data.
        """
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

    def __init__(self, id: str, text: Optional[str] = None, value: Optional[str] = None, focus: bool = False) -> None:
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
        """Create test instance with sample string input.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(id="test_string", text="Enter a string", value="Sample string", focus=False)

@DisplayerCategory.INPUT
class DisplayerItemInputStringIcon(DisplayerItem):
    """Specialized display to display an input string that also displays an associated MDI icon if valid."""

    def __init__(self, id: str, text: Optional[str] = None, value: Optional[str] = None) -> None:
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
        """Create test instance with sample string-icon input.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(id="test_stringicon", text="Icon String", value="star-outline")


@DisplayerCategory.INPUT
class DisplayerItemInputMultiText(DisplayerItem):
    """Specialized display to display a multi-line text list input."""

    def __init__(self, id: str, text: Optional[str] = None, value: Optional[list] = None) -> None:
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
        """Create test instance with sample multi-line text input.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(id="test_multitext", text="Enter multiple lines",
                   value=["Line 1", "Line 2", "Line 3"])


@DisplayerCategory.INPUT
class DisplayerItemInputFolder(DisplayerItem):
    """Specialized display to display a folder selection input."""

    def __init__(self, id: str, text: Optional[str] = None) -> None:
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
        """Folder input requires FilePond library.
        
        Returns:
            List of required resource paths.
        """
        return ['filepond']

    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample folder input.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(id="test_folder", text="Select Folder")

@DisplayerCategory.INPUT
class DisplayerItemInputFile(DisplayerItem):
    """Specialized display to display a file upload input."""

    def __init__(self, id: str, text: Optional[str] = None) -> None:
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
        """File input requires FilePond library.
        
        Returns:
            List of required resource paths.
        """
        return ['filepond']

    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample file input.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(id="test_file", text="Select File")

@DisplayerCategory.INPUT
class DisplayerItemInputImage(DisplayerItem):
    """Specialized display to display an image upload input box."""

    def __init__(self, id: str, text: Optional[str] = None) -> None:
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
        """Image input requires FilePond library.
        
        Returns:
            List of required resource paths.
        """
        return ['filepond']

    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample image input.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(id="test_image", text="Select Image")

@DisplayerCategory.MEDIA
class DisplayerItemCalendar(DisplayerItem):
    """Specialized display to display a full size calendar using FullCalendar library."""

    def __init__(self, id: str, view: str = "dayGridMonth", events: Optional[Union[Dict, List]] = None) -> None:
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
        self.m_data = events if events is not None else {}
        return

    @classmethod
    def get_required_resources(cls) -> list:
        """Calendar requires FullCalendar library.
        
        Returns:
            List of required resource paths.
        """
        return ['fullcalendar']

    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample calendar.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(id="test_calendar", view="dayGridMonth",
                   events=[
                       {"title": "Event 1", "start": "2024-01-15"},
                       {"title": "Event 2", "start": "2024-01-20", "end": "2024-01-22"}
                   ])


@DisplayerCategory.DISPLAY
class DisplayerItemCard(DisplayerItem):
    """
    Card component with colored header, icon, title, and body content.

    Creates a Bootstrap card with customizable header color, MDI icon,
    and optional footer buttons.

    Example:
        >>> card = DisplayerItemCard(
        ...     id="demo_card",
        ...     title="Feature Demo",
        ...     icon="mdi-play-circle",
        ...     header_color=BSstyle.PRIMARY,
        ...     body="This demonstrates a cool feature.",
        ...     footer_buttons=[
        ...         {"id": "run_btn", "text": "Run", "style": "primary"}
        ...     ]
        ... )
    """

    def __init__(
        self,
        id: str,
        title: str,
        body: str,
        icon: Optional[str] = None,
        header_color: BSstyle = BSstyle.PRIMARY,
        footer_buttons: Optional[List[Dict[str, str]]] = None
    ) -> None:
        """
        Initialize a card display item.

        Args:
            id: Unique identifier for the card
            title: Title text shown in the header
            body: Main content (HTML supported)
            icon: MDI icon name (e.g., "mdi-information")
            header_color: Bootstrap color for header (default: PRIMARY)
            footer_buttons: List of button dicts with keys: id, text, style, icon (optional)
        """
        super().__init__(DisplayerItems.CARD)
        self.m_itemId = id
        self.m_text = title  # Title
        self.m_value = body  # Body content
        self.m_icon = icon
        self.m_style = header_color.value if isinstance(header_color, BSstyle) else header_color
        self.m_data = footer_buttons or []

    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample card.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(
            id="test_card",
            title="Test Card",
            icon="mdi mdi-shield",
            header_color=BSstyle.PRIMARY,
            body="This is a test card with sample content.",
            footer_buttons=[
                {"id": "test_btn", "text": "Click Me", "style": "primary"}
            ]
        )


@DisplayerCategory.DISPLAY
@DisplayerCategory.DISPLAY
class DisplayerItemDynamicContent(DisplayerItem):
    """
    Placeholder div for content that will be updated dynamically.

    Creates a container with an ID that can be targeted by emit_reload()
    for dynamic updates without page refresh.

    Example:
        >>> content = DisplayerItemDynamicContent(
        ...     id="live_status",
        ...     initial_content="<p>Waiting for updates...</p>",
        ...     card=True
        ... )

        # Later in threaded action:
        scheduler.emit_reload([{
            'id': 'live_status',
            'content': '<p>Updated at 12:45!</p>'
        }])
    """

    def __init__(
        self,
        id: str,
        initial_content: str = "",
        card: bool = False
    ) -> None:
        """
        Initialize a dynamic content placeholder.

        Args:
            id: Unique identifier (used by emit_reload to target this element)
            initial_content: Initial HTML/text content
            card: If True, wraps content in card styling
        """
        super().__init__(DisplayerItems.DYNAMICCONTENT)
        self.m_itemId = id
        self.m_text = initial_content
        self.m_disabled = card  # Reusing disabled flag for card styling

    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample dynamic content.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(
            id="test_dynamic",
            initial_content="<p>This content will be updated dynamically.</p>",
            card=True
        )


@DisplayerCategory.INPUT
class DisplayerItemButtonGroup(DisplayerItem):
    """
    Group of buttons displayed horizontally or vertically.

    Creates multiple buttons in a Bootstrap button group layout.

    Example:
        >>> btn_group = DisplayerItemButtonGroup(
        ...     id="demo_controls",
        ...     buttons=[
        ...         {"id": "start", "text": "Start", "icon": "mdi-play", "style": "success"},
        ...         {"id": "stop", "text": "Stop", "icon": "mdi-stop", "style": "danger"},
        ...         {"id": "reset", "text": "Reset", "icon": "mdi-refresh", "style": "warning"}
        ...     ],
        ...     layout="horizontal"
        ... )
    """

    def __init__(
        self,
        id: str,
        buttons: List[Dict[str, str]],
        layout: str = "horizontal"
    ) -> None:
        """
        Initialize a button group display item.

        Args:
            id: Unique identifier for the button group
            buttons: List of button dicts with keys:
                - id: Button ID (required)
                - text: Button text (required)
                - style: Bootstrap style (default: "primary")
                - icon: MDI icon name (optional)
                - disabled: Boolean (optional)
            layout: "horizontal" or "vertical"
        """
        super().__init__(DisplayerItems.BUTTONGROUP)
        self.m_itemId = id
        self.m_data = buttons
        self.m_value = layout  # horizontal or vertical

    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample button group.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(
            id="test_btn_group",
            buttons=[
                {"id": "btn1", "text": "Button 1", "style": "primary"},
                {"id": "btn2", "text": "Button 2", "style": "success"},
                {"id": "btn3", "text": "Button 3", "style": "danger"}
            ],
            layout="horizontal"
        )


@DisplayerCategory.DISPLAY
class DisplayerItemIconText(DisplayerItem):
    """
    Simple line with icon and text displayed inline.

    Creates a compact icon + text combination, useful for feature lists
    or quick information display.

    Example:
        >>> icon_text = DisplayerItemIconText(
        ...     id="feature1",
        ...     icon="mdi-check-circle",
        ...     text="Real-time updates enabled",
        ...     color=BSstyle.SUCCESS
        ... )
    """

    def __init__(
        self,
        id: str,
        icon: str,
        text: str,
        color: Optional[BSstyle] = None,
        link: Optional[str] = None
    ) -> None:
        """
        Initialize an icon+text display item.

        Args:
            id: Unique identifier
            icon: MDI icon name (e.g., "mdi-check")
            text: Text content to display
            color: Bootstrap color for text (optional)
            link: URL to link to (optional, makes it clickable)
        """
        super().__init__(DisplayerItems.ICONTEXT)
        self.m_itemId = id
        self.m_icon = icon
        self.m_text = text
        self.m_style = color.value if isinstance(color, BSstyle) and color else None
        self.m_path = link  # Using path for link URL

    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample icon+text.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(
            id="test_icontext",
            icon="mdi mdi-information",
            text="Sample icon text item",
            color=BSstyle.PRIMARY
        )


@DisplayerCategory.DISPLAY
class DisplayerItemActionButtons(DisplayerItem):
    """
    Row action buttons for CRUD operations (View, Edit, Delete).

    Creates a compact inline button group with icon-based action buttons,
    commonly used in table rows or list items for quick actions.

    Each button can have:
    - Icon (MDI or Bootstrap Icons)
    - Tooltip
    - URL/Link
    - Color style
    - Enable/disable state

    Example:
        >>> # Full custom actions
        >>> actions = DisplayerItemActionButtons(
        ...     id="user_123_actions",
        ...     actions=[
        ...         {"type": "view", "url": "/users/123", "tooltip": "View details"},
        ...         {"type": "edit", "url": "/users/123/edit", "tooltip": "Edit user"},
        ...         {"type": "delete", "url": "/users/123/delete", "tooltip": "Delete user", "disabled": False}
        ...     ]
        ... )

        >>> # Quick default actions with URLs
        >>> actions = DisplayerItemActionButtons(
        ...     id="item_456_actions",
        ...     view_url="/items/456",
        ...     edit_url="/items/456/edit",
        ...     delete_url="/items/456/delete"
        ... )

        >>> # Only edit and delete
        >>> actions = DisplayerItemActionButtons(
        ...     id="comment_789_actions",
        ...     edit_url="/comments/789/edit",
        ...     delete_url="/comments/789/delete"
        ... )
    """

    # Default action configurations
    DEFAULT_ACTIONS = {
        "view": {
            "icon": "mdi mdi-eye",
            "style": "info",
            "tooltip": "View"
        },
        "edit": {
            "icon": "mdi mdi-pencil",
            "style": "warning",
            "tooltip": "Edit"
        },
        "delete": {
            "icon": "mdi mdi-delete",
            "style": "danger",
            "tooltip": "Delete"
        },
        "download": {
            "icon": "mdi mdi-download",
            "style": "success",
            "tooltip": "Download"
        },
        "copy": {
            "icon": "mdi mdi-content-copy",
            "style": "secondary",
            "tooltip": "Copy"
        }
    }

    def __init__(
        self,
        id: str,
        actions: Optional[List[Dict[str, Any]]] = None,
        view_url: Optional[str] = None,
        edit_url: Optional[str] = None,
        delete_url: Optional[str] = None,
        size: str = "sm",
        style: str = "buttons"  # "buttons" or "icons"
    ) -> None:
        """
        Initialize action buttons display item.

        Args:
            id: Unique identifier for the button group
            actions: List of custom action dicts with keys:
                - type: Action type ("view", "edit", "delete", or custom)
                - url: Link URL (optional)
                - icon: Icon class (optional, overrides default)
                - style: Bootstrap style (optional, overrides default)
                - tooltip: Tooltip text (optional, overrides default)
                - disabled: Boolean (optional, default False)
            view_url: Quick setup - URL for view action
            edit_url: Quick setup - URL for edit action
            delete_url: Quick setup - URL for delete action
            size: Button size ("sm", "md", "lg")
            style: Display style ("buttons" for btn, "icons" for plain icons)
        """
        super().__init__(DisplayerItems.ACTIONBUTTONS)
        self.m_itemId = id
        self.m_value = size  # sm, md, lg
        self.m_style = style  # buttons or icons

        # Build actions list
        if actions is not None:
            self.m_data = actions
        else:
            # Quick setup mode: build from individual URLs
            self.m_data = []
            if view_url:
                self.m_data.append({
                    "type": "view",
                    "url": view_url,
                    **self.DEFAULT_ACTIONS["view"]
                })
            if edit_url:
                self.m_data.append({
                    "type": "edit",
                    "url": edit_url,
                    **self.DEFAULT_ACTIONS["edit"]
                })
            if delete_url:
                self.m_data.append({
                    "type": "delete",
                    "url": delete_url,
                    **self.DEFAULT_ACTIONS["delete"]
                })

    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample action buttons.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(
            id="test_actions",
            view_url="https://www.google.com",
            edit_url="https://www.google.com",
            delete_url="https://www.google.com"
        )


@DisplayerCategory.DISPLAY
class DisplayerItemConsole(DisplayerItem):
    """
    Console output display with monospace font and dark terminal-like styling.

    Displays text content in a styled console/terminal format with:
    - Dark background (#1e1e1e)
    - Light text color (#d4d4d4)
    - Monospace font
    - Scrollable container
    - Optional max height

    Perfect for showing command output, logs, or terminal sessions.

    Example:
        >>> console = DisplayerItemConsole(
        ...     id="build_output",
        ...     lines=["Building project...", "Compiling src/main.py", "Build successful!"],
        ...     max_height="400px"
        ... )
    """

    def __init__(
        self,
        id: str,
        lines: List[str],
        max_height: str = "300px",
        title: Optional[str] = None
    ) -> None:
        """
        Initialize a console display item.

        Args:
            id: Unique identifier
            lines: List of console output lines to display
            max_height: Maximum height before scrolling (e.g., "300px", "20rem")
            title: Optional title/header for the console block
        """
        super().__init__(DisplayerItems.CONSOLE)
        self.m_itemId = id
        self.m_data = lines  # Using m_data for lines list
        self.m_style = max_height  # Using m_style for max_height
        self.m_header = title  # Using m_header for optional title

    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample console output.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(
            id="test_console",
            lines=[
                "$ npm install",
                "Installing dependencies...",
                "✓ lodash@4.17.21",
                "✓ axios@1.4.0",
                "✓ react@18.2.0",
                "",
                "Build completed successfully!"
            ],
            max_height="200px",
            title="Build Output"
        )


@DisplayerCategory.DISPLAY
class DisplayerItemCode(DisplayerItem):
    """
    Code block display with syntax highlighting support.

    Displays formatted code with:
    - Syntax highlighting (via highlight.js or Prism.js)
    - Line numbers (optional)
    - Copy button (optional)
    - Language badge
    - Light/dark theme support

    Supports many languages: python, javascript, java, c++, sql, json, yaml, etc.

    Example:
        >>> code = DisplayerItemCode(
        ...     id="sample_code",
        ...     code='def hello():\\n    print("Hello, World!")',
        ...     language="python",
        ...     show_line_numbers=True,
        ...     title="Example Function"
        ... )
    """

    def __init__(
        self,
        id: str,
        code: str,
        language: str = "text",
        show_line_numbers: bool = False,
        title: Optional[str] = None,
        max_height: str = "500px"
    ) -> None:
        """
        Initialize a code display item.

        Args:
            id: Unique identifier
            code: Source code content to display
            language: Programming language for syntax highlighting
                     (python, javascript, java, cpp, sql, json, yaml, bash, etc.)
            show_line_numbers: Whether to show line numbers in gutter
            title: Optional title/filename for the code block
            max_height: Maximum height before scrolling
        """
        super().__init__(DisplayerItems.CODE)
        self.m_itemId = id
        self.m_text = code  # Using m_text for code content
        self.m_path = language  # Using m_path for language
        self.m_header = title  # Using m_header for title
        self.m_style = max_height  # Using m_style for max_height
        self.m_disabled = show_line_numbers  # Using m_disabled for line numbers flag

    @classmethod
    def get_required_resources(cls) -> List[str]:
        """Code display requires Highlight.js for syntax highlighting.
        
        Returns:
            List of required resource paths.
        """
        return ['highlightjs']

    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample code.
        
        Returns:
            Instance of the class with test data.
        """
        sample_code = '''def fibonacci(n):
    """Calculate Fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Test the function
for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")'''

        return cls(
            id="test_code",
            code=sample_code,
            language="python",
            show_line_numbers=True,
            title="fibonacci.py"
        )


@DisplayerCategory.DISPLAY
class DisplayerItemProgressBar(DisplayerItem):
    """
    Display a Bootstrap progress bar.
    
    Shows visual progress indicator with percentage, label, and optional animation.
    Supports different styles (colors) and can show striped/animated bars.
    
    Example:
        >>> # Simple progress bar
        >>> item = DisplayerItemProgressBar("progress1", 75)
        >>> 
        >>> # Styled with label
        >>> item = DisplayerItemProgressBar(
        ...     "progress2", 
        ...     60, 
        ...     label="Uploading...",
        ...     style=BSstyle.SUCCESS,
        ...     striped=True,
        ...     animated=True
        ... )
        >>> 
        >>> # Custom height
        >>> item = DisplayerItemProgressBar("progress3", 90, height=30)
    """
    
    def __init__(
        self,
        id: str,
        value: int,
        label: Optional[str] = None,
        style: BSstyle = BSstyle.PRIMARY,
        striped: bool = False,
        animated: bool = False,
        height: int = 25,
        show_percentage: bool = True
    ) -> None:
        """
        Initialize a progress bar item.
        
        Args:
            id: Unique identifier
            value: Progress percentage (0-100)
            label: Optional text label to display
            style: Bootstrap style (color) - PRIMARY, SUCCESS, INFO, WARNING, ERROR
            striped: Whether to show striped pattern
            animated: Whether to animate the stripes
            height: Height of the progress bar in pixels
            show_percentage: Whether to show percentage number inside bar
        """
        super().__init__(DisplayerItems.PROGRESSBAR)
        self.m_itemId = id
        self.m_value = max(0, min(100, value))  # Clamp between 0-100
        self.m_text = label
        self.m_style = style.value if isinstance(style, BSstyle) else style
        self.m_data = {
            "striped": striped,
            "animated": animated,
            "height": height,
            "show_percentage": show_percentage
        }
    
    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample progress.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(
            id="test_progress",
            value=65,
            label="Processing...",
            style=BSstyle.INFO,
            striped=True,
            animated=True
        )


class DisplayerItemGridEditor(DisplayerItem):
    """
    Interactive grid layout editor using GridStack.js.
    
    Provides a drag-and-drop interface for creating custom grid layouts.
    The layout configuration is automatically saved to a hidden field as JSON
    on every change (add, remove, drag, resize).
    
    Use this for allowing users to customize their dashboard layouts or
    create custom form arrangements.
    """

    def __init__(
        self, 
        id: str, 
        fields: Dict[str, str],
        value: Optional[str] = None,
        columns: int = 12
    ) -> None:
        """
        Initialize a grid layout editor.

        Args:
            id: Unique identifier for the editor and hidden field
            fields: Dictionary mapping field IDs to display names
                   Example: {"field1": "First Field", "field2": "Second Field"}
            value: Optional JSON string with existing layout configuration
                  If provided, editor will load this layout on initialization
            columns: Number of grid columns (default: 12, matching Bootstrap)

        Example:
            >>> editor = DisplayerItemGridEditor(
            ...     id="layout_editor",
            ...     fields={
            ...         "user_info": "User Information",
            ...         "stats": "Statistics",
            ...         "activity": "Recent Activity"
            ...     },
            ...     value='{"version":"1.0","columns":12,"items":[...]}'
            ... )
        """
        super().__init__(DisplayerItems.GRIDEDITOR)
        self.m_id = id
        self.m_data = fields  # field_id -> field_name mapping
        self.m_value = value  # JSON string of layout config
        self.m_text = str(columns)  # Store columns count in m_text

    @classmethod
    def get_required_resources(cls) -> List[str]:
        """Grid editor requires GridStack library.
        
        Returns:
            List of required resource paths.
        """
        return ['gridstack']

    @classmethod
    def instantiate_test(cls):
        """Create test instance with sample fields.
        
        Returns:
            Instance of the class with test data.
        """
        return cls(
            id="test_grid_editor",
            fields={
                "header": "Header Section",
                "sidebar": "Sidebar Widget",
                "main": "Main Content",
                "footer": "Footer Info"
            },
            columns=12
        )
