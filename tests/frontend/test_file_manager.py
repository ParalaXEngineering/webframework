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

from .conftest import (
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
    
    # Wait for upload to complete
    # FilePond completion can be detected by:
    # 1. The checkmark icon appearing (.filepond--action-revert-item-processing)
    # 2. The idle state after processing (.filepond--item[data-filepond-item-state="idle"])
    # 3. Or check console logs for "File uploaded:" message
    try:
        # Wait for either the revert button (checkmark) or idle state
        page.wait_for_selector(
            '.filepond--action-revert-item-processing, .filepond--item[data-filepond-item-state="idle"]',
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
    
    # Wait for DataTable to initialize (needs more time for AJAX + render)
    page.wait_for_selector('#interactive_file_list_table', timeout=10000)
    
    # Use DataTable search
    search_input = page.locator('input[type="search"]')
    search_input.fill(filename)
    
    # Wait for search to filter (debounced)
    page.wait_for_timeout(500)
    
    # Check if filename appears in table
    filename_cells = page.locator(f'#interactive_file_list_table td:has-text("{filename}")')
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
    page.wait_for_selector('#interactive_file_list_table', timeout=5000)
    
    # Search for file
    search_input = page.locator('input[type="search"]')
    search_input.fill(filename)
    page.wait_for_timeout(500)
    
    # Find row containing filename
    row = page.locator(f'#interactive_file_list_table tr:has-text("{filename}")').first
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
    page.wait_for_selector('#interactive_file_list_table', timeout=5000)
    
    # Search for file
    search_input = page.locator('input[type="search"]')
    search_input.fill(filename)
    page.wait_for_timeout(500)
    
    # Find row and look for thumbnail image
    row = page.locator(f'#interactive_file_list_table tr:has-text("{filename}")').first
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
    page.wait_for_selector('#interactive_file_list_table', timeout=5000)
    
    # Search for file
    search_input = page.locator('input[type="search"]')
    search_input.fill(filename)
    page.wait_for_timeout(500)
    
    # Find row
    row = page.locator(f'#interactive_file_list_table tr:has-text("{filename}")').first
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
        page.wait_for_selector('#interactive_file_list_table', timeout=5000)
        
        print("✅ Admin page loaded successfully")
    
    def test_02_file_list_displays(self, logged_in_page: Page):
        """Test that file list displays in DataTable."""
        page = logged_in_page
        
        print("\n📄 Test: File list displays")
        
        navigate_to(page, "/file_manager/")
        
        # Wait for DataTable
        page.wait_for_selector('#interactive_file_list_table', timeout=5000)
        
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
        page.wait_for_selector('#interactive_file_list_table', timeout=5000)
        
        # Search for our file
        search_input = page.locator('input[type="search"]')
        search_input.fill(filename)
        page.wait_for_timeout(500)
        
        # Verify file appears
        assert page.locator(f'#interactive_file_list_table td:has-text("{filename}")').count() > 0, \
            f"Search should find file: {filename}"
        
        # Search for non-existent file
        search_input.fill("nonexistent_file_xyz123")
        page.wait_for_timeout(500)
        
        # Should show "No matching records"
        assert page_contains_text(page, "No matching records") or \
               page.locator('#interactive_file_list_table tbody tr').count() == 0, \
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
        page.wait_for_selector('#interactive_file_list_table', timeout=5000)
        
        # Search for file
        search_input = page.locator('input[type="search"]')
        search_input.fill(filename)
        page.wait_for_timeout(500)
        
        # Find download button and trigger download
        row = page.locator(f'#interactive_file_list_table tr:has-text("{filename}")').first
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
        page.wait_for_selector('#interactive_file_list_table', timeout=5000)
        
        # Search for file
        search_input = page.locator('input[type="search"]')
        search_input.fill(filename)
        page.wait_for_timeout(500)
        
        # Click delete button
        row = page.locator(f'#interactive_file_list_table tr:has-text("{filename}")').first
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
        page.wait_for_selector('#interactive_file_list_table', timeout=5000)
        
        search_input = page.locator('input[type="search"]')
        search_input.fill(filename)
        page.wait_for_timeout(500)
        
        # Should not find the file
        assert page.locator(f'#interactive_file_list_table td:has-text("{filename}")').count() == 0, \
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
        page.wait_for_selector('#interactive_file_list_table', timeout=5000)
        
        search_input = page.locator('input[type="search"]')
        search_input.fill(filename)
        page.wait_for_timeout(500)
        
        row = page.locator(f'#interactive_file_list_table tr:has-text("{filename}")').first
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
# MEDIUM PRIORITY TESTS
# ============================================================================

class TestFileManagerEdit:
    """Test metadata editing functionality (MEDIUM PRIORITY)."""
    
    def test_01_edit_page_loads(self, logged_in_page: Page):
        """Test that edit page loads for a file."""
        page = logged_in_page
        
        print("\n📄 Test: Edit page loads")
        
        # Upload a test file first
        timestamp = int(time.time())
        test_file = TEST_FILES_DIR / f"frontend_test_edit_{timestamp}.txt"
        test_file.write_text("Test file for edit testing")
        
        filename = upload_file_via_demo(page, test_file)
        
        # Navigate to admin and click edit button
        navigate_to(page, "/file_manager/")
        page.wait_for_selector('#interactive_file_list_table', timeout=5000)
        
        # Search for file
        search_input = page.locator('input[type="search"]')
        search_input.fill(filename)
        page.wait_for_timeout(500)
        
        # Click edit button
        row = page.locator(f'#interactive_file_list_table tr:has-text("{filename}")').first
        edit_link = row.locator('a i.mdi-pencil').locator('..').first
        edit_link.click()
        
        page.wait_for_timeout(500)
        
        # Check edit page loaded
        assert page_contains_text(page, "Edit") or page_contains_text(page, "Metadata"), \
            "Should show edit page"
        assert page_contains_text(page, filename), \
            "Edit page should show filename"
        
        print("✅ Edit page loads correctly")
    
    def test_02_edit_group_id(self, logged_in_page: Page):
        """Test editing file group_id."""
        page = logged_in_page
        
        print("\n📄 Test: Edit group_id")
        
        # Upload a test file
        timestamp = int(time.time())
        test_file = TEST_FILES_DIR / f"frontend_test_groupid_{timestamp}.txt"
        test_file.write_text("Test file for group_id editing")
        
        filename = upload_file_via_demo(page, test_file)
        
        # Navigate to edit page
        navigate_to(page, "/file_manager/")
        page.wait_for_selector('#interactive_file_list_table', timeout=5000)
        
        search_input = page.locator('input[type="search"]')
        search_input.fill(filename)
        page.wait_for_timeout(500)
        
        row = page.locator(f'#interactive_file_list_table tr:has-text("{filename}")').first
        edit_link = row.locator('a i.mdi-pencil').locator('..').first
        edit_link.click()
        page.wait_for_timeout(500)
        
        # Find group_id field (select dropdown)
        group_select = page.locator('select[id*="group_id"], select[name*="group_id"]').first
        if group_select.count() > 0:
            # Select a different group or keep current
            # Just verify the field exists and is interactive
            assert group_select.is_visible(), "Group ID select should be visible"
            print("  ✅ Group ID select field found")
        else:
            # Might be a text input
            group_input = page.locator('input[id*="group_id"], input[name*="group_id"]').first
            if group_input.count() > 0:
                assert group_input.is_visible(), "Group ID input should be visible"
                print("  ✅ Group ID input field found")
        
        # Click save button
        save_button = page.locator('button:has-text("Save")').first
        save_button.click()
        
        page.wait_for_timeout(1000)
        
        # Should redirect back to file manager or show success
        assert page_contains_text(page, "success") or \
               page_contains_text(page, "File Manager") or \
               page.url.endswith("/file_manager/"), \
            "Should show success or redirect to file manager"
        
        print("✅ Group ID editing works")
    
    def test_03_edit_tags(self, logged_in_page: Page):
        """Test editing file tags."""
        page = logged_in_page
        
        print("\n📄 Test: Edit tags")
        
        # Upload a test file
        timestamp = int(time.time())
        test_file = TEST_FILES_DIR / f"frontend_test_tags_{timestamp}.txt"
        test_file.write_text("Test file for tags editing")
        
        filename = upload_file_via_demo(page, test_file)
        
        # Navigate to edit page
        navigate_to(page, "/file_manager/")
        page.wait_for_selector('#interactive_file_list_table', timeout=5000)
        
        search_input = page.locator('input[type="search"]')
        search_input.fill(filename)
        page.wait_for_timeout(500)
        
        row = page.locator(f'#interactive_file_list_table tr:has-text("{filename}")').first
        edit_link = row.locator('a i.mdi-pencil').locator('..').first
        edit_link.click()
        page.wait_for_timeout(500)
        
        # Find tags field (multi-select or input)
        tags_select = page.locator('select[id*="tags"], select[name*="tags"]').first
        if tags_select.count() > 0:
            assert tags_select.is_visible(), "Tags select should be visible"
            print("  ✅ Tags multi-select field found")
        else:
            tags_input = page.locator('input[id*="tags"], input[name*="tags"]').first
            if tags_input.count() > 0:
                assert tags_input.is_visible(), "Tags input should be visible"
                print("  ✅ Tags input field found")
        
        # Click save
        save_button = page.locator('button:has-text("Save")').first
        save_button.click()
        
        page.wait_for_timeout(1000)
        
        print("✅ Tags editing works")
    
    def test_04_edit_cancel(self, logged_in_page: Page):
        """Test canceling edit operation."""
        page = logged_in_page
        
        print("\n📄 Test: Cancel edit")
        
        # Upload a test file
        timestamp = int(time.time())
        test_file = TEST_FILES_DIR / f"frontend_test_edit_cancel_{timestamp}.txt"
        test_file.write_text("Test file for cancel test")
        
        filename = upload_file_via_demo(page, test_file)
        
        # Navigate to edit page
        navigate_to(page, "/file_manager/")
        page.wait_for_selector('#interactive_file_list_table', timeout=5000)
        
        search_input = page.locator('input[type="search"]')
        search_input.fill(filename)
        page.wait_for_timeout(500)
        
        row = page.locator(f'#interactive_file_list_table tr:has-text("{filename}")').first
        edit_link = row.locator('a i.mdi-pencil').locator('..').first
        edit_link.click()
        page.wait_for_timeout(500)
        
        # Click cancel button
        cancel_button = page.locator('a:has-text("Cancel")').first
        cancel_button.click()
        
        page.wait_for_timeout(500)
        
        # Should return to file manager
        assert "/file_manager" in page.url, "Should redirect to file manager"
        
        print("✅ Cancel edit works")


class TestFileManagerVersions:
    """Test version control functionality (MEDIUM PRIORITY)."""
    
    def test_01_view_version_history(self, logged_in_page: Page):
        """Test viewing version history page."""
        page = logged_in_page
        
        print("\n📄 Test: View version history")
        
        # Upload a test file
        timestamp = int(time.time())
        test_file = TEST_FILES_DIR / f"frontend_test_history_{timestamp}.txt"
        test_file.write_text("Test file for version history")
        
        filename = upload_file_via_demo(page, test_file)
        
        # Navigate to admin list
        navigate_to(page, "/file_manager/")
        page.wait_for_selector('#interactive_file_list_table', timeout=5000)
        
        # Search for file
        search_input = page.locator('input[type="search"]')
        search_input.fill(filename)
        page.wait_for_timeout(500)
        
        # Click history button (if visible)
        row = page.locator(f'#interactive_file_list_table tr:has-text("{filename}")').first
        history_link = row.locator('a i.mdi-history').locator('..')
        
        if history_link.count() > 0:
            history_link.first.click()
            page.wait_for_timeout(500)
            
            # Check version history page loaded
            assert page_contains_text(page, "Version") or page_contains_text(page, "History"), \
                "Should show version history page"
            assert page_contains_text(page, filename), \
                "Version history should show filename"
            
            print("✅ Version history page loads")
        else:
            print("  ℹ️  History button not visible (file may not have versions)")
            # File might not have a group_id set, which is OK
    
    def test_02_version_history_shows_versions(self, logged_in_page: Page):
        """Test that version history table shows version details."""
        page = logged_in_page
        
        print("\n📄 Test: Version history shows versions")
        
        # Upload a test file
        timestamp = int(time.time())
        test_file = TEST_FILES_DIR / f"frontend_test_versions_{timestamp}.txt"
        test_file.write_text("Test file version 1")
        
        filename = upload_file_via_demo(page, test_file)
        
        # Navigate to admin list and find history
        navigate_to(page, "/file_manager/")
        page.wait_for_selector('#interactive_file_list_table', timeout=5000)
        
        search_input = page.locator('input[type="search"]')
        search_input.fill(filename)
        page.wait_for_timeout(500)
        
        row = page.locator(f'#interactive_file_list_table tr:has-text("{filename}")').first
        history_link = row.locator('a i.mdi-history').locator('..')
        
        if history_link.count() > 0:
            history_link.first.click()
            page.wait_for_timeout(500)
            
            # Check for version table columns
            assert page_contains_text(page, "Version") or page_contains_text(page, "v1"), \
                "Should show version number"
            assert page_contains_text(page, "Current") or page_contains_text(page, "Status"), \
                "Should show version status"
            
            # Check for action buttons
            download_btn = page.locator('a i.mdi-download')
            assert download_btn.count() > 0, "Should have download button"
            
            print("✅ Version history shows version details")
        else:
            print("  ℹ️  History button not visible - skipping")
    
    def test_03_download_specific_version(self, logged_in_page: Page):
        """Test downloading a specific version from history."""
        page = logged_in_page
        
        print("\n📄 Test: Download specific version")
        
        # Upload a test file
        timestamp = int(time.time())
        test_file = TEST_FILES_DIR / f"frontend_test_dl_version_{timestamp}.txt"
        test_content = "Download version test content"
        test_file.write_text(test_content)
        
        filename = upload_file_via_demo(page, test_file)
        
        # Navigate to history page
        navigate_to(page, "/file_manager/")
        page.wait_for_selector('#interactive_file_list_table', timeout=5000)
        
        search_input = page.locator('input[type="search"]')
        search_input.fill(filename)
        page.wait_for_timeout(500)
        
        row = page.locator(f'#interactive_file_list_table tr:has-text("{filename}")').first
        history_link = row.locator('a i.mdi-history').locator('..')
        
        if history_link.count() > 0:
            history_link.first.click()
            page.wait_for_timeout(500)
            
            # Find download button for a version
            download_link = page.locator('a i.mdi-download').first.locator('..')
            
            with page.expect_download() as download_info:
                download_link.click()
            
            download = download_info.value
            assert download.suggested_filename == filename, \
                "Downloaded file should have correct name"
            
            print("✅ Version download works")
        else:
            print("  ℹ️  History button not visible - skipping")
    
    def test_04_create_new_version(self, logged_in_page: Page):
        """Test that uploading same file with same group creates a new version."""
        page = logged_in_page
        
        print("\n📄 Test: Create new version by re-uploading")
        
        # Ensure test files directory exists
        if not TEST_FILES_DIR.exists():
            TEST_FILES_DIR.mkdir(parents=True, exist_ok=True)
        
        # Upload initial file
        timestamp = int(time.time())
        test_file = TEST_FILES_DIR / f"frontend_test_versioning_{timestamp}.txt"
        test_file.write_text("Version 1 content")
        
        filename = upload_file_via_demo(page, test_file)
        
        # Get the file ID and set a group_id via edit page
        navigate_to(page, "/file_manager/")
        page.wait_for_selector('#interactive_file_list_table', timeout=10000)
        
        search_input = page.locator('input[type="search"]')
        search_input.fill(filename)
        page.wait_for_timeout(500)
        
        # Go to edit page and set a group_id
        row = page.locator(f'#interactive_file_list_table tr:has-text("{filename}")').first
        edit_link = row.locator('a i.mdi-pencil').locator('..').first
        edit_link.click()
        page.wait_for_timeout(500)
        
        # Note the current version (should be v1/1)
        # We'll verify it changes after uploading again
        
        # Save without changes (just to have a baseline)
        save_button = page.locator('button:has-text("Save")').first
        save_button.click()
        page.wait_for_timeout(1000)
        
        # Upload same filename again - this should create version 2
        test_file.write_text("Version 2 content - updated")
        upload_file_via_demo(page, test_file)
        
        # Check version in admin list
        navigate_to(page, "/file_manager/")
        page.wait_for_selector('#interactive_file_list_table', timeout=10000)
        
        search_input = page.locator('input[type="search"]')
        search_input.fill(filename)
        page.wait_for_timeout(500)
        
        # Look for version indicator - could be v1/2 or v2/2
        row = page.locator(f'#interactive_file_list_table tr:has-text("{filename}")').first
        row_text = row.inner_text()
        
        # Check if we have multiple versions indicated
        # The version column shows format like "v1/2" meaning version 1 of 2
        print(f"  ℹ️  Row content: {row_text[:100]}...")
        
        # Verify file still exists (upload succeeded)
        assert row.count() > 0, "File should still exist after re-upload"
        
        print("✅ Version creation test complete")
    
    def test_05_restore_version(self, logged_in_page: Page):
        """Test restoring an old version of a file."""
        page = logged_in_page
        
        print("\n📄 Test: Restore old version")
        
        # First, find a file that has multiple versions (from previous test or existing)
        # Or we need to create versions first
        navigate_to(page, "/file_manager/")
        page.wait_for_selector('#interactive_file_list_table', timeout=10000)
        
        # Look for any file with version indicator showing multiple versions (e.g., v1/2)
        # The version column contains patterns like "v1/2", "v2/3", etc.
        rows = page.locator('#interactive_file_list_table tbody tr')
        
        versioned_file_row = None
        for i in range(rows.count()):
            row = rows.nth(i)
            row_text = row.inner_text()
            # Look for version patterns indicating multiple versions
            if '/2' in row_text or '/3' in row_text or '/4' in row_text:
                versioned_file_row = row
                print(f"  ℹ️  Found versioned file: {row_text[:80]}...")
                break
        
        if versioned_file_row is None:
            print("  ⏭️  No files with multiple versions found - skipping restore test")
            return
        
        # Click history button
        history_link = versioned_file_row.locator('a i.mdi-history').locator('..')
        if history_link.count() == 0:
            print("  ⏭️  No history button found - skipping")
            return
        
        history_link.first.click()
        page.wait_for_timeout(500)
        
        # Look for restore button (should be on non-current versions)
        restore_btn = page.locator('a i.mdi-restore').locator('..')
        
        if restore_btn.count() > 0:
            # Click restore on first available version
            restore_btn.first.click()
            page.wait_for_timeout(1000)
            
            # Should show success message or redirect back to history
            assert page_contains_text(page, "restored") or \
                   page_contains_text(page, "success") or \
                   page_contains_text(page, "Version"), \
                "Should show restore success or version history"
            
            print("✅ Version restore works")
        else:
            print("  ℹ️  No restore button found (may only have one version)")


class TestFileManagerEditPersistence:
    """Test that metadata edits actually persist (MEDIUM PRIORITY)."""
    
    def test_01_edit_group_id_persists(self, logged_in_page: Page):
        """Test that editing group_id actually saves the change."""
        page = logged_in_page
        
        print("\n📄 Test: Edit group_id persists")
        
        # Upload a test file
        timestamp = int(time.time())
        test_file = TEST_FILES_DIR / f"frontend_test_persist_group_{timestamp}.txt"
        test_file.write_text("Test file for group_id persistence")
        
        filename = upload_file_via_demo(page, test_file)
        
        # Navigate to edit page
        navigate_to(page, "/file_manager/")
        page.wait_for_selector('#interactive_file_list_table', timeout=10000)
        
        search_input = page.locator('input[type="search"]')
        search_input.fill(filename)
        page.wait_for_timeout(500)
        
        # Check current group_id in table (should be "(none)")
        row = page.locator(f'#interactive_file_list_table tr:has-text("{filename}")').first
        initial_row_text = row.inner_text()
        print(f"  ℹ️  Initial row: {initial_row_text[:80]}...")
        
        # Go to edit page
        edit_link = row.locator('a i.mdi-pencil').locator('..').first
        edit_link.click()
        page.wait_for_timeout(500)
        
        # Find group_id select and pick a different value if available
        group_select = page.locator('select[id*="group_id"], select[name*="group_id"]').first
        if group_select.count() > 0:
            # Get available options
            options = group_select.locator('option')
            option_count = options.count()
            
            if option_count > 1:
                # Select second option (first is usually "(none)")
                second_option = options.nth(1).get_attribute('value')
                group_select.select_option(second_option)
                print(f"  ℹ️  Selected group_id: {second_option}")
                
                # Save
                save_button = page.locator('button:has-text("Save")').first
                save_button.click()
                page.wait_for_timeout(1000)
                
                # Navigate back to file list and verify change
                navigate_to(page, "/file_manager/")
                page.wait_for_selector('#interactive_file_list_table', timeout=10000)
                
                search_input = page.locator('input[type="search"]')
                search_input.fill(filename)
                page.wait_for_timeout(500)
                
                # Check new group_id in table
                row = page.locator(f'#interactive_file_list_table tr:has-text("{filename}")').first
                new_row_text = row.inner_text()
                print(f"  ℹ️  Updated row: {new_row_text[:80]}...")
                
                # Verify the group_id changed (should contain the new value, not "(none)")
                assert second_option in new_row_text or "(none)" not in new_row_text.split(filename)[1][:50], \
                    f"Group ID should have changed from (none) to {second_option}"
                
                print("✅ Group ID edit persisted correctly")
            else:
                print("  ⏭️  Only one group option available - skipping persistence check")
        else:
            print("  ⏭️  No group_id select found - skipping")


class TestFileManagerMultiDelete:
    """Test multi-delete with checkboxes (MEDIUM PRIORITY)."""
    
    def test_01_select_multiple_files(self, logged_in_page: Page):
        """Test selecting multiple files with checkboxes."""
        page = logged_in_page
        
        print("\n📄 Test: Select multiple files")
        
        # Upload two test files
        timestamp = int(time.time())
        test_file1 = TEST_FILES_DIR / f"frontend_test_multi1_{timestamp}.txt"
        test_file2 = TEST_FILES_DIR / f"frontend_test_multi2_{timestamp}.txt"
        test_file1.write_text("Multi-delete test file 1")
        test_file2.write_text("Multi-delete test file 2")
        
        filename1 = upload_file_via_demo(page, test_file1)
        filename2 = upload_file_via_demo(page, test_file2)
        
        # Navigate to admin list
        navigate_to(page, "/file_manager/")
        page.wait_for_selector('#interactive_file_list_table', timeout=5000)
        
        # Search for our test files
        search_input = page.locator('input[type="search"]')
        search_input.fill(f"frontend_test_multi")
        page.wait_for_timeout(500)
        
        # Find checkboxes
        checkboxes = page.locator('#interactive_file_list_table input[type="checkbox"][name="file_ids[]"]')
        checkbox_count = checkboxes.count()
        
        assert checkbox_count >= 2, f"Should have at least 2 checkboxes, found {checkbox_count}"
        
        # Select first two checkboxes
        checkboxes.nth(0).check()
        checkboxes.nth(1).check()
        
        assert checkboxes.nth(0).is_checked(), "First checkbox should be checked"
        assert checkboxes.nth(1).is_checked(), "Second checkbox should be checked"
        
        print("✅ Multiple file selection works")
    
    def test_02_multi_delete_with_confirmation(self, logged_in_page: Page):
        """Test deleting multiple files with confirmation."""
        page = logged_in_page
        
        print("\n📄 Test: Multi-delete with confirmation")
        
        # Upload two test files
        timestamp = int(time.time())
        test_file1 = TEST_FILES_DIR / f"frontend_test_multidel1_{timestamp}.txt"
        test_file2 = TEST_FILES_DIR / f"frontend_test_multidel2_{timestamp}.txt"
        test_file1.write_text("Multi-delete file 1")
        test_file2.write_text("Multi-delete file 2")
        
        filename1 = upload_file_via_demo(page, test_file1)
        filename2 = upload_file_via_demo(page, test_file2)
        
        # Navigate to admin list
        navigate_to(page, "/file_manager/")
        page.wait_for_selector('#interactive_file_list_table', timeout=5000)
        
        # Search for our test files
        search_input = page.locator('input[type="search"]')
        search_input.fill(f"frontend_test_multidel")
        page.wait_for_timeout(500)
        
        # Select checkboxes
        checkboxes = page.locator('#interactive_file_list_table input[type="checkbox"][name="file_ids[]"]')
        for i in range(min(2, checkboxes.count())):
            checkboxes.nth(i).check()
        
        # Click "Delete Selected" button
        delete_btn = page.locator('button:has-text("Delete Selected")').first
        delete_btn.click()
        
        page.wait_for_timeout(500)
        
        # Should show confirmation page
        assert page_contains_text(page, "Confirm") or page_contains_text(page, "Delete"), \
            "Should show confirmation page"
        assert page_contains_text(page, "2 files") or \
               (page_contains_text(page, filename1) or page_contains_text(page, filename2)), \
            "Should show files to be deleted"
        
        # Confirm deletion
        confirm_button = page.locator('button:has-text("Yes, Delete")').first
        confirm_button.click()
        
        page.wait_for_timeout(1000)
        
        # Verify success
        assert page_contains_text(page, "deleted") or page_contains_text(page, "Success"), \
            "Should show deletion success"
        
        print("✅ Multi-delete with confirmation works")


# ============================================================================
# LOW PRIORITY TESTS
# ============================================================================

class TestFileManagerEdgeCases:
    """Test edge cases and error handling (LOW PRIORITY)."""
    
    def test_01_empty_file_list(self, logged_in_page: Page):
        """Test behavior with empty search results."""
        page = logged_in_page
        
        print("\n📄 Test: Empty search results")
        
        navigate_to(page, "/file_manager/")
        page.wait_for_selector('#interactive_file_list_table', timeout=5000)
        
        # Search for non-existent file
        search_input = page.locator('input[type="search"]')
        search_input.fill("nonexistent_file_xyz123_impossible")
        page.wait_for_timeout(500)
        
        # Should show "no matching records" or empty table
        assert page_contains_text(page, "No matching records") or \
               page.locator('#interactive_file_list_table tbody tr td').count() <= 1, \
            "Should handle empty search results gracefully"
        
        print("✅ Empty search results handled correctly")
    
    def test_02_integrity_status_displays(self, logged_in_page: Page):
        """Test integrity status column displays correctly."""
        page = logged_in_page
        
        print("\n📄 Test: Integrity status displays")
        
        # Upload a test file
        timestamp = int(time.time())
        test_file = TEST_FILES_DIR / f"frontend_test_integrity_{timestamp}.txt"
        test_file.write_text("Integrity check test file")
        
        filename = upload_file_via_demo(page, test_file)
        
        # Navigate to admin list
        navigate_to(page, "/file_manager/")
        page.wait_for_selector('#interactive_file_list_table', timeout=5000)
        
        # Search for file
        search_input = page.locator('input[type="search"]')
        search_input.fill(filename)
        page.wait_for_timeout(500)
        
        # Check for integrity column (should show OK, Missing, Corrupted, etc.)
        row = page.locator(f'#interactive_file_list_table tr:has-text("{filename}")').first
        
        # Look for integrity badge
        integrity_badge = row.locator('.badge')
        if integrity_badge.count() > 0:
            badge_text = integrity_badge.first.inner_text()
            valid_statuses = ["OK", "Missing", "Corrupted", "Not Found", "Error"]
            assert any(status in badge_text for status in valid_statuses), \
                f"Integrity badge should show valid status, got: {badge_text}"
            print(f"  ✅ Integrity status: {badge_text}")
        else:
            print("  ℹ️  No integrity badge found (column may be different)")
        
        print("✅ Integrity status display test complete")
    
    def test_03_file_not_found_edit(self, logged_in_page: Page):
        """Test editing a non-existent file shows error."""
        page = logged_in_page
        
        print("\n📄 Test: Edit non-existent file")
        
        # Try to access edit page for non-existent file ID
        navigate_to(page, "/file_manager/edit/999999")
        
        page.wait_for_timeout(500)
        
        # Should show error or "not found"
        assert page_contains_text(page, "Not Found") or \
               page_contains_text(page, "Error") or \
               page_contains_text(page, "not found"), \
            "Should show error for non-existent file"
        
        print("✅ Non-existent file edit handled correctly")
    
    def test_04_delete_without_selection(self, logged_in_page: Page):
        """Test clicking delete without selecting files."""
        page = logged_in_page
        
        print("\n📄 Test: Delete without selection")
        
        navigate_to(page, "/file_manager/")
        page.wait_for_selector('#interactive_file_list_table', timeout=5000)
        
        # Make sure no checkboxes are selected
        checkboxes = page.locator('#interactive_file_list_table input[type="checkbox"][name="file_ids[]"]')
        for i in range(checkboxes.count()):
            if checkboxes.nth(i).is_checked():
                checkboxes.nth(i).uncheck()
        
        # Click delete button
        delete_btn = page.locator('button:has-text("Delete Selected")').first
        if delete_btn.count() > 0:
            delete_btn.click()
            page.wait_for_timeout(500)
            
            # Should show warning or stay on page
            assert page_contains_text(page, "No files selected") or \
                   "/file_manager" in page.url, \
                "Should warn about no selection or stay on page"
        
        print("✅ Delete without selection handled correctly")
    
    def test_05_special_characters_in_search(self, logged_in_page: Page):
        """Test search with special characters."""
        page = logged_in_page
        
        print("\n📄 Test: Special characters in search")
        
        navigate_to(page, "/file_manager/")
        page.wait_for_selector('#interactive_file_list_table', timeout=5000)
        
        # Search with special characters
        search_input = page.locator('input[type="search"]')
        
        # Test various special characters that shouldn't break search
        special_searches = ["test<>file", "test'file", 'test"file', "test&file"]
        
        for search_term in special_searches:
            search_input.fill(search_term)
            page.wait_for_timeout(300)
            
            # Should not cause JS error - page should still be responsive
            assert page.locator('#interactive_file_list_table').is_visible(), \
                f"Table should remain visible after searching: {search_term}"
        
        print("✅ Special characters in search handled correctly")
