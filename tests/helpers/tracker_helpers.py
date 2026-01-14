"""
Tracker Helper Functions

Extracted from test_sea_system_data.py (source of truth).
All functions use conftest.py helpers for navigation and error checking.
"""

from playwright.sync_api import Page

from tests.frontend.conftest import (
    navigate_to, fill_form_field, select_form_option,
    extract_id_from_url, extract_id_from_table, check_for_flash_errors
)


def create_tracker(page: Page, module_id: int, name: str = None,
                  attributes: dict = None) -> int:
    """Create a tracker from a module.
    
    Args:
        page: Playwright page (must be logged in)
        module_id: ID of the module to create tracker from
        name: Tracker name (optional for auto-increment modules)
        attributes: Optional dict of attribute values to set after creation
    
    Returns:
        Tracker ID
    
    Example:
        tracker_id = create_tracker(page, module_id, "BOARD-001", {"Status": "Active"})
    """
    print(f"\nCreating tracker: {name or '(auto)'} (from module ID: {module_id})")
    
    navigate_to(page, "/tracker/create")
    
    # Select module
    module_select = page.locator('select[name="Create Tracker.module_selection"]')
    module_select.wait_for(state='visible', timeout=5000)
    
    options = module_select.locator('option').all()
    module_option_value = None
    for opt in options:
        opt_value = opt.get_attribute('value')
        if opt_value and f"[ID:{module_id}]" in opt_value:
            module_option_value = opt_value
            break
    
    if not module_option_value:
        option_values = [opt.get_attribute('value') for opt in options]
        raise AssertionError(
            f"Could not find module ID {module_id} in dropdown!\n"
            f"Available options: {option_values}"
        )
    
    select_form_option(page, "Create Tracker.module_selection", module_option_value)
    page.wait_for_timeout(300)
    
    # Fill name if provided (auto-increment modules don't need name)
    if name:
        fill_form_field(page, "Create Tracker.tracker_name", name)
    
    # Click Create
    create_btn = page.locator('button:has-text("Create"), button[name*="btn_create"]')
    create_btn.first.click()
    
    # Wait for navigation to complete (should redirect to view page)
    page.wait_for_url('**/tracker/view/**', timeout=5000)
    check_for_flash_errors(page)
    
    # Extract tracker ID from the view page URL
    tracker_id = extract_id_from_url(page)
    
    print(f"Tracker created with ID: {tracker_id}")
    
    # Set attributes if provided
    if attributes:
        _set_tracker_attributes(page, tracker_id, attributes)
    
    return tracker_id


def create_auto_increment_tracker(page: Page, module_id: int, 
                                 attributes: dict = None) -> int:
    """Create a tracker for modules with auto-increment ID (name is auto-generated).
    
    Args:
        page: Playwright page
        module_id: ID of the module
        attributes: Optional dict of attribute values
    
    Returns:
        Tracker ID
    
    Example:
        tracker_id = create_auto_increment_tracker(page, batch_module_id, {"Status": "Open"})
    """
    print(f"\nCreating auto-increment tracker (module_id={module_id})")
    
    navigate_to(page, "/tracker/create")
    page.wait_for_timeout(200)
    
    # Select module
    module_select = page.locator('select[name*="module_selection"]').first
    options = module_select.locator('option').all()
    
    selected_value = None
    for opt in options:
        opt_value = opt.get_attribute('value')
        if opt_value and f"[ID:{module_id}]" in opt_value:
            selected_value = opt_value
            break
    
    if not selected_value:
        raise ValueError(f"Could not find module option with ID {module_id}")
    
    select_form_option(page, "module_selection", selected_value)
    page.wait_for_timeout(500)
    
    # Don't fill name - it's auto-generated
    
    # Click Create
    page.click('button[name="Create Tracker.btn_create"]')
    page.wait_for_timeout(500)
    check_for_flash_errors(page)
    
    tracker_id = extract_id_from_url(page)
    print(f"Auto-increment tracker created with ID: {tracker_id}")
    
    # Set attributes if provided
    if attributes:
        _set_tracker_attributes(page, tracker_id, attributes)
    
    return tracker_id


