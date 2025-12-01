"""
Settings - Modern settings interface with clear, descriptive type names.

Supported field types with intuitive naming:

- string: Simple text input
- int: Numeric input with validation
- bool: Checkbox (true/false)
- select: Dropdown menu with predefined options
- serial_port: Serial port selection (auto-detects or uses provided options)
- icon: Icon selector with preview
- text_list: User-defined list of text items
- multi_select: Multi-select checkboxes from predefined options
- key_value_pairs: User-defined key-value text pairs
- dropdown_mapping: Predefined keys with text values

Config structure:
::

    {
      "category": {
        "friendly": "Human Readable Label",
        "setting_key": {
          "friendly": "Setting Label",
          "type": "<one of the types above>",
          "value": <actual_value>,
          "options": [...],  // for select, multi_select, dropdown_mapping
          "persistent": true/false
        }
      }
    }
"""

# Standard library
from urllib.parse import urlparse, parse_qs

# Third-party
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

# Framework modules - constants and i18n
from ..modules.constants import (
    STATUS_OK,
    STATUS_SERVER_ERROR,
    BOOL_TRUE_VALUES,
    DELIMITER_SPLIT
)
from ..modules.i18n.messages import (
    ERROR_SETTINGS_MANAGER_NOT_INIT,
    ERROR_AUTH_NOT_INIT,
    ERROR_NOT_LOGGED_IN,
    ERROR_SETTING_UNKNOWN_TYPE,
    ERROR_SAVING_USER_OVERRIDE,
    ERROR_SAVING_GLOBAL_CONFIG,
    ERROR_SAVING_SETTINGS,
    MSG_SETTINGS_SAVED,
    MSG_NO_OVERRIDABLE_SETTINGS,
    TEXT_SETTINGS,
    TEXT_CONFIGURATION_SETTINGS,
    TEXT_SETTINGS_CATEGORIES,
    TEXT_CATEGORY,
    TEXT_DESCRIPTION,
    TEXT_SETTINGS_COUNT,
    TEXT_ACTIONS,
    TEXT_SETTING,
    TEXT_TYPE,
    TEXT_VALUE,
    TEXT_USER_OVERRIDABLE,
    TEXT_USER_FRAMEWORK_SETTINGS,
    TEXT_VIEW_SETTINGS,
    TEXT_SAVE_SETTINGS,
    TEXT_CONFIGURATION_OPTIONS
)

# Framework modules - core functionality
from ..modules import displayer
from ..modules.auth import require_admin, require_login
from ..modules.log.logger_factory import get_logger
from ..modules.utilities import util_post_to_json, util_post_unmap

logger = get_logger(__name__)

bp = Blueprint("settings", __name__, url_prefix="/settings")

# For testing: bypass auth in displayer
_bypass_AUTH = False

# =============================================================================
# Domain-Specific Constants (Settings Module)
# =============================================================================

# Configuration and URLs
CONFIG_WRAPPER = "settings"
URL_PREFIX_OVERRIDABLE = "overridable_"
FORM_FIELD_CSRF_TOKEN = "csrf_token"
FORM_FIELD_SAVE = "save"

# Setting Type Names (domain-specific to settings module)
TYPE_STRING = "string"
TYPE_INT = "int"
TYPE_INTEGER = "integer"
TYPE_NUMBER = "number"
TYPE_BOOL = "bool"
TYPE_BOOLEAN = "boolean"
TYPE_SELECT = "select"
TYPE_DROPDOWN = "dropdown"
TYPE_MULTI_SELECT = "multi_select"
TYPE_MULTISELECT = "multiselect"
TYPE_TEXT_LIST = "text_list"
TYPE_LIST = "list"
TYPE_ARRAY = "array"
TYPE_KEY_VALUE = "key_value_pairs"
TYPE_DICT = "dict"
TYPE_OBJECT = "object"
TYPE_DROPDOWN_MAPPING = "dropdown_mapping"
TYPE_ICON = "icon"
TYPE_SERIAL_PORT = "serial_port"

# Type Color Scheme (UI-specific mapping)
TYPE_COLORS = {
    TYPE_STRING: displayer.BSstyle.INFO,
    TYPE_INT: displayer.BSstyle.PRIMARY,
    TYPE_BOOL: displayer.BSstyle.SUCCESS,
    TYPE_SELECT: displayer.BSstyle.WARNING,
    TYPE_TEXT_LIST: displayer.BSstyle.SECONDARY,
    TYPE_KEY_VALUE: displayer.BSstyle.SECONDARY,
}

