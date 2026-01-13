"""
Attribute Helper Functions

Extracted from test_sea_system_data.py (source of truth).
All functions use conftest.py helpers for navigation and error checking.
"""

from playwright.sync_api import Page
from submodules.tracker.src.kinds import Atomic

from tests.frontend.conftest import (
    navigate_to, fill_form_field, select_form_option,
    check_for_flash_errors, wait_for_page_ready
)


def add_atomic_attribute(page: Page, manifest_id: int, attr_name: str, 
                        atomic_type: str, flags: dict = None):
    """Add an atomic attribute to a manifest.
    
    Args:
        page: Playwright page
        manifest_id: ID of the manifest to edit
        attr_name: Name of the attribute
        atomic_type: Atomic type value (e.g., "str", "int", "text", "select")
        flags: Optional dict of flags to set (e.g., {"in_id": True, "is_array": True})
    
    Example:
        add_atomic_attribute(page, manifest_id, "Description", "text")
        add_atomic_attribute(page, manifest_id, "Count", "int", {"is_array": True})
    """
    print(f"  Adding atomic attribute: {attr_name} ({atomic_type})")
    
    navigate_to(page, f"/admin/manifests/edit/{manifest_id}")
    
    add_btn = page.locator('button:has-text("Add Attribute"), a:has-text("Add Attribute")')
    if add_btn.count() == 0:
        raise AssertionError(
            f"'Add Attribute' button not found!\n"
            f"Current URL: {page.url}"
        )
    
    add_btn.first.click()
    wait_for_page_ready(page, "clicking 'Add Attribute' button")
    
    # Wait for the attr_name field to be truly ready (not just present)
    # The form takes time to render, especially on Windows
    page.wait_for_selector('input[name*="attr_name"]', state="attached", timeout=5000)
    page.wait_for_timeout(200)  # Extra stability wait
    
    fill_form_field(page, "attr_name", attr_name)
    select_form_option(page, "kind_type", "atomic")
    select_form_option(page, "kind_value_atomic", atomic_type)
    
    # Handle flags
    if flags:
        if flags.get("in_id"):
            inid_checkbox = page.locator('input[type="checkbox"][name*="flag_inid"]')
            if inid_checkbox.count() > 0:
                inid_checkbox.first.check()
        
        if flags.get("is_array"):
            array_checkbox = page.locator('input[type="checkbox"][name="Add Attribute.flag_is_array"]')
            if array_checkbox.count() > 0:
                array_checkbox.check()
        
        if flags.get("cascades"):
            cascade_checkbox = page.locator('input[type="checkbox"][name*="flag_cascades"]')
            if cascade_checkbox.count() > 0:
                cascade_checkbox.first.check()
    
    submit_btn = page.locator('button[name="Add Attribute.btn_save"]')
    if submit_btn.count() == 0:
        raise AssertionError(
            f"Submit button not found!\n"
            f"Current URL: {page.url}"
        )
    
    submit_btn.first.click(force=True)
    wait_for_page_ready(page, "submitting attribute form")
    check_for_flash_errors(page)
    
    print(f"  Attribute added: {attr_name}")


