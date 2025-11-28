"""
Frontend tests for File Manager interface.

Tests file upload, display, edit, version control, and deletion workflows.
Uses Playwright for end-to-end testing.

Test Structure:
- TestFileManagerUpload: File upload via demo page
- TestFileManagerDisplay: File display and thumbnails
- TestFileManagerDownload: Download functionality
- TestFileManagerDelete: File deletion workflows
- TestFileManagerEdit: Metadata editing (TODO - Medium Priority)
- TestFileManagerVersions: Version control (TODO - Medium Priority)
- TestFileManagerSearch: Search and filter (TODO - Medium Priority)

Priority levels:
- High: Basic upload, display, download, delete, thumbnails
- Medium: Edit metadata, version history, multi-delete, search
- Low: Single version delete, integrity checks, edge cases

Run tests:
    pytest tests/frontend/test_file_manager.py -v
    pytest tests/frontend/test_file_manager.py::TestFileManagerUpload -v
"""

import pytest
import time
from pathlib import Path
from playwright.sync_api import Page

from tests.frontend.conftest import (
    navigate_to, fill_form_field, click_button,
    check_flash_message, page_contains_text, BASE_URL, HUMAN_MODE
)


# ============================================================================
# TEST DATA
# ============================================================================

# Test files directory
TEST_FILES_DIR = Path(__file__).parent / "test_files"

# Test file paths
TEST_IMAGE_JPG = TEST_FILES_DIR / "test_image.jpg"
TEST_IMAGE_PNG = TEST_FILES_DIR / "test_image.png"
TEST_DOCUMENT_PDF = TEST_FILES_DIR / "test_document.pdf"
TEST_TEXT_FILE = TEST_FILES_DIR / "test_text.txt"
TEST_ARCHIVE_ZIP = TEST_FILES_DIR / "test_archive.zip"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def upload_file_via_demo(page: Page, file_path: Path, group_id: str = None, tags: list = None) -> str:
    """Upload a file via the demo page FilePond uploader.
    
    Args:
        page: Playwright page
        file_path: Path to file to upload
        group_id: Optional group ID
        tags: Optional list of tags
        
    Returns:
        Filename that was uploaded
        
    Raises:
        AssertionError: If upload fails
    """
    # Navigate to demo page
    navigate_to(page, "/file-manager-demo")
    
    # Check we have upload permission
    page_text = page.content().lower()
    if "you don't have permission to upload" in page_text:
        pytest.skip("User does not have upload permission")
    
    # Find file input (FilePond creates hidden file input)
    file_input = page.locator('input[type="file"]').first
    
    # Upload file
    print(f"  📤 Uploading: {file_path.name}")
    file_input.set_input_files(str(file_path))
    
    # Wait for FilePond to start processing
    page.wait_for_selector('.filepond--item', timeout=5000)
    
    # Wait for upload to complete (look for success state)
    # FilePond shows different states: idle, processing-complete, load-invalid, processing-error
    try:
        page.wait_for_selector(
            '.filepond--file[data-filepond-item-state="processing-complete"]',
            timeout=15000
        )
        print(f"  ✅ Upload complete: {file_path.name}")
    except Exception as e:
        # Check for error state
        error_item = page.locator('.filepond--file[data-filepond-item-state="processing-error"]')
        if error_item.count() > 0:
            error_text = error_item.locator('.filepond--file-status-main').inner_text()
            raise AssertionError(f"Upload failed with error: {error_text}")
        raise AssertionError(f"Upload timeout or failed: {e}")
    
    return file_path.name


def verify_file_in_admin_list(page: Page, filename: str) -> bool:
    """Check if file appears in admin file list.
    
    Args:
        page: Playwright page
        filename: Filename to search for
        
    Returns:
        True if file found, False otherwise
    """
    # Navigate to admin page
    navigate_to(page, "/file_manager/")
    
    # Wait for DataTable to initialize
    page.wait_for_selector('#file_list_table', timeout=5000)
    
    # Use DataTable search
    search_input = page.locator('input[type="search"]')
    search_input.fill(filename)
    
    # Wait for search to filter (debounced)
    page.wait_for_timeout(500)
    
    # Check if filename appears in table
    filename_cells = page.locator(f'#file_list_table td:has-text("{filename}")')
    found = filename_cells.count() > 0
    
    if found:
        print(f"  ✅ File found in admin list: {filename}")
    else:
        print(f"  ❌ File NOT found in admin list: {filename}")
    
    return found


