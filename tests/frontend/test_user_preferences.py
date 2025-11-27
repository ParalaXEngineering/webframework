"""
Frontend tests for User Preferences page (/user/preferences).

Tests preferences management including:
- Page loading and display
- Theme selection
- Dashboard layout selection
- Guest user restrictions
- Preferences persistence
- Framework preferences redirect

Tests are ordered to build on each other for efficiency.
"""

import pytest
from playwright.sync_api import Page

from tests.frontend.conftest import (
    navigate_to, select_form_option, click_button, 
    check_flash_message, page_contains_text, login, logout
)


class TestUserPreferencesPage:
    """Test user preferences page functionality with ordered tests."""
    
    def test_01_preferences_page_loads(self, logged_in_page: Page):
        """Test that preferences page loads without errors."""
        page = logged_in_page
        
        print("\n📄 Test: Preferences page loads")
        navigate_to(page, "/user/preferences")
        
        # Check page title
        assert "Preferences" in page.title() or "preferences" in page.title().lower(), \
            "Page title should contain 'Preferences'"
        
        # Check for key sections
        assert page_contains_text(page, "General Preferences"), \
            "Page should contain 'General Preferences' section"
        
        # Check no internal server error
        assert not page_contains_text(page, "Internal server error"), \
            "Page should not contain 'Internal server error'"
        
        print("✅ Preferences page loaded successfully")
    
    def test_02_preferences_shows_current_settings(self, logged_in_page: Page):
        """Test that preferences displays current settings."""
        page = logged_in_page
        
        print("\n📄 Test: Preferences shows current settings")
        navigate_to(page, "/user/preferences")
        
        # Check for theme selector
        theme_select = page.locator('select[name*="select_theme"]').first
        assert theme_select.count() > 0, "Theme selector should be present"
        
        # Check for dashboard layout selector
        layout_select = page.locator('select[name*="select_layout"]').first
        assert layout_select.count() > 0, "Dashboard layout selector should be present"
        
        # Get current values
        theme_value = theme_select.input_value()
        layout_value = layout_select.input_value()
        
        print(f"  Current theme: {theme_value}")
        print(f"  Current layout: {layout_value}")
        
        assert theme_value in ["light", "dark"], "Theme should be 'light' or 'dark'"
        assert layout_value in ["default", "compact", "wide"], \
            "Layout should be 'default', 'compact', or 'wide'"
        
        print("✅ Current settings displayed correctly")
    
    def test_03_change_theme_to_dark(self, logged_in_page: Page):
        """Test changing theme to dark mode."""
        page = logged_in_page
        
        print("\n📄 Test: Change theme to dark")
        navigate_to(page, "/user/preferences")
        
        # Select dark theme
        select_form_option(page, "select_theme", "dark")
        
        # Save preferences
        click_button(page, "btn_save_prefs")
        page.wait_for_timeout(500)
        
        # Check for success message
        assert check_flash_message(page, "success", "success") or \
               page_contains_text(page, "saved"), \
            "Should show success message after saving preferences"
        
        # Reload and verify
        navigate_to(page, "/user/preferences")
        theme_select = page.locator('select[name*="select_theme"]').first
        current_theme = theme_select.input_value()
        
        assert current_theme == "dark", \
            f"Theme should be 'dark' after save, got '{current_theme}'"
        
        print("✅ Theme changed to dark successfully")
    
    def test_04_change_theme_to_light(self, logged_in_page: Page):
        """Test changing theme back to light mode."""
        page = logged_in_page
        
        print("\n📄 Test: Change theme to light")
        navigate_to(page, "/user/preferences")
        
        # Select light theme
        select_form_option(page, "select_theme", "light")
        
        # Save preferences
        click_button(page, "btn_save_prefs")
        page.wait_for_timeout(500)
        
        # Check for success message
        assert check_flash_message(page, "success", "success") or \
               page_contains_text(page, "saved"), \
            "Should show success message"
        
        # Reload and verify
        navigate_to(page, "/user/preferences")
        theme_select = page.locator('select[name*="select_theme"]').first
        current_theme = theme_select.input_value()
        
        assert current_theme == "light", \
            f"Theme should be 'light' after save, got '{current_theme}'"
        
        print("✅ Theme changed to light successfully")
    
    def test_05_change_dashboard_layout_compact(self, logged_in_page: Page):
        """Test changing dashboard layout to compact."""
        page = logged_in_page
        
        print("\n📄 Test: Change layout to compact")
        navigate_to(page, "/user/preferences")
        
        # Select compact layout
        select_form_option(page, "select_layout", "compact")
        
        # Save preferences
        click_button(page, "btn_save_prefs")
        page.wait_for_timeout(500)
        
        # Check for success message
        assert check_flash_message(page, "success", "success") or \
               page_contains_text(page, "saved"), \
            "Should show success message"
        
        # Reload and verify
        navigate_to(page, "/user/preferences")
        layout_select = page.locator('select[name*="select_layout"]').first
        current_layout = layout_select.input_value()
        
        assert current_layout == "compact", \
            f"Layout should be 'compact' after save, got '{current_layout}'"
        
        print("✅ Layout changed to compact successfully")
    
    def test_06_change_dashboard_layout_wide(self, logged_in_page: Page):
        """Test changing dashboard layout to wide."""
        page = logged_in_page
        
        print("\n📄 Test: Change layout to wide")
        navigate_to(page, "/user/preferences")
        
        # Select wide layout
        select_form_option(page, "select_layout", "wide")
        
        # Save preferences
        click_button(page, "btn_save_prefs")
        page.wait_for_timeout(500)
        
        # Reload and verify
        navigate_to(page, "/user/preferences")
        layout_select = page.locator('select[name*="select_layout"]').first
        current_layout = layout_select.input_value()
        
        assert current_layout == "wide", \
            f"Layout should be 'wide' after save, got '{current_layout}'"
        
        print("✅ Layout changed to wide successfully")
    
    def test_07_change_dashboard_layout_default(self, logged_in_page: Page):
        """Test changing dashboard layout back to default."""
        page = logged_in_page
        
        print("\n📄 Test: Change layout to default")
        navigate_to(page, "/user/preferences")
        
        # Select default layout
        select_form_option(page, "select_layout", "default")
        
        # Save preferences
        click_button(page, "btn_save_prefs")
        page.wait_for_timeout(500)
        
        # Reload and verify
        navigate_to(page, "/user/preferences")
        layout_select = page.locator('select[name*="select_layout"]').first
        current_layout = layout_select.input_value()
        
        assert current_layout == "default", \
            f"Layout should be 'default' after save, got '{current_layout}'"
        
        print("✅ Layout changed to default successfully")
    
    def test_08_module_settings_displayed(self, logged_in_page: Page):
        """Test that module settings section is displayed."""
        page = logged_in_page
        
        print("\n📄 Test: Module settings display")
        navigate_to(page, "/user/preferences")
        
        # Check for module settings section
        assert page_contains_text(page, "Module Settings"), \
            "Page should contain 'Module Settings' section"
        
        # Check that module settings are shown as JSON or structured data
        page_text = page.content()
        has_json_display = "<pre" in page_text.lower() or "module_settings" in page_text.lower()
        assert has_json_display, "Module settings should be displayed"
        
        print("✅ Module settings section displayed")
    
    def test_09_breadcrumb_navigation(self, logged_in_page: Page):
        """Test that breadcrumb navigation works."""
        page = logged_in_page
        
        print("\n📄 Test: Breadcrumb navigation")
        navigate_to(page, "/user/preferences")
        
        # Check for breadcrumbs
        breadcrumb = page.locator('nav[aria-label="breadcrumb"], .breadcrumb')
        assert breadcrumb.count() > 0, "Page should have breadcrumb navigation"
        
        # Check breadcrumb contains Home and Preferences
        breadcrumb_text = breadcrumb.first.inner_text().lower()
        assert "home" in breadcrumb_text, "Breadcrumb should contain 'Home'"
        assert "preferences" in breadcrumb_text, "Breadcrumb should contain 'Preferences'"
        
        print("✅ Breadcrumb navigation present")


