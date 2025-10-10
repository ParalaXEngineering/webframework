"""
Test for multiple SERVER_SIDE DataTables in TABS layout.

Regression test for bug where only the last table's responsive_addon was preserved.
The fix ensures responsive_addon dictionaries are merged instead of overwritten.
"""

import pytest
from flask import Flask
from bs4 import BeautifulSoup

from src.modules import displayer


@pytest.fixture
def test_app():
    """Minimal Flask app for rendering."""
    import os
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    template_path = os.path.join(workspace_root, "templates")
    
    app = Flask(__name__, template_folder=template_path)
    app.config["TESTING"] = True
    app.secret_key = "test-secret"
    
    return app


def test_multiple_tables_in_tabs_preserve_all_responsive_addon(test_app):
    """
    Verify that multiple SERVER_SIDE tables in TABS layout all get registered.
    
    Before the fix: Only last table appeared in responsive_addon (overwrote previous).
    After the fix: All tables preserved via dictionary merging.
    """
    disp = displayer.Displayer()
    disp.add_generic("Multi-Table TABS")
    
    # Create TABS layout with 3 tabs
    tab_titles = ["Log 1", "Log 2", "Log 3"]
    master_layout_id = disp.add_master_layout(
        displayer.DisplayerLayout(displayer.Layouts.TABS, tab_titles)
    )
    
    # Add SERVER_SIDE table to each tab
    for tab_index, tab_name in enumerate(tab_titles):
        disp.add_slave_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.TABLE,
                columns=["#", "Message"],
                datatable_config={
                    "table_id": f"table_{tab_index}",
                    "mode": displayer.TableMode.SERVER_SIDE,
                    "api_endpoint": "test.api",
                    "columns": [{"data": "id"}, {"data": "message"}]
                }
            ),
            column=tab_index,
            layout_id=master_layout_id
        )
    
    # Check internal m_all_layout instead of calling display()
    # (display() requires access_manager which complicates testing)
    assert "responsive_addon" in disp.m_all_layout, "Should have responsive_addon"
    
    responsive_addon = disp.m_all_layout["responsive_addon"]
    assert len(responsive_addon) == 3, f"Expected 3 tables, got {len(responsive_addon)}"
    
    # Verify all table IDs present
    expected_ids = {"table_0", "table_1", "table_2"}
    actual_ids = set(responsive_addon.keys())
    assert actual_ids == expected_ids, f"Expected {expected_ids}, got {actual_ids}"
    
    # Verify each table has proper config
    for table_id, config in responsive_addon.items():
        assert config.get("type") == displayer.TableMode.SERVER_SIDE.value, \
            f"Table {table_id} should be SERVER_SIDE type"
        assert config.get("api") == "test.api", \
            f"Table {table_id} should have correct API endpoint"


def test_multiple_mixed_tables_in_tabs(test_app):
    """
    Test TABS with mix of SIMPLE, INTERACTIVE, and SERVER_SIDE tables.
    """
    disp = displayer.Displayer()
    disp.add_generic("Mixed Tables")
    
    master_layout_id = disp.add_master_layout(
        displayer.DisplayerLayout(displayer.Layouts.TABS, ["Simple", "Interactive", "ServerSide"])
    )
    
    # Tab 0: SIMPLE (no datatable_config)
    disp.add_slave_layout(
        displayer.DisplayerLayout(displayer.Layouts.TABLE, columns=["A", "B"]),
        column=0,
        layout_id=master_layout_id
    )
    
    # Tab 1: INTERACTIVE
    disp.add_slave_layout(
        displayer.DisplayerLayout(
            displayer.Layouts.TABLE,
            columns=["X", "Y"],
            datatable_config={
                "table_id": "interactive_table",
                "mode": displayer.TableMode.INTERACTIVE
            }
        ),
        column=1,
        layout_id=master_layout_id
    )
    
    # Tab 2: SERVER_SIDE
    disp.add_slave_layout(
        displayer.DisplayerLayout(
            displayer.Layouts.TABLE,
            columns=["P", "Q"],
            datatable_config={
                "table_id": "server_table",
                "mode": displayer.TableMode.SERVER_SIDE,
                "api_endpoint": "api.data"
            }
        ),
        column=2,
        layout_id=master_layout_id
    )
    
    # Check internal m_all_layout
    responsive_addon = disp.m_all_layout.get("responsive_addon", {})
    assert len(responsive_addon) == 2, f"Expected 2 DataTables, got {len(responsive_addon)}"
    assert "interactive_table" in responsive_addon
    assert "server_table" in responsive_addon


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