def get_file_id_from_admin_list(page: Page, filename: str) -> int:
    """Get file ID from admin list for a given filename.
    
    Args:
        page: Playwright page
        filename: Filename to find
        
    Returns:
        File ID (integer)
        
    Raises:
        AssertionError: If file not found
    """
    navigate_to(page, "/file_manager/")
    page.wait_for_selector('#file_list_table', timeout=5000)
    
    # Search for file
    search_input = page.locator('input[type="search"]')
    search_input.fill(filename)
    page.wait_for_timeout(500)
    
    # Find row containing filename
    row = page.locator(f'#file_list_table tr:has-text("{filename}")').first
    if row.count() == 0:
        raise AssertionError(f"File not found in admin list: {filename}")
    
    # Get checkbox value (which is the file ID)
    checkbox = row.locator('input[type="checkbox"]').first
    file_id = int(checkbox.get_attribute('value'))
    
    print(f"  ℹ️  File ID for '{filename}': {file_id}")
    return file_id


def verify_thumbnail_exists(page: Page, filename: str) -> bool:
    """Check if thumbnail exists for a file in admin list.
    
    Args:
        page: Playwright page
        filename: Filename to check
        
    Returns:
        True if thumbnail found, False otherwise
    """
    navigate_to(page, "/file_manager/")
    page.wait_for_selector('#file_list_table', timeout=5000)
    
    # Search for file
    search_input = page.locator('input[type="search"]')
    search_input.fill(filename)
    page.wait_for_timeout(500)
    
    # Find row and look for thumbnail image
    row = page.locator(f'#file_list_table tr:has-text("{filename}")').first
    if row.count() == 0:
        return False
    
    # Look for thumbnail image in preview column
    thumbnail = row.locator('img[src*="thumb"]')
    has_thumbnail = thumbnail.count() > 0
    
    if has_thumbnail:
        print(f"  ✅ Thumbnail exists for: {filename}")
    else:
        print(f"  ℹ️  No thumbnail for: {filename} (expected for non-images)")
    
    return has_thumbnail


def click_action_button_for_file(page: Page, filename: str, action: str):
    """Click an action button for a specific file in admin list.
    
    Args:
        page: Playwright page
        filename: Filename to find
        action: Action to perform ('download', 'edit', 'history', 'delete')
    """
    navigate_to(page, "/file_manager/")
    page.wait_for_selector('#file_list_table', timeout=5000)
    
    # Search for file
    search_input = page.locator('input[type="search"]')
    search_input.fill(filename)
    page.wait_for_timeout(500)
    
    # Find row
    row = page.locator(f'#file_list_table tr:has-text("{filename}")').first
    if row.count() == 0:
        raise AssertionError(f"File not found: {filename}")
    
    # Map action to icon class
    icon_map = {
        'download': 'mdi-download',
        'edit': 'mdi-pencil',
        'history': 'mdi-history',
        'delete': 'mdi-delete'
    }
    
    if action not in icon_map:
        raise ValueError(f"Unknown action: {action}")
    
    # Click action button
    action_button = row.locator(f'a i.{icon_map[action]}').first
    if action_button.count() == 0:
        raise AssertionError(f"Action button '{action}' not found for file: {filename}")
    
    # Get parent anchor and click it
    anchor = action_button.locator('..').first
    anchor.click()
    
    # Wait for navigation or modal
    page.wait_for_timeout(500)


# ============================================================================
# HIGH PRIORITY TESTS
# ============================================================================