# Setting Metadata Keys
METADATA_FRIENDLY = "friendly"
METADATA_TYPE = "type"
METADATA_VALUE = "value"
METADATA_OPTIONS = "options"
METADATA_OVERRIDABLE = "overridable_by_user"
METADATA_DESCRIPTION = "_description"
METADATA_CATEGORY_DESCRIPTION = "_category_description"

# Route Links (internal references)
TEXT_SETTINGS_LINK = "settings.index"
TEXT_FRAMEWORK_SETTINGS_LINK = "settings.user_view"

# Table Column Definitions
COLUMNS_CATEGORY_TABLE = [TEXT_CATEGORY, TEXT_DESCRIPTION, TEXT_SETTINGS_COUNT, TEXT_ACTIONS]
COLUMNS_SETTING_ADMIN = [TEXT_SETTING, TEXT_TYPE, TEXT_VALUE, TEXT_USER_OVERRIDABLE]
COLUMNS_SETTING_USER = [TEXT_SETTING, TEXT_TYPE, TEXT_VALUE]

# Serial Port Configuration
SERIAL_PORT_NONE = "None"


def get_manager():
    """Get the global settings manager instance (initialized at startup)."""
    from ..modules.settings import settings_manager
    return settings_manager


@bp.route("/", methods=["GET"])
@require_admin()
def index():
    """Settings dashboard - main entry point."""
    manager = get_manager()
    if not manager:
        return ERROR_SETTINGS_MANAGER_NOT_INIT, STATUS_SERVER_ERROR
    
    disp = displayer.Displayer()
    disp.add_generic(TEXT_SETTINGS, display=False)
    disp.set_title(TEXT_CONFIGURATION_SETTINGS)
    
    # Add breadcrumbs
    disp.add_breadcrumb(TEXT_SETTINGS, TEXT_SETTINGS_LINK, [])
    
    # Categories overview in a nice table
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle=TEXT_SETTINGS_CATEGORIES
    ))
    
    # Create simple table layout (no DataTables)
    layout_id = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE,
        columns=COLUMNS_CATEGORY_TABLE
    ))
    
    categories = manager.list_categories()
    for line, category in enumerate(categories):
        friendly = manager.get_category_friendly(category)
        settings = manager.get_category(category)
        count = len(settings)
        
        # Category name with icon
        disp.add_display_item(
            displayer.DisplayerItemText(f"<strong>{friendly}</strong>"),
            column=0, line=line, layout_id=layout_id
        )
        
        # Description (could be enhanced with metadata from manager)
        disp.add_display_item(
            displayer.DisplayerItemText(f"{TEXT_CONFIGURATION_OPTIONS} {friendly.lower()}"),
            column=1, line=line, layout_id=layout_id
        )
        
        # Settings count badge
        badge_style = displayer.BSstyle.INFO if count > 0 else displayer.BSstyle.SECONDARY
        disp.add_display_item(
            displayer.DisplayerItemBadge(f"{count} {TEXT_SETTINGS.lower()}", badge_style),
            column=2, line=line, layout_id=layout_id
        )
        
        # Action button - edit only (inline editing, no separate view page)
        disp.add_display_item(
            displayer.DisplayerItemActionButtons(
                id=f"actions_{category}",
                edit_url=f"/settings/view?category={category}",
                style="icons",
                size="sm"
            ),
            column=3, line=line, layout_id=layout_id
        )
    
    return render_template("base_content.j2", content=disp.display(bypass_auth=_bypass_AUTH), target="")


@bp.route("/view", methods=["GET", "POST"])
@require_admin()
def view():
    """View and edit settings with inline form."""
    return _view_settings(user_mode=False)


@bp.route("/user_view", methods=["GET", "POST"])
@require_login()
def user_view():
    """View and edit user-overridable settings with inline form (no admin required)."""
    return _view_settings(user_mode=True)