def create_simple_tracker(page: Page, module_id: int, name: str, 
                         attributes: dict) -> int:
    """Create a tracker with given attributes (alias for create_tracker).
    
    Note: IN_ID attributes (PN, SN) are typically inferred from the tracker name.
    Only non-IN_ID attributes need to be set via edit.
    
    Args:
        page: Playwright page
        module_id: ID of the module
        name: Tracker name
        attributes: Dict of attribute values
    
    Returns:
        Tracker ID
    """
    # Always create - don't check for existing trackers since /tracker/list
    # is paginated and doesn't show all trackers. The create_tracker function
    # handles deduplication via the page redirecting to view if needed.
    return create_tracker(page, module_id, name, attributes)


def _set_tracker_attributes(page: Page, tracker_id: int, attributes: dict):
    """Internal helper to set tracker attributes after creation."""
    navigate_to(page, f"/tracker/edit/{tracker_id}")
    page.wait_for_timeout(200)
    
    for attr_name, value in attributes.items():
        # Handle embedded manifest (dict value)
        if isinstance(value, dict):
            # For embedded manifests, each sub-field needs to be set
            for sub_key, sub_value in value.items():
                field_selector = f'input[name*="{attr_name}"][name*="{sub_key}"], textarea[name*="{attr_name}"][name*="{sub_key}"]'
                field = page.locator(field_selector).first
                if field.count() > 0:
                    field.fill(str(sub_value))
            continue
        
        field_selector = f'input[name="Edit Tracker.attributes.{attr_name}"], textarea[name="Edit Tracker.attributes.{attr_name}"], select[name="Edit Tracker.attributes.{attr_name}"]'
        field = page.locator(field_selector).first
        
        if field.count() > 0:
            tag_name = field.evaluate("el => el.tagName")
            if tag_name == "SELECT":
                select_form_option(page, f"Edit Tracker.attributes.{attr_name}", value)
            elif tag_name == "TEXTAREA":
                field.evaluate(f"el => el.value = '{value}'")
            else:
                field_type = field.get_attribute("type")
                if field_type == "checkbox":
                    if value:
                        field.check()
                    else:
                        field.uncheck()
                else:
                    field.fill(str(value))
    
    # Save
    page.click('button[type="submit"]:has-text("Save")', no_wait_after=True, timeout=10000)
    page.wait_for_timeout(200)
    check_for_flash_errors(page)


def edit_tracker_field(page: Page, tracker_id: int, field_name: str, 
                      value: str, is_rich_text: bool = False):
    """Edit a single tracker field.
    
    Args:
        page: Playwright page
        tracker_id: ID of the tracker
        field_name: Name of the field to edit
        value: New value
        is_rich_text: Whether this is a rich text field (uses different method)
    
    Example:
        edit_tracker_field(page, tracker_id, "Status", "Active")
    """
    print(f"  Editing field '{field_name}' = '{value}'")
    
    navigate_to(page, f"/tracker/edit/{tracker_id}")
    page.wait_for_timeout(200)
    
    field_selector = f'input[name="Edit Tracker.attributes.{field_name}"], textarea[name="Edit Tracker.attributes.{field_name}"], select[name="Edit Tracker.attributes.{field_name}"]'
    field = page.locator(field_selector).first
    
    if field.count() > 0:
        tag_name = field.evaluate("el => el.tagName")
        if tag_name == "SELECT":
            select_form_option(page, f"Edit Tracker.attributes.{field_name}", value)
        elif tag_name == "TEXTAREA" or is_rich_text:
            field.evaluate(f"el => el.value = '{value}'")
        else:
            field.fill(str(value))
    
    page.click('button[type="submit"]:has-text("Save")', no_wait_after=True, timeout=10000)
    page.wait_for_timeout(200)
    check_for_flash_errors(page)
    
    print(f"  Field updated")


def upload_file_to_tracker(page: Page, tracker_id: int, field_name: str, 
                          file_path: str):
    """Upload a file to a tracker's file field.
    
    Args:
        page: Playwright page
        tracker_id: ID of the tracker
        field_name: Name of the file field
        file_path: Path to the file to upload
    
    Example:
        upload_file_to_tracker(page, tracker_id, "Documents", "/path/to/file.pdf")
    """
    print(f"  Uploading file to '{field_name}'")
    
    navigate_to(page, f"/tracker/edit/{tracker_id}")
    page.wait_for_timeout(200)
    
    file_input = page.locator(f'input[type="file"][name*="{field_name}"]').first
    if file_input.count() > 0:
        file_input.set_input_files(file_path)
        page.wait_for_timeout(500)
    
    page.click('button[type="submit"]:has-text("Save")', no_wait_after=True, timeout=10000)
    page.wait_for_timeout(200)
    check_for_flash_errors(page)
    
    print(f"  File uploaded")


