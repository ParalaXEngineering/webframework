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
    """Get or create settings manager instance."""
    global _settings_manager
    if _settings_manager is None:
        config_path = os.path.join(os.getcwd(), "config.json")
        _settings_manager = SettingsManager(config_path)
        _settings_manager.load()
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
        
        # Action buttons
        disp.add_display_item(
            displayer.DisplayerItemActionButtons(
                id=f"actions_{category}",
                view_url=f"/settings/view?category={category}",
                edit_url=f"/settings/edit?category={category}",
                style="icons",
                size="sm"
            ),
            column=3, line=line, layout_id=layout_id
        )
    
    return render_template("base_content.j2", content=disp.display(bypass_auth=_bypass_auth), target="")


@bp.route("/view", methods=["GET"])
@require_admin
def view():
    """View settings in read-only table format."""
    manager = get_manager()
    category_filter = request.args.get("category")
    
    disp = displayer.Displayer()
    disp.add_generic("View Settings", display=False)
    disp.set_title("View Settings")
    
    # Add breadcrumbs
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Settings", "settings.index", [])
    if category_filter:
        disp.add_breadcrumb(f"View {manager.get_category_friendly(category_filter)}", "settings.view", [f"category={category_filter}"])
    else:
        disp.add_breadcrumb("View All Settings", "settings.view", [])
    
    all_settings = manager.get_all_settings()
    
    # Filter by category if specified
    categories_to_show = [category_filter] if category_filter else manager.list_categories()
    
    for category in categories_to_show:
        if category not in all_settings:
            continue
            
        category_data = all_settings[category]
        friendly_name = category_data.get("friendly", category)
        
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [12], subtitle=friendly_name, spacing=2
        ))
        
        # Create simple table for this category (no DataTables)
        layout_id = disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.TABLE,
            columns=["Setting", "Type", "Current Value", "Actions"]
        ))
        
        line = 0
        for key, setting in category_data.items():
            if key == "friendly" or not isinstance(setting, dict):
                continue
            
            friendly = setting.get("friendly", key)
            setting_type = setting.get("type", "string")
            value = setting.get("value")
            
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
            
            # Current value (formatted nicely)
            if setting_type == "bool":
                value_display = "✓ Yes" if value else "✗ No"
            elif setting_type in ["text_list", "multi_select"]:
                value_display = f"{len(value) if value else 0} items"
            elif setting_type in ["key_value_pairs", "dropdown_mapping"]:
                value_display = f"{len(value) if value else 0} entries"
            else:
                value_display = str(value) if value is not None else "<em>Not set</em>"
            
            disp.add_display_item(
                displayer.DisplayerItemText(value_display),
                column=2, line=line, layout_id=layout_id
            )
            
            # Action buttons - edit only (no view/delete for individual settings)
            full_key = f"{category}.{key}"
            disp.add_display_item(
                displayer.DisplayerItemActionButtons(
                    id=f"actions_{category}_{key}",
                    edit_url=f"/settings/edit?category={category}#{full_key}",
                    style="icons",
                    size="sm"
                ),
                column=3, line=line, layout_id=layout_id
            )
            
            line += 1
    
    return render_template("base_content.j2", content=disp.display(bypass_auth=_bypass_auth), target="")


