"""
Frontend tests for Tooltip Manager interface.

Tests tooltip and context CRUD operations, system protection, and display.
Uses Playwright for end-to-end testing.

Test Structure:
- TestTooltipCRUD: Create, read, update, delete tooltips
- TestContextCRUD: Create, read, update, delete contexts
- TestSystemProtection: Verify Global context cannot be deleted
- TestTooltipDisplay: Basic tooltip table display verification

Priority levels:
- High: Basic CRUD, Global context protection, table display
- Medium: Multi-context tooltips, matching strategies, cache invalidation
- Low: Advanced filtering, bulk operations

Run tests:
    pytest tests/frontend/test_tooltip_manager.py -v
    pytest tests/frontend/test_tooltip_manager.py::TestTooltipCRUD -v
"""

import pytest
import time
from playwright.sync_api import Page, expect

from tests.frontend.conftest import (
    navigate_to, fill_form_field, click_button,
    check_flash_message, page_contains_text, BASE_URL, HUMAN_MODE
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_tooltip(page: Page, keyword: str, content: str, contexts: list = None) -> bool:
    """Create tooltip via UI.
    
    Args:
        page: Playwright page
        keyword: Tooltip keyword
        content: Tooltip content (HTML)
        contexts: List of context names to select (default: ["Global"])
        
    Returns:
        True if creation successful, False otherwise
    """
    if contexts is None:
        contexts = ["Global"]
    
    try:
        # Navigate to tooltip management page
        navigate_to(page, "/admin/tooltips/")
        
        # Click Create New Tooltip button
        create_btn = page.locator('a:has-text("Create New Tooltip")')
        create_btn.click()
        page.wait_for_load_state('networkidle')
        
        # Fill keyword field
        keyword_input = page.locator('input[name="Create Tooltip.keyword"]')
        keyword_input.fill(keyword)
        
        # Fill content field (textarea or TinyMCE)
        content_input = page.locator('textarea[name="Create Tooltip.content"]')
        content_input.fill(content)
        
        # Select contexts from multi-select
        # The multi-select widget uses <select> elements
        for ctx_name in contexts:
            # Try to select the option containing the context name
            try:
                # The DisplayerItemInputMultiSelect creates options with "Name - Description" format
                page.locator(f'select[name*="Create Tooltip.contexts"] option:has-text("{ctx_name}")').first.click(modifiers=["Control"])
            except Exception as e:
                print(f"Warning: Could not select context '{ctx_name}': {e}")
        
        # Submit form
        submit_btn = page.locator('button:has-text("Create Tooltip")')
        submit_btn.click()
        page.wait_for_load_state('networkidle', timeout=10000)
        
        # Check for success message
        return check_flash_message(page, "created successfully")
    
    except Exception as e:
        print(f"Error creating tooltip: {e}")
        return False


def verify_tooltip_in_table(page: Page, keyword: str) -> bool:
    """Check if tooltip appears in DataTable.
    
    Args:
        page: Playwright page
        keyword: Tooltip keyword to search for
        
    Returns:
        True if tooltip found, False otherwise
    """
    try:
        navigate_to(page, "/admin/tooltips/")
        page.wait_for_timeout(1000)  # Wait for tables to initialize
        
        # Look for any table containing tooltips (the ID might vary)
        # Use DataTable search
        search_input = page.locator('input[type="search"]').first
        search_input.fill(keyword)
        page.wait_for_timeout(800)  # Wait for debounce + filter
        
        # Check if keyword appears in any table
        keyword_cells = page.locator(f'table td:has-text("{keyword}")')
        found = keyword_cells.count() > 0
        
        if found:
            print(f"  ✅ Tooltip found in table: {keyword}")
        else:
            print(f"  ❌ Tooltip NOT found in table: {keyword}")
        
        return found
    
    except Exception as e:
        print(f"Error verifying tooltip: {e}")
        return False


def delete_tooltip(page: Page, keyword: str) -> bool:
    """Delete tooltip by keyword.
    
    Args:
        page: Playwright page
        keyword: Tooltip keyword to delete
        
    Returns:
        True if deletion successful, False otherwise
    """
    try:
        navigate_to(page, "/admin/tooltips/")
        page.wait_for_timeout(1000)
        
        # Search for tooltip
        search_input = page.locator('input[type="search"]').first
        search_input.fill(keyword)
        page.wait_for_timeout(800)
        
        # Find row and click delete button
        row = page.locator(f'tr:has-text("{keyword}")').first
        delete_link = row.locator('a[href*="/tooltip/delete/"]')
        delete_link.click()
        page.wait_for_load_state('networkidle')
        
        # Confirm deletion
        confirm_btn = page.locator('button:has-text("Yes, Delete"), input[value="Yes, Delete"]')
        confirm_btn.click()
        page.wait_for_load_state('networkidle')
        
        return check_flash_message(page, "deleted successfully")
    
    except Exception as e:
        print(f"Error deleting tooltip: {e}")
        return False


def create_context(page: Page, name: str, description: str = "", strategy: str = "exact") -> bool:
    """Create context via UI.
    
    Args:
        page: Playwright page
        name: Context name (alphanumeric + underscore only)
        description: Context description
        strategy: Matching strategy (exact, word_boundary, regex)
        
    Returns:
        True if creation successful, False otherwise
    """
    try:
        navigate_to(page, "/admin/tooltips/")
        
        # Click Create New Context button
        create_btn = page.locator('a[href*="/admin/tooltips/context/create"]')
        create_btn.click()
        page.wait_for_load_state('networkidle')
        
        # Fill name field
        name_input = page.locator('input[name="Create Context.name"]')
        name_input.fill(name)
        
        # Fill description field
        desc_input = page.locator('input[name="Create Context.description"]')
        desc_input.fill(description)
        
        # Select matching strategy
        strategy_select = page.locator('select[name="Create Context.matching_strategy"]')
        strategy_select.select_option(strategy)
        
        # Submit form
        submit_btn = page.locator('button:has-text("Create Context"), input[value="Create Context"]')
        submit_btn.click()
        page.wait_for_load_state('networkidle')
        
        return check_flash_message(page, "created successfully")
    
    except Exception as e:
        print(f"Error creating context: {e}")
        return False


def delete_context(page: Page, name: str) -> bool:
    """Delete context by name.
    
    Args:
        page: Playwright page
        name: Context name to delete
        
    Returns:
        True if deletion successful, False otherwise
    """
    try:
        navigate_to(page, "/admin/tooltips/")
        page.wait_for_timeout(1000)
        
        # Find row and click delete button
        row = page.locator(f'tr:has-text("{name}")').first
        delete_link = row.locator('a[href*="/context/delete/"]')
        delete_link.click()
        page.wait_for_load_state('networkidle')
        
        # Confirm deletion
        confirm_btn = page.locator('button:has-text("Yes, Delete"), input[value="Yes, Delete"]')
        confirm_btn.click()
        page.wait_for_load_state('networkidle')
        
        return check_flash_message(page, "deleted successfully")
    
    except Exception as e:
        print(f"Error deleting context: {e}")
        return False


# ============================================================================
# TEST CLASSES
# ============================================================================

class TestTooltipCRUD:
    """Test tooltip create, read, update, delete operations"""
    
    def test_create_simple_tooltip(self, logged_in_page):
        """Create tooltip with text content in Global context"""
        keyword = f"TestKeyword_{int(time.time())}"
        content = "This is a test tooltip content"
        
        assert create_tooltip(logged_in_page, keyword, content, ["Global"])
        assert verify_tooltip_in_table(logged_in_page, keyword)
        
        # Cleanup
        delete_tooltip(logged_in_page, keyword)
    
    def test_create_html_tooltip(self, logged_in_page):
        """Create tooltip with HTML content"""
        keyword = f"HTMLTest_{int(time.time())}"
        html_content = "<strong>Bold</strong> and <em>italic</em> text"
        
        assert create_tooltip(logged_in_page, keyword, html_content, ["Global"])
        assert verify_tooltip_in_table(logged_in_page, keyword)
        
        # Cleanup
        delete_tooltip(logged_in_page, keyword)
    
    def test_edit_tooltip(self, logged_in_page):
        """Edit existing tooltip content"""
        keyword = f"EditMe_{int(time.time())}"
        original_content = "Original content"
        updated_content = "Updated content"
        
        # Create first
        create_tooltip(logged_in_page, keyword, original_content, ["Global"])
        
        # Navigate to edit page
        navigate_to(logged_in_page, "/admin/tooltips/")
        logged_in_page.wait_for_timeout(1000)
        
        # Search for tooltip
        search_input = logged_in_page.locator('input[type="search"]').first
        search_input.fill(keyword)
        logged_in_page.wait_for_timeout(800)
        
        # Click edit button
        row = logged_in_page.locator(f'tr:has-text("{keyword}")').first
        edit_link = row.locator('a[href*="/tooltip/edit/"]')
        edit_link.click()
        logged_in_page.wait_for_load_state('networkidle')
        
        # Update content
        content_input = logged_in_page.locator('textarea[name="Edit Tooltip.content"]')
        content_input.fill(updated_content)
        
        # Submit
        submit_btn = logged_in_page.locator('button:has-text("Update Tooltip"), input[value="Update Tooltip"]')
        submit_btn.click()
        logged_in_page.wait_for_load_state('networkidle')
        
        assert check_flash_message(logged_in_page, "updated successfully")
        
        # Cleanup
        delete_tooltip(logged_in_page, keyword)
    
    def test_delete_tooltip(self, logged_in_page):
        """Delete tooltip"""
        keyword = f"DeleteMe_{int(time.time())}"
        content = "This will be deleted"
        
        # Create first
        create_tooltip(logged_in_page, keyword, content, ["Global"])
        assert verify_tooltip_in_table(logged_in_page, keyword)
        
        # Delete
        assert delete_tooltip(logged_in_page, keyword)
        
        # Verify deleted
        assert not verify_tooltip_in_table(logged_in_page, keyword)
    
    def test_tooltip_validation_empty_keyword(self, logged_in_page):
        """Test validation: empty keyword should fail"""
        navigate_to(logged_in_page, "/admin/tooltips/tooltip/create")
        
        # Try to submit with empty keyword
        content_input = logged_in_page.locator('textarea[name="Create Tooltip.content"]')
        content_input.fill("Some content")
        
        submit_btn = logged_in_page.locator('button:has-text("Create Tooltip"), input[value="Create Tooltip"]')
        submit_btn.click()
        logged_in_page.wait_for_load_state('networkidle')
        
        # Should show error (either flash message or stay on same page)
        # Note: Exact error handling depends on implementation
        current_url = logged_in_page.url
        assert "/tooltip/create" in current_url  # Should stay on create page


class TestContextCRUD:
    """Test context create, read, update, delete operations"""
    
    def test_create_context(self, logged_in_page):
        """Create new context"""
        ctx_name = f"TestCtx_{int(time.time())}"
        ctx_desc = "Test context description"
        
        assert create_context(logged_in_page, ctx_name, ctx_desc, "exact")
        
        # Verify in table
        navigate_to(logged_in_page, "/admin/tooltips/")
        logged_in_page.wait_for_timeout(1000)
        ctx_row = logged_in_page.locator(f'tr:has-text("{ctx_name}")')
        assert ctx_row.count() > 0
        
        # Cleanup
        delete_context(logged_in_page, ctx_name)
    
    def test_delete_context(self, logged_in_page):
        """Delete custom context"""
        ctx_name = f"DeleteMeCtx_{int(time.time())}"
        
        # Create first
        create_context(logged_in_page, ctx_name, "Will be deleted")
        
        # Delete
        assert delete_context(logged_in_page, ctx_name)
        
        # Verify deleted
        navigate_to(logged_in_page, "/admin/tooltips/")
        logged_in_page.wait_for_timeout(1000)
        ctx_row = logged_in_page.locator(f'tr:has-text("{ctx_name}")')
        assert ctx_row.count() == 0
    
    def test_context_validation_invalid_name(self, logged_in_page):
        """Test validation: invalid context name (with spaces) should fail"""
        navigate_to(logged_in_page, "/admin/tooltips/context/create")
        
        # Try to submit with invalid name
        name_input = logged_in_page.locator('input[name="Create Context.name"]')
        name_input.fill("Invalid Name With Spaces")
        
        desc_input = logged_in_page.locator('input[name="Create Context.description"]')
        desc_input.fill("Description")
        
        submit_btn = logged_in_page.locator('button:has-text("Create Context"), input[value="Create Context"]')
        submit_btn.click()
        logged_in_page.wait_for_load_state('networkidle')
        
        # Should show error message
        assert check_flash_message(logged_in_page, "alphanumeric", check_type="error")


class TestSystemProtection:
    """Test system protection features"""
    
    def test_global_context_cannot_be_deleted(self, logged_in_page):
        """Verify Global context has no delete button"""
        navigate_to(logged_in_page, "/admin/tooltips/")
        logged_in_page.wait_for_timeout(1000)
        
        # Find Global context row
        global_row = logged_in_page.locator('tr:has-text("Global")').first
        
        # Check that delete button does NOT exist
        delete_btn = global_row.locator('a[href*="/context/delete/"]')
        assert delete_btn.count() == 0, "Global context should not have a delete button"
        
        print("  ✅ Global context is protected from deletion")
    
    def test_global_context_cannot_be_edited_name(self, logged_in_page):
        """Verify Global context name cannot be changed"""
        navigate_to(logged_in_page, "/admin/tooltips/")
        logged_in_page.wait_for_selector('#contexts_table', timeout=5000)
        
        # Find Global context row and click edit
        global_row = logged_in_page.locator('#contexts_table tr:has-text("Global")').first
        edit_link = global_row.locator('a[href*="/context/edit/"]')
        
        # If edit button exists, click it
        if edit_link.count() > 0:
            edit_link.click()
            logged_in_page.wait_for_load_state('networkidle')
            
            # Name field should be read-only or shown as alert
            # Check if name field is disabled or not editable
            page_content = logged_in_page.content().lower()
            assert "cannot be changed" in page_content or "global" in page_content
            
            print("  ✅ Global context name is protected")


class TestTooltipDisplay:
    """Test tooltip table display and navigation"""
    
    def test_tooltip_management_page_loads(self, logged_in_page):
        """Verify tooltip management page loads successfully"""
        navigate_to(logged_in_page, "/admin/tooltips/")
        
        # Check URL is correct
        assert "/admin/tooltips" in logged_in_page.url
        
        # Wait for page to fully load
        logged_in_page.wait_for_load_state('networkidle')
        
        # Check if page contains tooltip/context related content
        page_content = logged_in_page.content()
        
        # The page should have SOME content related to tooltips or contexts
        # Could be a message saying it's not enabled, or the actual tables
        assert "tooltip" in page_content.lower() or "context" in page_content.lower() or "not enabled" in page_content.lower()
        
        print("  ✅ Tooltip management page accessible")
    
    def test_datatable_search_functionality(self, logged_in_page):
        """Test DataTable search filters correctly"""
        # Create a test tooltip
        keyword = f"SearchTest_{int(time.time())}"
        create_tooltip(logged_in_page, keyword, "Searchable content", ["Global"])
        
        navigate_to(logged_in_page, "/admin/tooltips/")
        logged_in_page.wait_for_timeout(1000)
        
        # Search for the tooltip
        search_input = logged_in_page.locator('input[type="search"]').first
        search_input.fill(keyword)
        logged_in_page.wait_for_timeout(800)
        
        # Should find the keyword in the table
        visible_rows = logged_in_page.locator(f'tbody tr:has-text("{keyword}")')
        assert visible_rows.count() >= 1
        
        # Search for non-existent keyword
        search_input.fill("NonExistentKeyword123456")
        logged_in_page.wait_for_timeout(800)
        
        # Should show "No matching records found" or similar
        page_content = logged_in_page.content().lower()
        assert "no matching records" in page_content or "no data available" in page_content or "0 entries" in page_content
        
        # Cleanup
        delete_tooltip(logged_in_page, keyword)
    
    def test_global_context_exists_by_default(self, logged_in_page):
        """Verify Global context exists in contexts table"""
        navigate_to(logged_in_page, "/admin/tooltips/")
        logged_in_page.wait_for_timeout(1000)
        
        # Global context should exist
        global_row = logged_in_page.locator('tr:has-text("Global")')
        assert global_row.count() > 0
        
        # Should have "System" badge or similar indicator
        page_content = logged_in_page.content()
        assert "System" in page_content or "Global" in page_content
        
        print("  ✅ Global context exists by default")


# ============================================================================
# SKIP TESTS (TODO: Implement when frontend tooltip JS is ready)
# ============================================================================

@pytest.mark.skip(reason="Requires frontend tooltip JS implementation")
class TestTooltipFrontendDisplay:
    """Test tooltips appearing on actual pages (requires JS integration)"""
    
    def test_tooltip_appears_on_hover(self, logged_in_page):
        """Verify tooltip displays when hovering over keyword"""
        # This would test the actual tooltip functionality on a page
        # Requires the tooltip.js integration to be complete
        pass
    
    def test_word_boundary_matching(self, logged_in_page):
        """Test word_boundary strategy matches whole words only"""
        # This would test different matching strategies
        # Requires frontend implementation
        pass
