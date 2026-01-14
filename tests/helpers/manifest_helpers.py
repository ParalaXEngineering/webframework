"""
Manifest Helper Functions

Extracted from test_sea_system_data.py (source of truth).
All functions use conftest.py helpers for navigation and error checking.
"""

from playwright.sync_api import Page
from submodules.tracker.src.kinds import Atomic

from tests.frontend.conftest import (
    navigate_to, fill_form_field, select_form_option,
    extract_id_from_url, check_for_flash_errors
)


def create_manifest(page: Page, name: str) -> int:
    """Create a new manifest and return its ID.
    
    Args:
        page: Playwright page (must be logged in)
        name: Name for the new manifest
    
    Returns:
        Manifest ID (extracted from URL after creation)
    
    Example:
        manifest_id = create_manifest(page, "MyManifest")
    """
    print(f"\nCreating manifest: {name}")
    
    navigate_to(page, "/admin/manifests/create")
    
    fill_form_field(page, "manifest_name", name)
    
    create_btn = page.locator('button:has-text("Create Manifest")')
    if create_btn.count() == 0:
        buttons = page.locator('button').all()
        button_texts = [btn.inner_text() for btn in buttons]
        raise AssertionError(
            f"'Create Manifest' button not found!\n"
            f"Available buttons: {button_texts}\n"
            f"Current URL: {page.url}"
        )
    
    create_btn.first.click()
    page.wait_for_timeout(500)
    check_for_flash_errors(page)
    
    current_url = page.url
    if '/edit/' not in current_url:
        error_msg = page.locator('.alert-danger, .alert-warning').first
        if error_msg.count() > 0:
            error_text = error_msg.inner_text()
            raise AssertionError(
                f"Manifest creation failed!\n"
                f"Still on: {current_url}\n"
                f"Error message: {error_text}"
            )
        else:
            raise AssertionError(
                f"Manifest creation failed - no redirect to edit page!\n"
                f"Current URL: {current_url}"
            )
    
    manifest_id = extract_id_from_url(page)
    print(f"Manifest created with ID: {manifest_id}")
    return manifest_id


def create_linkable_manifest(page: Page, name: str, in_id_fields: list[str], 
                            is_trackable: bool = True) -> int:
    """Create a linkable manifest with IN_ID fields.
    
    Args:
        page: Playwright page
        name: Manifest name
        in_id_fields: List of field names to mark as IN_ID (e.g., ["PN", "SN"])
        is_trackable: Whether to set IS_TRACKABLE flag (default True)
    
    Returns:
        Manifest ID
    
    Example:
        manifest_id = create_linkable_manifest(page, "Board", ["PN", "SN"])
    """
    from tests.helpers.attribute_helpers import add_atomic_attribute
    
    print(f"\nCreating linkable manifest: {name} with IN_ID fields: {in_id_fields}")
    
    # Create base manifest
    manifest_id = create_manifest(page, name)
    
    # Add IN_ID fields as STRING atomics
    for field_name in in_id_fields:
        add_atomic_attribute(page, manifest_id, field_name, Atomic.STRING.value)
    
    # Set IN_ID flag on each field
    for field_name in in_id_fields:
        navigate_to(page, f"/admin/manifests/edit_attribute/{manifest_id}/{field_name}")
        page.wait_for_timeout(200)
        inid_checkbox = page.locator('input[name="Edit Attribute.flag_inid"]')
        if inid_checkbox.count() > 0:
            inid_checkbox.check()
            page.click('button[name="Edit Attribute.btn_save"]')
            page.wait_for_timeout(200)
            check_for_flash_errors(page)
    
    # Set IS_LINKABLE flag on manifest (CRITICAL!)
    navigate_to(page, f"/admin/manifests/edit/{manifest_id}")
    page.wait_for_timeout(200)
    linkable_checkbox = page.locator('input[type="checkbox"][name*="flag_islinkable"]')
    if linkable_checkbox.count() > 0:
        linkable_checkbox.first.check()
        page.click('button[name="Edit Manifest.btn_save_name"]')
        page.wait_for_timeout(200)
        check_for_flash_errors(page)
    
    # Set IS_TRACKABLE flag if requested
    if is_trackable:
        navigate_to(page, f"/admin/manifests/edit/{manifest_id}")
        page.wait_for_timeout(200)
        trackable_checkbox = page.locator('input[type="checkbox"][name*="flag_istrackable"]')
        if trackable_checkbox.count() > 0:
            trackable_checkbox.first.check()
            page.click('button[name="Edit Manifest.btn_save_name"]')
            page.wait_for_timeout(200)
            check_for_flash_errors(page)
    
    print(f"Linkable manifest created: {name} (ID: {manifest_id})")
    return manifest_id