class TestGuestUserPreferences:
    """Test guest user restrictions on preferences page."""
    
    def test_01_guest_can_view_preferences(self, page: Page):
        """Test that GUEST user can view preferences page."""
        # Login as GUEST
        login(page, "GUEST", "")
        
        print("\n📄 Test: GUEST user can view preferences")
        navigate_to(page, "/user/preferences")
        
        # Page should load
        assert "Preferences" in page.title() or "preferences" in page.title().lower(), \
            "GUEST should be able to view preferences page"
        
        # Check no internal server error
        assert not page_contains_text(page, "Internal server error"), \
            "Page should not contain errors"
        
        print("✅ GUEST can view preferences page")
    
    def test_02_guest_sees_readonly_notice(self, page: Page):
        """Test that GUEST user sees read-only notice."""
        # Login as GUEST
        login(page, "GUEST", "")
        
        print("\n📄 Test: GUEST sees read-only notice")
        navigate_to(page, "/user/preferences")
        
        # Should see guest mode notice
        page_text = page.content().lower()
        has_guest_notice = (
            "guest" in page_text and (
                "read-only" in page_text or
                "readonly" in page_text or
                "cannot modify" in page_text or
                "view" in page_text
            )
        )
        
        assert has_guest_notice, \
            "GUEST user should see notice about read-only mode"
        
        print("✅ GUEST sees read-only notice")
    
    def test_03_guest_cannot_save_preferences(self, page: Page):
        """Test that GUEST user cannot save preferences."""
        # Login as GUEST
        login(page, "GUEST", "")
        
        print("\n📄 Test: GUEST cannot save preferences")
        navigate_to(page, "/user/preferences")
        
        # Check if save button is disabled or hidden
        save_button = page.locator('button[name*="btn_save_prefs"]')
        
        # Button should either not exist or be disabled
        button_exists = save_button.count() > 0
        
        if button_exists:
            # If button exists, it might be disabled
            is_disabled = save_button.first.is_disabled()
            assert is_disabled, "Save button should be disabled for GUEST"
            print("  Save button is disabled for GUEST")
        else:
            # Button doesn't exist for GUEST
            print("  Save button hidden for GUEST")
        
        print("✅ GUEST cannot save preferences")
        
        # Logout GUEST
        logout(page)


