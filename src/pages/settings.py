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

from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..modules.settings import SettingsManager
from ..modules import displayer
from .common import require_admin
import os


bp = Blueprint("settings", __name__, url_prefix="/settings")

# Global settings manager
_settings_manager = None

# For testing: bypass auth in displayer
_bypass_auth = False


def get_manager():
    """Get or create settings manager instance and merge optional configs based on site_conf."""
    global _settings_manager
    if _settings_manager is None:
        from ..modules import site_conf
        
        config_path = os.path.join(os.getcwd(), "config.json")
        _settings_manager = SettingsManager(config_path)
        _settings_manager.load()
        
        # Merge optional configurations based on enabled features
        if site_conf.site_conf_obj:
            _settings_manager.merge_optional_configs(site_conf.site_conf_obj)
    return _settings_manager


@bp.route("/", methods=["GET"])
@require_admin
def index():
    """Settings dashboard - main entry point."""
    manager = get_manager()
    
    disp = displayer.Displayer()
    disp.add_generic("Settings", display=False)
    disp.set_title("Configuration Settings")
    
    # Add breadcrumbs
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Settings", "settings.index", [])
    
    # Categories overview in a nice table
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Settings Categories"
    ))
    
    # Create simple table layout (no DataTables)
    layout_id = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE,
        columns=["Category", "Description", "Settings Count", "Actions"]
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
            displayer.DisplayerItemText(f"Configuration options for {friendly.lower()}"),
            column=1, line=line, layout_id=layout_id
        )
        
        # Settings count badge
        badge_style = displayer.BSstyle.INFO if count > 0 else displayer.BSstyle.SECONDARY
        disp.add_display_item(
            displayer.DisplayerItemBadge(f"{count} settings", badge_style),
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
    
    return render_template("base_content.j2", content=disp.display(bypass_auth=_bypass_auth), target="")


@bp.route("/view", methods=["GET", "POST"])
@require_admin
def view():
    """View and edit settings with inline form."""
    return _view_settings(user_mode=False)


@bp.route("/user_view", methods=["GET", "POST"])
def user_view():
    """View and edit user-overridable settings with inline form (no admin required)."""
    return _view_settings(user_mode=True)


def _view_settings(user_mode=False):
    """Internal function to view and edit settings with optional user filtering."""
    manager = get_manager()
    category_filter = request.args.get("category")
    
    # Handle POST - save settings
    if request.method == "POST":
        if user_mode:
            # Save to user overrides
            try:
                from ..modules.auth.auth_manager import auth_manager
                current_user = auth_manager.get_current_user()
                if not current_user:
                    flash("Not logged in", "danger")
                    return redirect(url_for('common.login'))
                
                # Process form data
                for form_key, form_value in request.form.items():
                    if form_key in ["csrf_token", "save"]:
                        continue
                    
                    # Strip ALL module prefixes (can be duplicated)
                    cleaned_key = form_key
                    while '.' in cleaned_key:
                        parts = cleaned_key.split('.', 1)  # Split only on first dot
                        if ' ' in parts[0]:  # First part is a module name with spaces
                            cleaned_key = parts[1] if len(parts) > 1 else cleaned_key
                        else:
                            break  # No more module prefixes
                    
                    # Get setting metadata to determine type
                    try:
                        # Parse key to get category and setting name
                        if '.' in cleaned_key:
                            parts = cleaned_key.split('.')
                            category_name = parts[0]
                            setting_name = '.'.join(parts[1:])
                            all_settings = manager.get_all_settings()
                            
                            if category_name in all_settings:
                                # Navigate to the setting
                                setting_data = all_settings[category_name]
                                for part in setting_name.split('.'):
                                    if isinstance(setting_data, dict) and part in setting_data:
                                        setting_data = setting_data[part]
                                    else:
                                        setting_data = None
                                        break
                                
                                if setting_data and isinstance(setting_data, dict):
                                    setting_type = setting_data.get("type", "string")
                                    
                                    # Type conversion
                                    if setting_type == "int":
                                        try:
                                            form_value = int(form_value)
                                        except (ValueError, TypeError):
                                            form_value = setting_data.get("value", 0)
                                    elif setting_type == "bool":
                                        form_value = form_value in [True, "true", "on", "1", 1]
                                    
                                    # Save to user override
                                    auth_manager.set_user_framework_override(current_user, cleaned_key, form_value)
                    except Exception:
                        pass  # Skip invalid settings
                
                flash("Settings saved successfully!", "success")
                return redirect(url_for('settings.user_view', category=category_filter) if category_filter else url_for('settings.user_view'))
            except Exception as e:
                flash(f"Error saving settings: {str(e)}", "danger")
        else:
            # Admin mode - save to global config
            try:
                # Process form data
                for form_key, form_value in request.form.items():
                    if form_key in ["csrf_token", "save"]:
                        continue
                    
                    # Handle overridable checkbox
                    if form_key.startswith("overridable_"):
                        setting_key = form_key.replace("overridable_", "")
                        manager.set_setting_metadata(setting_key, "overridable_by_user", True)
                        continue
                    
                    # Get setting type to convert value properly
                    try:
                        # Parse key to get category and setting name
                        if '.' in form_key:
                            parts = form_key.split('.')
                            category_name = parts[0]
                            setting_name = '.'.join(parts[1:])
                            all_settings = manager.get_all_settings()
                            
                            if category_name in all_settings:
                                # Navigate to the setting
                                setting_data = all_settings[category_name]
                                for part in setting_name.split('.'):
                                    if isinstance(setting_data, dict) and part in setting_data:
                                        setting_data = setting_data[part]
                                    else:
                                        setting_data = None
                                        break
                                
                                if setting_data and isinstance(setting_data, dict):
                                    setting_type = setting_data.get("type", "string")
                                    
                                    # Type conversion
                                    if setting_type == "int":
                                        try:
                                            form_value = int(form_value)
                                        except (ValueError, TypeError):
                                            form_value = setting_data.get("value", 0)
                                    elif setting_type == "bool":
                                        form_value = form_value in [True, "true", "on", "1", 1]
                                    
                                    # Save to global config
                                    manager.set_setting(form_key, form_value)
                    except Exception:
                        pass  # Skip invalid settings
                
                # Handle unchecked overridable checkboxes (set to False)
                all_settings = manager.get_all_settings()
                for category in all_settings:
                    category_data = all_settings[category]
                    for key in category_data:
                        if key == "friendly" or not isinstance(category_data[key], dict):
                            continue
                        full_key = f"{category}.{key}"
                        checkbox_name = f"overridable_{full_key}"
                        if checkbox_name not in request.form:
                            manager.set_setting_metadata(full_key, "overridable_by_user", False)
                
                manager.save()
                flash("Settings saved successfully!", "success")
                return redirect(url_for('settings.view', category=category_filter) if category_filter else url_for('settings.view'))
            except Exception as e:
                flash(f"Error saving settings: {str(e)}", "danger")
    
    disp = displayer.Displayer()
    
    if user_mode:
        disp.add_generic("My Framework Settings", display=False)
        disp.set_title("My Framework Settings")
        disp.add_breadcrumb("Home", "demo.index", [])
        disp.add_breadcrumb("Framework Settings", "settings.user_view", [])
    else:
        disp.add_generic("View Settings", display=False)
        disp.set_title("View Settings")
        disp.add_breadcrumb("Home", "demo.index", [])
        disp.add_breadcrumb("Settings", "settings.index", [])
        if category_filter:
            disp.add_breadcrumb(f"View {manager.get_category_friendly(category_filter)}", "settings.view", [f"category={category_filter}"])
        else:
            disp.add_breadcrumb("View All Settings", "settings.view", [])
    
    all_settings = manager.get_all_settings()
    
    # Filter by category if specified
    categories_to_show = [category_filter] if category_filter else manager.list_categories()
    
    # Get user overrides if in user mode
    user_overrides = {}
    if user_mode:
        try:
            from ..modules.auth.auth_manager import auth_manager
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
        friendly_name = category_data.get("friendly", category)
        
        # In user mode, check if category has any overridable settings
        if user_mode:
            has_overridable_in_category = any(
                setting.get("overridable_by_user", False)
                for key, setting in category_data.items()
                if key != "friendly" and isinstance(setting, dict)
            )
            if not has_overridable_in_category:
                continue  # Skip category in user mode
        
        has_overridable = True
        
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [12], subtitle=friendly_name, spacing=2
        ))
        
        # Create simple table for this category with inline editing
        if user_mode:
            columns = ["Setting", "Type", "Value"]
        else:
            columns = ["Setting", "Type", "Value", "User Overridable"]
        
        layout_id = disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.TABLE,
            columns=columns
        ))
        
        line = 0
        for key, setting in category_data.items():
            if key == "friendly" or not isinstance(setting, dict):
                continue
            
            is_overridable = setting.get("overridable_by_user", False)
            
            # In user mode, skip non-overridable settings
            if user_mode and not is_overridable:
                continue
            
            friendly = setting.get("friendly", key)
            setting_type = setting.get("type", "string")
            value = setting.get("value")
            options = setting.get("options", [])
            
            # In user mode, use user's override value if present
            full_key = f"{category}.{key}"
            if user_mode and full_key in user_overrides:
                value = user_overrides[full_key]
            
            # Form field name - just use the key, Displayer will add module prefix
            form_field_name = full_key
            
            # Setting name
            disp.add_display_item(
                displayer.DisplayerItemText(f"<strong>{friendly}</strong>"),
                column=0, line=line, layout_id=layout_id
            )
            
            # Type badge
            type_colors = {
                "string": displayer.BSstyle.INFO,
                "int": displayer.BSstyle.PRIMARY,
                "bool": displayer.BSstyle.SUCCESS,
                "select": displayer.BSstyle.WARNING,
                "text_list": displayer.BSstyle.SECONDARY,
                "key_value_pairs": displayer.BSstyle.SECONDARY,
            }
            type_color = type_colors.get(setting_type, displayer.BSstyle.SECONDARY)
            disp.add_display_item(
                displayer.DisplayerItemBadge(setting_type, type_color),
                column=1, line=line, layout_id=layout_id
            )
            
            # Value - render appropriate input widget
            if setting_type == "bool":
                disp.add_display_item(
                    displayer.DisplayerItemInputCheckbox(form_field_name, "", value or False),
                    column=2, line=line, layout_id=layout_id
                )
            elif setting_type == "int":
                disp.add_display_item(
                    displayer.DisplayerItemInputNumeric(form_field_name, "", value or 0),
                    column=2, line=line, layout_id=layout_id
                )
            elif setting_type == "select":
                disp.add_display_item(
                    displayer.DisplayerItemInputSelect(form_field_name, "", value, options or []),
                    column=2, line=line, layout_id=layout_id
                )
            else:  # string, text, etc.
                disp.add_display_item(
                    displayer.DisplayerItemInputString(form_field_name, "", value or ""),
                    column=2, line=line, layout_id=layout_id
                )
            
            # Overridable checkbox (only in admin mode)
            if not user_mode:
                checkbox_name = f"overridable_{full_key}"
                disp.add_display_item(
                    displayer.DisplayerItemInputCheckbox(checkbox_name, "", is_overridable),
                    column=3, line=line, layout_id=layout_id
                )
            
            line += 1
    
    # In user mode, show message if no overridable settings found
    if user_mode and not has_overridable:
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [12]
        ))
        disp.add_display_item(
            displayer.DisplayerItemAlert(
                "No settings are currently configured as user-overridable. Contact your administrator.",
                displayer.BSstyle.INFO
            ),
            column=0
        )
    else:
        # Add Save button
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [12], alignment=[displayer.BSalign.R], spacing=2
        ))
        disp.add_display_item(displayer.DisplayerItemButton("save", "Save Settings"), 0)
    
    target = "settings.user_view" if user_mode else "settings.view"
    return render_template("base_content.j2", content=disp.display(bypass_auth=_bypass_auth), target=target)