@bp.route("/edit", methods=["GET", "POST"])
@require_admin
def edit():
    """Edit settings form with all field types."""
    manager = get_manager()
    
    if request.method == "POST":
        # Process form submission
        # Complex structures need custom parsing to handle module prefix and various field types
        
        # Strip module prefix from all form keys and organize by setting
        cleaned_form = {}
        for form_key, form_value in request.form.items():
            if form_key in ["csrf_token", "save"]:
                continue
            
            # Strip module prefix if present (e.g., "Edit Settings.category.key" -> "category.key")
            if '.' in form_key:
                parts = form_key.split('.')
                # If first part has spaces, it's likely the module name
                if ' ' in parts[0] and len(parts) >= 3:
                    cleaned_key = '.'.join(parts[1:])  # Skip module name
                else:
                    cleaned_key = form_key
                cleaned_form[cleaned_key] = form_value
        
        all_settings = manager.get_all_settings()
        
        # Collect bool fields for unchecked handling
        bool_fields = set()
        for category in all_settings:
            category_data = all_settings[category]
            for key in category_data:
                if key == "friendly" or not isinstance(category_data[key], dict):
                    continue
                setting = category_data[key]
                if setting.get("type") == "bool":
                    bool_fields.add(f"{category}.{key}")
        
        # Group form fields by setting (handle complex types that have suffixes like .list0, .list1)
        setting_groups = {}
        for form_key, form_value in cleaned_form.items():
            # Extract base setting key (category.key) from forms like "category.key.list0"
            parts = form_key.split('.')
            if len(parts) >= 2:
                category = parts[0]
                key = parts[1]
                base_key = f"{category}.{key}"
                
                if base_key not in setting_groups:
                    setting_groups[base_key] = []
                setting_groups[base_key].append((form_key, form_value))
        
        # Process each setting
        for base_key, field_data in setting_groups.items():
            parts = base_key.split('.')
            if len(parts) < 2:
                continue
            
            category = parts[0]
            key = parts[1]
            
            if category not in all_settings or key not in all_settings[category]:
                continue
            
            setting = all_settings[category][key]
            if not isinstance(setting, dict):
                continue
            
            setting_type = setting.get("type", "string")
            
            # Handle different types
            if setting_type in ["string", "select", "serial_port", "icon"]:
                # Simple single-value fields
                if len(field_data) > 0:
                    value = field_data[0][1]
                    try:
                        manager.set_setting(base_key, value)
                    except Exception as e:
                        print(f"Error setting {base_key}: {e}")
            
            elif setting_type == "int":
                if len(field_data) > 0:
                    try:
                        value = int(field_data[0][1])
                    except (ValueError, TypeError):
                        value = 0
                    try:
                        manager.set_setting(base_key, value)
                    except Exception as e:
                        print(f"Error setting {base_key}: {e}")
            
            elif setting_type == "bool":
                # Checkbox - if present in form, it's checked (True)
                if len(field_data) > 0:
                    value = field_data[0][1] in [True, "true", "on", "1", 1]
                    bool_fields.discard(base_key)
                else:
                    value = False
                try:
                    manager.set_setting(base_key, value)
                except Exception as e:
                    print(f"Error setting {base_key}: {e}")
            
            elif setting_type == "text_list":
                # Parse list from form (comes as .list0, .list1, etc.)
                list_values = []
                for form_key, form_value in field_data:
                    if '.list' in form_key and form_value:
                        list_values.append(form_value)
                try:
                    manager.set_setting(base_key, list_values)
                except Exception as e:
                    print(f"Error setting {base_key}: {e}")
            
            elif setting_type == "multi_select":
                # Multi-select comes as multiple values with same name
                selected_values = [fv for fk, fv in field_data if fv != "on"]
                # Handle checkbox format (name_value: on)
                checkbox_values = []
                for form_key, form_value in field_data:
                    if form_value == "on" and '_' in form_key:
                        checkbox_values.append(form_key.split('_')[-1])
                
                final_values = selected_values if selected_values else checkbox_values
                try:
                    manager.set_setting(base_key, final_values)
                except Exception as e:
                    print(f"Error setting {base_key}: {e}")
            
            elif setting_type == "key_value_pairs":
                # TextText widget sends .mapleft0/.mapright0, .mapleft1/.mapright1, etc.
                # .mapleft = key (text input), .mapright = value (text input)
                dict_values = {}
                # Group by index
                map_data = {}
                for form_key, form_value in field_data:
                    if '.mapleft' in form_key:
                        # Extract index
                        idx = form_key.split('.mapleft')[-1]
                        if idx not in map_data:
                            map_data[idx] = {}
                        map_data[idx]['key'] = form_value
                    elif '.mapright' in form_key:
                        idx = form_key.split('.mapright')[-1]
                        if idx not in map_data:
                            map_data[idx] = {}
                        map_data[idx]['value'] = form_value
                
                # Build dict from paired data
                for idx in map_data:
                    if 'key' in map_data[idx] and 'value' in map_data[idx]:
                        key = map_data[idx]['key']
                        value = map_data[idx]['value']
                        if key and value:  # Only add if both are present
                            dict_values[key] = value
                
                try:
                    manager.set_setting(base_key, dict_values)
                except Exception as e:
                    print(f"Error setting {base_key}: {e}")
            
            elif setting_type == "dropdown_mapping":
                # SelectText widget sends .mapleft0/.mapright0, .mapleft1/.mapright1, etc.
                # .mapleft = key (from dropdown), .mapright = value (text input)
                dict_values = {}
                # Group by index
                map_data = {}
                for form_key, form_value in field_data:
                    if '.mapleft' in form_key:
                        # Extract index
                        idx = form_key.split('.mapleft')[-1]
                        if idx not in map_data:
                            map_data[idx] = {}
                        map_data[idx]['key'] = form_value
                    elif '.mapright' in form_key:
                        idx = form_key.split('.mapright')[-1]
                        if idx not in map_data:
                            map_data[idx] = {}
                        map_data[idx]['value'] = form_value
                
                # Build dict from paired data
                for idx in map_data:
                    if 'key' in map_data[idx] and 'value' in map_data[idx]:
                        key = map_data[idx]['key']
                        value = map_data[idx]['value']
                        if key and value:  # Only add if both are present
                            dict_values[key] = value
                
                try:
                    manager.set_setting(base_key, dict_values)
                except Exception as e:
                    print(f"Error setting {base_key}: {e}")
        
        # Set any remaining unchecked boolean fields to False
        for bool_field in bool_fields:
            try:
                manager.set_setting(bool_field, False)
            except Exception as e:
                print(f"Error setting {bool_field}: {e}")
        
        # Save immediately
        manager.save()
        
        flash("Settings updated successfully", "success")
        return redirect(url_for("settings.index"))
    
    # GET - Show edit form
    category_filter = request.args.get("category")
    
    disp = displayer.Displayer()
    disp.add_generic("Edit Settings", display=False)
    disp.set_title("Edit Settings")
    
    # Add breadcrumbs
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Settings", "settings.index", [])
    if category_filter:
        disp.add_breadcrumb(f"Edit {manager.get_category_friendly(category_filter)}", "settings.edit", [f"category={category_filter}"])
    else:
        disp.add_breadcrumb("Edit All Settings", "settings.edit", [])
    
    all_settings = manager.get_all_settings()
    
    # Filter by category if specified
    categories_to_show = [category_filter] if category_filter else manager.list_categories()
    
    for category in categories_to_show:
        if category not in all_settings:
            continue
            
        category_data = all_settings[category]
        friendly_name = category_data.get("friendly", category)
        
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [12], subtitle=friendly_name, spacing=2
        ))
        
        for key, setting in category_data.items():
            if key == "friendly" or not isinstance(setting, dict):
                continue
            
            _render_setting_input(disp, category, key, setting)
    
    # Save button
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], alignment=[displayer.BSalign.R], spacing=2
    ))
    disp.add_display_item(displayer.DisplayerItemButton("save", "Save Changes"), 0)
    
    return render_template("base_content.j2", content=disp.display(bypass_auth=_bypass_auth), target="settings.edit")


