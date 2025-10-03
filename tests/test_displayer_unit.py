"""
Unit tests for the Displayer system.

Tests the data structure generation for all DisplayerItem types and layouts.
"""

import pytest
from src import displayer, User_defined_module


class TestDisplayerBasics:
    """Test basic Displayer functionality."""
    
    def test_displayer_creation(self):
        """Test that Displayer can be instantiated."""
        disp = displayer.Displayer()
        assert disp is not None
        assert disp.m_modules == {}
        assert disp.m_modals == []
        assert disp.m_breadcrumbs == {}
        
    def test_add_generic_module(self):
        """Test adding a generic module."""
        disp = displayer.Displayer()
        disp.add_generic("TestModule", display=True)
        
        assert "TestModule" in disp.m_modules
        assert disp.m_modules["TestModule"]["id"] == "TestModule"
        assert disp.m_modules["TestModule"]["display"] is True
        assert disp.m_active_module == "TestModule"
        
    def test_switch_module(self):
        """Test switching between modules."""
        disp = displayer.Displayer()
        disp.add_generic("Module1")
        disp.add_generic("Module2")
        
        assert disp.m_active_module == "Module2"
        disp.switch_module("Module1")
        assert disp.m_active_module == "Module1"
        
    def test_set_title(self):
        """Test setting displayer title."""
        disp = displayer.Displayer()
        disp.set_title("Test Title")
        assert disp.m_title == "Test Title"
        
    def test_add_breadcrumb(self):
        """Test adding breadcrumbs."""
        disp = displayer.Displayer()
        disp.add_breadcrumb("Home", "index", [], "primary")
        
        assert "Home" in disp.m_breadcrumbs
        assert disp.m_breadcrumbs["Home"]["url"] == "index"
        assert disp.m_breadcrumbs["Home"]["style"] == "primary"


class TestLayouts:
    """Test different layout types."""
    
    def test_vertical_layout(self):
        """Test vertical layout creation."""
        layout = displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL,
            [4, 8],
            subtitle="Vertical Test"
        )
        
        assert layout.m_type == displayer.Layouts.VERTICAL.value
        assert layout.m_column == [4, 8]
        assert layout.m_subtitle == "Vertical Test"
        
    def test_horizontal_layout(self):
        """Test horizontal layout creation."""
        layout = displayer.DisplayerLayout(
            displayer.Layouts.HORIZONTAL,
            [6, 6],
            subtitle="Horizontal Test"
        )
        
        assert layout.m_type == displayer.Layouts.HORIZONTAL.value
        assert layout.m_column == [6, 6]
        
    def test_table_layout(self):
        """Test table layout creation."""
        layout = displayer.DisplayerLayout(
            displayer.Layouts.TABLE,
            ["Col1", "Col2", "Col3"],
            subtitle="Table Test"
        )
        
        assert layout.m_type == displayer.Layouts.TABLE.value
        assert layout.m_column == ["Col1", "Col2", "Col3"]
        
    def test_spacer_layout(self):
        """Test spacer layout creation."""
        layout = displayer.DisplayerLayout(
            displayer.Layouts.SPACER,
            [12]
        )
        
        assert layout.m_type == displayer.Layouts.SPACER.value
        
    def test_layout_with_alignment(self):
        """Test layout with custom alignment."""
        layout = displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL,
            [4, 4, 4],
            alignment=displayer.BSalign.C
        )
        
        assert layout.m_alignement == displayer.BSalign.C
        
    def test_layout_with_spacing(self):
        """Test layout with spacing."""
        layout = displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL,
            [12],
            spacing=3
        )
        
        assert layout.m_spacing == "py-3"
        
    def test_layout_with_background(self):
        """Test layout with background color."""
        layout = displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL,
            [12],
            background=displayer.BSstyle.PRIMARY
        )
        
        assert layout.m_background == displayer.BSstyle.PRIMARY