def _render_setting_row(disp, layout_id, line, category, key, setting, user_mode, user_overrides):
    """Helper function to render a single setting row in a table."""
    is_overridable = setting.get(METADATA_OVERRIDABLE, False)
    
    # In user mode, skip non-overridable settings
    if user_mode and not is_overridable:
        return False  # Signal that row was not rendered
    
    friendly = setting.get(METADATA_FRIENDLY, key)
    setting_type = setting.get(METADATA_TYPE, TYPE_STRING)
    value = setting.get(METADATA_VALUE)
    options = setting.get(METADATA_OPTIONS, [])
    
    # In user mode, use user's override value if present
    full_key = f"{category}.{key}"
    if user_mode and full_key in user_overrides:
        value = user_overrides[full_key]
    
    # Form field name
    form_field_name = full_key
    
    # Setting name
    disp.add_display_item(
        displayer.DisplayerItemText(f"<strong>{friendly}</strong>"),
        column=0, line=line, layout_id=layout_id
    )
    
    # Type badge
    type_color = TYPE_COLORS.get(setting_type, displayer.BSstyle.SECONDARY)
    disp.add_display_item(
        displayer.DisplayerItemBadge(setting_type, type_color),
        column=1, line=line, layout_id=layout_id
    )
    
    # Value - render appropriate input widget based on type
    if setting_type in (TYPE_BOOL, TYPE_BOOLEAN):
        # Boolean - checkbox
        disp.add_display_item(
            displayer.DisplayerItemInputCheckbox(form_field_name, "", value if isinstance(value, bool) else False),
            column=2, line=line, layout_id=layout_id
        )
    elif setting_type in (TYPE_INT, TYPE_INTEGER, TYPE_NUMBER):
        # Integer/Number - numeric input
        disp.add_display_item(
            displayer.DisplayerItemInputNumeric(form_field_name, "", value if isinstance(value, (int, float)) else 0),
            column=2, line=line, layout_id=layout_id
        )
    elif setting_type in (TYPE_SELECT, TYPE_DROPDOWN):
        # Single select dropdown
        disp.add_display_item(
            displayer.DisplayerItemInputSelect(form_field_name, "", value, options or []),
            column=2, line=line, layout_id=layout_id
        )
    elif setting_type in (TYPE_MULTI_SELECT, TYPE_MULTISELECT):
        # Multi-select checkboxes
        disp.add_display_item(
            displayer.DisplayerItemInputMultiSelect(form_field_name, "", value if isinstance(value, list) else [], options or []),
            column=2, line=line, layout_id=layout_id
        )
    elif setting_type in (TYPE_TEXT_LIST, TYPE_LIST, TYPE_ARRAY):
        # User-editable list
        disp.add_display_item(
            displayer.DisplayerItemInputTextList(form_field_name, "", value if isinstance(value, list) else []),
            column=2, line=line, layout_id=layout_id
        )
    elif setting_type in (TYPE_KEY_VALUE, TYPE_DICT, TYPE_OBJECT):
        # Key-value pairs
        value_list = [[k, v] for k, v in (value or {}).items()] if isinstance(value, dict) else []
        disp.add_display_item(
            displayer.DisplayerItemInputKeyValue(form_field_name, "", value_list),
            column=2, line=line, layout_id=layout_id
        )
    elif setting_type == TYPE_DROPDOWN_MAPPING:
        # Dropdown with custom values
        value_list = [[k, v] for k, v in (value or {}).items()] if isinstance(value, dict) else []
        disp.add_display_item(
            displayer.DisplayerItemInputDropdownValue(form_field_name, "", value_list, options or []),
            column=2, line=line, layout_id=layout_id
        )
    elif setting_type == TYPE_ICON:
        # Icon selector
        disp.add_display_item(
            displayer.DisplayerItemInputStringIcon(form_field_name, "", value if isinstance(value, str) else ""),
            column=2, line=line, layout_id=layout_id
        )
    elif setting_type == TYPE_SERIAL_PORT:
        # Serial port selector
        try:
            import serial.tools.list_ports
            serial_ports = [port.device for port in serial.tools.list_ports.comports()]
        except ImportError:
            serial_ports = options or [SERIAL_PORT_NONE]
        disp.add_display_item(
            displayer.DisplayerItemInputSelect(form_field_name, "", value, serial_ports),
            column=2, line=line, layout_id=layout_id
        )
    elif setting_type == TYPE_STRING:
        # Explicit string type
        disp.add_display_item(
            displayer.DisplayerItemInputString(form_field_name, "", value if isinstance(value, str) else str(value or "")),
            column=2, line=line, layout_id=layout_id
        )
    else:
        # Unknown type - log warning and render as string with alert
        logger.warning(f"{ERROR_SETTING_UNKNOWN_TYPE} '{setting_type}' for {category}.{key}, rendering as string input")
        disp.add_display_item(
            displayer.DisplayerItemInputString(form_field_name, "", str(value or "")),
            column=2, line=line, layout_id=layout_id
        )
    
    # Overridable checkbox (only in admin mode)
    if not user_mode:
        checkbox_name = f"{URL_PREFIX_OVERRIDABLE}{full_key}"
        disp.add_display_item(
            displayer.DisplayerItemInputCheckbox(checkbox_name, "", is_overridable),
            column=3, line=line, layout_id=layout_id
        )
    
    return True  # Signal that row was rendered


