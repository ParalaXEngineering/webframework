"""
Unit tests for dynamic resource loading in the displayer system.

Tests verify that:
1. Items with required resources trigger resource registration
2. Layouts (especially tables) trigger appropriate resource registration
3. HTML output includes the correct CSS/JS files based on registered resources
4. Resources are properly reset between renders
"""

import os
from src.displayer import (
    Displayer,
    DisplayerLayout,
    Layouts,
    DisplayerItemGraph,
    DisplayerItemCalendar,
    DisplayerItemInputFile,
    DisplayerItemInputFolder,
    DisplayerItemInputImage,
    DisplayerItemText,
    ResourceRegistry,
)


def check_html_for_resources(test_name: str, expected_resources: list, unexpected_resources: list = None):
    """
    Helper to check if generated HTML contains expected resources.
    
    :param test_name: Name of the test item (e.g., 'DisplayerItemInputFile')
    :param expected_resources: List of strings that should be in the HTML
    :param unexpected_resources: List of strings that should NOT be in the HTML
    :return: tuple of (has_expected, missing, has_unexpected)
    """
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    html_file = os.path.join(output_dir, f"item_{test_name}.html")
    
    if not os.path.exists(html_file):
        return False, expected_resources, []
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    missing = [res for res in expected_resources if res not in html]
    
    if unexpected_resources:
        found_unexpected = [res for res in unexpected_resources if res in html]
    else:
        found_unexpected = []
    
    has_all_expected = len(missing) == 0
    has_no_unexpected = len(found_unexpected) == 0
    
    return has_all_expected and has_no_unexpected, missing, found_unexpected


class TestResourceRegistry:
    """Test the ResourceRegistry class directly."""
    
    def test_registry_reset(self):
        """Test that registry can be reset."""
        ResourceRegistry.require('datatables')
        assert 'datatables' in ResourceRegistry._required_vendors
        
        ResourceRegistry.reset()
        assert len(ResourceRegistry._required_vendors) == 0
    
    def test_require_single_resource(self):
        """Test requiring a single resource."""
        ResourceRegistry.reset()
        ResourceRegistry.require('apexcharts')
        
        assert 'apexcharts' in ResourceRegistry._required_vendors
        js_cdn = ResourceRegistry.get_required_js_cdn()
        assert 'https://cdn.jsdelivr.net/npm/apexcharts' in js_cdn
    
    def test_require_multiple_resources(self):
        """Test requiring multiple resources at once."""
        ResourceRegistry.reset()
        ResourceRegistry.require('datatables', 'sweetalert', 'filepond')
        
        assert 'datatables' in ResourceRegistry._required_vendors
        assert 'sweetalert' in ResourceRegistry._required_vendors
        assert 'filepond' in ResourceRegistry._required_vendors
        
        css = ResourceRegistry.get_required_css()
        js = ResourceRegistry.get_required_js()
        
        # Check CSS includes
        assert any('datatables' in path for path in css)
        assert any('sweetalert' in path for path in css)
        assert any('filepond' in path for path in css)
        
        # Check JS includes
        assert any('datatables' in path for path in js)
        assert any('sweetalert' in path for path in js)
        assert any('filepond' in path for path in js)
    
    def test_get_required_css(self):
        """Test getting required CSS files."""
        ResourceRegistry.reset()
        ResourceRegistry.require('datatables')
        
        css = ResourceRegistry.get_required_css()
        assert 'vendors/datatables.net/datatables.min.css' in css
    
    def test_get_required_js(self):
        """Test getting required JS files."""
        ResourceRegistry.reset()
        ResourceRegistry.require('datatables')
        
        js = ResourceRegistry.get_required_js()
        assert 'vendors/datatables.net/datatables.min.js' in js
        assert 'js/datatables-init.js' in js
    
    def test_get_required_cdn(self):
        """Test getting required CDN resources."""
        ResourceRegistry.reset()
        ResourceRegistry.require('apexcharts')
        
        cdn = ResourceRegistry.get_required_js_cdn()
        assert 'https://cdn.jsdelivr.net/npm/apexcharts' in cdn