def _render_setting_input(disp, category, key, setting):
    """
    Render appropriate input for a setting based on its type.
    
    Supports all original types from settings.py.
    """
    full_key = f"{category}.{key}"
    friendly = setting.get("friendly", key)
    setting_type = setting.get("type", "string")
    value = setting.get("value")
    options = setting.get("options", [])
    
    if setting_type == "string":
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [3, 9], spacing=2
        ))
        disp.add_display_item(displayer.DisplayerItemText(friendly), 0)
        disp.add_display_item(
            displayer.DisplayerItemInputString(full_key, None, value),
            1
        )
    
    elif setting_type == "int":
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [3, 9], spacing=2
        ))
        disp.add_display_item(displayer.DisplayerItemText(friendly), 0)
        disp.add_display_item(
            displayer.DisplayerItemInputNumeric(full_key, None, value),
            1
        )
    
    elif setting_type == "bool":
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [3, 9], spacing=2
        ))
        disp.add_display_item(displayer.DisplayerItemText(friendly), 0)
        disp.add_display_item(
            displayer.DisplayerItemInputCheckbox(full_key, None, value),
            1
        )
    
    elif setting_type == "select":
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [3, 9], spacing=2
        ))
        disp.add_display_item(displayer.DisplayerItemText(friendly), 0)
        disp.add_display_item(
            displayer.DisplayerItemInputSelect(full_key, None, value, options),
            1
        )
    
    elif setting_type == "serial_port":
        # Use options from config if available, otherwise try to detect serial ports
        serial_ports = options if options else []
        if not serial_ports:
            try:
                import serial.tools.list_ports
                serial_ports = [port.device for port in serial.tools.list_ports.comports()]
            except ImportError:
                serial_ports = ["None"]
        
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [3, 9], spacing=2
        ))
        disp.add_display_item(displayer.DisplayerItemText(friendly), 0)
        disp.add_display_item(
            displayer.DisplayerItemInputSelect(full_key, None, value, serial_ports or ["None"]),
            1
        )
    
    elif setting_type == "icon":
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [3, 9], spacing=2
        ))
        disp.add_display_item(displayer.DisplayerItemText(friendly), 0)
        disp.add_display_item(
            displayer.DisplayerItemInputStringIcon(full_key, None, value),
            1
        )
    
    elif setting_type == "key_value_pairs":
        # Key-value pairs: dict of key-value text pairs (merges old multistring and free_mapping)
        # Convert dict {"line1": "First line", "line2": "Second line"} to list [["line1", "First line"], ...]
        value_list = [[k, v] for k, v in value.items()] if isinstance(value, dict) else []
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [3, 9], spacing=2
        ))
        disp.add_display_item(displayer.DisplayerItemText(friendly), 0)
        disp.add_display_item(
            displayer.DisplayerItemInputKeyValue(full_key, None, value_list),
            1
        )
    
    elif setting_type == "multi_select":
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [3, 9], spacing=2
        ))
        disp.add_display_item(displayer.DisplayerItemText(friendly), 0)
        disp.add_display_item(
            displayer.DisplayerItemInputMultiSelect(full_key, None, value, options),
            1
        )
    
    elif setting_type == "text_list":
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [3, 9], spacing=2
        ))
        disp.add_display_item(displayer.DisplayerItemText(friendly), 0)
        disp.add_display_item(
            displayer.DisplayerItemInputTextList(full_key, None, value),
            1
        )
    
    elif setting_type == "dropdown_mapping":
        # Dropdown mapping: select from predefined keys, enter text value
        # Convert dict {"host": "localhost", "port": "8080"} to list [["host", "localhost"], ["port", "8080"]]
        value_list = [[k, v] for k, v in value.items()] if isinstance(value, dict) else []
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [3, 9], spacing=2
        ))
        disp.add_display_item(displayer.DisplayerItemText(friendly), 0)
        disp.add_display_item(
            displayer.DisplayerItemInputDropdownValue(full_key, None, value_list, options),
            1
        )
    
    else:
        # Default: treat as string
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [3, 9], spacing=2
        ))
        disp.add_display_item(displayer.DisplayerItemText(friendly), 0)
        disp.add_display_item(
            displayer.DisplayerItemInputString(full_key, None, str(value)),
            1
        )