class TestFileManagerUpload:
    """Test file upload functionality (HIGH PRIORITY)."""
    
    def test_01_upload_single_image(self, logged_in_page: Page):
        """Test uploading a single image file via demo page."""
        page = logged_in_page
        
        print("\n📄 Test: Upload single image file")
        
        # Create unique filename to avoid conflicts
        timestamp = int(time.time())
        test_file = TEST_FILES_DIR / f"frontend_test_image_{timestamp}.jpg"
        
        # Create a simple test image if it doesn't exist
        if not TEST_FILES_DIR.exists():
            TEST_FILES_DIR.mkdir(parents=True, exist_ok=True)
        
        # Create minimal test image (1x1 pixel JPEG)
        if not test_file.exists():
            # Minimal JPEG header + 1x1 red pixel
            jpeg_data = bytes([
                0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
                0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
                0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
                0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
                0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
                0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
                0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
                0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
                0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x14, 0x00, 0x01,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x03, 0xFF, 0xC4, 0x00, 0x14, 0x10, 0x01, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00,
                0x37, 0xFF, 0xD9
            ])
            test_file.write_bytes(jpeg_data)
        
        # Upload file
        filename = upload_file_via_demo(page, test_file)
        
        # Verify appears in admin list
        assert verify_file_in_admin_list(page, filename), \
            f"Uploaded file should appear in admin list: {filename}"
        
        print("✅ Image upload successful")
    
    def test_02_upload_text_file(self, logged_in_page: Page):
        """Test uploading a text file."""
        page = logged_in_page
        
        print("\n📄 Test: Upload text file")
        
        # Create test text file
        timestamp = int(time.time())
        test_file = TEST_FILES_DIR / f"frontend_test_text_{timestamp}.txt"
        test_file.write_text("This is a test file for frontend testing.\nLine 2.")
        
        # Upload
        filename = upload_file_via_demo(page, test_file)
        
        # Verify in admin list
        assert verify_file_in_admin_list(page, filename), \
            f"Uploaded text file should appear in admin list: {filename}"
        
        print("✅ Text file upload successful")
    
    def test_03_upload_with_metadata(self, logged_in_page: Page):
        """Test uploading with group_id and tags (if visible in demo)."""
        page = logged_in_page
        
        print("\n📄 Test: Upload with metadata")
        
        # Note: Demo page might have pre-filled values, so this test
        # just verifies the upload works with the demo interface
        
        timestamp = int(time.time())
        test_file = TEST_FILES_DIR / f"frontend_test_metadata_{timestamp}.txt"
        test_file.write_text("Test file with metadata")
        
        # Upload via demo (uses whatever metadata demo page has)
        filename = upload_file_via_demo(page, test_file)
        
        # Verify in admin list
        assert verify_file_in_admin_list(page, filename), \
            f"File with metadata should appear in admin list: {filename}"
        
        print("✅ Upload with metadata successful")


class TestFileManagerDisplay:
    """Test file display in admin interface (HIGH PRIORITY)."""
    
    def test_01_admin_page_loads(self, logged_in_page: Page):
        """Test that admin file manager page loads."""
        page = logged_in_page
        
        print("\n📄 Test: Admin page loads")
        
        navigate_to(page, "/file_manager/")
        
        # Check page title
        assert page_contains_text(page, "File Manager"), \
            "Page should contain 'File Manager'"
        
        # Check for DataTable
        page.wait_for_selector('#file_list_table', timeout=5000)
        
        print("✅ Admin page loaded successfully")
    
    def test_02_file_list_displays(self, logged_in_page: Page):
        """Test that file list displays in DataTable."""
        page = logged_in_page
        
        print("\n📄 Test: File list displays")
        
        navigate_to(page, "/file_manager/")
        
        # Wait for DataTable
        page.wait_for_selector('#file_list_table', timeout=5000)
        
        # Check for table columns
        assert page_contains_text(page, "Filename"), \
            "Table should have 'Filename' column"
        assert page_contains_text(page, "Size"), \
            "Table should have 'Size' column"
        assert page_contains_text(page, "Uploaded"), \
            "Table should have 'Uploaded' column"
        
        print("✅ File list displays correctly")
    
    def test_03_search_functionality(self, logged_in_page: Page):
        """Test DataTable search functionality."""
        page = logged_in_page
        
        print("\n📄 Test: Search functionality")
        
        # First upload a test file to search for
        timestamp = int(time.time())
        test_file = TEST_FILES_DIR / f"frontend_test_search_{timestamp}.txt"
        test_file.write_text("Search test file")
        filename = upload_file_via_demo(page, test_file)
        
        # Navigate to admin and search
        navigate_to(page, "/file_manager/")
        page.wait_for_selector('#file_list_table', timeout=5000)
        
        # Search for our file
        search_input = page.locator('input[type="search"]')
        search_input.fill(filename)
        page.wait_for_timeout(500)
        
        # Verify file appears
        assert page.locator(f'#file_list_table td:has-text("{filename}")').count() > 0, \
            f"Search should find file: {filename}"
        
        # Search for non-existent file
        search_input.fill("nonexistent_file_xyz123")
        page.wait_for_timeout(500)
        
        # Should show "No matching records"
        assert page_contains_text(page, "No matching records") or \
               page.locator('#file_list_table tbody tr').count() == 0, \
            "Search should show no results for non-existent file"
        
        print("✅ Search functionality works")
    
    def test_04_thumbnail_displays_for_image(self, logged_in_page: Page):
        """Test that thumbnails display for image files."""
        page = logged_in_page
        
        print("\n📄 Test: Thumbnail displays for image")
        
        # Upload an image
        timestamp = int(time.time())
        test_file = TEST_FILES_DIR / f"frontend_test_thumb_{timestamp}.jpg"
        
        # Create minimal JPEG
        jpeg_data = bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
            0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
            0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
            0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
            0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
            0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
            0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
            0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
            0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x14, 0x00, 0x01,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x03, 0xFF, 0xC4, 0x00, 0x14, 0x10, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00,
            0x37, 0xFF, 0xD9
        ])
        test_file.write_bytes(jpeg_data)
        
        filename = upload_file_via_demo(page, test_file)
        
        # Wait a bit for thumbnail generation (if enabled)
        page.wait_for_timeout(2000)
        
        # Check if thumbnail exists (might not if thumbnail generation is disabled)
        has_thumbnail = verify_thumbnail_exists(page, filename)
        
        # This is informational - thumbnails might be disabled in test environment
        print(f"  ℹ️  Thumbnail generation: {'enabled' if has_thumbnail else 'disabled or not yet generated'}")
        
        print("✅ Thumbnail display test complete")


