"""
Unit tests for DisplayerLayout module.

Tests layout creation, GRID validation, DataTable configuration,
and backward compatibility.
"""

import pytest
from src.modules.displayer.layout import DisplayerLayout
from src.modules.displayer.core import Layouts, BSalign, BSstyle, TableMode, MAZERStyles


class TestLayoutBasics:
    """Test basic layout creation and properties."""
    
    def test_vertical_layout_creation(self):
        """Test creating a basic VERTICAL layout."""
        layout = DisplayerLayout(
            layoutType=Layouts.VERTICAL,
            columns=[6, 6],
            alignment=[BSalign.L, BSalign.R]
        )
        
        assert layout.m_type == Layouts.VERTICAL.value
        assert layout.m_column == [6, 6]
        assert layout.m_alignement == [BSalign.L, BSalign.R]
    
    def test_horizontal_layout_creation(self):
        """Test creating a HORIZONTAL layout."""
        layout = DisplayerLayout(
            layoutType=Layouts.HORIZONTAL,
            columns=[12],
            alignment=BSalign.C
        )
        
        assert layout.m_type == Layouts.HORIZONTAL.value
        assert layout.m_column == [12]
        # Should normalize single alignment to list
        assert layout.m_alignement == [BSalign.C]
    
    def test_layout_with_spacing(self):
        """Test layout with integer spacing converts to py-{spacing}."""
        layout = DisplayerLayout(
            layoutType=Layouts.VERTICAL,
            columns=[12],
            spacing=3
        )
        
        assert layout.m_spacing == "py-3"
    
    def test_layout_with_large_spacing(self):
        """Test layout with spacing > 5 caps at py-5."""
        layout = DisplayerLayout(
            layoutType=Layouts.VERTICAL,
            columns=[12],
            spacing=10
        )
        
        assert layout.m_spacing == "py-5"
    
    def test_layout_with_string_spacing(self):
        """Test layout with custom string spacing."""
        layout = DisplayerLayout(
            layoutType=Layouts.VERTICAL,
            columns=[12],
            spacing="mt-3 mb-4"
        )
        
        assert layout.m_spacing == "mt-3 mb-4"
    
    def test_layout_with_background(self):
        """Test layout with background style."""
        layout = DisplayerLayout(
            layoutType=Layouts.VERTICAL,
            columns=[12],
            background=BSstyle.LIGHT
        )
        
        assert layout.m_background == BSstyle.LIGHT
    
    def test_layout_with_style(self):
        """Test layout with custom style."""
        layout = DisplayerLayout(
            layoutType=Layouts.VERTICAL,
            columns=[12],
            style=MAZERStyles.CARD
        )
        
        assert layout.m_style == MAZERStyles.CARD


class TestGridLayout:
    """Test GRID layout functionality."""
    
    def test_grid_layout_requires_config(self):
        """Test that GRID layout requires grid_config parameter."""
        with pytest.raises(ValueError, match="GRID layout requires grid_config"):
            DisplayerLayout(
                layoutType=Layouts.GRID,
                columns=[12]
            )
    
    def test_grid_layout_valid_config(self):
        """Test creating GRID layout with valid configuration."""
        grid_config = {
            "version": "1.0",
            "columns": 12,
            "items": [
                {"field_id": "item1", "x": 0, "y": 0, "w": 6, "h": 1},
                {"field_id": "item2", "x": 6, "y": 0, "w": 6, "h": 1}
            ]
        }
        
        layout = DisplayerLayout(
            layoutType=Layouts.GRID,
            grid_config=grid_config
        )
        
        assert layout.m_type == Layouts.GRID.value
        assert layout.m_grid_config == grid_config
    
    def test_grid_config_must_be_dict(self):
        """Test that grid_config must be a dictionary."""
        with pytest.raises(ValueError, match="grid_config must be a dictionary"):
            DisplayerLayout(
                layoutType=Layouts.GRID,
                grid_config="not a dict"
            )
    
    def test_grid_config_requires_items(self):
        """Test that grid_config must contain items key."""
        with pytest.raises(ValueError, match="must contain 'items' key"):
            DisplayerLayout(
                layoutType=Layouts.GRID,
                grid_config={"version": "1.0"}
            )
    
    def test_grid_items_must_be_list(self):
        """Test that items must be a list."""
        with pytest.raises(ValueError, match="must be a list"):
            DisplayerLayout(
                layoutType=Layouts.GRID,
                grid_config={"items": "not a list"}
            )
    
    def test_grid_item_must_be_dict(self):
        """Test that each grid item must be a dictionary."""
        with pytest.raises(ValueError, match="Item 0 must be a dictionary"):
            DisplayerLayout(
                layoutType=Layouts.GRID,
                grid_config={"items": ["not a dict"]}
            )
    
    def test_grid_item_requires_all_keys(self):
        """Test that grid items must have all required keys."""
        with pytest.raises(ValueError, match="Item 0 missing required key: h"):
            DisplayerLayout(
                layoutType=Layouts.GRID,
                grid_config={
                    "items": [{"field_id": "item1", "x": 0, "y": 0, "w": 6}]
                }
            )
    
    def test_grid_item_width_bounds(self):
        """Test that grid item width must be between 1 and 12."""
        with pytest.raises(ValueError, match="width .* must be between 1 and 12"):
            DisplayerLayout(
                layoutType=Layouts.GRID,
                grid_config={
                    "items": [{"field_id": "item1", "x": 0, "y": 0, "w": 15, "h": 1}]
                }
            )
    
    def test_grid_item_x_bounds(self):
        """Test that grid item x position must be valid."""
        with pytest.raises(ValueError, match="x position must be between 0 and 11"):
            DisplayerLayout(
                layoutType=Layouts.GRID,
                grid_config={
                    "items": [{"field_id": "item1", "x": 12, "y": 0, "w": 6, "h": 1}]
                }
            )
    
    def test_grid_item_exceeds_bounds(self):
        """Test that grid items cannot exceed 12-column bounds."""
        with pytest.raises(ValueError, match="exceeds grid bounds"):
            DisplayerLayout(
                layoutType=Layouts.GRID,
                grid_config={
                    "items": [{"field_id": "item1", "x": 8, "y": 0, "w": 6, "h": 1}]
                }
            )
    
    def test_grid_layout_display(self):
        """Test grid layout display output structure."""
        grid_config = {
            "items": [
                {"field_id": "item1", "x": 0, "y": 0, "w": 6, "h": 1},
                {"field_id": "item2", "x": 6, "y": 0, "w": 6, "h": 1}
            ]
        }
        
        layout = DisplayerLayout(
            layoutType=Layouts.GRID,
            grid_config=grid_config,
            userid="test_grid"
        )
        
        container = []
        layout.display(container, id=1)
        
        assert len(container) == 1
        result = container[0]
        assert result["object"] == "layout"
        assert result["type"] == Layouts.GRID.value
        assert result["id"] == 1
        assert result["grid_config"] == grid_config
        assert result["user_id"] == "test_grid"
        assert "item1" in result["containers"]
        assert "item2" in result["containers"]