def _view_settings(user_mode=False):
    """Internal function to view and edit settings with optional user filtering."""
    manager = get_manager()
    if not manager:
        return ERROR_SETTINGS_MANAGER_NOT_INIT, STATUS_SERVER_ERROR
    category_filter = request.args.get("category")
    
    # If POST and no category in args, try to get it from referrer
    if request.method == "POST" and not category_filter and request.referrer:
        parsed = urlparse(request.referrer)
        query_params = parse_qs(parsed.query)
        if 'category' in query_params:
            category_filter = query_params['category'][0]
    
    # Handle POST - save settings
    if request.method == "POST":
        if user_mode:
            # Save to user overrides
            try:
                from ..modules.auth import auth_manager
                if not auth_manager:
                    flash(ERROR_AUTH_NOT_INIT, "danger")
                    return redirect(url_for('common.login'))
                current_user = auth_manager.get_current_user()
                if not current_user:
                    flash(ERROR_NOT_LOGGED_IN, "danger")
                    return redirect(url_for('common.login'))
                
                # Use util_post_to_json to parse form data
                form_data = util_post_to_json(dict(request.form))
                
                # Strip module prefix
                settings_data = {}
                for key, value in form_data.items():
                    if isinstance(value, dict) and key not in [FORM_FIELD_CSRF_TOKEN, FORM_FIELD_SAVE]:
                        settings_data.update(value)
                    elif key not in [FORM_FIELD_CSRF_TOKEN, FORM_FIELD_SAVE]:
                        settings_data[key] = value
                
                # Apply util_post_unmap to convert mapleft/mapright to dicts
                wrapped_data = {CONFIG_WRAPPER: settings_data}
                unmapped_data = util_post_unmap(wrapped_data)
                settings_data = unmapped_data.get(CONFIG_WRAPPER, settings_data)
                
                # Build list of all expected bool settings for checkbox handling
                # Unchecked checkboxes don't send data, so we need to default them to False
                all_bool_settings = set()
                if category_filter:
                    categories_to_check = [category_filter]
                else:
                    categories_to_check = manager.list_categories()
                
                for cat in categories_to_check:
                    cat_data = manager.get_category(cat)
                    for key, setting in cat_data.items():  # type: ignore
                        if key == METADATA_FRIENDLY or not isinstance(setting, dict):
                            continue
                        if METADATA_TYPE in setting:
                            setting_type = setting[METADATA_TYPE]
                            if setting_type in [TYPE_BOOL, TYPE_BOOLEAN]:
                                full_key = f"{cat}.{key}"
                                all_bool_settings.add(full_key)
                        else:
                            # Check nested subcategories
                            for subkey, subsetting in setting.items():
                                if subkey in [METADATA_FRIENDLY, METADATA_DESCRIPTION] or not isinstance(subsetting, dict):
                                    continue
                                if METADATA_TYPE in subsetting:
                                    setting_type = subsetting[METADATA_TYPE]
                                    if setting_type in [TYPE_BOOL, TYPE_BOOLEAN]:
                                        full_key = f"{cat}.{key}.{subkey}"
                                        all_bool_settings.add(full_key)
                
                # Track which settings were actually processed
                processed_settings = set()
                
                # Process each setting
                for category, category_data in settings_data.items():
                    if category in [FORM_FIELD_CSRF_TOKEN, FORM_FIELD_SAVE]:
                        continue
                    
                    if not isinstance(category_data, dict):
                        continue
                    
                    for setting_key, value in category_data.items():
                        if setting_key in [FORM_FIELD_CSRF_TOKEN, FORM_FIELD_SAVE]:
                            continue
                        
                        full_key = f"{category}.{setting_key}"
                        processed_settings.add(full_key)
                        
                        # Get setting metadata to determine expected type
                        try:
                            parts = full_key.split('.')
                            category_name = parts[0]
                            setting_name = '.'.join(parts[1:])
                            all_settings = manager.get_all_settings()
                            
                            if category_name in all_settings:
                                setting_data = all_settings[category_name]
                                for part in setting_name.split('.'):
                                    if isinstance(setting_data, dict) and part in setting_data:
                                        setting_data = setting_data[part]
                                    else:
                                        setting_data = None
                                        break
                                
                                if setting_data and isinstance(setting_data, dict):
                                    setting_type = setting_data.get(METADATA_TYPE, TYPE_STRING)
                                    
                                    # Type conversion based on setting type
                                    if setting_type in [TYPE_INT, TYPE_INTEGER, TYPE_NUMBER]:
                                        try:
                                            value = int(value)
                                        except (ValueError, TypeError):
                                            value = setting_data.get(METADATA_VALUE, 0)
                                    elif setting_type in [TYPE_BOOL, TYPE_BOOLEAN]:
                                        value = value in BOOL_TRUE_VALUES
                                    elif setting_type in [TYPE_TEXT_LIST, TYPE_LIST, TYPE_ARRAY]:
                                        # util_post_to_json may already parse as list
                                        if isinstance(value, list):
                                            pass  # Already a list
                                        elif isinstance(value, str):
                                            value = [v.strip() for v in value.split(DELIMITER_SPLIT) if v.strip()]  # Split and filter empty
                                        else:
                                            value = []
                                    elif setting_type in [TYPE_MULTI_SELECT, TYPE_MULTISELECT]:
                                        # Multi-select uses checkbox format: key_value: on
                                        # util_post_to_json already parsed this as list
                                        if isinstance(value, list):
                                            pass  # Already a list
                                        elif isinstance(value, str):
                                            value = [v.strip() for v in value.split(DELIMITER_SPLIT) if v.strip()]
                                        else:
                                            value = []
                                    # For dicts (key_value_pairs, dropdown_mapping), already parsed correctly
                                    
                                    # Save to user override
                                    if auth_manager:
                                        auth_manager.set_user_framework_override(current_user, full_key, value)
                                        
                                        # Special handling for language change - update session immediately
                                        if full_key == "framework_ui.language":
                                            session['locale'] = value
                                            logger.info(f"[i18n] Language changed to '{value}' for user '{current_user}', session updated")
                                            print(f"[i18n] *** SESSION UPDATED: locale = '{value}' for user '{current_user}'")
                                            print(f"[i18n] *** Session dict: {dict(session)}")
                        except Exception:
                            logger.exception(ERROR_SAVING_USER_OVERRIDE)
                
                # Handle unchecked checkboxes - set to False
                for bool_key in all_bool_settings:
                    if bool_key not in processed_settings:
                        if auth_manager:
                            auth_manager.set_user_framework_override(current_user, bool_key, False)
                
                flash(MSG_SETTINGS_SAVED, "success")
                # Stay on the same page - rebuild URL with category if present
                if category_filter:
                    return redirect(url_for('settings.user_view', category=category_filter))
                else:
                    return redirect(url_for('settings.user_view'))
            except Exception as e:
                logger.exception(ERROR_SAVING_SETTINGS)
                flash(f"{ERROR_SAVING_SETTINGS}: {str(e)}", "danger")
        else:
            # Admin mode - save to global config
            try:
                # Use util_post_to_json to parse form data
                form_data = util_post_to_json(dict(request.form))
                
                # Strip module prefix (e.g., "View Settings" or "My Framework Settings")
                # The form_data will have structure: {'Module Name': {'category': {'setting': value}}}
                # We need to extract just the settings part
                settings_data = {}
                for key, value in form_data.items():
                    if isinstance(value, dict) and key not in [FORM_FIELD_CSRF_TOKEN, FORM_FIELD_SAVE]:
                        # This is the module wrapper, extract its contents
                        settings_data.update(value)
                    elif key not in [FORM_FIELD_CSRF_TOKEN, FORM_FIELD_SAVE]:
                        # Direct setting (shouldn't happen but handle it)
                        settings_data[key] = value
                
                # Apply util_post_unmap to convert mapleft/mapright to dicts
                # util_post_unmap expects structure: {module: {item: {cat: {mapleft0: x, mapright0: y}}}}
                # We need to wrap our data appropriately
                wrapped_data = {CONFIG_WRAPPER: settings_data}
                unmapped_data = util_post_unmap(wrapped_data)
                settings_data = unmapped_data.get(CONFIG_WRAPPER, settings_data)
                
                # Track overridable checkboxes
                overridable_keys = set()
                
                # Extract overridable checkboxes
                # util_post_to_json parses checkboxes like: overridable_category.setting: on
                # As: {"overridable_category": {"setting": "1"}}
                # We need to reconstruct the full keys as "category.setting"
                for key in list(settings_data.keys()):
                    if key.startswith(URL_PREFIX_OVERRIDABLE):
                        # Extract the category name (remove "overridable_" prefix)
                        category = key.replace(URL_PREFIX_OVERRIDABLE, "")
                        
                        if isinstance(settings_data[key], dict):
                            # Dictionary of setting_name: "1" for checked boxes
                            for setting_name in settings_data[key].keys():
                                full_key = f"{category}.{setting_name}"
                                overridable_keys.add(full_key)
                            settings_data.pop(key)
                        elif isinstance(settings_data[key], list):
                            # List format (alternative parsing)
                            overridable_keys.update(settings_data[key])
                            settings_data.pop(key)
                
                # Build list of all expected bool settings for checkbox handling
                all_bool_settings = set()
                if category_filter:
                    categories_to_check = [category_filter]
                else:
                    categories_to_check = manager.list_categories()
                
                for cat in categories_to_check:
                    cat_data = manager.get_category(cat)
                    for key, setting in cat_data.items():  # type: ignore
                        if key == METADATA_FRIENDLY or not isinstance(setting, dict):
                            continue
                        if METADATA_TYPE in setting:
                            setting_type = setting[METADATA_TYPE]
                            if setting_type in [TYPE_BOOL, TYPE_BOOLEAN]:
                                full_key = f"{cat}.{key}"
                                all_bool_settings.add(full_key)
                        else:
                            # Check nested subcategories
                            for subkey, subsetting in setting.items():
                                if subkey in [METADATA_FRIENDLY, METADATA_DESCRIPTION] or not isinstance(subsetting, dict):
                                    continue
                                if METADATA_TYPE in subsetting:
                                    setting_type = subsetting[METADATA_TYPE]
                                    if setting_type in [TYPE_BOOL, TYPE_BOOLEAN]:
                                        full_key = f"{cat}.{key}.{subkey}"
                                        all_bool_settings.add(full_key)
                
                # Track which settings were actually processed
                processed_settings = set()
                
                # Process each setting
                for category, category_data in settings_data.items():
                    if category in [FORM_FIELD_CSRF_TOKEN, FORM_FIELD_SAVE]:
                        continue
                    
                    if not isinstance(category_data, dict):
                        continue
                    
                    for setting_key, value in category_data.items():
                        if setting_key in [FORM_FIELD_CSRF_TOKEN, FORM_FIELD_SAVE]:
                            continue
                        
                        full_key = f"{category}.{setting_key}"
                        processed_settings.add(full_key)
                        
                        # Get setting metadata to determine expected type
                        try:
                            parts = full_key.split('.')
                            category_name = parts[0]
                            setting_name = '.'.join(parts[1:])
                            all_settings = manager.get_all_settings()
                            
                            if category_name in all_settings:
                                setting_data = all_settings[category_name]
                                for part in setting_name.split('.'):
                                    if isinstance(setting_data, dict) and part in setting_data:
                                        setting_data = setting_data[part]
                                    else:
                                        setting_data = None
                                        break
                                
                                if setting_data and isinstance(setting_data, dict):
                                    setting_type = setting_data.get(METADATA_TYPE, TYPE_STRING)
                                    
                                    # Type conversion based on setting type
                                    if setting_type in [TYPE_INT, TYPE_INTEGER, TYPE_NUMBER]:
                                        try:
                                            value = int(value)
                                        except (ValueError, TypeError):
                                            value = setting_data.get(METADATA_VALUE, 0)
                                    elif setting_type in [TYPE_BOOL, TYPE_BOOLEAN]:
                                        value = value in BOOL_TRUE_VALUES
                                    elif setting_type in [TYPE_TEXT_LIST, TYPE_LIST, TYPE_ARRAY]:
                                        # util_post_to_json may already parse as list
                                        if isinstance(value, list):
                                            pass  # Already a list
                                        elif isinstance(value, str):
                                            value = [v.strip() for v in value.split(DELIMITER_SPLIT) if v.strip()]  # Split and filter empty
                                        else:
                                            value = []
                                    elif setting_type in [TYPE_MULTI_SELECT, TYPE_MULTISELECT]:
                                        # Multi-select uses checkbox format: key_value: on
                                        # util_post_to_json already parsed this as list
                                        if isinstance(value, list):
                                            pass  # Already a list
                                        elif isinstance(value, str):
                                            value = [v.strip() for v in value.split(DELIMITER_SPLIT) if v.strip()]
                                        else:
                                            value = []
                                    # For dicts (key_value_pairs, dropdown_mapping), already parsed correctly
                                    
                                    # Save to global config
                                    manager.set_setting(full_key, value)
                                    
                                    # Special handling for language change - update session immediately
                                    if full_key == "framework_ui.language":
                                        session['locale'] = value
                                        logger.info(f"[i18n] Global language changed to '{value}', session updated")
                        except Exception:
                            logger.exception(ERROR_SAVING_GLOBAL_CONFIG)
                
                # Handle unchecked checkboxes - set to False
                for bool_key in all_bool_settings:
                    if bool_key not in processed_settings:
                        manager.set_setting(bool_key, False)
                
                # Handle overridable checkboxes
                for setting_key in overridable_keys:
                    manager.set_setting_metadata(setting_key, METADATA_OVERRIDABLE, True)
                
                # Handle unchecked overridable checkboxes (set to False)
                # Need to check both direct settings and subcategory settings
                all_settings = manager.get_all_settings()
                for category in all_settings:  # type: ignore
                    category_data = all_settings[category]
                    for key in category_data:  # type: ignore
                        if key == METADATA_FRIENDLY or not isinstance(category_data[key], dict):
                            continue
                        
                        # Check if this is a direct setting (has 'type' field)
                        if METADATA_TYPE in category_data[key]:
                            full_key = f"{category}.{key}"
                            if full_key not in overridable_keys:
                                manager.set_setting_metadata(full_key, METADATA_OVERRIDABLE, False)
                        else:
                            # This is a subcategory, check its nested settings
                            subcat_data = category_data[key]
                            if isinstance(subcat_data, dict):
                                for subkey in subcat_data:  # type: ignore
                                    if subkey in [METADATA_FRIENDLY, METADATA_DESCRIPTION] or not isinstance(subcat_data[subkey], dict):
                                        continue
                                    if METADATA_TYPE in subcat_data[subkey]:
                                        full_key = f"{category}.{key}.{subkey}"
                                        if full_key not in overridable_keys:
                                            manager.set_setting_metadata(full_key, METADATA_OVERRIDABLE, False)
                
                manager.save()
                flash(MSG_SETTINGS_SAVED, "success")
                # Stay on the same page - rebuild URL with category if present
                if category_filter:
                    return redirect(url_for('settings.view', category=category_filter))
                else:
                    return redirect(url_for('settings.view'))
            except Exception as e:
                logger.exception(ERROR_SAVING_SETTINGS)
                flash(f"{ERROR_SAVING_SETTINGS}: {str(e)}", "danger")
    
    disp = displayer.Displayer()
    
    if user_mode:
        disp.add_generic(TEXT_USER_FRAMEWORK_SETTINGS, display=False)
        disp.set_title(TEXT_USER_FRAMEWORK_SETTINGS)
        disp.add_breadcrumb(TEXT_USER_FRAMEWORK_SETTINGS, TEXT_FRAMEWORK_SETTINGS_LINK, [])
    else:
        disp.add_generic(TEXT_VIEW_SETTINGS, display=False)
        disp.set_title(TEXT_VIEW_SETTINGS)
        disp.add_breadcrumb(TEXT_SETTINGS, TEXT_SETTINGS_LINK, [])
        if category_filter:
            disp.add_breadcrumb(f"{TEXT_VIEW_SETTINGS} {manager.get_category_friendly(category_filter)}", "settings.view", [f"category={category_filter}"])
        else:
            disp.add_breadcrumb(f"{TEXT_VIEW_SETTINGS} All {TEXT_SETTINGS.lower()}", "settings.view", [])
    
    all_settings = manager.get_all_settings()
    
    # Filter by category if specified
    categories_to_show = [category_filter] if category_filter else manager.list_categories()
    
    # Get user overrides if in user mode
    user_overrides = {}
    if user_mode:
        try:
            from ..modules.auth import auth_manager
            if auth_manager:
                current_user = auth_manager.get_current_user()
                if current_user:
                    user_prefs = auth_manager.get_user_prefs(current_user)
                    user_overrides = user_prefs.get("framework_overrides", {})
        except Exception:
            pass
    
    has_overridable = False
    for category in categories_to_show:
        if category not in all_settings:
            continue
            
        category_data = all_settings[category]
        friendly_name = category_data.get(METADATA_FRIENDLY, category)
        
        # In user mode, check if category has any overridable settings
        if user_mode:
            has_overridable_in_category = any(
                setting.get(METADATA_OVERRIDABLE, False)
                for key, setting in category_data.items()  # type: ignore
                if key != METADATA_FRIENDLY and isinstance(setting, dict)
            )
            if not has_overridable_in_category:
                continue  # Skip category in user mode
        
        has_overridable = True
        
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [12], subtitle=friendly_name, spacing=2
        ))
        
        # Show category description if present
        if METADATA_CATEGORY_DESCRIPTION in category_data:
            desc_data = category_data[METADATA_CATEGORY_DESCRIPTION]
            if isinstance(desc_data, dict) and METADATA_VALUE in desc_data:
                disp.add_display_item(
                    displayer.DisplayerItemAlert(desc_data[METADATA_VALUE], displayer.BSstyle.INFO),
                    column=0
                )
        
        # Separate subcategories from direct settings
        subcategories = {}
        direct_settings = {}
        
        for key, setting in category_data.items():  # type: ignore
            if key in [METADATA_FRIENDLY, METADATA_CATEGORY_DESCRIPTION] or not isinstance(setting, dict):
                continue
            
            # Check if this is a subcategory (has nested settings with 'type' field)
            if METADATA_TYPE not in setting and METADATA_FRIENDLY in setting:
                # This is a subcategory
                subcategories[key] = setting
            elif METADATA_TYPE in setting:
                # This is a direct setting
                direct_settings[key] = setting
        
        # Render direct settings first (if any)
        if direct_settings:
            columns = COLUMNS_SETTING_USER if user_mode else COLUMNS_SETTING_ADMIN
            
            layout_id = disp.add_master_layout(displayer.DisplayerLayout(
                displayer.Layouts.TABLE,
                columns=columns
            ))
            
            line = 0
            for key, setting in direct_settings.items():
                _render_setting_row(disp, layout_id, line, category, key, setting, user_mode, user_overrides)
                line += 1
        
        # Render each subcategory
        for subcat_key, subcat_data in subcategories.items():
            subcat_friendly = subcat_data.get(METADATA_FRIENDLY, subcat_key)
            
            # Add subcategory subtitle
            disp.add_master_layout(displayer.DisplayerLayout(
                displayer.Layouts.VERTICAL, [12], subtitle=f"{subcat_friendly}", spacing=1
            ))
            
            # Show subcategory description if present
            if METADATA_DESCRIPTION in subcat_data:
                desc_data = subcat_data[METADATA_DESCRIPTION]
                if isinstance(desc_data, dict) and METADATA_VALUE in desc_data:
                    disp.add_display_item(
                        displayer.DisplayerItemAlert(desc_data[METADATA_VALUE], displayer.BSstyle.LIGHT),
                        column=0
                    )
            
            # Create table for subcategory settings
            columns = COLUMNS_SETTING_USER if user_mode else COLUMNS_SETTING_ADMIN
            
            layout_id = disp.add_master_layout(displayer.DisplayerLayout(
                displayer.Layouts.TABLE,
                columns=columns
            ))
            
            line = 0
            for key, setting in subcat_data.items():
                if key in [METADATA_FRIENDLY, METADATA_DESCRIPTION] or not isinstance(setting, dict):
                    continue
                
                if METADATA_TYPE not in setting:
                    continue  # Skip non-setting items
                
                # Use full key including subcategory: category.subcat_key.key
                if _render_setting_row(disp, layout_id, line, category, f"{subcat_key}.{key}", setting, user_mode, user_overrides):
                    line += 1
    
    # In user mode, show message if no overridable settings found
    if user_mode and not has_overridable:
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [12]
        ))
        disp.add_display_item(
            displayer.DisplayerItemAlert(
                MSG_NO_OVERRIDABLE_SETTINGS,
                displayer.BSstyle.INFO
            ),
            column=0
        )
    else:
        # Add Save button
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [12], alignment=[displayer.BSalign.R], spacing=2
        ))
        disp.add_display_item(displayer.DisplayerItemButton(FORM_FIELD_SAVE, TEXT_SAVE_SETTINGS), 0)
    
    # Set form target - displayer will handle the current URL automatically
    target = "settings.user_view" if user_mode else "settings.view"
    return render_template("base_content.j2", content=disp.display(bypass_auth=_bypass_AUTH), target=target)

