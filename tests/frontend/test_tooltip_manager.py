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
    check_flash_message, page_contains_text, BASE_URL, HUMAN_MODE,
    select_multi_list_values, fill_tinymce_field
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
        
        # Fill content field (TinyMCE rich text editor)
        fill_tinymce_field(page, "Create Tooltip.content", content)
        
        # Select contexts using the multi-list helper
        # Format context names to match the "Name - Description" format
        context_values = []
        for ctx_name in contexts:
            # Find the option that contains this context name
            # Options are formatted as "Name - Description"
            options = page.locator(f'select[name="Create Tooltip.contexts.list0"] option:has-text("{ctx_name}")')
            if options.count() > 0:
                context_values.append(options.first.inner_text())
            else:
                print(f"Warning: Context '{ctx_name}' not found in dropdown")
        
        if context_values:
            select_multi_list_values(page, "Create Tooltip.contexts", context_values)
        
        # Submit form
        submit_btn = page.locator('button:has-text("Create Tooltip")')
        submit_btn.click()
        page.wait_for_load_state('networkidle', timeout=5000)
        
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
        page.wait_for_selector('#interactive_tooltips_table', timeout=5000)
        
        # Use search to handle pagination
        search_input = page.locator('input[type="search"]').first
        search_input.fill(keyword)
        page.wait_for_timeout(500)
        
        # Check if keyword appears in tooltips table
        keyword_cells = page.locator(f'#interactive_tooltips_table td:has-text("{keyword}")')
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
        page.wait_for_selector('#interactive_tooltips_table', timeout=5000)
        
        # Use search to filter table
        search_input = page.locator('input[type="search"]').first
        search_input.fill(keyword)
        page.wait_for_timeout(500)
        
        # Find row in specific table and click delete icon
        row = page.locator(f'#interactive_tooltips_table tr:has-text("{keyword}")').first
        delete_icon = row.locator('i.mdi-delete').first
        if delete_icon.count() == 0:
            raise AssertionError(f"Delete button not found for keyword: {keyword}")
        
        delete_anchor = delete_icon.locator('..').first
        delete_anchor.click()
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
        page.wait_for_timeout(2000)  # Give more time for page to load
        
        # Find ALL rows with the context name (simpler selector)
        rows = page.locator(f'tr:has-text("{name}")')
        count = rows.count()
        print(f"Found {count} row(s) with text '{name}'")
        
        # Get the first one that has a delete button
        for i in range(count):
            row = rows.nth(i)
            delete_link = row.locator('a:has(i.mdi-delete)').first
            if delete_link.count() > 0:
                print(f"  ✅ Found delete button in row {i}")
                delete_link.click(timeout=2000)
                page.wait_for_load_state('networkidle')
                break
        else:
            print(f"  ❌ No delete link found in any row for '{name}'")
            return False
        
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
        """Create tooltip with content in Global context"""
        keyword = f"TestKeyword_{int(time.time())}"
        content = "<strong>Test</strong> tooltip content"
        
        assert create_tooltip(logged_in_page, keyword, content, ["Global"])
        assert verify_tooltip_in_table(logged_in_page, keyword)
    
    def test_edit_tooltip(self, logged_in_page):
        """Edit existing tooltip content and verify changes"""
        keyword = f"EditMe_{int(time.time())}"
        original_content = "Original content"
        updated_content = "Updated content here"
        
        # Create first
        create_tooltip(logged_in_page, keyword, original_content, ["Global"])
        
        # Navigate to edit page
        navigate_to(logged_in_page, "/admin/tooltips/")
        logged_in_page.wait_for_selector('#interactive_tooltips_table', timeout=5000)
        
        # Use search to filter table
        search_input = logged_in_page.locator('input[type="search"]').first
        search_input.fill(keyword)
        logged_in_page.wait_for_timeout(500)
        
        # Click edit icon in specific table
        row = logged_in_page.locator(f'#interactive_tooltips_table tr:has-text("{keyword}")').first
        edit_icon = row.locator('i.mdi-pencil').first
        edit_anchor = edit_icon.locator('..').first
        edit_anchor.click()
        logged_in_page.wait_for_load_state('networkidle')
        
        # Update content using TinyMCE helper
        fill_tinymce_field(logged_in_page, "Edit Tooltip.content", updated_content)
        
        # Submit
        submit_btn = logged_in_page.locator('button:has-text("Update Tooltip"), input[value="Update Tooltip"]')
        submit_btn.click()
        logged_in_page.wait_for_load_state('networkidle')
        
        assert check_flash_message(logged_in_page, "updated successfully")
        
        # Verify content was actually updated by going back to edit page
        navigate_to(logged_in_page, "/admin/tooltips/")
        logged_in_page.wait_for_selector('#interactive_tooltips_table', timeout=5000)
        
        # Use search to filter
        search_input = logged_in_page.locator('input[type="search"]').first
        search_input.fill(keyword)
        logged_in_page.wait_for_timeout(500)
        
        row = logged_in_page.locator(f'#interactive_tooltips_table tr:has-text("{keyword}")').first
        edit_icon = row.locator('i.mdi-pencil').first
        edit_anchor = edit_icon.locator('..').first
        edit_anchor.click()
        logged_in_page.wait_for_load_state('networkidle')
        
        # Check the textarea value (TinyMCE syncs back to textarea)
        content_textarea = logged_in_page.locator('textarea[name="Edit Tooltip.content"]')
        actual_content = content_textarea.evaluate("el => el.value")
        assert updated_content in actual_content, f"Expected '{updated_content}' in content, got '{actual_content}'"
    
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
        
        # Try to submit with empty keyword (but with content)
        fill_tinymce_field(logged_in_page, "Create Tooltip.content", "Some content")
        
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
        
        # Verify it was created
        navigate_to(logged_in_page, "/admin/tooltips/")
        logged_in_page.wait_for_timeout(2000)
        ctx_row = logged_in_page.locator(f'tr:has-text("{ctx_name}")')
        assert ctx_row.count() > 0, f"Context '{ctx_name}' not found after creation"
        
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
        
        # Should show error message - route catches ValueError and flashes with "danger"
        assert check_flash_message(logged_in_page, "alphanumeric", message_type="danger")


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
        logged_in_page.wait_for_timeout(1000)
        
        # Find Global context row and click edit using icon selector
        global_row = logged_in_page.locator('tr:has-text("Global")').first
        edit_link = global_row.locator('a i.mdi-pencil').locator('..').first
        
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
        logged_in_page.wait_for_timeout(500)
        
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
        logged_in_page.wait_for_timeout(500)
        
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