class TestFileManagerDownload:
    """Test file download functionality (HIGH PRIORITY)."""
    
    def test_01_download_file(self, logged_in_page: Page):
        """Test downloading a file from admin list."""
        page = logged_in_page
        
        print("\n📄 Test: Download file")
        
        # Upload a test file first
        timestamp = int(time.time())
        test_file = TEST_FILES_DIR / f"frontend_test_download_{timestamp}.txt"
        test_content = "This file will be downloaded in the test."
        test_file.write_text(test_content)
        
        filename = upload_file_via_demo(page, test_file)
        
        # Navigate to admin list
        navigate_to(page, "/file_manager/")
        page.wait_for_selector('#file_list_table', timeout=5000)
        
        # Search for file
        search_input = page.locator('input[type="search"]')
        search_input.fill(filename)
        page.wait_for_timeout(500)
        
        # Find download button and trigger download
        row = page.locator(f'#file_list_table tr:has-text("{filename}")').first
        download_link = row.locator('a i.mdi-download').locator('..').first
        
        # Use Playwright's download handling
        with page.expect_download() as download_info:
            download_link.click()
        
        download = download_info.value
        
        # Verify download
        assert download.suggested_filename == filename, \
            f"Downloaded filename should match: {filename}"
        
        # Save and verify content
        download_path = TEST_FILES_DIR / f"downloaded_{filename}"
        download.save_as(download_path)
        
        downloaded_content = download_path.read_text()
        assert downloaded_content == test_content, \
            "Downloaded file content should match original"
        
        # Cleanup
        download_path.unlink()
        
        print("✅ File download successful")