def add_manifest_attribute(page: Page, manifest_id: int, attr_name: str,
                          target_manifest_name: str, is_array: bool = False,
                          cascades: bool = False):
    """Add a ManifestKind attribute (embedded manifest) to a manifest.
    
    Args:
        page: Playwright page
        manifest_id: ID of the manifest to edit
        attr_name: Name of the attribute
        target_manifest_name: Name of the manifest to embed
        is_array: Whether this is an array attribute
        cascades: Whether to enable cascade flag (propagate to children)
    
    Example:
        add_manifest_attribute(page, board_manifest_id, "Components", "Component", is_array=True)
    """
    print(f"  Adding manifest attribute: {attr_name} -> {target_manifest_name} (array={is_array})")
    
    navigate_to(page, f"/admin/manifests/edit/{manifest_id}")
    
    add_btn = page.locator('button:has-text("Add Attribute"), a:has-text("Add Attribute")')
    add_btn.first.click()
    
    # Wait for the form to be fully rendered (Windows timing issue)
    page.wait_for_selector('input[name*="attr_name"]', state="attached", timeout=5000)
    page.wait_for_timeout(200)
    
    fill_form_field(page, "attr_name", attr_name)
    select_form_option(page, "kind_type", "manifest")
    page.wait_for_timeout(200)
    
    # Select manifest
    manifest_select = page.locator('select[name*="kind_value_manifest"]').first
    options = manifest_select.locator('option').all()
    
    selected = False
    for opt in options:
        opt_value = opt.get_attribute('value')
        if opt_value and target_manifest_name in opt_value:
            select_form_option(page, "kind_value_manifest", opt_value)
            selected = True
            break
    
    if not selected:
        select_form_option(page, "kind_value_manifest", target_manifest_name)
    
    page.wait_for_timeout(200)
    
    if is_array:
        array_checkbox = page.locator('input[type="checkbox"][name="Add Attribute.flag_is_array"]')
        if array_checkbox.count() > 0:
            array_checkbox.check()
    
    if cascades:
        cascade_checkbox = page.locator('input[type="checkbox"][name*="flag_cascades"]')
        if cascade_checkbox.count() > 0:
            cascade_checkbox.first.check()
    
    save_btn = page.locator('button[name="Add Attribute.btn_save"]')
    save_btn.click()
    page.wait_for_timeout(500)
    check_for_flash_errors(page)
    
    print(f"  Manifest attribute added: {attr_name}")


def add_linkable_attribute(page: Page, manifest_id: int, attr_name: str, 
                          linkable_manifest_name: str, is_array: bool = True,
                          cascades: bool = False):
    """Add a linkable attribute (ManifestKind pointing to linkable manifest).
    
    This is an alias for add_manifest_attribute with is_array=True by default,
    as linkable attributes are typically arrays (e.g., Components, Parts, etc.)
    
    Args:
        page: Playwright page
        manifest_id: ID of the manifest to edit
        attr_name: Name of the attribute
        linkable_manifest_name: Name of the linkable manifest to reference
        is_array: Whether this is an array (default True)
        cascades: Whether to enable cascade flag (propagate to children)
    
    Example:
        add_linkable_attribute(page, product_manifest_id, "Boards", "Board")
        add_linkable_attribute(page, product_manifest_id, "Quality Tests", "Quality Test", cascades=True)
    """
    add_manifest_attribute(page, manifest_id, attr_name, linkable_manifest_name, is_array, cascades)


def add_select_attribute(page: Page, manifest_id: int, attr_name: str, 
                        target_module_name: str = None, is_array: bool = False):
    """Add a SELECT type attribute (dropdown with options).
    
    Note: Options are configured later via set_module_attribute_options() in module configuration.
    The target_module_name parameter is kept for API compatibility but is not used.
    
    Args:
        page: Playwright page
        manifest_id: ID of the manifest to edit
        attr_name: Name of the attribute
        target_module_name: (Unused) Kept for API compatibility
        is_array: Whether this is an array attribute
    
    Example:
        add_select_attribute(page, manifest_id, "Status")
    """
    print(f"  Adding SELECT attribute: {attr_name}")
    
    navigate_to(page, f"/admin/manifests/add_attribute/{manifest_id}")
    
    # Wait for form to be fully rendered (Windows timing issue)
    page.wait_for_selector('input[name*="attr_name"]', state="attached", timeout=5000)
    page.wait_for_timeout(200)
    
    fill_form_field(page, "attr_name", attr_name)
    select_form_option(page, "kind_type", "atomic")
    page.wait_for_timeout(200)
    select_form_option(page, "kind_value_atomic", "select")
    page.wait_for_timeout(200)
    
    if is_array:
        array_checkbox = page.locator('input[type="checkbox"][name="Add Attribute.flag_array"]')
        if array_checkbox.count() > 0:
            array_checkbox.first.check()
    
    save_btn = page.locator('button[name="Add Attribute.btn_save"]')
    save_btn.click()
    page.wait_for_timeout(500)
    check_for_flash_errors(page)
    
    print(f"  SELECT attribute added: {attr_name}")


