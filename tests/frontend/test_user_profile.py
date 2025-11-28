"""
Frontend tests for User Profile page (/user/profile).

Tests profile management including:
- Page loading and display
- Profile information updates (display name, email)
- Avatar upload
- Password changes
- Account information display
- Error handling and validation

Tests are ordered to build on each other for efficiency.
"""

import pytest
from pathlib import Path
from playwright.sync_api import Page

from tests.frontend.conftest import (
    navigate_to, fill_form_field, click_button, 
    check_flash_message, page_contains_text, BASE_URL
)


class TestUserProfilePage:
    """Test user profile page functionality with ordered tests."""
    
    def test_01_profile_page_loads(self, logged_in_page: Page):
        """Test that profile page loads without errors."""
        page = logged_in_page
        
        print("\n📄 Test: Profile page loads")
        navigate_to(page, "/user/profile")
        
        # Check page title
        assert page_contains_text(page, "My Profile"), \
            "Page title should contain 'Profile'"
        
        # Check for key sections
        assert page_contains_text(page, "Profile Information"), \
            "Page should contain 'Profile Information' section"
        assert page_contains_text(page, "Profile Picture"), \
            "Page should contain 'Profile Picture' section"
        
        # Check no internal server error
        assert not page_contains_text(page, "Internal server error"), \
            "Page should not contain 'Internal server error'"
        
        print("✅ Profile page loaded successfully")
    
    def test_02_profile_shows_current_user_info(self, logged_in_page: Page):
        """Test that profile displays current user information."""
        page = logged_in_page
        
        print("\n📄 Test: Profile shows current user info")
        navigate_to(page, "/user/profile")
        
        # Check for account information section
        assert page_contains_text(page, "Account Information"), \
            "Page should contain 'Account Information' section"
        
        # Check for username display
        assert page_contains_text(page, "Username"), \
            "Page should display username label"
        
        # Check for groups display
        assert page_contains_text(page, "Groups"), \
            "Page should display groups label"
        
        print("✅ User info displayed correctly")
    
    def test_03_update_display_name(self, logged_in_page: Page):
        """Test updating display name."""
        page = logged_in_page
        
        print("\n📄 Test: Update display name")
        navigate_to(page, "/user/profile")
        
        # Get current display name field
        display_name_input = page.locator('input[name*="input_display_name"]').first
        old_value = display_name_input.input_value()
        print(f"  Current display name: {old_value}")
        
        # Update display name
        new_display_name = "Test Admin Updated"
        fill_form_field(page, "input_display_name", new_display_name)
        
        # Click update button
        click_button(page, "btn_update_info")
        page.wait_for_timeout(500)
        
        # Check for success message
        assert check_flash_message(page, "success", "success") or \
               page_contains_text(page, "updated") or \
               page_contains_text(page, "success"), \
            "Should show success message after update"
        
        # Verify the display name was updated by reloading and checking
        navigate_to(page, "/user/profile")
        display_name_input = page.locator('input[name*="input_display_name"]').first
        current_value = display_name_input.input_value()
        
        assert current_value == new_display_name, \
            f"Display name should be updated to '{new_display_name}', got '{current_value}'"
        
        print(f"✅ Display name updated successfully to: {new_display_name}")
    
    def test_04_update_email(self, logged_in_page: Page):
        """Test updating email address."""
        page = logged_in_page
        
        print("\n📄 Test: Update email")
        navigate_to(page, "/user/profile")
        
        # Update email
        new_email = "testadmin@example.com"
        fill_form_field(page, "input_email", new_email)
        
        # Click update button
        click_button(page, "btn_update_info")
        page.wait_for_timeout(500)
        
        # Check for success message
        assert check_flash_message(page, "success", "success") or \
               page_contains_text(page, "updated"), \
            "Should show success message after email update"
        
        # Verify email was updated
        navigate_to(page, "/user/profile")
        email_input = page.locator('input[name*="input_email"]').first
        current_value = email_input.input_value()
        
        assert current_value == new_email, \
            f"Email should be updated to '{new_email}', got '{current_value}'"
        
        print(f"✅ Email updated successfully to: {new_email}")
    
    def test_05_empty_display_name_validation(self, logged_in_page: Page):
        """Test that empty display name is rejected."""
        page = logged_in_page
        
        print("\n📄 Test: Empty display name validation")
        navigate_to(page, "/user/profile")
        
        # Try to set empty display name
        fill_form_field(page, "input_display_name", "")
        
        # Click update button
        click_button(page, "btn_update_info")
        page.wait_for_timeout(500)
        
        # Should show error or stay on same page with validation message
        page_text = page.content().lower()
        has_error = (
            "cannot be empty" in page_text or
            "required" in page_text or
            check_flash_message(page, "error", "danger") or
            check_flash_message(page, "cannot", "danger")
        )
        
        assert has_error, "Should show error for empty display name"
        
        print("✅ Empty display name validation works")
    
    def test_06_avatar_upload(self, logged_in_page: Page):
        """Test avatar image upload."""
        page = logged_in_page
        
        print("\n📄 Test: Avatar upload")
        navigate_to(page, "/user/profile")
        
        # Find file input and upload test avatar
        avatar_file_path = Path(__file__).parent / "test_avatar.jpg"
        assert avatar_file_path.exists(), "Test avatar file should exist"
        
        # Upload file
        file_input = page.locator('input[type="file"][name*="file_avatar"]').first
        file_input.set_input_files(str(avatar_file_path))
        
        # Click upload button
        click_button(page, "btn_upload_avatar")
        page.wait_for_timeout(500)
        
        # Check for success message
        assert check_flash_message(page, "success", "success") or \
               page_contains_text(page, "updated") or \
               page_contains_text(page, "uploaded"), \
            "Should show success message after avatar upload"
        
        # Verify avatar image is displayed (check for img tag with avatar)
        navigate_to(page, "/user/profile")
        avatar_img = page.locator('img[src*="avatar"], img[src*="users/"]').first
        assert avatar_img.count() > 0, "Avatar image should be displayed"
        
        print("✅ Avatar uploaded successfully")
    
    def test_07_invalid_file_type_rejected(self, logged_in_page: Page):
        """Test that non-image files are rejected for avatar."""
        page = logged_in_page
        
        print("\n📄 Test: Invalid file type rejection")
        navigate_to(page, "/user/profile")
        
        # Create a temporary text file
        temp_file = Path(__file__).parent / "test_invalid.txt"
        temp_file.write_text("This is not an image")
        
        try:
            # Try to upload text file
            file_input = page.locator('input[type="file"][name*="file_avatar"]').first
            file_input.set_input_files(str(temp_file))
            
            # Click upload button
            click_button(page, "btn_upload_avatar")
            page.wait_for_timeout(500)
            
            # Should show error message
            assert check_flash_message(page, "error", "danger") or \
                   check_flash_message(page, "not allowed", "danger") or \
                   page_contains_text(page, "only") or \
                   page_contains_text(page, "jpeg") or \
                   page_contains_text(page, "png"), \
                "Should show error for invalid file type"
            
            print("✅ Invalid file type rejected correctly")
        
        finally:
            # Cleanup temp file
            if temp_file.exists():
                temp_file.unlink()
    
    def test_08_change_password_success(self, logged_in_page: Page):
        """Test successful password change."""
        page = logged_in_page
        
        print("\n📄 Test: Change password")
        navigate_to(page, "/user/profile")
        
        # Check if password change section exists (only for users with passwords)
        if not page_contains_text(page, "Change Password"):
            print("⚠️  Password change section not available (passwordless account)")
            pytest.skip("Password change not available for this user")
        
        # Now test changing password from 'admin123' to 'newpass123'
        # Note: Using raw HTML inputs since DisplayerItemInputPassword doesn't exist yet
        page.fill('input#input_current_password', 'admin123')
        page.fill('input#input_new_password', 'newpass123')
        page.fill('input#input_confirm_password', 'newpass123')
        
        # Click change password button
        click_button(page, "btn_change_password")
        page.wait_for_timeout(500)
        
        # Check for success message
        assert check_flash_message(page, "success", "success") or \
               page_contains_text(page, "changed"), \
            "Should show success message after password change"
        
        print("✅ Password changed successfully")
        
        # IMPORTANT: Change password back immediately to not break subsequent tests
        navigate_to(page, "/user/profile")
        page.fill('input#input_current_password', 'newpass123')
        page.fill('input#input_new_password', 'admin123')
        page.fill('input#input_confirm_password', 'admin123')
        click_button(page, "btn_change_password")
        page.wait_for_timeout(500)
        
        # Verify password was restored
        assert check_flash_message(page, "success", "success") or \
               page_contains_text(page, "changed"), \
            "Should show success message after restoring password"
        
        print("✅ Password reset to original")
    
    def test_09_wrong_current_password(self, logged_in_page: Page):
        """Test that wrong current password is rejected."""
        page = logged_in_page
        
        print("\n📄 Test: Wrong current password rejection")
        navigate_to(page, "/user/profile")
        
        # Check if password change section exists
        if not page_contains_text(page, "Change Password"):
            pytest.skip("Password change not available")
        
        # Try to change password with wrong current password
        page.fill('input#input_current_password', 'wrongpassword')
        page.fill('input#input_new_password', 'newpass123')
        page.fill('input#input_confirm_password', 'newpass123')
        
        # Click change password button
        click_button(page, "btn_change_password")
        page.wait_for_timeout(500)
        
        # Should show error
        assert check_flash_message(page, "error", "danger") or \
               check_flash_message(page, "incorrect", "danger") or \
               page_contains_text(page, "incorrect"), \
            "Should show error for incorrect current password"
        
        print("✅ Wrong current password rejected correctly")
    
    def test_10_password_mismatch(self, logged_in_page: Page):
        """Test that mismatched passwords are rejected."""
        page = logged_in_page
        
        print("\n📄 Test: Password mismatch rejection")
        navigate_to(page, "/user/profile")
        
        # Check if password change section exists
        if not page_contains_text(page, "Change Password"):
            pytest.skip("Password change not available")
        
        # Try to change password with mismatched confirmation
        page.fill('input#input_current_password', 'admin123')
        page.fill('input#input_new_password', 'newpass123')
        page.fill('input#input_confirm_password', 'different123')
        
        # Click change password button
        click_button(page, "btn_change_password")
        page.wait_for_timeout(500)
        
        # Should show error
        assert check_flash_message(page, "error", "danger") or \
               page_contains_text(page, "do not match") or \
               page_contains_text(page, "match"), \
            "Should show error for mismatched passwords"
        
        print("✅ Password mismatch rejected correctly")
    
    def test_11_weak_password_rejected(self, logged_in_page: Page):
        """Test that weak passwords are rejected."""
        page = logged_in_page
        
        print("\n📄 Test: Weak password rejection")
        navigate_to(page, "/user/profile")
        
        # Check if password change section exists
        if not page_contains_text(page, "Change Password"):
            pytest.skip("Password change not available")
        
        # Try weak passwords
        weak_passwords = ["123", "abc", "12345"]
        
        for weak_pwd in weak_passwords:
            page.fill('input#input_current_password', 'admin123')
            page.fill('input#input_new_password', weak_pwd)
            page.fill('input#input_confirm_password', weak_pwd)
            
            # Click change password button
            click_button(page, "btn_change_password")
            page.wait_for_timeout(500)
            
            # Should show error
            has_error = (
                check_flash_message(page, "error", "danger") or
                page_contains_text(page, "at least") or
                page_contains_text(page, "invalid") or
                page_contains_text(page, "strength")
            )
            
            if has_error:
                print(f"  ✅ Weak password '{weak_pwd}' rejected")
                break
        else:
            pytest.fail("At least one weak password should be rejected")
        
        print("✅ Weak password validation works")
    
    def test_12_account_info_displayed(self, logged_in_page: Page):
        """Test that account information is properly displayed."""
        page = logged_in_page
        
        print("\n📄 Test: Account information display")
        navigate_to(page, "/user/profile")
        
        # Check for account information table
        assert page_contains_text(page, "Account Information"), \
            "Should have Account Information section"
        
        # Check for key fields
        required_fields = ["Username", "Groups"]
        for field in required_fields:
            assert page_contains_text(page, field), \
                f"Account information should display '{field}'"
        
        # Check for dates (created, last login)
        page_text = page.content().lower()
        has_dates = "created" in page_text or "login" in page_text
        assert has_dates, "Should display account creation or login dates"
        
        print("✅ Account information displayed correctly")
    
    def test_13_breadcrumb_navigation(self, logged_in_page: Page):
        """Test that breadcrumb navigation works."""
        page = logged_in_page
        
        print("\n📄 Test: Breadcrumb navigation")
        navigate_to(page, "/user/profile")
        
        # Check for breadcrumbs
        breadcrumb = page.locator('nav[aria-label="breadcrumb"], .breadcrumb')
        assert breadcrumb.count() > 0, "Page should have breadcrumb navigation"
        
        # Check breadcrumb contains Home and Profile
        breadcrumb_text = breadcrumb.first.inner_text().lower()
        assert "home" in breadcrumb_text, "Breadcrumb should contain 'Home'"
        assert "profile" in breadcrumb_text, "Breadcrumb should contain 'Profile'"
        
        print("✅ Breadcrumb navigation present")
    
    def test_14_profile_page_responsive(self, logged_in_page: Page):
        """Test that profile page layout is present and structured."""
        page = logged_in_page
        
        print("\n📄 Test: Profile page structure")
        navigate_to(page, "/user/profile")
        
        # Check for form elements
        forms = page.locator('form').all()
        assert len(forms) > 0, "Page should contain forms"
        
        # Check for input fields
        inputs = page.locator('input').all()
        assert len(inputs) >= 2, "Page should have multiple input fields"
        
        # Check for buttons
        buttons = page.locator('button').all()
        assert len(buttons) >= 2, "Page should have multiple action buttons"
        
        print(f"✅ Page structure: {len(forms)} forms, {len(inputs)} inputs, {len(buttons)} buttons")