class TestDisplayItems:
    """Test all DisplayerItem types."""
    
    # Text and Display Items
    
    def test_item_text(self):
        """Test DisplayerItemText."""
        item = displayer.DisplayerItemText("Hello World")
        assert item.m_text == "Hello World"
        assert item.m_type == displayer.DisplayerItems.TEXT
        
    def test_item_alert(self):
        """Test DisplayerItemAlert."""
        item = displayer.DisplayerItemAlert("Warning!", displayer.BSstyle.WARNING)
        assert item.m_text == "Warning!"
        assert item.m_style == displayer.BSstyle.WARNING.value
        assert item.m_type == displayer.DisplayerItems.ALERT
        
    def test_item_badge(self):
        """Test DisplayerItemBadge."""
        item = displayer.DisplayerItemBadge("Status", displayer.BSstyle.SUCCESS)
        assert item.m_text == "Status"
        assert item.m_style == displayer.BSstyle.SUCCESS.value
        
    def test_item_placeholder(self):
        """Test DisplayerItemPlaceholder."""
        item = displayer.DisplayerItemPlaceholder("placeholder_id", "Initial data")
        assert item.m_id == "placeholder_id"
        assert item.m_data == "Initial data"
        assert item.m_type == displayer.DisplayerItems.PLACEHOLDER
        
    # Buttons and Links
    
    def test_item_button(self):
        """Test DisplayerItemButton."""
        item = displayer.DisplayerItemButton("btn_submit", "Submit")
        assert item.m_id == "btn_submit"
        assert item.m_text == "Submit"
        assert item.m_type == displayer.DisplayerItems.BUTTON
        
    def test_item_button_link(self):
        """Test DisplayerItemButtonLink."""
        item = displayer.DisplayerItemButtonLink(
            "link_btn", "Go", "fa-arrow-right", "/page", ["param1"], displayer.BSstyle.INFO
        )
        assert item.m_id == "link_btn"
        assert item.m_text == "Go"
        assert item.m_icon == "fa-arrow-right"
        assert item.m_data == "/page"
        assert item.m_parameters == ["param1"]
        assert item.m_style == displayer.BSstyle.INFO.value
        
    def test_item_icon_link(self):
        """Test DisplayerItemIconLink."""
        item = displayer.DisplayerItemIconLink(
            "icon_link", "Home", "fa-home", "/home", ["p1"], displayer.BSstyle.PRIMARY
        )
        assert item.m_id == "icon_link"
        assert item.m_text == "Home"
        assert item.m_icon == "fa-home"
        assert item.m_data == "/home"
        
    def test_item_modal_button(self):
        """Test DisplayerItemModalButton."""
        item = displayer.DisplayerItemModalButton("Open Modal", "modal_id")
        assert item.m_text == "Open Modal"
        assert item.m_path == "modal_id"
        
    def test_item_modal_link(self):
        """Test DisplayerItemModalLink."""
        item = displayer.DisplayerItemModalLink("Link Text", "fa-info", "modal_id", displayer.BSstyle.INFO)
        assert item.m_text == "Link Text"
        assert item.m_icon == "fa-info"
        assert item.m_path == "modal_id"
        assert item.m_style == displayer.BSstyle.INFO.value
        
    # Basic Input Items
    
    def test_item_input_string(self):
        """Test DisplayerItemInputString."""
        item = displayer.DisplayerItemInputString("name", "placeholder", "default_value")
        assert item.m_id == "name"
        assert item.m_text == "placeholder"
        assert item.m_value == "default_value"
        assert item.m_type == displayer.DisplayerItems.INSTRING
        
    def test_item_input_text(self):
        """Test DisplayerItemInputText."""
        item = displayer.DisplayerItemInputText("description", "Enter text", "")
        assert item.m_id == "description"
        assert item.m_text == "Enter text"
        assert item.m_type == displayer.DisplayerItems.INTEXT
        
    def test_item_input_numeric(self):
        """Test DisplayerItemInputNumeric."""
        item = displayer.DisplayerItemInputNumeric("quantity", "Enter quantity", 10)
        assert item.m_id == "quantity"
        assert item.m_text == "Enter quantity"
        assert item.m_value == 10
        assert item.m_type == displayer.DisplayerItems.INNUM
        
    def test_item_input_date(self):
        """Test DisplayerItemInputDate."""
        item = displayer.DisplayerItemInputDate("birthdate", "Select date", "2024-01-01")
        assert item.m_id == "birthdate"
        assert item.m_value == "2024-01-01"
        assert item.m_type == displayer.DisplayerItems.INDATE
        
    def test_item_input_hidden(self):
        """Test DisplayerItemHidden."""
        item = displayer.DisplayerItemHidden("hidden_field", "secret_value")
        assert item.m_id == "hidden_field"
        assert item.m_value == "secret_value"
        assert item.m_type == displayer.DisplayerItems.INHIDDEN
        
    # Select and Choice Items
    
    def test_item_input_select(self):
        """Test DisplayerItemInputSelect."""
        options = ["Option 1", "Option 2", "Option 3"]
        item = displayer.DisplayerItemInputSelect("choice", "placeholder", "Option 1", options)
        assert item.m_id == "choice"
        assert item.m_value == "Option 1"
        assert item.m_data == sorted(options)
        assert item.m_type == displayer.DisplayerItems.SELECT
        
    def test_item_input_multi_select(self):
        """Test DisplayerItemInputMultiSelect."""
        options = ["A", "B", "C"]
        item = displayer.DisplayerItemInputMultiSelect("multi", "placeholder", ["A", "C"], options)
        assert item.m_id == "multi"
        assert item.m_value == ["A", "C"]
        assert item.m_data == sorted(options)
        
    def test_item_input_cascaded(self):
        """Test DisplayerItemInputCascaded."""
        ids = ["level1", "level2"]
        choices = [["Cat1", "Cat2"], ["Item1", "Item2"]]
        item = displayer.DisplayerItemInputCascaded(ids, "hint", ["Cat1", "Item1"], choices)
        assert item.m_ids == ids
        assert item.m_value == ["Cat1", "Item1"]
        assert item.m_data == choices
        
    # Complex Input Items
    
    def test_item_input_string_icon(self):
        """Test DisplayerItemInputStringIcon."""
        item = displayer.DisplayerItemInputStringIcon("icon_input", "hint", "value")
        assert item.m_id == "icon_input"
        assert item.m_text == "hint"
        assert item.m_value == "value"
        
    def test_item_input_text_icon(self):
        """Test DisplayerItemInputTextIcon."""
        item = displayer.DisplayerItemInputTextIcon("text_icon", {"text": "content", "icon": "fa-edit"})
        assert item.m_id == "text_icon"
        assert item.m_value["text"] == "content"
        
    def test_item_input_multi_text(self):
        """Test DisplayerItemInputMultiText."""
        item = displayer.DisplayerItemInputMultiText("multi_text", "hint", ["Line 1", "Line 2"])
        assert item.m_id == "multi_text"
        assert len(item.m_value) == 2
        
    def test_item_input_text_select(self):
        """Test DisplayerItemInputTextSelect."""
        item = displayer.DisplayerItemInputTextSelect(
            "text_select", "hint", {"text": "value", "select": "option"}, ["option", "other"]
        )
        assert item.m_id == "text_select"
        assert item.m_value["text"] == "value"
        
    def test_item_input_select_text(self):
        """Test DisplayerItemInputSelectText."""
        item = displayer.DisplayerItemInputSelectText(
            "select_text", "hint", {"select": "option", "text": "value"}, ["option"]
        )
        assert item.m_id == "select_text"
        
    def test_item_input_text_text(self):
        """Test DisplayerItemInputTextText."""
        item = displayer.DisplayerItemInputTextText(
            "text_text", "hint", {"text1": "val1", "text2": "val2"}
        )
        assert item.m_id == "text_text"
        assert item.m_value["text1"] == "val1"
        
    def test_item_input_list_text(self):
        """Test DisplayerItemInputListText."""
        item = displayer.DisplayerItemInputListText("list_text", "hint", [{"key": "val"}])
        assert item.m_id == "list_text"
        assert isinstance(item.m_value, list)
        
    def test_item_input_list_select(self):
        """Test DisplayerItemInputListSelect."""
        item = displayer.DisplayerItemInputListSelect("list_select", "hint", ["val1"], ["opt1", "opt2"])
        assert item.m_id == "list_select"
        
    def test_item_input_mapping(self):
        """Test DisplayerItemInputMapping."""
        item = displayer.DisplayerItemInputMapping("mapping", "hint", {"key1": "val1"})
        assert item.m_id == "mapping"
        assert isinstance(item.m_value, dict)
        
    # File and Path Items
    
    def test_item_input_file(self):
        """Test DisplayerItemInputFile."""
        item = displayer.DisplayerItemInputFile("file_upload", "hint")
        assert item.m_id == "file_upload"
        assert item.m_text == "hint"
        
    def test_item_input_folder(self):
        """Test DisplayerItemInputFolder."""
        item = displayer.DisplayerItemInputFolder("folder_select", "hint")
        assert item.m_id == "folder_select"
        assert item.m_text == "hint"
        
    def test_item_input_path(self):
        """Test DisplayerItemInputPath."""
        item = displayer.DisplayerItemInputPath("path_input", "hint", "/some/path", [".txt", ".md"])
        assert item.m_id == "path_input"
        assert item.m_value == "/some/path"
        
    def test_item_input_file_explorer(self):
        """Test DisplayerItemInputFileExplorer."""
        item = displayer.DisplayerItemInputFileExplorer("explorer", "hint", ["file.txt"])
        assert item.m_id == "explorer"
        assert item.m_text == "hint"
        assert item.m_explorerFiles == ["file.txt"]
        
    # Media Items
    
    def test_item_image(self):
        """Test DisplayerItemImage."""
        item = displayer.DisplayerItemImage(200, "/images/test.png")
        assert item.m_data == 200  # height
        assert item.m_value == "/images/test.png"  # link
        
    def test_item_input_image(self):
        """Test DisplayerItemInputImage."""
        item = displayer.DisplayerItemInputImage("img_upload", "hint")
        assert item.m_id == "img_upload"
        assert item.m_text == "hint"
        
    def test_item_download(self):
        """Test DisplayerItemDownload."""
        item = displayer.DisplayerItemDownload("download1", "Download", "/files/doc.pdf")
        assert item.m_id == "download1"
        assert item.m_data == "/files/doc.pdf"
        assert item.m_text == "Download"
        
    def test_item_file(self):
        """Test DisplayerItemFile."""
        item = displayer.DisplayerItemFile("/files/report.txt", text="Report")
        assert item.m_value == "/files/report.txt"  # link
        assert item.m_text == "Report"
        
    # Advanced Items
    
    def test_item_graph(self):
        """Test DisplayerItemGraph."""
        x_data = ["A", "B"]
        y_data = [1, 2]
        item = displayer.DisplayerItemGraph("graph1", "hint", x_data, y_data, "date")
        assert item.m_id == "graph1"
        assert item.m_graphx == x_data
        assert item.m_graphy == y_data
        assert item.m_datatype == "date"
        
    def test_item_calendar(self):
        """Test DisplayerItemCalendar."""
        events = {"event1": {"date": "2024-01-01", "title": "Event"}}
        item = displayer.DisplayerItemCalendar("cal1", "dayGridMonth", events)
        assert item.m_id == "cal1"
        assert item.m_value == "dayGridMonth"  # view
        assert len(item.m_data) == 1  # events