class TestFrameworkPreferences:
    """Test framework preferences redirect."""
    
    def test_01_framework_preferences_redirects(self, logged_in_page: Page):
        """Test that /user/framework_preferences redirects to settings page."""
        page = logged_in_page
        
        print("\n📄 Test: Framework preferences redirect")
        
        # Navigate to framework preferences
        page.goto(f"{page.url.split('/')[0]}//{page.url.split('/')[2]}/user/framework_preferences")
        page.wait_for_load_state('networkidle')
        
        # Should redirect to settings page
        current_url = page.url
        assert "/settings" in current_url, \
            f"Should redirect to settings page, but got: {current_url}"
        
        # Check no errors
        assert not page_contains_text(page, "Internal server error"), \
            "Redirect should work without errors"
        
        print(f"✅ Redirected correctly to: {current_url}")


class TestPreferencesPersistence:
    """Test that preferences persist across sessions."""
    
    def test_01_preferences_persist_after_logout(self, page: Page):
        """Test that preferences persist after logout and login."""
        # Login as admin
        login(page, "admin", "admin123")
        
        print("\n📄 Test: Preferences persist across sessions")
        navigate_to(page, "/user/preferences")
        
        # Set unique preferences
        select_form_option(page, "select_theme", "dark")
        select_form_option(page, "select_layout", "wide")
        
        # Save
        click_button(page, "btn_save_prefs")
        page.wait_for_timeout(500)
        
        print("  Saved preferences: theme=dark, layout=wide")
        
        # Logout
        logout(page)
        print("  Logged out")
        
        # Login again
        login(page, "admin", "admin123")
        print("  Logged back in")
        
        # Check preferences
        navigate_to(page, "/user/preferences")
        
        theme_select = page.locator('select[name*="select_theme"]').first
        layout_select = page.locator('select[name*="select_layout"]').first
        
        current_theme = theme_select.input_value()
        current_layout = layout_select.input_value()
        
        assert current_theme == "dark", \
            f"Theme should persist as 'dark', got '{current_theme}'"
        assert current_layout == "wide", \
            f"Layout should persist as 'wide', got '{current_layout}'"
        
        print("✅ Preferences persisted correctly across sessions")
        
        # Reset to defaults
        select_form_option(page, "select_theme", "light")
        select_form_option(page, "select_layout", "default")
        click_button(page, "btn_save_prefs")
        page.wait_for_timeout(500)
        
        print("  Reset preferences to defaults")
