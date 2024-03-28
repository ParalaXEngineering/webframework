from submodules.framework.src import access_manager

from enum import Enum


class Layouts(Enum):
    VERTICAL = "VERT"
    HORIZONTAL = "HORIZ"
    TABLE = "TABLE"
    SPACER = "SPACER"


class DisplayerItems(Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    FILE = "FILE"
    BADGE = "BADGE"
    INDATE = "INDATE"
    INBOX = "INBOX"
    INNUM = "INNUM"
    INHIDDEN = "INHIDDEN"
    INTEXT = "INTEXT"
    INSTRING = "INSTRING"
    INMULTITEXT = "INMULTITEXT"
    INFILE = "INFILE"
    INFOLDER = "INFOLDER"
    INTEXTICON = "INTEXTICON"
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
    PLACEHOLDER = "PLACEHOLDER"
    INPATH = "INPATH"


class BSstyle(Enum):
    PRIMARY = "primary"
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    ERROR = "danger"
    DARK = "dark"
    LIGHT = "light"
    NONE = "none"


class BSalign(Enum):
    L = "start"
    R = "end"
    C = "center"


class DisplayerLayout:
    #g_next_layout = 0
    g_last_layout = None

    """Generic class to store information about a layout"""

    def __init__(
        self,
        layoutType: Layouts,
        columns: list = [],
        subtitle=None,
        alignment: BSalign = None,
        spacing: int = 0,
        height: int = 0,
        background: BSstyle = None,
        responsive = None
    ) -> None:
        """Constructor

        :param layoutType: The layout type
        :type layoutType: Layouts
        :param columns: Size of the columns (int), one item for one size. The sum should not be more than 12, defaults to []
        :type columns: list, optional
        :param subtitle: An optional subtitle for the layout, defaults to None
        :type subtitle: _type_, optional
        :param alignment: A table of the same length as the columns, with the alignment, defaults to None
        :type alignment: BSalign, optional
        :param spacing: A spacing as defined by bootstratp, that is from 0 to 5, defaults to 0
        :type spacing: int, optional
        :param height: A height value. This value will correspond to the height of a default line, and can be used to align divs with several lines that are next to each other
        :type height: int, optional
        """
        self.m_type = layoutType.value
        self.m_column = columns
        self.m_subtitle = subtitle
        self.m_alignement = alignment
        self.m_height = height
        self.m_background = background
        self.m_responsive = responsive

        if spacing <= 5:
            self.m_spacing = spacing
        else:
            spacing = 5

    def display(self, container: list, id: int): # -> int:
        """Add this item to a container view. Should be reimplemented by the child

        :param container: The container in which the display item should be appended. The items are added by order of adding in the code
        :type container: list
        :param parent_id: If we are in a form, each different form will have a parent id
        :type parent_id: str
        :return The layout id of the newly created layout
        """
        current_layout = {
            "object": "layout",
            "type": self.m_type,
            "id": id,
            "subtitle": self.m_subtitle,
            "background": self.m_background.value if self.m_background else None
        }

        if self.m_type == Layouts.TABLE.value:
            current_layout["header"] = self.m_column
            current_layout["responsive"] = self.m_responsive
            current_layout["lines"] = None

        else:
            # Check column size
            column_size = 0
            col_nb = 0
            containers = []
            alignments = []
            for col in self.m_column:
                column_size += col
                containers.append([])
                if not self.m_alignement or col_nb >= len(self.m_alignement):
                    alignments.append(BSalign.L.value)
                else:
                    alignments.append(self.m_alignement[col_nb].value)

                col_nb += 1

            if column_size > 12 or column_size == 0:
                current_layout["columns"] = []
                current_layout["containers"] = []
            else:
                current_layout["columns"] = self.m_column
                current_layout["containers"] = containers
            current_layout["align"] = alignments
            current_layout["spacing"] = self.m_spacing

        container.append(current_layout)

        #DisplayerLayout.g_next_layout += 1
        #return self.g_next_layout


class DisplayerItem:
    """Generic class to store the information about a display item. A display item is the atomic information used to display stuff on the screen."""

    def __init__(self, itemType: DisplayerItems) -> None:
        """Constructor

        :param itemType: The type of item that this display is. Should be used by any child item
        :type itemType: DisplayerItems
        """
        self.m_type = itemType

    def display(self, container: list, parent_id: str = None) -> None:
        """Add this item to a container view. Should be reimplemented by the child

        :param container: The container in which the display item should be appended. The items are added by order of adding in the code
        :type container: list
        :param parent_id: If we are in a form, each different form will have a parent id
        :type parent_id: str
        """
        item = {"object": "item", "type": self.m_type.value}

        # Check exisitings common variables, so basic items don't need to reimplement this function
        if hasattr(self, "m_text"):
            item["text"] = self.m_text
        if hasattr(self, "m_level"):
            item["level"] = self.m_level
        if hasattr(self, "m_value"):
            item["value"] = self.m_value
        if hasattr(self, "m_style"):
            item["style"] = self.m_style
        if hasattr(self, "m_disabled"):
            item["disabled"] = self.m_disabled
        if hasattr(self, "m_data"):
            item["data"] = self.m_data
        if hasattr(self, "m_header"):
            item["header"] = self.m_header
        if hasattr(self, "m_possibles"):
            item["possibles"] = self.m_possibles
        if hasattr(self, "m_path"):
            item["path"] = self.m_path
        if hasattr(self, "m_icon"):
            item["icon"] = self.m_icon
        if hasattr(self, "m_endpoint"):
            item["endpoint"] = self.m_endpoint
        if hasattr(self, "m_ids"):
            item["id"] = []
            if parent_id:
                for id in self.m_ids:
                    item["id"].append(parent_id + "." + id)
            else:
                item["id"] = self.m_ids

        if hasattr(self, "m_id"):
            if parent_id:
                item["id"] = parent_id + "." + self.m_id
            else:
                item["id"] = self.m_id
        if hasattr(self, "m_itemId"):
            item["itemId"] = self.m_itemId

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


class DisplayerItemPlaceholder(DisplayerItem):
    """Specialized display item to set a placeholder with an id which can be filled later"""

    def __init__(self, id: str, data: str = "") -> None:
        """Initialize with the text content

        :param id: The id of the placehpmder
        :type id: str
        :param data: some data that are already in the placeholder
        :type data: str
        """
        super().__init__(DisplayerItems.PLACEHOLDER)
        self.m_id = id
        self.m_data = data


class DisplayerItemAlert(DisplayerItem):
    """Specialized display item to display a an alert with a bootstrap style"""

    def __init__(self, text: str, highlightType: BSstyle = BSstyle.SUCCESS) -> None:
        """Initialize with the text content

        :param text: The text content
        :type text: str
        :param highlightType: The level of the higlight, which will translate into a different color displayed
        :type highlightType: BSstyle
        """
        super().__init__(DisplayerItems.ALERT)
        self.m_text = text
        self.m_style = highlightType.value

    def setText(self, text: str):
        self.m_text = text
        return


class DisplayerItemText(DisplayerItem):
    """Specialized display item to display a simple line of text"""

    def __init__(self, text: str) -> None:
        """Initialize with the text content

        :param text: The text content
        :type text: str
        """
        super().__init__(DisplayerItems.TEXT)
        self.m_text = text

class DisplayerItemHidden(DisplayerItem):
    """Specialized display to display a hidden field"""

    def __init__(self, id: str, value: str = None) -> None:
        super().__init__(DisplayerItems.INHIDDEN)
        self.m_value = value
        self.m_id = id
        return


class DisplayerItemIconLink(DisplayerItem):
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
        """Initialize with the text content

        :param text: The text content
        :type text: str
        :param icon: The icon name of the mdi icons. Do not prefix with mdi-
        :type icon: str
        :param link: the link (in the flask terms) to point to. Can be set to empty to only have an icon
        :type link: str
        :param parameters: a list of text line with the parameters after the link, that is after a "?". Those will be passed with a GET method
        :type parameters: list
        """
        super().__init__(DisplayerItems.ICONLINK)
        self.m_text = text
        self.m_id = id
        self.m_data = link
        self.m_icon = icon
        self.m_parameters = parameters
        self.m_style = color.value
        return

    def display(self, container: list, parent_id: str = None) -> None:
        """Add this item to a container view. Should be reimplemented by the child

        :param container: The container in which the display item should be appended. The items are added by order of adding in the code
        :type container: list
        :param parent_id: If we are in a form, each different form will have a parent id
        :type parent_id: str
        """
        super().display(container, parent_id)
        container[-1]["icon"] = self.m_icon
        container[-1]["parameters"] = self.m_parameters
        return


class DisplayerItemButton(DisplayerItem):
    """Specialized display item to display a simple button"""

    def __init__(self, id: str, text: str) -> None:
        """Initialize with the text content

        :param text: The text content
        :type text: str
        """
        super().__init__(DisplayerItems.BUTTON)
        self.m_text = text
        self.m_id = id
        return
    
class DisplayerItemModalButton(DisplayerItem):
    """Specialized display item to display a button to show a modal"""

    def __init__(self, text: str, link: str) -> None:
        """Initialize with the text content

        :param text: The text content
        :type text: str
        """
        super().__init__(DisplayerItems.MODALBUTTON)
        self.m_text = text
        self.m_path = link
        return
    
class DisplayerItemModalLink(DisplayerItem):
    """Specialized display item to display a link icon"""

    def __init__(
        self,
        text: str,
        icon: str,
        link: str = "",
        color: BSstyle = BSstyle.PRIMARY,
    ) -> None:
        """Initialize with the text content

        :param text: The text content
        :type text: str
        :param icon: The icon name of the mdi icons. Do not prefix with mdi-
        :type icon: str
        :param link: the link (in the flask terms) to point to. Can be set to empty to only have an icon
        :type link: str
        :param parameters: a list of text line with the parameters after the link, that is after a "?". Those will be passed with a GET method
        :type parameters: list
        """
        super().__init__(DisplayerItems.MODALLINK)
        self.m_text = text
        self.m_path = link
        self.m_icon = icon
        self.m_style = color.value
        return


class DisplayerItemBadge(DisplayerItem):
    """Specialized display item to display a badge with a color"""

    def __init__(self, text: str, highlightType: BSstyle = BSstyle.SUCCESS) -> None:
        """Initialize with the text content

        :param text: The text content
        :type text: str
        :param highlightType: The level of the higlight, which will translate into a different color displayed
        :type highlightType: BSstyle
        """
        super().__init__(DisplayerItems.BADGE)
        self.m_text = text
        self.m_style = highlightType.value

    def setText(self, text: str):
        self.m_text = text
        return


class DisplayerItemDownload(DisplayerItem):
    """Specialized display item to display a simple download button"""

    def __init__(self, id: str, text: str, link) -> None:
        """Initialize with the text content

        :param text: The text content
        :type text: str
        :param link: The link to the file
        :type link: str
        """
        super().__init__(DisplayerItems.DOWNLOAD)
        self.m_text = text
        self.m_id = id
        self.m_data = link

        return


class DisplayerItemImage(DisplayerItem):
    """Specialized display item to display an image"""

    def __init__(self, height: str, link: str, endpoint: str = None, path: str = None) -> None:
        """Initialize with the text content

        :param height: The height of the image
        :type height: int
        :param link: The link to the image. Can be either the name of the file, or a full http adress.
        :type link: str
        :param endpoint: If using local path, then an endpoint must be used, which is in reference with the endpoint defined in site_conf
        :type endpoint: str
        :param path: The path relative to the endpoint
        :type path: str
        """
        super().__init__(DisplayerItems.IMAGE)
        self.m_data = height
        self.m_value = link
        self.m_path = path
        self.m_endpoint = endpoint

        return

class DisplayerItemFile(DisplayerItem):
    """Specialized display item to display an image"""

    def __init__(self, link: str, endpoint: str = None, path: str = None, text: str = None) -> None:
        """Initialize with the text content

        :param link: The link to the image. Can be either the name of the file, or a full http adress.
        :type link: str
        :param endpoint: If using local path, then an endpoint must be used, which is in reference with the endpoint defined in site_conf
        :type endpoint: str
        :param path: The path relative to the endpoint
        :type path: str
        """
        super().__init__(DisplayerItems.FILE)
        self.m_text = text
        self.m_value = link
        self.m_path = path
        self.m_endpoint = endpoint
        return
    
class DisplayerItemInputBox(DisplayerItem):
    """Specialized display to display an input checkbox"""

    def __init__(self, id: str, text: str = None, value: bool = None) -> None:
        super().__init__(DisplayerItems.INBOX)
        self.m_text = text
        self.m_value = value
        self.m_id = id
        return


class DisplayerItemGraph(DisplayerItem):
    """Specialized display to display an input file explorer"""

    def __init__(self, id: str, text: str = None, x: list = [], y: list = [], data_type="date") -> None:
        """Initialize the display item

            :param id: The id for the input form
            :type id: str
            :param text: An optional accompniing text, defaults to None
            :type text: str, optional
            :param x: List of x values
            :type x: list, optional
            :param y: List of data values
            :type y: list, optional
            :param data_type: The datatype, see the js library, defaults to "date"
        :type data_type: str, optional

        """
        super().__init__(DisplayerItems.GRAPH)
        self.m_text = text
        self.m_id = id

        self.m_graphx = x
        self.m_graphy = y
        self.m_datatype = data_type
        return

    def display(self, container: list, parent_id: str = None) -> None:
        """Add this item to a container view. Should be reimplemented by the child

        :param container: The container in which the display item should be appended. The items are added by order of adding in the code
        :type container: list
        :param parent_id: If we are in a form, each different form will have a parent id
        :type parent_id: str
        """
        super().display(container, parent_id)
        container[-1]["id"] = self.m_id.replace(" ", "_")
        container[-1]["graph_x"] = self.m_graphx
        container[-1]["graph_y"] = self.m_graphy
        container[-1]["graph_type"] = self.m_datatype
        container[-1]["id"] = container[-1]["id"].replace(".", "")  # Forbidden in javascript variables
        return


class DisplayerItemInputFileExplorer(DisplayerItem):
    """Specialized display to display an input file explorer"""

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
        """Initialize the display item

        :param id: The id for the input form
        :type id: str
        :param text: An optional accompniing text, defaults to None
        :type text: str, optional
        :param files: A list of file already present, defaults to []
        :type files: list, optional
        :param title: A list of the titles of the file explorers, defaults to []
        :type title: list, optional
        :param icons: A list of the icons (the mdi project names) of the file explorers, defaults to []
        :type icons: list, optional
        :param classes: A list of the classes (the bootsrap classes such as danger, success or primary) used in the file explorers, defaults to []
        :type classes: list, optional
        :param hiddens:  A list of true / false to indicate if a file explorer has a button to collapse the content, defaults to []
        :type hiddens: list, optional
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

    def display(self, container: list, parent_id: str = None) -> None:
        """Add this item to a container view. Should be reimplemented by the child

        :param container: The container in which the display item should be appended. The items are added by order of adding in the code
        :type container: list
        :param parent_id: If we are in a form, each different form will have a parent id
        :type parent_id: str
        """
        super().display(container, parent_id)
        container[-1]["explorer_files"] = self.m_explorerFiles
        container[-1]["explorer_titles"] = self.m_explorerTitles
        container[-1]["explorer_icons"] = self.m_explorerIcons
        container[-1]["explorer_classes"] = self.m_explorerClasses
        container[-1]["explorer_hiddens"] = self.m_explorerHiddens
        return

class DisplayerItemInputCascaded(DisplayerItem):
    """Specialized display to have multiple select choices, where each level depend on the previous one
    :param ids: The ids of each levels of the cascade
    :type ids: list
    :param value: The current value of the cascade
    :type value: list, containing each value for each level of the cascade
    :param choices: The possibles choices for each cascade
    :type choices: list of list, with a choice list for each level of the cascade
    :param level: If only one level of the cascade should be displayed, use this parameter
    :type: level: int, that correspond on the position in the list of the level, or -1 if all levels needs to be displayed"""

    def __init__(self, ids: list, text: str = None, value: list = None, choices: list = [], level: int = -1) -> None:
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

class DisplayerItemInputSelect(DisplayerItem):
    """Specialized display to display an input select box"""

    def __init__(self, id: str, text: str = None, value: bool = None, choices: list = []) -> None:
        super().__init__(DisplayerItems.SELECT)
        self.m_text = text
        self.m_value = value
        self.m_id = id
        if isinstance(choices, list):
            choices.sort()
        self.m_data = choices
        return


class DisplayerItemInputPath(DisplayerItem):
    """Specialized display to display a path dropdown menu.

    For the moment, this is only supported in AltiumHelper, we need to do something more generic. The path_variable consist of the type of path, symbol or footprint
    """

    def __init__(
        self,
        id: str,
        text: str = None,
        value: str = None,
        path: str = "",
        possibles: list = [],
    ) -> None:
        super().__init__(DisplayerItems.INPATH)
        self.m_text = text
        self.m_value = value
        self.m_id = id
        self.m_data = path
        self.m_possibles = possibles
        return


class DisplayerItemInputMultiSelect(DisplayerItem):
    """Specialized display to display a multiple select with a possibility to add them on the fly"""

    def __init__(self, id: str, text: str = None, value: bool = None, choices: list = []) -> None:
        super().__init__(DisplayerItems.INMULTISELECT)
        choices.sort()
        self.m_text = text
        self.m_value = value
        self.m_id = id
        self.m_data = choices
        return


class DisplayerItemInputMapping(DisplayerItem):
    """Specialized display to display a mapping with a possibility to add them on the fly"""

    def __init__(self, id: str, text: str = None, value: bool = None, choices: list = []) -> None:
        super().__init__(DisplayerItems.INMAPPING)
        choices.sort()
        self.m_text = text
        self.m_value = value
        self.m_id = id
        self.m_data = choices
        return


class DisplayerItemInputListSelect(DisplayerItem):
    """Specialized display to display a set of list select"""

    def __init__(self, id: str, text: str = None, value: bool = None, choices: list = []) -> None:
        super().__init__(DisplayerItems.INLISTSELECT)
        choices.sort()
        self.m_text = text
        self.m_value = value
        self.m_id = id
        self.m_data = choices
        return


class DisplayerItemInputTextSelect(DisplayerItem):
    """Specialized display to display a mapping for a text and a selection for the user"""

    def __init__(self, id: str, text: str = None, value: str = None, choices: list = []) -> None:
        super().__init__(DisplayerItems.INTEXTSELECT)
        choices.sort()
        self.m_text = text
        self.m_value = value
        self.m_id = id
        self.m_data = choices
        return


class DisplayerItemInputSelectText(DisplayerItem):
    """Specialized display to display a mapping for a selection for the user then a text"""

    def __init__(self, id: str, text: str = None, value: str = None, choices: list = []) -> None:
        super().__init__(DisplayerItems.INSELECTTEXT)
        choices.sort()
        self.m_text = text
        self.m_value = value
        self.m_id = id
        self.m_data = choices
        return


class DisplayerItemInputDualTextSelect(DisplayerItem):
    """Specialized display to display a mapping for a dual text and a selection for the user"""

    def __init__(self, id: str, text: str = None, value: str = None, choices: list = []) -> None:
        super().__init__(DisplayerItems.INDUALTEXTSELECT)
        choices.sort()
        self.m_text = text
        self.m_value = value
        self.m_id = id
        self.m_data = choices
        return


class DisplayerItemInputDualSelectText(DisplayerItem):
    """Specialized display to display a mapping for a dual selection for the user then a text"""

    def __init__(self, id: str, text: str = None, value: str = None, choices: list = []) -> None:
        super().__init__(DisplayerItems.INDUALSELECTTEXT)
        choices.sort()
        self.m_text = text
        self.m_value = value
        self.m_id = id
        self.m_data = choices
        return


class DisplayerItemInputTextText(DisplayerItem):
    """Specialized display to display a mapping with two texts"""

    def __init__(self, id: str, text: str = None, value: str = None) -> None:
        super().__init__(DisplayerItems.INTEXTTEXT)
        self.m_text = text
        self.m_value = value
        self.m_id = id
        return


class DisplayerItemInputListText(DisplayerItem):
    """Specialized display to display a list of input text"""

    def __init__(self, id: str, text: str = None, value: dict = None) -> None:
        super().__init__(DisplayerItems.INLISTTEXT)
        self.m_text = text
        self.m_value = value
        self.m_id = id
        return


class DisplayerItemInputNumeric(DisplayerItem):
    """Specialized display to display an input number"""

    def __init__(self, id: str, text: str = None, value: float = None) -> None:
        super().__init__(DisplayerItems.INNUM)
        self.m_text = text
        self.m_value = value
        self.m_id = id
        return


class DisplayerItemInputDate(DisplayerItem):
    """Specialized display to display an input date.
    Date shall be in format YYYY-MM-DD or YYYY-MM-DDT000:00 if the minute and hour is also needed"""

    def __init__(self, id: str, text: str = None, value: str = None) -> None:
        super().__init__(DisplayerItems.INDATE)
        self.m_text = text
        self.m_value = value
        self.m_id = id
        return


class DisplayerItemInputText(DisplayerItem):
    """Specialized display to display an input number"""

    def __init__(self, id: str, text: str = None, value: str = None) -> None:
        super().__init__(DisplayerItems.INTEXT)
        self.m_text = text
        self.m_value = value
        self.m_id = id
        return
    
class DisplayerItemInputString(DisplayerItem):
    """Specialized display to display an input number"""

    def __init__(self, id: str, text: str = None, value: str = None) -> None:
        super().__init__(DisplayerItems.INSTRING)
        self.m_text = text
        self.m_value = value
        self.m_id = id
        return


class DisplayerItemInputMultiText(DisplayerItem):
    """Specialized display to display an input number"""

    def __init__(self, id: str, text: str = None, value: str = None) -> None:
        super().__init__(DisplayerItems.INMULTITEXT)
        self.m_text = text
        self.m_value = value
        self.m_id = id
        return


class DisplayerItemInputTextIcon(DisplayerItem):
    """Specialized display to display a relation text / icon"""

    def __init__(self, id: str, value: str = None) -> None:
        super().__init__(DisplayerItems.INTEXTICON)
        self.m_value = value
        self.m_id = id
        return

class DisplayerItemInputFolder(DisplayerItem):
    """Specialized display to display an input number"""

    def __init__(self, id: str, text: str = None) -> None:
        super().__init__(DisplayerItems.INFOLDER)
        self.m_text = text
        self.m_id = id
        return

class DisplayerItemInputFile(DisplayerItem):
    """Specialized display to display an input number"""

    def __init__(self, id: str, text: str = None) -> None:
        super().__init__(DisplayerItems.INFILE)
        self.m_text = text
        self.m_id = id
        return
    
class DisplayerItemInputImage(DisplayerItem):
    """Specialized display to display an input image box"""

    def __init__(self, id: str, text: str = None) -> None:
        super().__init__(DisplayerItems.INIMAGE)
        self.m_text = text
        self.m_id = id
        return


class Displayer:
    """Main displayer class to construct the information displayed on the screen.

    The displayer is constituted of several modules (each module is a single form and card), which are them self created with layouts that can be stack on top of another
    (for instance vertical layouts, horizontal ones, etc...). In each layouts, there is one or more display items that holds the information displayed

    The modules, layouts and items are always displayed in the order in which they have been added in the displayer.
    """

    def __init__(self):
        self.m_modules = {}
        self.m_modals = []
        self.g_next_layout = 0

        self.m_active_module = None
        return

    def add_module(self, module: dict, name_override: str = None, display: bool = True):
        """Prepare a new module for displaying. An optionnal ID can be affected to this module
        The module is then set to active, which means that everything will be added on it.

        :param module: A module
        :type module: list
        :param name_override: An optionnal name overriding, instead of the default name
        :type name_override: str
        :param display: Display the title
        :type display: bool
        """

        self.m_modules[module.m_default_name] = {
            "id": module.m_default_name,
            "type": module.m_type,
            "display": display,
        }
        if name_override:
            self.m_modules[module.m_default_name]["name_override"] = name_override

        self.m_active_module = module.m_default_name
        return

    def add_generic(self, name: str, display: bool = True):
        """Prepare a generic item for displaying

        :param name: The item name
        :type name: str
        :param display: Display the title
        :type display: bool
        """
        self.m_modules[name] = {"id": name, "type": None, "display": display}

        self.m_active_module = name
        return

    def switch_module(self, name: str) -> None:
        """Switch the current module to the given one, if it exists.

        :param name: The name of the currently active module
        :type name: str
        """
        if name in self.m_modules:
            self.m_active_module = name

        return

    def find_layout(self, searchable_layout=[], layout_id=-1) -> list:
        """Find a layout recursively and return it, or an empty table if not found

        :param searchable_layout: A list of item that can also be layouts, defaults to []
        :type searchable_layout: list, optional
        :param layout_id: The layout to search, defaults to -1
        :type layout_id: int, optional
        :return: The found layout, or an empty list
        :rtype: list
        """
        if layout_id == -1:
            return []

        for potential_layout in searchable_layout:
            if "object" in potential_layout and potential_layout["object"] == "layout":
                # We have a layout and not a display item
                if potential_layout["id"] == layout_id:
                    return potential_layout
                else:
                    if "containers" in potential_layout:
                        for item in potential_layout["containers"]:
                            sublayouts = self.find_layout(item, layout_id)
                            if sublayouts:
                                return sublayouts

        return []

    def add_display_item(
        self,
        item: DisplayerItems,
        column: int = 0,
        layout_id: int = -1,
        disabled: bool = False,
        id: int = None,
        line: int = -1,
    ) -> bool:
        """Add a new display item.

        :param item: The item to add
        :type item: DisplayerItems
        :param column: The column of the layout in which it will be added, defaults to 0
        :type column: int, optional
        :param layout_id: The layout id of the parent layout, defaults to -1 (last one added)
        :type layout_id: int, optional
        :param id: If set, the whole item will have an id, so a javascript can update its content later
        :type id: str, optional
        :param line: If set, the line in the layout is forced. Some layout don't have the notion of lines, so it might be skipped. If the line is needed
        by the layout and it is not specified, either tthere is an item in the column (in which case a new line is created) or not (in which case the column is filled)
        :type line: int, optional
        :return: True if success, False if the given information are not correct
        :rtype: bool
        """

        # Check that there is at least a module and a layout
        if not self.m_active_module or "layouts" not in self.m_modules[self.m_active_module]:
            return False

        # Try to find the layout
        if layout_id == -1:
            layout_id = self.g_next_layout - 1

        layout = self.find_layout(self.m_modules[self.m_active_module]["layouts"], layout_id)
        if not layout:
            return False

        if layout["type"] == Layouts.VERTICAL.value:
            # Check that there is enought columns
            if column >= len(layout["containers"]):
                return False

        elif layout["type"] == Layouts.TABLE.value:
            # Do we have at least a line?
            if not layout["lines"]:
                layout["lines"] = [[[] for _ in range(len(layout["header"]))]]

            if line == -1:
                # Check if we need to create a new line
                if layout["lines"][-1][column]:
                    layout["lines"].append([[] for _ in range(len(layout["header"]))])
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

        return True
    
    def add_modal(self, id: str, modal: str, header: str = "") -> None:
        self.m_modals.append({"id": id, "content": modal.display(), "header": header})

        return

    def add_table_layout(self, header: list = [], subtitle=None) -> int:
        if "layouts" not in self.m_modules[self.m_active_module]:
            self.m_modules[self.m_active_module]["layouts"] = []

        current_layout = {"type": Layouts.TABLE.value}
        current_layout["header"] = header
        current_layout["lines"] = None
        current_layout["subtitle"] = subtitle
        self.m_modules[self.m_active_module]["layouts"].append(current_layout)
        self.m_current_layout = len(self.m_modules[self.m_active_module]["layouts"]) - 1

        return len(self.m_modules[self.m_active_module]["layouts"]) - 1

    def add_slave_layout(
        self,
        layout: DisplayerLayout,
        column: int = 0,
        layout_id: int = -1,
        line: int = -1,
    ):
        if layout_id == -1:
            layout_id = self.g_next_layout - 1

        master_layout = self.find_layout(self.m_modules[self.m_active_module]["layouts"], layout_id)
        if not master_layout:
            return -1

        if layout.m_type == Layouts.VERTICAL.value:
            # Check that there is enought columns
            if column >= len(master_layout["containers"]):
                return -1

        # Add the display item
        if layout.m_type == Layouts.VERTICAL.value:
            layout.display(master_layout["containers"][column], self.g_next_layout)
            self.g_next_layout += 1
            return self.g_next_layout - 1
            

    def add_master_layout(self, layout: DisplayerLayout) -> None:
        if "layouts" not in self.m_modules[self.m_active_module]:
            self.m_modules[self.m_active_module]["layouts"] = []

        self.m_last_layout = layout
        layout.display(self.m_modules[self.m_active_module]["layouts"], self.g_next_layout)
        self.g_next_layout += 1
        return self.g_next_layout - 1

    def duplicate_master_layout(self) -> None:
        """Add a new layout, identical to the previous one"""
        if self.m_last_layout:
            self.m_last_layout.display(self.m_modules[self.m_active_module]["layouts"], self.g_next_layout)
            self.g_next_layout += 1
            return self.g_next_layout - 1

        return None

    def display(self, bypass_auth: bool = False) -> dict:
        """Return the information to pass to the template

        :return: The dictionnary needed for the template to display
        :rtype: dict
        """
        serve_modules = {}
        serve_modules["modals"] = self.m_modals

        for module in self.m_modules:  
            if not bypass_auth:
                auth = access_manager.auth_object.authorize_module(module)
            else: 
                auth = True
            if auth:
                serve_modules[module] = self.m_modules[module]

        return serve_modules

    def set_default_layout(self, id: int) -> None:
        """Impose the default layout back to a given one so that for any future item added, if layout is not specified, the layout id will be this one

        :param id: A new layout id
        :type id: int
        """
        self.g_next_layout = id
        return