class TestDisplayerItemResources:
    """Test that displayer items register their required resources."""
    
    def test_graph_requires_apexcharts(self):
        """Test that Graph items require ApexCharts."""
        ResourceRegistry.reset()
        disp = Displayer()
        disp.add_generic("Test")
        
        layout = DisplayerLayout(Layouts.VERTICAL, [12])
        disp.add_master_layout(layout)
        
        graph = DisplayerItemGraph(
            id="test_graph",
            text="Test Graph",
            x=[1640995200000, 1641081600000],
            y={"Series1": [10, 20]},
            data_type="date"
        )
        
        disp.add_display_item(graph)
        
        # Check that apexcharts was registered
        assert 'apexcharts' in ResourceRegistry._required_vendors
        
        # Check that CDN is in required resources
        cdn = ResourceRegistry.get_required_js_cdn()
        assert 'https://cdn.jsdelivr.net/npm/apexcharts' in cdn
    
    def test_calendar_requires_fullcalendar(self):
        """Test that Calendar items require FullCalendar."""
        ResourceRegistry.reset()
        disp = Displayer()
        disp.add_generic("Test")
        
        layout = DisplayerLayout(Layouts.VERTICAL, [12])
        disp.add_master_layout(layout)
        
        calendar = DisplayerItemCalendar(
            id="test_calendar",
            view="dayGridMonth",
            events={}
        )
        
        disp.add_display_item(calendar)
        
        # Check that fullcalendar was registered
        assert 'fullcalendar' in ResourceRegistry._required_vendors
        
        # Check that JS is in required resources
        js = ResourceRegistry.get_required_js()
        assert any('fullcalendar' in path for path in js)
    
    def test_file_input_requires_filepond(self):
        """Test that File input items require FilePond."""
        ResourceRegistry.reset()
        disp = Displayer()
        disp.add_generic("Test")
        
        layout = DisplayerLayout(Layouts.VERTICAL, [12])
        disp.add_master_layout(layout)
        
        file_input = DisplayerItemInputFile(
            id="test_file",
            text="Upload File"
        )
        
        disp.add_display_item(file_input)
        
        # Check that filepond was registered
        assert 'filepond' in ResourceRegistry._required_vendors
        
        # Check CSS and JS
        css = ResourceRegistry.get_required_css()
        js = ResourceRegistry.get_required_js()
        
        assert any('filepond' in path for path in css)
        assert any('filepond' in path for path in js)
        assert 'js/filepond-init.js' in js
    
    def test_folder_input_requires_filepond(self):
        """Test that Folder input items require FilePond."""
        ResourceRegistry.reset()
        disp = Displayer()
        disp.add_generic("Test")
        
        layout = DisplayerLayout(Layouts.VERTICAL, [12])
        disp.add_master_layout(layout)
        
        folder_input = DisplayerItemInputFolder(
            id="test_folder",
            text="Select Folder"
        )
        
        disp.add_display_item(folder_input)
        
        # Check that filepond was registered
        assert 'filepond' in ResourceRegistry._required_vendors
    
    def test_image_input_requires_filepond(self):
        """Test that Image input items require FilePond."""
        ResourceRegistry.reset()
        disp = Displayer()
        disp.add_generic("Test")
        
        layout = DisplayerLayout(Layouts.VERTICAL, [12])
        disp.add_master_layout(layout)
        
        image_input = DisplayerItemInputImage(
            id="test_image",
            text="Upload Image"
        )
        
        disp.add_display_item(image_input)
        
        # Check that filepond was registered
        assert 'filepond' in ResourceRegistry._required_vendors
    
    def test_text_item_no_resources(self):
        """Test that simple text items don't require special resources."""
        ResourceRegistry.reset()
        disp = Displayer()
        disp.add_generic("Test")
        
        layout = DisplayerLayout(Layouts.VERTICAL, [12])
        disp.add_master_layout(layout)
        
        text_item = DisplayerItemText(text="Simple text")
        disp.add_display_item(text_item)
        
        # Should have no special resources registered
        assert len(ResourceRegistry._required_vendors) == 0
    
    def test_input_text_requires_tinymce(self):
        """Test that InputText (textarea) items require TinyMCE."""
        ResourceRegistry.reset()
        disp = Displayer()
        disp.add_generic("Test")
        
        layout = DisplayerLayout(Layouts.VERTICAL, [12])
        disp.add_master_layout(layout)
        
        from src.displayer import DisplayerItemInputText
        text_input = DisplayerItemInputText(
            id="test_textarea",
            text="Enter description",
            value="Initial text"
        )
        
        disp.add_display_item(text_input)
        
        # Check that tinymce was registered
        assert 'tinymce' in ResourceRegistry._required_vendors
        
        # Check that JS is in required resources
        js = ResourceRegistry.get_required_js()
        assert any('tinymce' in path for path in js)


