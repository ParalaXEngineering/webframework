"""
Displayer system for creating dynamic web page interfaces.

The displayer system provides a structured way to build web interfaces using:
- Layouts: Organize content (VERTICAL, HORIZONTAL, TABLE, TABS, SPACER)
- Items: Individual UI components (text, inputs, buttons, images, etc.)
- Modules: Grouped sections of content
- Resources: Automatic CSS/JS dependency management

Example:
    >>> from src.modules.displayer import Displayer, DisplayerLayout, Layouts
    >>> from src.modules.displayer import DisplayerItemText, DisplayerItemButton
    >>> 
    >>> disp = Displayer()
    >>> disp.add_generic("MyPage")
    >>> layout_id = disp.add_master_layout(DisplayerLayout(Layouts.HORIZONTAL, columns=[8, 4]))
    >>> disp.add_display_item(DisplayerItemText("Welcome!"), column=0)
    >>> disp.add_display_item(DisplayerItemButton("Click Me", "/action"), column=1)
    >>> data = disp.display()
"""

# Core components
from .core import (
    ResourceRegistry,
    DisplayerCategory,
    Layouts,
    TableMode,
    DisplayerItems,
    BSstyle,
    BSalign,
    MAZERStyles
)

# Layout system
from .layout import DisplayerLayout

# Main displayer class
from .displayer import Displayer

# All displayer items
from .items import (
    DisplayerItem,
    DisplayerItemPlaceholder,
    DisplayerItemAlert,
    DisplayerItemText,
    DisplayerItemSeparator,
    DisplayerItemHidden,
    DisplayerItemIconLink,
    DisplayerItemButtonLink,
    DisplayerItemButton,
    DisplayerItemModalButton,
    DisplayerItemModalLink,
    DisplayerItemBadge,
    DisplayerItemDownload,
    DisplayerItemImage,
    DisplayerItemFile,
    DisplayerItemInputBox,
    DisplayerItemGraph,
    DisplayerItemInputFileExplorer,
    DisplayerItemInputCascaded,
    DisplayerItemInputSelect,
    DisplayerItemInputMultiSelect,
    DisplayerItemInputMapping,
    DisplayerItemInputListSelect,
    DisplayerItemInputTextSelect,
    DisplayerItemInputSelectText,
    DisplayerItemInputDualTextSelect,
    DisplayerItemInputDualSelectText,
    DisplayerItemInputTextText,
    DisplayerItemInputListText,
    DisplayerItemInputNumeric,
    DisplayerItemInputDate,
    DisplayerItemInputText,
    DisplayerItemInputTextJS,
    DisplayerItemInputString,
    DisplayerItemInputStringIcon,
    DisplayerItemInputMultiText,
    DisplayerItemInputFolder,
    DisplayerItemInputFile,
    DisplayerItemInputImage,
    DisplayerItemCalendar,
    # New items
    DisplayerItemCard,
    DisplayerItemAlertBox,
    DisplayerItemDynamicContent,
    DisplayerItemButtonGroup,
    DisplayerItemIconText,
)

__all__ = [
    # Core
    'ResourceRegistry',
    'DisplayerCategory',
    'Layouts',
    'DisplayerItems',
    'BSstyle',
    'BSalign',
    'MAZERStyles',
    
    # Main classes
    'Displayer',
    'DisplayerLayout',
    'DisplayerItem',
    
    # Display items
    'DisplayerItemPlaceholder',
    'DisplayerItemAlert',
    'DisplayerItemText',
    'DisplayerItemSeparator',
    'DisplayerItemHidden',
    'DisplayerItemIconLink',
    'DisplayerItemButtonLink',
    'DisplayerItemButton',
    'DisplayerItemModalButton',
    'DisplayerItemModalLink',
    'DisplayerItemBadge',
    'DisplayerItemDownload',
    'DisplayerItemImage',
    'DisplayerItemFile',
    'DisplayerItemInputBox',
    'DisplayerItemGraph',
    
    # Input items
    'DisplayerItemInputFileExplorer',
    'DisplayerItemInputCascaded',
    'DisplayerItemInputSelect',
    'DisplayerItemInputMultiSelect',
    'DisplayerItemInputMapping',
    'DisplayerItemInputListSelect',
    'DisplayerItemInputTextSelect',
    'DisplayerItemInputSelectText',
    'DisplayerItemInputDualTextSelect',
    'DisplayerItemInputDualSelectText',
    'DisplayerItemInputTextText',
    'DisplayerItemInputListText',
    'DisplayerItemInputNumeric',
    'DisplayerItemInputDate',
    'DisplayerItemInputText',
    'DisplayerItemInputTextJS',
    'DisplayerItemInputString',
    'DisplayerItemInputStringIcon',
    'DisplayerItemInputMultiText',
    'DisplayerItemInputFolder',
    'DisplayerItemInputFile',
    'DisplayerItemInputImage',
    
    # Advanced items
    'DisplayerItemCalendar',
    
    # New items
    'DisplayerItemCard',
    'DisplayerItemAlertBox',
    'DisplayerItemDynamicContent',
    'DisplayerItemButtonGroup',
    'DisplayerItemIconText',
]

# Backward compatibility aliases for clearer naming
# These allow old code to work while providing more intuitive names
DisplayerItemInputCheckbox = DisplayerItemInputBox
DisplayerItemInputKeyValue = DisplayerItemInputTextText
DisplayerItemInputTextList = DisplayerItemInputMultiText
DisplayerItemInputDropdownValue = DisplayerItemInputSelectText

# Add aliases to __all__ for public API
__all__.extend([
    'DisplayerItemInputCheckbox',
    'DisplayerItemInputKeyValue', 
    'DisplayerItemInputTextList',
    'DisplayerItemInputDropdownValue',
])
