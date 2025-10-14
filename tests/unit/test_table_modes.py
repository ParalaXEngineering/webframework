"""
Tests for new TableMode API and backward compatibility.
"""

import pytest
import warnings
import os
from flask import Flask
from src.modules.displayer import (
    Displayer, DisplayerLayout, Layouts, TableMode,
    DisplayerItemText, DisplayerItemButton
)
from src.modules import access_manager


# Mock access manager for tests
class MockAuthObject:
    def authorize_module(self, module):
        return True
    
    def get_user(self):
        return "test_user"


@pytest.fixture(autouse=True)
def mock_access():
    """Mock access manager for all tests."""
    access_manager.auth_object = MockAuthObject()
    yield
    access_manager.auth_object = None


def test_table_mode_enum():
    """Test TableMode enum values."""
    assert TableMode.SIMPLE.value == "simple"
    assert TableMode.INTERACTIVE.value == "interactive"
    assert TableMode.BULK_DATA.value == "bulk_data"
    assert TableMode.SERVER_SIDE.value == "server_side"


def test_simple_table_no_datatable(mock_access):
    """Test simple HTML table without DataTables."""
    disp = Displayer()
    disp.add_generic("Test")
    
    layout_id = disp.add_master_layout(DisplayerLayout(
        Layouts.TABLE,
        columns=["Name", "Email", "Status"]
        # No datatable_config = plain HTML table
    ))
    
    # Add rows manually with items
    disp.add_display_item(DisplayerItemText("Alice"), 0, line=0, layout_id=layout_id)
    disp.add_display_item(DisplayerItemText("alice@example.com"), 1, line=0, layout_id=layout_id)
    disp.add_display_item(DisplayerItemText("Active"), 2, line=0, layout_id=layout_id)
    
    result = disp.display()
    assert "Test" in result
    assert "layouts" in result["Test"]


def test_interactive_mode_with_new_api(mock_access):
    """Test interactive mode with manual item population."""
    disp = Displayer()
    disp.add_generic("Interactive Table")
    
    layout_id = disp.add_master_layout(DisplayerLayout(
        Layouts.TABLE,
        columns=["Name", "Actions"],
        datatable_config={
            "table_id": "interactive_test",
            "mode": TableMode.INTERACTIVE,
            "searchable_columns": [0]
        }
    ))
    
    disp.add_display_item(DisplayerItemText("Alice"), 0, line=0, layout_id=layout_id)
    disp.add_display_item(DisplayerItemButton("edit_btn", "Edit"), 1, line=0, layout_id=layout_id)
    
    result = disp.display()
    assert "all_layout" in result
    assert "responsive_addon" in result["all_layout"]
    assert "interactive_test" in result["all_layout"]["responsive_addon"]
    
    config = result["all_layout"]["responsive_addon"]["interactive_test"]
    assert config["type"] == "interactive"
    assert config["columns"] == [0]


def test_bulk_data_mode(mock_access):
    """Test bulk data mode with pre-loaded data."""
    disp = Displayer()
    disp.add_generic("Bulk Data Table")
    
    test_data = [
        {"Name": "Alice", "Email": "alice@example.com", "Status": "Active"},
        {"Name": "Bob", "Email": "bob@example.com", "Status": "Inactive"}
    ]
    
    disp.add_master_layout(DisplayerLayout(
        Layouts.TABLE,
        columns=["Name", "Email", "Status"],
        datatable_config={
            "table_id": "bulk_test",
            "mode": TableMode.BULK_DATA,
            "data": test_data,
            "columns": [
                {"data": "Name"},
                {"data": "Email"},
                {"data": "Status"}
            ],
            "searchable_columns": [0, 1]
        }
    ))
    
    result = disp.display()
    assert "all_layout" in result
    assert "responsive_addon" in result["all_layout"]
    assert "bulk_test" in result["all_layout"]["responsive_addon"]
    
    config = result["all_layout"]["responsive_addon"]["bulk_test"]
    assert config["type"] == "bulk_data"
    assert config["data"] == test_data
    assert len(config["ajax_columns"]) == 3
    assert config["columns"] == [0, 1]