class TestLayoutResources:
    """Test that layouts register their required resources."""
    
    def test_table_layout_requires_datatables(self):
        """Test that TABLE layout with responsive option requires DataTables."""
        ResourceRegistry.reset()
        disp = Displayer()
        disp.add_generic("Test")
        
        # Create a responsive table layout
        layout = DisplayerLayout(
            Layouts.TABLE,
            columns=["Column 1", "Column 2", "Column 3"],
            responsive={"test_table": {"type": "basic"}}
        )
        disp.add_master_layout(layout)
        
        # Check that datatables was registered
        assert 'datatables' in ResourceRegistry._required_vendors
        
        # Check CSS and JS
        css = ResourceRegistry.get_required_css()
        js = ResourceRegistry.get_required_js()
        
        assert 'vendors/datatables.net/datatables.min.css' in css
        assert 'vendors/datatables.net/datatables.min.js' in js
        assert 'js/datatables-init.js' in js
    
    def test_vertical_layout_no_resources(self):
        """Test that simple vertical layouts don't require resources."""
        ResourceRegistry.reset()
        disp = Displayer()
        disp.add_generic("Test")
        
        layout = DisplayerLayout(Layouts.VERTICAL, [6, 6])
        disp.add_master_layout(layout)
        
        # Should have no resources registered
        assert len(ResourceRegistry._required_vendors) == 0
    
    def test_horizontal_layout_no_resources(self):
        """Test that simple horizontal layouts don't require resources."""
        ResourceRegistry.reset()
        disp = Displayer()
        disp.add_generic("Test")
        
        layout = DisplayerLayout(Layouts.HORIZONTAL, [12])
        disp.add_master_layout(layout)
        
        # Should have no resources registered
        assert len(ResourceRegistry._required_vendors) == 0


class TestResourceAccumulation:
    """Test that resources accumulate correctly during displayer build."""
    
    def test_multiple_items_accumulate_resources(self):
        """Test that multiple items with different resources accumulate correctly."""
        ResourceRegistry.reset()
        disp = Displayer()
        disp.add_generic("Complex Page")
        
        layout = DisplayerLayout(Layouts.VERTICAL, [6, 6])
        disp.add_master_layout(layout)
        
        # Add graph (needs apexcharts)
        graph = DisplayerItemGraph(
            id="graph1",
            x=[1640995200000],
            y={"Series": [10]}
        )
        disp.add_display_item(graph, column=0)
        
        # Add file input (needs filepond)
        file_input = DisplayerItemInputFile(id="file1", text="Upload")
        disp.add_display_item(file_input, column=1)
        
        # Check that both resources are registered
        assert 'apexcharts' in ResourceRegistry._required_vendors
        assert 'filepond' in ResourceRegistry._required_vendors
        
        # Check that we get resources from both
        cdn = ResourceRegistry.get_required_js_cdn()
        js = ResourceRegistry.get_required_js()
        css = ResourceRegistry.get_required_css()
        
        assert 'https://cdn.jsdelivr.net/npm/apexcharts' in cdn
        assert any('filepond' in path for path in js)
        assert any('filepond' in path for path in css)