class TestDataTableLayout:
    """Test TABLE layout with DataTable configurations."""
    
    def test_table_layout_basic(self):
        """Test creating a basic TABLE layout."""
        layout = DisplayerLayout(
            layoutType=Layouts.TABLE,
            columns=["Name", "Email", "Status"]
        )
        
        assert layout.m_type == Layouts.TABLE.value
        assert layout.m_column == ["Name", "Email", "Status"]
    
    def test_table_with_datatable_config(self):
        """Test TABLE layout with new datatable_config."""
        config = {
            "table_id": "users",
            "mode": TableMode.INTERACTIVE,
            "searchable_columns": [0, 1]
        }
        
        layout = DisplayerLayout(
            layoutType=Layouts.TABLE,
            columns=["Name", "Email"],
            datatable_config=config
        )
        
        assert layout.m_datatable_config == config
        assert layout.m_responsive is None
    
    def test_table_with_bulk_data_mode(self):
        """Test TABLE layout with BULK_DATA mode."""
        data = [
            {"Name": "Alice", "Email": "alice@example.com"},
            {"Name": "Bob", "Email": "bob@example.com"}
        ]
        
        config = {
            "table_id": "users",
            "mode": TableMode.BULK_DATA,
            "data": data
        }
        
        layout = DisplayerLayout(
            layoutType=Layouts.TABLE,
            columns=["Name", "Email"],
            datatable_config=config
        )
        
        assert layout.m_datatable_config["mode"] == TableMode.BULK_DATA
        assert layout.m_datatable_config["data"] == data
    
    def test_table_with_server_side_mode(self):
        """Test TABLE layout with SERVER_SIDE mode."""
        config = {
            "table_id": "users",
            "mode": TableMode.SERVER_SIDE,
            "api_endpoint": "/api/users",
            "columns": [{"data": "name"}, {"data": "email"}]
        }
        
        layout = DisplayerLayout(
            layoutType=Layouts.TABLE,
            columns=["Name", "Email"],
            datatable_config=config
        )
        
        assert layout.m_datatable_config["mode"] == TableMode.SERVER_SIDE
        assert layout.m_datatable_config["api_endpoint"] == "/api/users"
    
    def test_table_cannot_have_both_configs(self):
        """Test that responsive and datatable_config cannot both be specified."""
        with pytest.raises(ValueError, match="Cannot specify both"):
            DisplayerLayout(
                layoutType=Layouts.TABLE,
                columns=["Name"],
                responsive={"table1": {"type": "basic"}},
                datatable_config={"table_id": "table1", "mode": TableMode.INTERACTIVE}
            )
    
    def test_table_responsive_deprecation_warning(self):
        """Test that using responsive parameter triggers deprecation warning."""
        with pytest.warns(DeprecationWarning, match="'responsive' is deprecated"):
            layout = DisplayerLayout(
                layoutType=Layouts.TABLE,
                columns=["Name"],
                responsive={"table1": {"type": "basic"}}
            )
            
            assert layout.m_responsive is not None
            assert layout.m_datatable_config is None
    
    def test_table_display_with_datatable_config(self):
        """Test table display with new datatable_config format."""
        config = {
            "table_id": "test_table",
            "mode": TableMode.INTERACTIVE,
            "searchable_columns": [0, 1]
        }
        
        layout = DisplayerLayout(
            layoutType=Layouts.TABLE,
            columns=["Name", "Email", "Status"],
            datatable_config=config
        )
        
        container = []
        layout.display(container, id=1)
        
        assert len(container) == 1
        result = container[0]
        assert result["object"] == "layout"
        assert result["type"] == Layouts.TABLE.value
        assert result["header"] == ["Name", "Email", "Status"]
        assert result["responsive"] == "test_table"
        assert result["responsive_type"] == TableMode.INTERACTIVE.value