def test_server_side_mode(mock_access):
    """Test server-side mode with AJAX endpoint."""
    disp = Displayer()
    disp.add_generic("Server-Side Table")
    
    disp.add_master_layout(DisplayerLayout(
        Layouts.TABLE,
        columns=["Name", "Email", "Status"],
        datatable_config={
            "table_id": "ajax_test",
            "mode": TableMode.SERVER_SIDE,
            "api_endpoint": "api.get_users",
            "refresh_interval": 3000,
            "columns": [
                {"data": "Name"},
                {"data": "Email"},
                {"data": "Status"}
            ]
        }
    ))
    
    result = disp.display()
    assert "all_layout" in result
    assert "responsive_addon" in result["all_layout"]
    assert "ajax_test" in result["all_layout"]["responsive_addon"]
    
    config = result["all_layout"]["responsive_addon"]["ajax_test"]
    assert config["type"] == "server_side"
    assert config["api"] == "api.get_users"
    assert config["refresh_interval"] == 3000


def test_backward_compatibility_basic(mock_access):
    """Test that old 'responsive' with type='basic' still works."""
    disp = Displayer()
    disp.add_generic("Old API Basic")
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        disp.add_master_layout(DisplayerLayout(
            Layouts.TABLE,
            columns=["Name", "Status"],
            responsive={
                "old_basic": {
                    "type": "basic",
                    "columns": [0]
                }
            }
        ))
        
        # Check deprecation warning was issued
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "deprecated" in str(w[0].message).lower()
    
    result = disp.display()
    assert "responsive_addon" in result["all_layout"]
    assert "old_basic" in result["all_layout"]["responsive_addon"]


def test_backward_compatibility_advanced(mock_access):
    """Test that old 'responsive' with type='advanced' still works."""
    disp = Displayer()
    disp.add_generic("Old API Advanced")
    
    test_data = [{"Name": "Alice", "Status": "Active"}]
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        disp.add_master_layout(DisplayerLayout(
            Layouts.TABLE,
            columns=["Name", "Status"],
            responsive={
                "old_advanced": {
                    "type": "advanced",
                    "columns": [0, 1],
                    "ajax_columns": [{"data": "Name"}, {"data": "Status"}],
                    "data": test_data
                }
            }
        ))
        
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
    
    result = disp.display()
    config = result["all_layout"]["responsive_addon"]["old_advanced"]
    # Old type "advanced" is kept as-is for backward compat
    assert config["type"] == "advanced"
    assert config["data"] == test_data


def test_cannot_use_both_apis():
    """Test that using both 'responsive' and 'datatable_config' raises error."""
    with pytest.raises(ValueError, match="Cannot specify both"):
        DisplayerLayout(
            Layouts.TABLE,
            columns=["Name"],
            responsive={"table1": {"type": "basic"}},
            datatable_config={"table_id": "table2", "mode": TableMode.INTERACTIVE}
        )


def test_layout_preserves_standard_parameters(mock_access):
    """Test that standard layout parameters are preserved."""
    disp = Displayer()
    disp.add_generic("Standard Params")
    
    from src.modules.displayer import BSstyle, MAZERStyles
    
    disp.add_master_layout(DisplayerLayout(
        Layouts.TABLE,
        columns=["Name", "Status"],
        subtitle="User List",
        spacing=3,
        background=BSstyle.LIGHT,
        userid="custom_id",
        style=MAZERStyles.CARD,
        datatable_config={
            "table_id": "users",
            "mode": TableMode.BULK_DATA,
            "data": []
        }
    ))
    
    result = disp.display()
    layout = result["Standard Params"]["layouts"][0]
    
    assert layout["subtitle"] == "User List"
    assert layout["background"] == "light-secondary"
    assert layout["user_id"] == "custom_id"


def test_table_mode_string_values(mock_access):
    """Test using string values instead of enum."""
    disp = Displayer()
    disp.add_generic("String Mode")
    
    # Should work with string values too
    disp.add_master_layout(DisplayerLayout(
        Layouts.TABLE,
        columns=["Name"],
        datatable_config={
            "table_id": "string_test",
            "mode": "bulk_data",  # String instead of enum
            "data": []
        }
    ))
    
    result = disp.display()
    config = result["all_layout"]["responsive_addon"]["string_test"]
    assert config["type"] == "bulk_data"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