def add_to_tracker_array(page: Page, tracker_id: int, array_field: str, 
                        value: str, cascade: bool = False):
    """Add an item to a tracker's array field.
    
    Arrays use <select> dropdowns with naming patterns:
    - Multi-IN_ID: [0]_PN and [0]_SN (e.g., "DISPLAY-14_LCD2401")
    - Single-IN_ID: [0]_ID (e.g., "QC-000001")
    
    Args:
        page: Playwright page
        tracker_id: ID of the tracker
        array_field: Name of the array field
        value: Value to add. For multi-IN_ID use "PN_SN" format, for single-IN_ID just the ID
        cascade: Whether to check the cascade checkbox (requires flag_cascades on attribute)
    
    Example:
        add_to_tracker_array(page, product_id, "Assemblies", "DISPLAY-14_LCD2401")  # Multi-IN_ID
        add_to_tracker_array(page, product_id, "Quality Tests", "QC-000001", cascade=True)  # Single-IN_ID with cascade
    """
    print(f"  Adding to array '{array_field}': {value} (cascade={cascade})")
    
    navigate_to(page, f"/tracker/edit/{tracker_id}")
    page.wait_for_timeout(200)
    
    # Find the first empty slot - need to count existing filled slots
    # Try Multi-IN_ID format first (PN + SN)
    test_pn = page.locator(f'select[name="Edit Tracker.attributes.{array_field}[0]_PN"]')
    test_id = page.locator(f'select[name="Edit Tracker.attributes.{array_field}[0]_ID"]')
    
    # Determine slot index by checking which slots already have values
    slot_index = 0
    if test_pn.count() > 0:
        # Multi-IN_ID - count non-empty PN selects
        while True:
            pn_sel = page.locator(f'select[name="Edit Tracker.attributes.{array_field}[{slot_index}]_PN"]')
            if pn_sel.count() == 0:
                break
            # Check if this slot has a value
            pn_value = pn_sel.input_value()
            if not pn_value:
                break
            slot_index += 1
            if slot_index > 50:  # Safety limit
                break
    elif test_id.count() > 0:
        # Single-IN_ID - count non-empty ID selects
        while True:
            id_sel = page.locator(f'select[name="Edit Tracker.attributes.{array_field}[{slot_index}]_ID"]')
            if id_sel.count() == 0:
                break
            # Check if this slot has a value
            id_value = id_sel.input_value()
            if not id_value:
                break
            slot_index += 1
            if slot_index > 50:  # Safety limit
                break
    
    # Now use the found slot index
    # If array uses tabs, click the appropriate tab first
    # Find the specific tab container for this field by looking near the heading
    tab_container = page.locator(f'h6:text("{array_field}") + ul.nav-tabs')
    if tab_container.count() > 0:
        tab_id_prefix = tab_container.get_attribute('id')
        if tab_id_prefix:
            # Click the tab link for this slot (tab numbers are 1-indexed, slot_index is 0-indexed)
            tab_number = slot_index + 1
            tab_link = page.locator(f'a[id="{tab_id_prefix}_tab{tab_number}"]')
            if tab_link.count() > 0:
                print(f"  Clicking tab {tab_number} for array '{array_field}' slot [{slot_index}]")
                tab_link.click()
                # Wait for tab pane to be active and visible
                page.wait_for_selector(f'#{tab_id_prefix}_pane{tab_number}.show.active', timeout=3000)
                page.wait_for_timeout(200)  # Small delay for transitions
    
    pn_select = page.locator(f'select[name="Edit Tracker.attributes.{array_field}[{slot_index}]_PN"]')
    sn_select = page.locator(f'select[name="Edit Tracker.attributes.{array_field}[{slot_index}]_SN"]')
    id_select = page.locator(f'select[name="Edit Tracker.attributes.{array_field}[{slot_index}]_ID"]')
    
    if pn_select.count() > 0 and sn_select.count() > 0:
        # Multi-IN_ID: expect "PN_SN" format
        if '_' not in value:
            raise ValueError(f"Multi-IN_ID array '{array_field}' expects 'PN_SN' format, got: {value}")
        pn, sn = value.split('_', 1)
        
        # Select PN
        pn_select.select_option(label=pn)
        page.wait_for_timeout(300)  # Wait for cascade JS to populate SN options
        
        # Select SN
        sn_select.select_option(label=sn)
        
    elif id_select.count() > 0:
        # Single-IN_ID: just the ID value
        id_select.select_option(label=value)
        
    else:
        raise AssertionError(
            f"Could not find array select dropdowns for '{array_field}'!\n"
            f"Expected: select[name='Edit Tracker.attributes.{array_field}[0]_PN'] or\n"
            f"          select[name='Edit Tracker.attributes.{array_field}[0]_ID']\n"
            f"Current URL: {page.url}"
        )
    
    # Handle cascade checkbox if requested
    if cascade:
        cascade_checkbox = page.locator(f'input[name="Edit Tracker.attributes.cascade.{array_field}"]')
        if cascade_checkbox.count() > 0:
            cascade_checkbox.check()
        else:
            print(f"  Cascade checkbox not found for '{array_field}' - flag_cascades may not be enabled")
    
    page.click('button[type="submit"]:has-text("Save")')
    page.wait_for_url(f"**/tracker/edit/{tracker_id}", wait_until='domcontentloaded', timeout=2000)
    page.wait_for_timeout(200)
    check_for_flash_errors(page)
    
    print(f"  Item added to array")