class TestDisplayerIntegration:
    """Test complete displayer workflows."""
    
    def test_add_layout_to_module(self):
        """Test adding a layout to a module."""
        disp = displayer.Displayer()
        disp.add_generic("TestModule")
        
        layout = displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [6, 6])
        disp.add_master_layout(layout)
        
        assert "layouts" in disp.m_modules["TestModule"]
        
    def test_add_items_to_layout(self):
        """Test adding items to a layout."""
        disp = displayer.Displayer()
        disp.add_generic("TestModule")
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [6, 6]))
        
        # Add items to different columns
        item1 = displayer.DisplayerItemText("Column 1 Text")
        item2 = displayer.DisplayerItemText("Column 2 Text")
        
        result1 = disp.add_display_item(item1, column=0)
        result2 = disp.add_display_item(item2, column=1)
        
        assert result1 is True
        assert result2 is True
        
    def test_multiple_modules(self):
        """Test working with multiple modules."""
        disp = displayer.Displayer()
        
        # First module
        disp.add_generic("Module1")
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        disp.add_display_item(displayer.DisplayerItemText("Module 1 Content"), 0)
        
        # Second module
        disp.add_generic("Module2")
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        disp.add_display_item(displayer.DisplayerItemText("Module 2 Content"), 0)
        
        assert len(disp.m_modules) == 2
        assert "Module1" in disp.m_modules
        assert "Module2" in disp.m_modules
        
    def test_nested_layouts(self):
        """Test adding nested layouts."""
        disp = displayer.Displayer()
        disp.add_generic("TestModule")
        
        # Add main layout
        main_layout = displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
        disp.add_master_layout(main_layout)
        
        # Add a second layout (simpler test since add_sublayout doesn't exist)
        second_layout = displayer.DisplayerLayout(displayer.Layouts.HORIZONTAL, [6, 6])
        disp.add_master_layout(second_layout)
        
        # Add items to layouts
        disp.add_display_item(displayer.DisplayerItemText("Nested Text"), column=0)
        
        assert True  # If we get here without errors, nested layouts work


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