def add_file_attribute(page: Page, manifest_id: int, attr_name: str, is_array: bool = False):
    """Add a FILE type attribute.
    
    Args:
        page: Playwright page
        manifest_id: ID of the manifest to edit
        attr_name: Name of the attribute
        is_array: Whether this is an array attribute
    
    Example:
        add_file_attribute(page, manifest_id, "Documents", is_array=True)
    """
    print(f"  Adding FILE attribute: {attr_name}")
    
    navigate_to(page, f"/admin/manifests/add_attribute/{manifest_id}")
    
    # Wait for form to be fully rendered (Windows timing issue)
    page.wait_for_selector('input[name*="attr_name"]', state="attached", timeout=5000)
    page.wait_for_timeout(200)
    
    fill_form_field(page, "attr_name", attr_name)
    select_form_option(page, "kind_type", "atomic")
    select_form_option(page, "kind_value_atomic", "file")
    page.wait_for_timeout(200)
    
    if is_array:
        array_checkbox = page.locator('input[type="checkbox"][name="Add Attribute.flag_array"]')
        if array_checkbox.count() > 0:
            array_checkbox.first.check()
    
    save_btn = page.locator('button[name="Add Attribute.btn_save"]')
    save_btn.click()
    page.wait_for_timeout(500)
    check_for_flash_errors(page)
    
    print(f"  FILE attribute added: {attr_name}")


def add_auto_increment_attribute(page: Page, manifest_id: int, attr_name: str):
    """Add an AUTO_INCREMENT attribute.
    
    AUTO_INCREMENT attributes are automatically marked as IN_ID.
    The pattern is configured later in module configuration.
    
    Args:
        page: Playwright page
        manifest_id: ID of the manifest to edit
        attr_name: Name of the attribute (typically "ID")
    
    Example:
        add_auto_increment_attribute(page, batch_manifest_id, "ID")
    """
    print(f"  Adding auto-increment attribute: {attr_name}")
    
    navigate_to(page, f"/admin/manifests/add_attribute/{manifest_id}")
    
    # Wait for form to be fully rendered (Windows timing issue)
    page.wait_for_selector('input[name*="attr_name"]', state="attached", timeout=5000)
    page.wait_for_timeout(200)
    
    fill_form_field(page, "attr_name", attr_name)
    select_form_option(page, "kind_type", "atomic")
    page.wait_for_timeout(200)
    select_form_option(page, "kind_value_atomic", "auto_increment")
    page.wait_for_timeout(200)
    
    # Check IN_ID flag (required for auto_increment)
    inid_checkbox = page.locator('input[type="checkbox"][name*="flag_inid"]')
    if inid_checkbox.count() > 0:
        inid_checkbox.first.check()
    
    save_btn = page.locator('button[name="Add Attribute.btn_save"]')
    save_btn.click()
    page.wait_for_timeout(500)
    check_for_flash_errors(page)
    
    print(f"  AUTO_INCREMENT attribute added: {attr_name}")


