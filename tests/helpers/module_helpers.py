"""
Module Helper Functions

Extracted from test_sea_system_data.py (source of truth).
All functions use conftest.py helpers for navigation and error checking.
"""

import re
from playwright.sync_api import Page

from tests.frontend.conftest import (
    navigate_to, fill_form_field, select_form_option,
    extract_id_from_url, check_for_flash_errors
)


def create_module(page: Page, name: str, manifest_id: int, 
                 name_pattern: str = None) -> int:
    """Create a new module from a manifest and return its ID.
    
    Args:
        page: Playwright page (must be logged in)
        name: Name for the new module
        manifest_id: ID of the manifest to use as template
        name_pattern: Optional name pattern (e.g., "{PN}-{SN}")
    
    Returns:
        Module ID
    
    Example:
        module_id = create_module(page, "Board_Module", board_manifest_id)
    """
    print(f"\nCreating module: {name} (from manifest ID: {manifest_id})")
    
    navigate_to(page, "/admin/modules/create")
    
    # Check for "no manifests" warning
    no_manifests_warning = page.locator('.alert-warning:has-text("No manifests available")')
    if no_manifests_warning.count() > 0:
        raise AssertionError(
            f"No manifests available!\n"
            f"Manifest ID {manifest_id} was supposed to exist."
        )
    
    # Fill module name
    fill_form_field(page, "Create Module.module_name", name)
    
    # Select manifest
    manifest_select = page.locator('select[name="Create Module.manifest_id"]')
    manifest_select.wait_for(state='visible', timeout=5000)
    
    options = manifest_select.locator('option').all()
    manifest_option_value = None
    for opt in options:
        opt_value = opt.get_attribute('value')
        if opt_value and f"(ID: {manifest_id})" in opt_value:
            manifest_option_value = opt_value
            break
    
    if not manifest_option_value:
        option_values = [opt.get_attribute('value') for opt in options]
        raise AssertionError(
            f"Could not find manifest ID {manifest_id} in dropdown!\n"
            f"Available options: {option_values}"
        )
    
    select_form_option(page, "Create Module.manifest_id", manifest_option_value)
    
    # Set name pattern if provided
    if name_pattern:
        pattern_field = page.locator('input[name*="name_pattern"]')
        if pattern_field.count() > 0:
            pattern_field.fill(name_pattern)
    
    # Click Create Module button
    create_btn = page.locator('button:has-text("Create Module")')
    if create_btn.count() == 0:
        buttons = page.locator('button').all()
        button_texts = [btn.inner_text() for btn in buttons]
        raise AssertionError(
            f"'Create Module' button not found!\n"
            f"Available buttons: {button_texts}"
        )
    
    create_btn.first.click()
    page.wait_for_timeout(300)
    check_for_flash_errors(page)
    
    # Extract module_id from URL
    current_url = page.url
    if '/create' in current_url and 'module_id=' not in current_url:
        error_msg = page.locator('.alert-danger, .alert-warning').first
        if error_msg.count() > 0:
            error_text = error_msg.inner_text()
            raise AssertionError(
                f"Module creation failed!\n"
                f"Error: {error_text}"
            )
        else:
            raise AssertionError(f"Module creation failed - no redirect!")
    
    match = re.search(r'module_id=(\d+)', page.url)
    if match:
        module_id = int(match.group(1))
    else:
        module_id = extract_id_from_url(page)
    
    print(f"Module created with ID: {module_id}")
    return module_id


def delete_module(page: Page, module_id: int):
    """Delete a module.
    
    Args:
        page: Playwright page
        module_id: ID of the module to delete
    
    Example:
        delete_module(page, 123)
    """
    print(f"Deleting module ID: {module_id}")
    
    navigate_to(page, "/admin/modules/list")
    
    page.click(f'a[href*="/admin/modules/delete/{module_id}"]')
    
    try:
        page.click('button:has-text("Confirm"), button:has-text("Delete")', timeout=1000)
    except:
        pass  # No confirmation dialog
    
    page.wait_for_timeout(200)
    check_for_flash_errors(page)
    print(f"Module deleted")


def set_module_attribute_options(page: Page, module_id: int, attr_name: str, 
                                options: list[str]):
    """Set the options for a SELECT type attribute in a module.
    
    This navigates to the edit_attribute_value page and adds each option.
    
    Args:
        page: Playwright page
        module_id: ID of the module
        attr_name: Name of the SELECT attribute
        options: List of option values (e.g., ["Active", "Inactive", "Testing"])
    
    Example:
        set_module_attribute_options(page, module_id, "Status", ["Active", "Inactive"])
    """
    print(f"  Setting options for '{attr_name}': {options}")
    
    navigate_to(page, f"/admin/modules/edit_attribute_value/{module_id}/{attr_name}")
    page.wait_for_timeout(300)
    
    field_prefix = f"Edit Attribute Value.attr_{attr_name}_options"
    
    for i, option in enumerate(options):
        list_field_name = f"{field_prefix}.list{i}"
        
        if i > 0:
            add_button = page.locator(f"a[onclick*=\"setting_add_list('{field_prefix}')\"]")
            if add_button.count() > 0:
                add_button.click()
                page.wait_for_timeout(200)
        
        list_field = page.locator(f'input[name="{list_field_name}"]')
        if list_field.count() > 0:
            list_field.fill(option)
            page.wait_for_timeout(100)
    
    # Save
    save_btn = page.locator('button[name="Edit Attribute Value.btn_save"]')
    if save_btn.count() > 0:
        save_btn.click()
        page.wait_for_timeout(200)
        check_for_flash_errors(page)
    else:
        save_btn = page.locator('button:has-text("Save")')
        if save_btn.count() > 0:
            save_btn.first.click()
            page.wait_for_timeout(500)
            check_for_flash_errors(page)
    
    print(f"  Options set")


