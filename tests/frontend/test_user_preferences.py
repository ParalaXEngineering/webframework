"""
Frontend tests for User Preferences page (/user/preferences).

Tests theme preference management including:
- Page loading and display
- Theme selection
- Theme persistence
- localStorage synchronization

Tests are ordered to build on each other for efficiency.
"""

from playwright.sync_api import Page

from tests.frontend.conftest import (
    navigate_to, select_form_option, click_button, 
    check_flash_message, page_contains_text
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
        
        # Check for theme section
        assert page_contains_text(page, "Theme Preference"), \
            "Page should contain 'Theme Preference' section"
        
        # Check no internal server error
        assert not page_contains_text(page, "Internal server error"), \
            "Page should not contain 'Internal server error'"
        
        print("✅ Preferences page loaded successfully")
    
    def test_02_preferences_shows_current_theme(self, logged_in_page: Page):
        """Test that preferences displays current theme setting."""
        page = logged_in_page
        
        print("\n📄 Test: Preferences shows current theme")
        navigate_to(page, "/user/preferences")
        
        # Check for theme selector
        theme_select = page.locator('select[name*="select_theme"]').first
        assert theme_select.count() > 0, "Theme selector should be present"
        
        # Get current value
        theme_value = theme_select.input_value()
        print(f"  Current theme: {theme_value}")
        
        assert theme_value in ["light", "dark"], "Theme should be 'light' or 'dark'"
        
        print("✅ Current theme displayed correctly")
    
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