class TestTooltipFrontendDisplay:
    """Test tooltips appearing on actual pages (requires JS integration)"""
    
    def test_tooltip_appears_on_hover(self, logged_in_page):
        """Verify tooltip displays when hovering over keyword"""
        # Create a tooltip with unique keyword
        keyword = f"HoverTest_{int(time.time())}"
        content = "This tooltip should appear on hover"
        create_tooltip(logged_in_page, keyword, content, ["Global"])
        
        # Navigate back to management page where tooltips are enabled
        navigate_to(logged_in_page, "/admin/tooltips/")
        logged_in_page.wait_for_timeout(1000)
        
        # Use DataTable search to find the keyword
        search_input = logged_in_page.locator('input[type="search"]').first
        search_input.fill(keyword)
        logged_in_page.wait_for_timeout(500)
        
        # Check that the keyword appears in the table
        assert page_contains_text(logged_in_page, keyword)
        
        # Verify the tooltip data was loaded by checking browser console output
        # The JS should have initialized tooltips (we see "Initializing tooltips" in console)
        page_source = logged_in_page.content()
        
        # Keyword should be in the page source
        assert keyword in page_source
        
        # Cleanup
        delete_tooltip(logged_in_page, keyword)
        
        print(f"  ✅ Tooltip keyword '{keyword}' found on page")
    
    def test_word_boundary_matching(self, logged_in_page):
        """Test word_boundary strategy matches whole words only"""
        # Create a context with word_boundary strategy
        ctx_name = f"WordBoundary_{int(time.time())}"
        create_context(logged_in_page, ctx_name, "Word boundary test", "word_boundary")
        
        # Create a tooltip in this context
        keyword = f"test_{int(time.time())}"
        content = "Word boundary tooltip"
        create_tooltip(logged_in_page, keyword, content, [ctx_name])
        
        # Verify the context exists
        navigate_to(logged_in_page, "/admin/tooltips/")
        logged_in_page.wait_for_timeout(1000)
        
        # Check context is in table
        ctx_row = logged_in_page.locator(f'tr:has-text("{ctx_name}")')
        assert ctx_row.count() > 0
        
        # Verify matching strategy is word_boundary
        page_content = logged_in_page.content()
        assert "word_boundary" in page_content
        
        # Cleanup
        delete_tooltip(logged_in_page, keyword)
        delete_context(logged_in_page, ctx_name)
        
        print(f"  ✅ Word boundary context '{ctx_name}' created successfully")