class TestTabsLayout:
    """Test TABS layout functionality."""
    
    def test_tabs_layout_creation(self):
        """Test creating a TABS layout."""
        layout = DisplayerLayout(
            layoutType=Layouts.TABS,
            columns=["Tab 1", "Tab 2", "Tab 3"]
        )
        
        assert layout.m_type == Layouts.TABS.value
        assert layout.m_column == ["Tab 1", "Tab 2", "Tab 3"]
    
    def test_tabs_display_structure(self):
        """Test TABS layout display output."""
        layout = DisplayerLayout(
            layoutType=Layouts.TABS,
            columns=["Settings", "Profile", "Security"]
        )
        
        container = []
        layout.display(container, id=1)
        
        assert len(container) == 1
        result = container[0]
        assert result["type"] == Layouts.TABS.value
        assert result["header"] == ["Settings", "Profile", "Security"]
        # TABS creates one row with cells for each tab
        assert result["lines"] == [[[], [], []]]


class TestLayoutDisplay:
    """Test display() method for various layouts."""
    
    def test_vertical_layout_display(self):
        """Test VERTICAL layout display output."""
        layout = DisplayerLayout(
            layoutType=Layouts.VERTICAL,
            columns=[4, 4, 4],
            alignment=[BSalign.L, BSalign.C, BSalign.R],
            spacing=2,
            background=BSstyle.LIGHT
        )
        
        container = []
        layout.display(container, id=1)
        
        assert len(container) == 1
        result = container[0]
        assert result["object"] == "layout"
        assert result["type"] == Layouts.VERTICAL.value
        assert result["id"] == 1
        assert result["columns"] == [4, 4, 4]
        assert len(result["containers"]) == 3
        assert result["align"] == [BSalign.L.value, BSalign.C.value, BSalign.R.value]
        assert result["spacing"] == "py-2"
        assert result["background"] == BSstyle.LIGHT.value
    
    def test_horizontal_layout_display(self):
        """Test HORIZONTAL layout display output."""
        layout = DisplayerLayout(
            layoutType=Layouts.HORIZONTAL,
            columns=[12],
            alignment=BSalign.C
        )
        
        container = []
        layout.display(container, id=2)
        
        assert len(container) == 1
        result = container[0]
        assert result["type"] == Layouts.HORIZONTAL.value
        assert result["columns"] == [12]
        assert len(result["containers"]) == 1
    
    def test_layout_column_validation(self):
        """Test that invalid column sizes result in empty layout."""
        layout = DisplayerLayout(
            layoutType=Layouts.VERTICAL,
            columns=[6, 6, 4]  # Sums to 16, exceeds 12
        )
        
        container = []
        layout.display(container, id=1)
        
        result = container[0]
        assert result["columns"] == []
        assert result["containers"] == []
    
    def test_layout_zero_columns(self):
        """Test that zero columns results in empty layout."""
        layout = DisplayerLayout(
            layoutType=Layouts.VERTICAL,
            columns=[]
        )
        
        container = []
        layout.display(container, id=1)
        
        result = container[0]
        assert result["columns"] == []
        assert result["containers"] == []
    
    def test_layout_default_alignment(self):
        """Test that missing alignment defaults to left."""
        layout = DisplayerLayout(
            layoutType=Layouts.VERTICAL,
            columns=[6, 6]
        )
        
        container = []
        layout.display(container, id=1)
        
        result = container[0]
        assert result["align"] == [BSalign.L.value, BSalign.L.value]
    
    def test_layout_partial_alignment(self):
        """Test that partial alignment fills remaining with left align."""
        layout = DisplayerLayout(
            layoutType=Layouts.VERTICAL,
            columns=[4, 4, 4],
            alignment=[BSalign.C]  # Only one alignment for 3 columns
        )
        
        container = []
        layout.display(container, id=1)
        
        result = container[0]
        # First column uses specified alignment, rest default to left
        assert result["align"] == [BSalign.C.value, BSalign.L.value, BSalign.L.value]