def remove_from_tracker_array(page: Page, tracker_id: int, array_field: str, 
                             index: int):
    """Remove an item from a tracker's array field.
    
    Args:
        page: Playwright page
        tracker_id: ID of the tracker
        array_field: Name of the array field
        index: Index of the item to remove (0-based)
    
    Example:
        remove_from_tracker_array(page, product_id, "Boards", 0)
    """
    print(f"  Removing from array '{array_field}' at index {index}")
    
    navigate_to(page, f"/tracker/edit/{tracker_id}")
    page.wait_for_timeout(200)
    
    # Find remove button for this array item
    remove_btns = page.locator(f'button[name*="{array_field}"][name*="remove"], a[onclick*="{array_field}"][onclick*="remove"]').all()
    if index < len(remove_btns):
        remove_btns[index].click()
        page.wait_for_timeout(300)
    
    page.click('button[type="submit"]:has-text("Save")', no_wait_after=True, timeout=10000)
    page.wait_for_timeout(200)
    check_for_flash_errors(page)
    
    print(f"  Item removed from array")


def delete_tracker(page: Page, tracker_id: int):
    """Delete a tracker.
    
    Args:
        page: Playwright page
        tracker_id: ID of the tracker to delete
    
    Example:
        delete_tracker(page, 123)
    """
    print(f"Deleting tracker ID: {tracker_id}")
    
    navigate_to(page, "/tracker/list")
    
    delete_link = page.locator(f'a[href*="/tracker/delete/{tracker_id}"]')
    if delete_link.count() > 0:
        delete_link.click()
        page.wait_for_timeout(300)
        
        # Confirm if needed
        confirm_btn = page.locator('button:has-text("Delete"), button:has-text("Confirm")')
        if confirm_btn.count() > 0:
            confirm_btn.first.click()
            page.wait_for_timeout(300)
            check_for_flash_errors(page)
    
    print(f"Tracker deleted")


def add_sibling_relationship(page: Page, tracker1_id: int, tracker2_name: str):
    """Add a sibling relationship between two trackers.
    
    Uses the dedicated /tracker/add_sibling/{id} page with a select dropdown.
    The dropdown options contain the tracker name and ID in format:
    "PN_SN (Module) [ID:xxx]" or similar.
    
    Args:
        page: Playwright page
        tracker1_id: ID of the first tracker
        tracker2_name: Name (or partial name) of the sibling tracker to add
    
    Example:
        add_sibling_relationship(page, product1_id, "MOUSE-WIRELESS_MS001")
    """
    print(f"  Adding sibling relationship to '{tracker2_name}'")
    
    navigate_to(page, f"/tracker/add_sibling/{tracker1_id}")
    page.wait_for_timeout(200)
    
    # Find the sibling selection dropdown
    sibling_select = page.locator('select[name="Add Sibling.sibling_selection"]')
    if sibling_select.count() == 0:
        raise AssertionError(
            f"Sibling selection dropdown not found!\n"
            f"Expected: select[name='Add Sibling.sibling_selection']\n"
            f"Current URL: {page.url}"
        )
    
    # Find option containing the tracker name
    options = sibling_select.locator('option').all()
    selected_value = None
    for opt in options:
        opt_value = opt.get_attribute('value')
        if opt_value and tracker2_name in opt_value:
            selected_value = opt_value
            break
    
    if not selected_value:
        option_values = [opt.get_attribute('value') for opt in options]
        raise AssertionError(
            f"Could not find sibling option containing '{tracker2_name}'!\n"
            f"Available options: {option_values}"
        )
    
    sibling_select.select_option(value=selected_value)
    page.wait_for_timeout(200)
    
    # Click submit button
    submit_btn = page.locator('button[name="Add Sibling.btn_submit"]')
    if submit_btn.count() == 0:
        submit_btn = page.locator('button:has-text("Add Sibling")')
    
    submit_btn.first.click()
    page.wait_for_timeout(300)
    check_for_flash_errors(page)
    
    print(f"  Sibling relationship added")