class TestResourceReset:
    """Test that resources are properly reset between page renders."""
    
    def test_displayer_init_resets_resources(self):
        """Test that creating a new Displayer resets the resource registry."""
        ResourceRegistry.reset()
        ResourceRegistry.require('datatables', 'apexcharts')
        
        assert len(ResourceRegistry._required_vendors) == 2
        
        # Create new displayer - should reset
        _disp = Displayer()
        
        assert len(ResourceRegistry._required_vendors) == 0
    
    def test_multiple_displayers_independent(self):
        """Test that multiple displayer instances don't accumulate resources."""
        # First displayer with graph
        disp1 = Displayer()
        disp1.add_generic("Page 1")
        layout1 = DisplayerLayout(Layouts.VERTICAL, [12])
        disp1.add_master_layout(layout1)
        graph = DisplayerItemGraph(id="g1", x=[1], y={"S": [1]})
        disp1.add_display_item(graph)
        
        # Verify apexcharts is registered
        assert 'apexcharts' in ResourceRegistry._required_vendors
        cdn1 = ResourceRegistry.get_required_js_cdn()
        assert 'apexcharts' in str(cdn1)
        
        # Second displayer with file input (should reset and not have apexcharts)
        disp2 = Displayer()
        disp2.add_generic("Page 2")
        layout2 = DisplayerLayout(Layouts.VERTICAL, [12])
        disp2.add_master_layout(layout2)
        file_input = DisplayerItemInputFile(id="f1", text="Upload")
        disp2.add_display_item(file_input)
        
        # Verify filepond is registered but apexcharts is not
        assert 'filepond' in ResourceRegistry._required_vendors
        assert 'apexcharts' not in ResourceRegistry._required_vendors
        
        js2 = ResourceRegistry.get_required_js()
        cdn2 = ResourceRegistry.get_required_js_cdn()
        assert any('filepond' in path for path in js2)
        assert 'apexcharts' not in str(cdn2)


class TestHTMLResourceInclusion:
    """Test that generated HTML actually includes the required resources."""
    
    def test_file_input_html_has_filepond(self):
        """Test that DisplayerItemInputFile HTML includes FilePond resources."""
        success, missing, unexpected = check_html_for_resources(
            'DisplayerItemInputFile',
            expected_resources=[
                'filepond.min.css',
                'filepond.min.js',
                'filepond-init.js'
            ],
            unexpected_resources=[
                'apexcharts',
                'fullcalendar',
                'datatables.min.js'
            ]
        )
        
        assert success, f"Missing resources: {missing}, Unexpected resources: {unexpected}"
    
    def test_graph_html_has_apexcharts(self):
        """Test that DisplayerItemGraph HTML includes ApexCharts CDN."""
        success, missing, unexpected = check_html_for_resources(
            'DisplayerItemGraph',
            expected_resources=[
                'cdn.jsdelivr.net/npm/apexcharts'
            ],
            unexpected_resources=[
                'filepond',
                'fullcalendar',
                'datatables.min.js'
            ]
        )
        
        assert success, f"Missing resources: {missing}, Unexpected resources: {unexpected}"
    
    def test_calendar_html_has_fullcalendar(self):
        """Test that DisplayerItemCalendar HTML includes FullCalendar."""
        success, missing, unexpected = check_html_for_resources(
            'DisplayerItemCalendar',
            expected_resources=[
                'fullcalendar.min.js'
            ],
            unexpected_resources=[
                'filepond',
                'apexcharts',
                'datatables.min.js'
            ]
        )
        
        assert success, f"Missing resources: {missing}, Unexpected resources: {unexpected}"
    
    def test_text_html_has_no_vendor_resources(self):
        """Test that DisplayerItemText HTML has no vendor library resources."""
        success, missing, unexpected = check_html_for_resources(
            'DisplayerItemText',
            expected_resources=[
                # Only expect base CSS
                'app.css'
            ],
            unexpected_resources=[
                'filepond',
                'apexcharts',
                'fullcalendar',
                'datatables.min.js'
            ]
        )
        
        assert success, f"Missing resources: {missing}, Unexpected resources: {unexpected}"