def create_non_linkable_manifest(page: Page, name: str, in_id_fields: list[str]) -> int:
    """Create a non-linkable manifest (for embedded items/predefined lists).
    
    Non-linkable manifests cannot have trackers created directly - they are
    embedded in other trackers as ManifestKind attributes.
    
    Args:
        page: Playwright page
        name: Manifest name
        in_id_fields: List of field names to mark as IN_ID
    
    Returns:
        Manifest ID
    
    Example:
        manifest_id = create_non_linkable_manifest(page, "EmbeddedItem", ["Item"])
    """
    print(f"\nCreating non-linkable manifest: {name} with IN_ID fields: {in_id_fields}")
    
    navigate_to(page, "/admin/manifests/create")
    page.wait_for_timeout(200)
    
    fill_form_field(page, "manifest_name", name)
    
    # Uncheck IS_LINKABLE flag
    linkable_checkbox = page.locator('input[type="checkbox"][name*="flag_is_linkable"]')
    if linkable_checkbox.count() > 0:
        linkable_checkbox.first.uncheck()
    
    # Set IN_ID fields
    for i, field in enumerate(in_id_fields):
        field_input = page.locator(f'input[name="Create Manifest.in_id_fields_{i}"]')
        if field_input.count() > 0:
            field_input.fill(field)
    
    save_btn = page.locator('button:has-text("Create Manifest")')
    save_btn.click()
    page.wait_for_timeout(500)
    check_for_flash_errors(page)
    
    manifest_id = extract_id_from_url(page)
    print(f"Non-linkable manifest created with ID: {manifest_id}")
    return manifest_id


def delete_manifest(page: Page, manifest_id: int):
    """Delete a manifest.
    
    Args:
        page: Playwright page
        manifest_id: ID of the manifest to delete
    
    Example:
        delete_manifest(page, 123)
    """
    from tests.frontend.conftest import BASE_URL
    print(f"Deleting manifest ID: {manifest_id}")
    
    # Navigate directly using page.goto to avoid navigate_to's auto-flash check
    # (The delete confirmation page shows a warning which is expected)
    page.goto(f"{BASE_URL}/admin/manifests/delete/{manifest_id}")
    page.wait_for_load_state("domcontentloaded")
    
    # Click confirm/delete button
    confirm_btn = page.locator('button:has-text("Delete"), button[name*="btn_delete"]')
    if confirm_btn.count() > 0:
        confirm_btn.first.click()
        page.wait_for_load_state("domcontentloaded")
        # Only check for errors after the actual delete action
        check_for_flash_errors(page)
    else:
        raise AssertionError(f"Delete confirmation button not found for manifest {manifest_id}")
    
    print(f"Manifest deleted")


def enable_manifest_flag(page: Page, manifest_id: int, flag_name: str):
    """Enable a manifest flag (ALLOWS_SIBLINGS, ALLOWS_CASCADING, etc.).
    
    Args:
        page: Playwright page
        manifest_id: ID of the manifest
        flag_name: Flag name without prefix (e.g., "siblings", "cascading")
    
    Example:
        enable_manifest_flag(page, manifest_id, "siblings")
    """
    print(f"  Enabling flag: {flag_name} on manifest {manifest_id}")
    
    navigate_to(page, f"/admin/manifests/edit/{manifest_id}")
    page.wait_for_timeout(200)
    
    # Try common flag patterns
    flag_patterns = [
        f'input[type="checkbox"][name*="flag_{flag_name}"]',
        f'input[type="checkbox"][name*="{flag_name}"]',
    ]
    
    for pattern in flag_patterns:
        checkbox = page.locator(pattern)
        if checkbox.count() > 0:
            checkbox.first.check()
            page.click('button[name="Edit Manifest.btn_save_name"]')
            page.wait_for_timeout(200)
            check_for_flash_errors(page)
            print(f"  Flag {flag_name} enabled")
            return
    
    raise AssertionError(f"Could not find flag checkbox for '{flag_name}'")


def enable_siblings_on_manifest(page: Page, manifest_id: int):
    """Enable ALLOWS_SIBLINGS flag on manifest.
    
    Convenience wrapper for enable_manifest_flag.
    """
    enable_manifest_flag(page, manifest_id, "allows_siblings")


def enable_cascading_on_manifest(page: Page, manifest_id: int):
    """Enable ALLOWS_CASCADING flag on manifest.
    
    Convenience wrapper for enable_manifest_flag.
    """
    enable_manifest_flag(page, manifest_id, "allows_cascading")