def set_attribute_and_cascade(page: Page, tracker_id: int, attr_name: str, 
                              value: str):
    """Set an attribute value and cascade it to descendants.
    
    Args:
        page: Playwright page
        tracker_id: ID of the tracker
        attr_name: Name of the attribute with CASCADES flag
        value: Value to set and cascade
    
    Example:
        set_attribute_and_cascade(page, product_id, "Status", "Released")
    """
    print(f"  Setting and cascading '{attr_name}' = '{value}'")
    
    # First set the attribute
    edit_tracker_field(page, tracker_id, attr_name, value)
    
    # Look for cascade button/trigger
    navigate_to(page, f"/tracker/view/{tracker_id}")
    page.wait_for_timeout(200)
    
    cascade_btn = page.locator(f'button:has-text("Cascade"), a[href*="cascade"]').first
    if cascade_btn.count() > 0:
        cascade_btn.click()
        page.wait_for_timeout(200)
        check_for_flash_errors(page)
    
    print(f"  Attribute cascaded")


def verify_tracker_exists(page: Page, tracker_id: int, name: str = None):
    """Verify a tracker exists by navigating to its view page.
    
    Args:
        page: Playwright page
        tracker_id: ID of the tracker
        name: Optional expected name to verify
    
    Raises:
        AssertionError: If tracker not found or name doesn't match
    
    Example:
        verify_tracker_exists(page, tracker_id, "BOARD-001")
    """
    navigate_to(page, f"/tracker/view/{tracker_id}")
    page.wait_for_timeout(200)
    
    # Check we're on the view page (not an error)
    if f"/view/{tracker_id}" not in page.url:
        raise AssertionError(f"Tracker {tracker_id} not found - redirected to {page.url}")
    
    if name:
        page_content = page.content()
        if name not in page_content:
            raise AssertionError(f"Tracker name '{name}' not found on page")
    
    print(f"  Tracker {tracker_id} verified")


def verify_tracker_attribute(page: Page, tracker_id: int, attr_name: str, 
                            expected_value):
    """Verify a tracker has a specific attribute value.
    
    Args:
        page: Playwright page
        tracker_id: ID of the tracker
        attr_name: Name of the attribute
        expected_value: Expected value (str or dict for embedded manifests)
    
    Raises:
        AssertionError: If attribute value doesn't match
    
    Example:
        verify_tracker_attribute(page, tracker_id, "Status", "Active")
    """
    navigate_to(page, f"/tracker/view/{tracker_id}")
    page.wait_for_timeout(200)
    
    page_content = page.content()
    
    if isinstance(expected_value, dict):
        # For embedded manifests, check each sub-value
        for key, value in expected_value.items():
            if str(value) not in page_content:
                raise AssertionError(
                    f"Attribute '{attr_name}.{key}' = '{value}' not found on tracker {tracker_id}"
                )
    else:
        if str(expected_value) not in page_content:
            raise AssertionError(
                f"Attribute '{attr_name}' = '{expected_value}' not found on tracker {tracker_id}"
            )
    
    print(f"  Attribute '{attr_name}' verified")