def set_module_auto_increment_pattern(page: Page, module_id: int, attr_name: str, 
                                     pattern: str):
    """Set the auto-increment pattern for a module attribute.
    
    Args:
        page: Playwright page
        module_id: Module ID
        attr_name: Attribute name (e.g., "ID")
        pattern: Auto-increment pattern (e.g., "PF-{counter:06d}")
    
    Example:
        set_module_auto_increment_pattern(page, module_id, "ID", "BATCH-{counter:04d}")
    """
    print(f"  Setting auto-increment pattern for '{attr_name}': {pattern}")
    
    navigate_to(page, f"/admin/modules/edit_attribute_value/{module_id}/{attr_name}")
    page.wait_for_timeout(200)
    
    pattern_field = page.locator(f'input[name="Edit Attribute Value.attr_{attr_name}_auto_increment_pattern"]')
    if pattern_field.count() > 0:
        pattern_field.fill(pattern)
    
    save_btn = page.locator('button[name="Edit Attribute Value.btn_save"]')
    if save_btn.count() > 0:
        save_btn.click()
        page.wait_for_timeout(200)
        check_for_flash_errors(page)
    
    print(f"  Pattern set")


def configure_target_module(page: Page, module_id: int, attr_name: str,
                           target_module_id: int, default_value: str = None):
    """Configure target_module_id for a ManifestKind attribute.
    
    Args:
        page: Playwright page
        module_id: Module ID
        attr_name: Attribute name
        target_module_id: Target module ID to configure
        default_value: Optional default value to set
    
    Example:
        configure_target_module(page, board_module_id, "Status", status_module_id)
    """
    print(f"  Configuring {attr_name} -> target_module_id={target_module_id}")
    
    navigate_to(page, f"/admin/modules/edit_attribute_value/{module_id}/{attr_name}")
    page.wait_for_timeout(500)
    
    # Find and set target_module_id
    select_elem = page.locator('select[name*="target_module_id"]')
    if select_elem.count() > 0:
        options = select_elem.first.locator('option').all()
        for opt in options:
            opt_value = opt.get_attribute('value')
            if opt_value and f"(ID: {target_module_id})" in opt_value:
                select_form_option(page, select_elem.first.get_attribute('name'), opt_value)
                break
    
    # Set default value if provided
    if default_value:
        default_field = page.locator('input[name*="default"], select[name*="default"]').first
        if default_field.count() > 0:
            tag_name = default_field.evaluate("el => el.tagName")
            if tag_name == "SELECT":
                select_form_option(page, default_field.get_attribute('name'), default_value)
            else:
                default_field.fill(default_value)
    
    # Save
    save_btn = page.locator('button[name="Edit Attribute Value.btn_save"]')
    if save_btn.count() > 0:
        save_btn.click()  # Remove no_wait_after - let Playwright wait for navigation
        page.wait_for_timeout(500)  # Wait for page to settle
        check_for_flash_errors(page)
    
    print(f"  Target module configured")


def set_module_default(page: Page, module_id: int, field_name: str, value: str):
    """Set a default value for a module field.
    
    Args:
        page: Playwright page
        module_id: ID of the module
        field_name: Name of the field
        value: Default value
    
    Example:
        set_module_default(page, module_id, "Status", "Active")
    """
    print(f"  Setting default for '{field_name}': {value}")
    
    navigate_to(page, f"/admin/modules/create?module_id={module_id}")
    
    fill_form_field(page, field_name, value)
    
    page.click('button[type="submit"]:has-text("Save"), button[name*="btn_save"]')
    page.wait_for_timeout(200)
    check_for_flash_errors(page)
    
    print(f"  Default set")


def save_attribute_value(page: Page, module_id: int, attr_name: str):
    """Save an attribute value without making changes.
    
    This is a workaround to ensure auto-populated values (like target_module_id)
    are properly persisted to the database.
    
    Args:
        page: Playwright page
        module_id: Module ID
        attr_name: Attribute name
    
    Example:
        save_attribute_value(page, module_id, "Components")
    """
    navigate_to(page, f"/admin/modules/edit_attribute_value/{module_id}/{attr_name}")
    page.wait_for_timeout(300)
    
    save_btn = page.locator('button[name="Edit Attribute Value.btn_save"]')
    if save_btn.count() > 0:
        save_btn.click()
        page.wait_for_timeout(300)
        check_for_flash_errors(page)
