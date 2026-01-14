"""
Backup and Restore Helper Functions for Tests

Allows tests to save/restore database state programmatically or via UI.
"""

import time
from pathlib import Path
from playwright.sync_api import Page

from website.modules import backup_manager
from tests.frontend.conftest import (
    navigate_to, fill_form_field, check_for_flash_errors,
    wait_for_page_ready, BASE_URL
)


def create_test_backup(name: str, comment: str = "") -> tuple[bool, str]:
    """Create a backup of the current database state.
    
    Args:
        name: Backup name (will be timestamped)
        comment: Optional description
        
    Returns:
        (success, message) tuple
        
    Example:
        create_test_backup("after_manifests_created", "All manifests and modules set up")
    """
    return backup_manager.create_backup(
        name=name,
        comment=comment,
        user="pytest",
        include_config=False,
        include_files=False
    )


def restore_test_backup(backup_filename: str) -> tuple[bool, str]:
    """Restore database from a backup file.
    
    Args:
        backup_filename: Name of the backup file (e.g., "test_backup_20260108_123456.zip")
        
    Returns:
        (success, message) tuple
        
    Example:
        restore_test_backup("after_manifests_created_20260108_080400.zip")
    """
    return backup_manager.restore_backup(
        backup_filename=backup_filename,
        restore_config=False,
        restore_files=False
    )


def list_test_backups() -> list:
    """List all available backup files.
    
    Returns:
        List of backup metadata dictionaries
    """
    return backup_manager.list_backups()


def get_backup_path() -> Path:
    """Get the backup directory path.
    
    Returns:
        Path to backup directory
    """
    return backup_manager.get_backup_dir()


# ============================================================================
# UI-BASED BACKUP/RESTORE HELPERS (for frontend tests)
# ============================================================================

def create_backup_via_ui(page: Page, backup_name: str = None, 
                        include_config: bool = False,
                        include_files: bool = False) -> str:
    """Create a backup via the database tools UI.
    
    Args:
        page: Playwright page (must be logged in)
        backup_name: Name for the backup (auto-generated if None)
        include_config: Include configuration files
        include_files: Include uploaded files
    
    Returns:
        Backup filename (e.g., "my_backup_20260108_104027.zip")
    
    Example:
        filename = create_backup_via_ui(page, "test_backup")
    """
    if backup_name is None:
        backup_name = f"auto_backup_{int(time.time())}"
    
    print(f"\n💾 Creating backup '{backup_name}' via UI...")
    navigate_to(page, "/admin/tracker/database/")
    
    # Fill backup form
    fill_form_field(page, "Database Tools.backup_name", backup_name)
    
    # Set checkboxes if requested
    if include_config:
        page.check('input[name="Database Tools.include_config"]')
    
    if include_files:
        page.check('input[name="Database Tools.include_files"]')
    
    # Submit backup form
    page.click('button[name="Database Tools.btn_create_backup"]')
    
    # Wait for page to reload
    wait_for_page_ready(page, "backup creation")
    
    # Verify no errors
    check_for_flash_errors(page, expected=False)
    
    # Verify backup appears in table and extract filename
    page.wait_for_selector(f'text="{backup_name}"', timeout=5000)
    
    # Find the backup row and extract filename from restore link
    backup_row = page.locator(f'tr:has-text("{backup_name}")').first
    restore_link = backup_row.locator('a[href*="/restore_options/"]').first
    href = restore_link.get_attribute('href')
    backup_filename = href.split('/restore_options/')[-1]
    
    print(f"✓ Backup created: {backup_filename}")
    return backup_filename


def restore_backup_via_ui(page: Page, backup_filename: str):
    """Restore a backup via the database tools UI.
    
    Args:
        page: Playwright page (must be logged in)
        backup_filename: Filename of the backup to restore 
                        (e.g., "my_backup_20260108_104027.zip")
    
    Example:
        restore_backup_via_ui(page, "my_backup_20260108_104027.zip")
    """
    print(f"\n🔄 Restoring backup '{backup_filename}' via UI...")
    
    # Navigate to restore options page
    # Use manual navigation to avoid error checking (restore page has expected warning)
    page.goto(f"{BASE_URL}/admin/tracker/database/restore_options/{backup_filename}")
    page.wait_for_load_state('load')
    
    # Verify we're on restore page
    assert "Restore Options" in page.content(), "Not on restore options page"
    
    # Click restore button
    page.click('button[name="Restore Options.btn_restore"]')
    
    # Wait for page to reload
    wait_for_page_ready(page, "database restore")
    
    # Verify no errors
    check_for_flash_errors(page, expected=False)
    
    print(f"✓ Backup restored: {backup_filename}")


def delete_backup_via_ui(page: Page, backup_filename: str):
    """Delete a backup via the database tools UI.
    
    Args:
        page: Playwright page (must be logged in)
        backup_filename: Filename of the backup to delete
    
    Example:
        delete_backup_via_ui(page, "my_backup_20260108_104027.zip")
    """
    print(f"\n🗑️  Deleting backup '{backup_filename}' via UI...")
    
    navigate_to(page, "/admin/tracker/database/")
    
    # Find the backup row
    backup_row = page.locator(f'a[href*="{backup_filename}"]').first
    assert backup_row.count() > 0, f"Backup {backup_filename} not found"
    
    # Find and click delete button
    delete_link = page.locator(f'a[href*="/delete/{backup_filename}"]').first
    delete_link.click()
    
    # Wait for page to reload
    wait_for_page_ready(page, "backup deletion")
    
    # Verify no errors
    check_for_flash_errors(page, expected=False)
    
    print(f"✓ Backup deleted: {backup_filename}")
