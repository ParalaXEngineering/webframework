"""
Frontend tests for Translation/i18n system.

Tests language switching functionality:
- Setting language to English and verifying English text
- Setting language to French and verifying French translations
- Framework preferences page translation

Uses "My Framework Settings" / "Mes paramètres du framework" as visible indicator.
"""

import pytest
from playwright.sync_api import Page

from .conftest import (
    navigate_to, click_button, 
    page_contains_text, select_form_option
)


class TestTranslation:
    """Test translation system by switching languages."""
    
    def test_01_language_switch_to_english(self, logged_in_page: Page):
        """Test setting language to English and verifying translation."""
        page = logged_in_page
        
        print("\n📄 Test: Switch language to English")
        
        # Navigate to framework preferences
        navigate_to(page, "/settings/user_view")
        
        # Set language to English
        print("  Setting language to 'en'...")
        select_form_option(page, "language", "en")
        
        # Save settings
        click_button(page, "save")
        page.wait_for_timeout(500)
        
        # Navigate back to verify translation took effect
        navigate_to(page, "/settings/user_view")
        
        # Check for English text
        assert page_contains_text(page, "My Framework Settings"), \
            "Page should show 'My Framework Settings' in English"
        
        print("  ✅ English translation verified: 'My Framework Settings'")
        print("✅ Language switched to English successfully")
    
    def test_02_language_switch_to_french(self, logged_in_page: Page):
        """Test setting language to French and verifying translation."""
        page = logged_in_page
        
        print("\n📄 Test: Switch language to French")
        
        # Navigate to framework preferences
        navigate_to(page, "/settings/user_view")
        
        # Set language to French
        print("  Setting language to 'fr'...")
        select_form_option(page, "language", "fr")
        
        # Save settings
        click_button(page, "save")
        page.wait_for_timeout(500)
        
        # Navigate back to verify translation took effect
        navigate_to(page, "/settings/user_view")
        
        # Check for French text
        assert page_contains_text(page, "Mes paramètres du framework"), \
            "Page should show 'Mes paramètres du framework' in French"
        
        print("  ✅ French translation verified: 'Mes paramètres du framework'")
        print("✅ Language switched to French successfully")
    
    def test_03_language_persistence(self, logged_in_page: Page):
        """Test that language setting persists across page loads."""
        page = logged_in_page
        
        print("\n📄 Test: Language setting persistence")
        
        # Set to English first
        navigate_to(page, "/settings/user_view")
        select_form_option(page, "language", "en")
        click_button(page, "save")
        page.wait_for_timeout(500)
        
        # Navigate to another page and back
        navigate_to(page, "/")
        navigate_to(page, "/settings/user_view")
        
        # Should still show English
        assert page_contains_text(page, "My Framework Settings"), \
            "Language should persist as English"
        
        print("  ✅ English setting persisted")
        
        # Now switch to French
        select_form_option(page, "language", "fr")
        click_button(page, "save")
        page.wait_for_timeout(500)
        
        # Navigate away and back
        navigate_to(page, "/")
        navigate_to(page, "/settings/user_view")
        
        # Should now show French
        assert page_contains_text(page, "Mes paramètres du framework"), \
            "Language should persist as French"
        
        print("  ✅ French setting persisted")
        print("✅ Language setting persists correctly")
    
    def test_04_reset_to_english(self, logged_in_page: Page):
        """Reset language to English for other tests."""
        page = logged_in_page
        
        print("\n📄 Test: Reset language to English (cleanup)")
        
        # Navigate to framework preferences
        navigate_to(page, "/settings/user_view")
        
        # Set language back to English
        select_form_option(page, "language", "en")
        click_button(page, "save")
        page.wait_for_timeout(500)
        
        # Verify it's back to English
        navigate_to(page, "/settings/user_view")
        assert page_contains_text(page, "My Framework Settings"), \
            "Should be reset to English"
        
        print("  ✅ Language reset to English")
        print("✅ Cleanup complete")