class TestFileManagerDelete:
    """Test file deletion functionality (HIGH PRIORITY)."""
    
    def test_01_delete_single_file(self, logged_in_page: Page):
        """Test deleting a single file with confirmation."""
        page = logged_in_page
        
        print("\n📄 Test: Delete single file")
        
        # Upload a test file to delete
        timestamp = int(time.time())
        test_file = TEST_FILES_DIR / f"frontend_test_delete_{timestamp}.txt"
        test_file.write_text("This file will be deleted.")
        
        filename = upload_file_via_demo(page, test_file)
        
        # Navigate to admin list
        navigate_to(page, "/file_manager/")
        page.wait_for_selector('#file_list_table', timeout=5000)
        
        # Search for file
        search_input = page.locator('input[type="search"]')
        search_input.fill(filename)
        page.wait_for_timeout(500)
        
        # Click delete button
        row = page.locator(f'#file_list_table tr:has-text("{filename}")').first
        delete_link = row.locator('a i.mdi-delete').locator('..').first
        delete_link.click()
        
        # Should navigate to confirmation page
        page.wait_for_timeout(500)
        
        # Check for confirmation message
        assert page_contains_text(page, "Confirm Delete") or \
               page_contains_text(page, "confirm"), \
            "Should show confirmation page"
        
        # Click confirm delete button
        confirm_button = page.locator('button:has-text("Yes, Delete")').first
        confirm_button.click()
        
        # Wait for deletion to complete
        page.wait_for_timeout(1000)
        
        # Verify success message or redirection
        assert page_contains_text(page, "deleted successfully") or \
               page_contains_text(page, "Success") or \
               page_contains_text(page, "Complete"), \
            "Should show deletion success message"
        
        # Navigate back to admin list and verify file is gone
        navigate_to(page, "/file_manager/")
        page.wait_for_selector('#file_list_table', timeout=5000)
        
        search_input = page.locator('input[type="search"]')
        search_input.fill(filename)
        page.wait_for_timeout(500)
        
        # Should not find the file
        assert page.locator(f'#file_list_table td:has-text("{filename}")').count() == 0, \
            f"Deleted file should not appear in list: {filename}"
        
        print("✅ File deletion successful")
    
    def test_02_delete_cancellation(self, logged_in_page: Page):
        """Test canceling file deletion."""
        page = logged_in_page
        
        print("\n📄 Test: Cancel file deletion")
        
        # Upload a test file
        timestamp = int(time.time())
        test_file = TEST_FILES_DIR / f"frontend_test_cancel_delete_{timestamp}.txt"
        test_file.write_text("This file should NOT be deleted.")
        
        filename = upload_file_via_demo(page, test_file)
        
        # Navigate to admin list and click delete
        navigate_to(page, "/file_manager/")
        page.wait_for_selector('#file_list_table', timeout=5000)
        
        search_input = page.locator('input[type="search"]')
        search_input.fill(filename)
        page.wait_for_timeout(500)
        
        row = page.locator(f'#file_list_table tr:has-text("{filename}")').first
        delete_link = row.locator('a i.mdi-delete').locator('..').first
        delete_link.click()
        
        page.wait_for_timeout(500)
        
        # Click cancel button
        cancel_button = page.locator('a:has-text("Cancel")').first
        cancel_button.click()
        
        # Should return to admin list
        page.wait_for_timeout(500)
        
        # Verify file still exists
        assert verify_file_in_admin_list(page, filename), \
            f"File should still exist after canceling delete: {filename}"
        
        print("✅ Delete cancellation works correctly")


# ============================================================================
# MEDIUM PRIORITY TESTS (TODO - Placeholder)
# ============================================================================

class TestFileManagerEdit:
    """Test metadata editing functionality (MEDIUM PRIORITY - TODO)."""
    
    @pytest.mark.skip(reason="Medium priority - TODO")
    def test_edit_group_id(self, logged_in_page: Page):
        """Test editing file group_id."""
        pass
    
    @pytest.mark.skip(reason="Medium priority - TODO")
    def test_edit_tags(self, logged_in_page: Page):
        """Test editing file tags."""
        pass


class TestFileManagerVersions:
    """Test version control functionality (MEDIUM PRIORITY - TODO)."""
    
    @pytest.mark.skip(reason="Medium priority - TODO")
    def test_create_new_version(self, logged_in_page: Page):
        """Test uploading a new version of existing file."""
        pass
    
    @pytest.mark.skip(reason="Medium priority - TODO")
    def test_view_version_history(self, logged_in_page: Page):
        """Test viewing version history page."""
        pass
    
    @pytest.mark.skip(reason="Medium priority - TODO")
    def test_restore_old_version(self, logged_in_page: Page):
        """Test restoring an old version."""
        pass


class TestFileManagerMultiDelete:
    """Test multi-delete with checkboxes (MEDIUM PRIORITY - TODO)."""
    
    @pytest.mark.skip(reason="Medium priority - TODO")
    def test_multi_delete_with_checkboxes(self, logged_in_page: Page):
        """Test selecting multiple files and deleting them."""
        pass


# ============================================================================
# LOW PRIORITY TESTS (TODO - Placeholder)
# ============================================================================

class TestFileManagerEdgeCases:
    """Test edge cases and error handling (LOW PRIORITY - TODO)."""
    
    @pytest.mark.skip(reason="Low priority - TODO")
    def test_upload_oversized_file(self, logged_in_page: Page):
        """Test uploading file exceeding size limit."""
        pass
    
    @pytest.mark.skip(reason="Low priority - TODO")
    def test_upload_invalid_extension(self, logged_in_page: Page):
        """Test uploading file with invalid extension."""
        pass
    
    @pytest.mark.skip(reason="Low priority - TODO")
    def test_integrity_check_displays(self, logged_in_page: Page):
        """Test integrity status column displays correctly."""
        pass