def edit_inid_attribute_to_manifest(page: Page, manifest_id: int, attr_name: str, 
                                   target_manifest_name: str):
    """Edit an existing IN_ID attribute to use a manifest reference instead of atomic type.
    
    This is needed when an IN_ID field (like PN) should reference a predefined list
    instead of being a simple string. Critical for the TypeList pattern.
    
    Args:
        page: Playwright page
        manifest_id: ID of the manifest
        attr_name: Name of the IN_ID attribute to edit
        target_manifest_name: Name of the manifest to reference
    
    Example:
        # Change TypeCode from STRING to reference EmbeddedItem manifest
        edit_inid_attribute_to_manifest(page, typelist_manifest_id, "TypeCode", "EmbeddedItem")
    """
    print(f"  Editing IN_ID attribute '{attr_name}' to reference '{target_manifest_name}'")
    
    navigate_to(page, f"/admin/manifests/edit_attribute/{manifest_id}/{attr_name}")
    page.wait_for_timeout(200)
    
    # Change kind_type from atomic to manifest
    select_form_option(page, "kind_type", "manifest")
    page.wait_for_timeout(300)  # Wait for manifest dropdown to appear
    
    # Select the target manifest
    manifest_select = page.locator('select[name*="kind_value_manifest"]').first
    if manifest_select.count() > 0:
        options = manifest_select.locator('option').all()
        selected = False
        for opt in options:
            opt_value = opt.get_attribute('value')
            if opt_value and target_manifest_name in opt_value:
                select_form_option(page, "kind_value_manifest", opt_value)
                selected = True
                break
        
        if not selected:
            select_form_option(page, "kind_value_manifest", target_manifest_name)
    
    page.wait_for_timeout(200)
    
    # Save
    save_btn = page.locator('button:has-text("Update Attribute")')
    if save_btn.count() > 0:
        save_btn.click()
        page.wait_for_timeout(200)
        check_for_flash_errors(page)
    
    print(f"  Attribute updated to manifest reference")


def edit_attribute(page: Page, manifest_id: int, old_name: str,
                  new_name: str = None, new_type: str = None):
    """Edit an existing attribute.
    
    Args:
        page: Playwright page
        manifest_id: ID of the manifest
        old_name: Current attribute name
        new_name: New name (optional)
        new_type: New atomic type (optional)
    
    Example:
        edit_attribute(page, manifest_id, "OldName", new_name="NewName")
    """
    print(f"  Editing attribute: {old_name}")
    
    navigate_to(page, f"/admin/manifests/edit_attribute/{manifest_id}/{old_name}")
    page.wait_for_timeout(200)
    
    if new_name:
        fill_form_field(page, "attr_name", new_name)
    
    if new_type:
        select_form_option(page, "kind_type", "atomic")
        page.wait_for_timeout(200)
        select_form_option(page, "kind_value_atomic", new_type)
    
    save_btn = page.locator('button:has-text("Update Attribute")')
    if save_btn.count() > 0:
        save_btn.click()
        page.wait_for_timeout(200)
        check_for_flash_errors(page)
    
    print(f"  Attribute updated")


def delete_attribute(page: Page, manifest_id: int, attr_name: str):
    """Delete an attribute from a manifest.
    
    Args:
        page: Playwright page
        manifest_id: ID of the manifest
        attr_name: Name of the attribute to delete
    
    Example:
        delete_attribute(page, manifest_id, "OldField")
    """
    from tests.frontend.conftest import BASE_URL
    print(f"  Deleting attribute: {attr_name}")
    
    # Navigate directly using page.goto to avoid navigate_to's auto-flash check
    # (The delete confirmation page shows a warning which is expected)
    page.goto(f"{BASE_URL}/admin/manifests/delete_attribute/{manifest_id}/{attr_name}")
    page.wait_for_load_state("domcontentloaded")
    
    # Click confirm/delete button
    confirm_btn = page.locator('button:has-text("Delete"), button:has-text("Confirm"), button[name*="btn_delete"]')
    if confirm_btn.count() > 0:
        confirm_btn.first.click()
        page.wait_for_load_state("domcontentloaded")
        # Only check for errors after the actual delete action
        check_for_flash_errors(page)
    else:
        raise AssertionError(f"Delete confirmation button not found for attribute {attr_name}")
    
    print(f"  Attribute deleted")