def add_embedded_item(page: Page, tracker_id: int, field_name: str, 
                     attributes: dict = None):
    """Add an embedded item to a tracker's array attribute.
    
    Args:
        page: Playwright page
        tracker_id: Tracker ID
        field_name: Name of the embedded array field (e.g., "Manufacturing Steps")
        attributes: Dict of attribute values for the new item (excludes rich text/files)
    
    Example:
        add_embedded_item(page, board_id, "Manufacturing Steps", {
            "Step Name": "SMT Assembly",
            "Duration": 120,
            "Operator": "Tech-01"
        })
    """
    navigate_to(page, f"/tracker/edit/{tracker_id}")
    
    # Count existing items BEFORE adding
    delete_buttons_before = page.locator(f'button[name^="delete_attributes.{field_name}["]').count()
    
    # Click "Add Item" button
    add_button = page.locator(f'button[name="Edit Tracker.add_item_attributes.{field_name}"]')
    add_button.click()
    
    # Wait for new delete button to appear in DOM (indicates item was added)
    # Note: button may be hidden if not in active tab
    page.wait_for_selector(f'button[name="delete_attributes.{field_name}[{delete_buttons_before}]"]', state='attached', timeout=5000)
    
    # The new item index is the count before adding
    item_index = delete_buttons_before
    
    # Click the tab for the new item to make it active
    # Tab IDs follow pattern: tabs_{id}_tab{n} where n = item_index + 1
    # Find the specific tab container for this field by looking near the heading
    tab_container = page.locator(f'h6:text("{field_name}") + ul.nav-tabs')
    
    if tab_container.count() > 0:
        tab_id_prefix = tab_container.get_attribute('id')
        if tab_id_prefix:
            # Click the tab link for this item (tab numbers are 1-indexed)
            tab_number = item_index + 1
            tab_link = page.locator(f'a[id="{tab_id_prefix}_tab{tab_number}"]')
            if tab_link.count() > 0:
                tab_link.scroll_into_view_if_needed()
                tab_link.click(force=True)  # Force click to ensure it happens
                # Just wait for the pane to exist and be visible (don't require .active class)
                try:
                    page.locator(f'#{tab_id_prefix}_pane{tab_number}').wait_for(state='attached', timeout=2000)
                except:
                    # Tab might already be visible or DOM structure different
                    pass
                page.wait_for_timeout(300)  # Slightly longer delay for Bootstrap transitions
    
    # Fill attributes if provided
    if attributes:
        for attr_name, value in attributes.items():
            field_id = f"Edit Tracker.attributes.{field_name}[{item_index}].{attr_name}"
            
            # Skip file upload and rich text fields
            if 'Photos' in attr_name or 'Notes' in attr_name or 'Documents' in attr_name:
                continue
            
            # Check for linkable manifest reference (has _module and _ID selects)
            module_select = page.locator(f'select[name="{field_id}_module"]')
            id_select = page.locator(f'select[name="{field_id}_ID"]')
            
            if module_select.count() > 0 and id_select.count() > 0:
                # Handle linkable manifest reference (e.g., "Repair Order")
                # Value should be the tracker ID (e.g., "REPAIR-000001")
                # First, find which module contains this ID
                if value:
                    # Get all module options
                    module_options = module_select.locator('option').all_text_contents()
                    # Try each module until we find the ID
                    for module_name in module_options:
                        if module_name:  # Skip empty option
                            select_form_option(page, f"{field_id}_module", module_name)
                            page.wait_for_timeout(200)  # Wait for cascade
                            # Check if our ID is now available
                            id_options = id_select.locator('option').all_text_contents()
                            if str(value) in id_options:
                                select_form_option(page, f"{field_id}_ID", str(value))
                                break
            else:
                # Check if it's a select, input, or checkbox
                select_elem = page.locator(f'select[name="{field_id}"]')
                input_elem = page.locator(f'input[name="{field_id}"]')
                checkbox_elem = page.locator(f'input[type="checkbox"][name="{field_id}"]')
                
                if select_elem.count() > 0:
                    # Handle selects (including nested .Item selects)
                    item_select = page.locator(f'select[name="{field_id}.Item"]')
                    if item_select.count() > 0:
                        select_form_option(page, f"{field_id}.Item", str(value))
                    else:
                        select_form_option(page, field_id, str(value))
                elif checkbox_elem.count() > 0:
                    # Handle checkboxes
                    if value:
                        checkbox_elem.check()
                    else:
                        checkbox_elem.uncheck()
                elif input_elem.count() > 0:
                    # Force fill for elements in tab panes (might be hidden initially)
                    input_elem.first.fill(str(value), force=True)
    
    # Save changes
    page.click('button:has-text("Save Changes")')
    
    # Wait for redirect back to edit page
    page.wait_for_url(f"**/tracker/edit/{tracker_id}", wait_until='domcontentloaded', timeout=2000)
    page.wait_for_timeout(200)
    
    check_for_flash_errors(page)
    
    print(f"  Added embedded item to {field_name}")
