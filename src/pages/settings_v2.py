"""
Settings V2 Pages - Modern Flask blueprint using SettingsManager.

This module demonstrates the new settings architecture with clean separation
of concerns between presentation, business logic, and data layers.

Routes:
    GET  /settings_v2/              - Main settings dashboard
    GET  /settings_v2/view          - View all settings (read-only)
    GET  /settings_v2/edit          - Edit settings form
    POST /settings_v2/update        - Update settings (single or multiple)
    GET  /settings_v2/category/<name> - View category settings
    POST /settings_v2/category/<name> - Update category
    GET  /settings_v2/export        - Export settings to JSON
    POST /settings_v2/import        - Import settings from JSON
    POST /settings_v2/reset         - Reset settings to defaults
    GET  /settings_v2/search        - Search settings
    GET  /settings_v2/info/<key>    - Get detailed setting info
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file
from werkzeug.utils import secure_filename
import os
import tempfile
import json
from pathlib import Path

from ..modules.settings_manager import SettingsManager
from ..modules import access_manager
from ..modules import displayer


bp = Blueprint("settings_v2", __name__, url_prefix="/settings_v2")

# Initialize global settings manager (in production, use app context or config)
_settings_manager = None


def get_settings_manager():
    """Get or create settings manager instance."""
    global _settings_manager
    if _settings_manager is None:
        config_path = os.path.join(os.getcwd(), "config.json")
        _settings_manager = SettingsManager(config_path)
        _settings_manager.load()
    return _settings_manager


@bp.route("/", methods=["GET"])
def dashboard():
    """Display settings dashboard with overview and quick actions."""
    if not access_manager.auth_object.authorize_group("admin"):
        return render_template("unauthorized.j2")
    
    manager = get_settings_manager()
    
    # Build displayer
    disp = displayer.Displayer()
    disp.add_generic("Settings Dashboard", display=False)
    disp.set_title("Settings Management (V2)")
    
    # Overview section
    disp.add_master_layout(
        displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL,
            [12],
            subtitle="Settings Overview"
        )
    )
    
    categories = manager.list_categories()
    modified = manager.get_modified_settings()
    
    overview_html = f"""
    <div class="card">
        <div class="card-body">
            <h5 class="card-title">Configuration Status</h5>
            <ul class="list-group list-group-flush">
                <li class="list-group-item"><strong>Categories:</strong> {len(categories)}</li>
                <li class="list-group-item"><strong>Modified Settings:</strong> {len(modified)}</li>
                <li class="list-group-item"><strong>Config File:</strong> <code>{manager.storage.config_path}</code></li>
            </ul>
        </div>
    </div>
    """
    disp.add_display_item(displayer.DisplayerItemText(overview_html), 0)
    
    # Quick actions
    disp.add_master_layout(
        displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL,
            [3, 3, 3, 3],
            subtitle="Quick Actions",
            alignment=[displayer.BSalign.C] * 4
        )
    )
    
    disp.add_display_item(
        displayer.DisplayerItemButton(
            "view_settings",
            "View All Settings",
            style=displayer.BSstyle.INFO,
            link="/settings_v2/view"
        ),
        0
    )
    disp.add_display_item(
        displayer.DisplayerItemButton(
            "edit_settings",
            "Edit Settings",
            style=displayer.BSstyle.PRIMARY,
            link="/settings_v2/edit"
        ),
        1
    )
    disp.add_display_item(
        displayer.DisplayerItemButton(
            "export_settings",
            "Export Settings",
            style=displayer.BSstyle.SUCCESS,
            link="/settings_v2/export"
        ),
        2
    )
    disp.add_display_item(
        displayer.DisplayerItemButton(
            "search_settings",
            "Search Settings",
            style=displayer.BSstyle.WARNING,
            link="/settings_v2/search"
        ),
        3
    )
    
    # Categories list
    disp.add_master_layout(
        displayer.DisplayerLayout(
            displayer.Layouts.TABLE,
            ["Category", "Settings Count", "Actions"],
            "Categories"
        )
    )
    
    for i, category in enumerate(categories):
        category_settings = manager.get_category(category)
        disp.add_display_item(
            displayer.DisplayerItemText(f"<strong>{category.title()}</strong>"),
            0,
            line=i
        )
        disp.add_display_item(
            displayer.DisplayerItemBadge(str(len(category_settings)), displayer.BSstyle.INFO),
            1,
            line=i
        )
        disp.add_display_item(
            displayer.DisplayerItemText(
                f'<a href="/settings_v2/category/{category}" class="btn btn-sm btn-outline-primary">View</a> '
                f'<a href="/settings_v2/edit?category={category}" class="btn btn-sm btn-outline-secondary">Edit</a>'
            ),
            2,
            line=i
        )
    
    return render_template("base_content.j2", content=disp.display(), target="")


@bp.route("/view", methods=["GET"])
def view_settings():
    """Display all settings in read-only mode."""
    if not access_manager.auth_object.authorize_group("admin"):
        return render_template("unauthorized.j2")
    
    manager = get_settings_manager()
    
    # Build displayer
    disp = displayer.Displayer()
    disp.add_generic("View Settings", display=False)
    disp.set_title("All Settings (Read-Only)")
    
    # Group by categories
    categories = manager.list_categories()
    
    for category in categories:
        settings = manager.get_category(category)
        
        disp.add_master_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.TABLE,
                ["Setting", "Value", "Type", "Modified"],
                category.title()
            )
        )
        
        for i, (key, value) in enumerate(settings.items()):
            full_key = f"{category}.{key}"
            info = manager.get_setting_info(full_key)
            
            # Format value for display
            if isinstance(value, bool):
                display_value = "✓ Yes" if value else "✗ No"
                badge_style = displayer.BSstyle.SUCCESS if value else displayer.BSstyle.SECONDARY
                value_html = f'<span class="badge bg-{badge_style.value}">{display_value}</span>'
            elif isinstance(value, (int, float)):
                value_html = f"<code>{value}</code>"
            else:
                value_html = f"{value}"
            
            disp.add_display_item(
                displayer.DisplayerItemText(f"<strong>{key}</strong>"),
                0,
                line=i
            )
            disp.add_display_item(
                displayer.DisplayerItemText(value_html),
                1,
                line=i
            )
            disp.add_display_item(
                displayer.DisplayerItemBadge(info['type'], displayer.BSstyle.INFO),
                2,
                line=i
            )
            disp.add_display_item(
                displayer.DisplayerItemBadge(
                    "Modified" if info['modified'] else "Default",
                    displayer.BSstyle.WARNING if info['modified'] else displayer.BSstyle.SECONDARY
                ),
                3,
                line=i
            )
    
    # Back button
    disp.add_master_layout(
        displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL,
            [12],
            alignment=[displayer.BSalign.L]
        )
    )
    disp.add_display_item(
        displayer.DisplayerItemButton(
            "back",
            "← Back to Dashboard",
            style=displayer.BSstyle.SECONDARY,
            link="/settings_v2/"
        ),
        0
    )
    
    return render_template("base_content.j2", content=disp.display(), target="")


@bp.route("/edit", methods=["GET"])
def edit_settings():
    """Display settings editor form."""
    if not access_manager.auth_object.authorize_group("admin"):
        return render_template("unauthorized.j2")
    
    manager = get_settings_manager()
    category_filter = request.args.get('category')
    
    # Build displayer
    disp = displayer.Displayer()
    disp.add_generic("Edit Settings", display=False)
    disp.set_title(f"Edit Settings - {category_filter.title() if category_filter else 'All'}")
    
    categories = [category_filter] if category_filter else manager.list_categories()
    
    for category in categories:
        settings = manager.get_category(category)
        
        disp.add_master_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.VERTICAL,
                [12],
                subtitle=category.title()
            )
        )
        
        for key, value in settings.items():
            full_key = f"{category}.{key}"
            info = manager.get_setting_info(full_key)
            
            # Create input based on type
            disp.add_master_layout(
                displayer.DisplayerLayout(
                    displayer.Layouts.VERTICAL,
                    [4, 8],
                    spacing=2
                )
            )
            
            # Label with description
            label_html = f"<strong>{key.replace('_', ' ').title()}</strong>"
            if info.get('description'):
                label_html += f"<br><small class='text-muted'>{info['description']}</small>"
            disp.add_display_item(displayer.DisplayerItemText(label_html), 0)
            
            # Input field based on type
            if info['type'] == 'bool':
                disp.add_display_item(
                    displayer.DisplayerItemInputSelect(
                        full_key,
                        None,
                        str(value),
                        ["True", "False"]
                    ),
                    1
                )
            elif info['type'] == 'int':
                disp.add_display_item(
                    displayer.DisplayerItemInputNumeric(
                        full_key,
                        None,
                        value
                    ),
                    1
                )
            else:  # str
                disp.add_display_item(
                    displayer.DisplayerItemInputString(
                        full_key,
                        None,
                        value
                    ),
                    1
                )
    
    # Action buttons
    disp.add_master_layout(
        displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL,
            [3, 3, 3, 3],
            alignment=[displayer.BSalign.L, displayer.BSalign.L, displayer.BSalign.R, displayer.BSalign.R]
        )
    )
    
    disp.add_display_item(
        displayer.DisplayerItemButton("save", "Save Changes", style=displayer.BSstyle.PRIMARY),
        0
    )
    disp.add_display_item(
        displayer.DisplayerItemButton("cancel", "Cancel", style=displayer.BSstyle.SECONDARY, link="/settings_v2/"),
        1
    )
    
    if category_filter:
        disp.add_display_item(
            displayer.DisplayerItemButton(
                "reset_category",
                f"Reset {category_filter.title()} to Defaults",
                style=displayer.BSstyle.WARNING
            ),
            2
        )
    else:
        disp.add_display_item(
            displayer.DisplayerItemButton("reset_all", "Reset All to Defaults", style=displayer.BSstyle.DANGER),
            3
        )
    
    return render_template("base_content.j2", content=disp.display(), target="settings_v2.update_settings")


@bp.route("/update", methods=["POST"])
def update_settings():
    """Update settings from form submission."""
    if not access_manager.auth_object.authorize_group("admin"):
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    manager = get_settings_manager()
    
    try:
        # Parse form data
        data = request.form.to_dict()
        
        # Handle reset actions
        if "reset_all" in data:
            success = manager.reset_to_defaults()
            if success:
                flash("All settings reset to defaults ✅", "success")
            else:
                flash("Failed to reset settings ❌", "error")
            return redirect(url_for("settings_v2.dashboard"))
        
        if "reset_category" in data:
            # Extract category from one of the keys
            for key in data:
                if "." in key and key not in ["reset_category", "save", "cancel"]:
                    category = key.split(".")[0]
                    success = manager.reset_category_to_defaults(category)
                    if success:
                        flash(f"Category '{category}' reset to defaults ✅", "success")
                    else:
                        flash(f"Failed to reset category '{category}' ❌", "error")
                    return redirect(url_for("settings_v2.edit_settings", category=category))
        
        # Update individual settings
        updates = {}
        for key, value in data.items():
            if "." in key and key not in ["save", "cancel"]:
                # Convert value to appropriate type
                info = manager.get_setting_info(key)
                if info['type'] == 'bool':
                    value = value.lower() in ['true', '1', 'yes']
                elif info['type'] == 'int':
                    value = int(value)
                updates[key] = value
        
        if updates:
            # Validate before updating
            valid, error = manager.validate_settings()
            if not valid:
                flash(f"Validation failed: {error} ❌", "error")
                return redirect(request.referrer or url_for("settings_v2.edit_settings"))
            
            # Update all at once
            success = manager.update_multiple(updates)
            if success:
                flash(f"Successfully updated {len(updates)} setting(s) ✅", "success")
            else:
                flash("Failed to update settings ❌", "error")
        
        return redirect(request.referrer or url_for("settings_v2.dashboard"))
        
    except Exception as e:
        flash(f"Error updating settings: {str(e)} ❌", "error")
        return redirect(request.referrer or url_for("settings_v2.edit_settings"))


@bp.route("/category/<category_name>", methods=["GET"])
def view_category(category_name):
    """View settings for a specific category."""
    if not access_manager.auth_object.authorize_group("admin"):
        return render_template("unauthorized.j2")
    
    manager = get_settings_manager()
    
    try:
        settings = manager.get_category(category_name)
        
        # Build displayer
        disp = displayer.Displayer()
        disp.add_generic(f"{category_name.title()} Settings", display=False)
        disp.set_title(f"{category_name.title()} Settings")
        
        disp.add_master_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.TABLE,
                ["Setting", "Value", "Type", "Modified", "Actions"],
                ""
            )
        )
        
        for i, (key, value) in enumerate(settings.items()):
            full_key = f"{category_name}.{key}"
            info = manager.get_setting_info(full_key)
            
            # Format value
            if isinstance(value, bool):
                value_str = "✓ Yes" if value else "✗ No"
            else:
                value_str = str(value)
            
            disp.add_display_item(
                displayer.DisplayerItemText(f"<strong>{key}</strong>"),
                0,
                line=i
            )
            disp.add_display_item(
                displayer.DisplayerItemText(f"<code>{value_str}</code>"),
                1,
                line=i
            )
            disp.add_display_item(
                displayer.DisplayerItemBadge(info['type'], displayer.BSstyle.INFO),
                2,
                line=i
            )
            disp.add_display_item(
                displayer.DisplayerItemBadge(
                    "Modified" if info['modified'] else "Default",
                    displayer.BSstyle.WARNING if info['modified'] else displayer.BSstyle.SECONDARY
                ),
                3,
                line=i
            )
            disp.add_display_item(
                displayer.DisplayerItemText(
                    f'<a href="/settings_v2/info/{full_key}" class="btn btn-sm btn-outline-info">Details</a>'
                ),
                4,
                line=i
            )
        
        # Action buttons
        disp.add_master_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.VERTICAL,
                [3, 3, 6],
                alignment=[displayer.BSalign.L, displayer.BSalign.L, displayer.BSalign.R]
            )
        )
        
        disp.add_display_item(
            displayer.DisplayerItemButton(
                "edit",
                "Edit Category",
                style=displayer.BSstyle.PRIMARY,
                link=f"/settings_v2/edit?category={category_name}"
            ),
            0
        )
        disp.add_display_item(
            displayer.DisplayerItemButton(
                "back",
                "← Back",
                style=displayer.BSstyle.SECONDARY,
                link="/settings_v2/"
            ),
            1
        )
        
        return render_template("base_content.j2", content=disp.display(), target="")
        
    except KeyError:
        flash(f"Category '{category_name}' not found ❌", "error")
        return redirect(url_for("settings_v2.dashboard"))


@bp.route("/export", methods=["GET"])
def export_settings():
    """Export settings to JSON file."""
    if not access_manager.auth_object.authorize_group("admin"):
        return render_template("unauthorized.j2")
    
    manager = get_settings_manager()
    
    try:
        # Create temporary file for export
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        temp_path = temp_file.name
        temp_file.close()
        
        # Export settings
        success = manager.export_settings(temp_path)
        
        if success:
            return send_file(
                temp_path,
                as_attachment=True,
                download_name='config_export.json',
                mimetype='application/json'
            )
        else:
            flash("Failed to export settings ❌", "error")
            return redirect(url_for("settings_v2.dashboard"))
            
    except Exception as e:
        flash(f"Error exporting settings: {str(e)} ❌", "error")
        return redirect(url_for("settings_v2.dashboard"))


@bp.route("/import", methods=["GET", "POST"])
def import_settings():
    """Import settings from JSON file."""
    if not access_manager.auth_object.authorize_group("admin"):
        return render_template("unauthorized.j2")
    
    if request.method == "GET":
        # Show import form
        disp = displayer.Displayer()
        disp.add_generic("Import Settings", display=False)
        disp.set_title("Import Settings from JSON")
        
        disp.add_master_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.VERTICAL,
                [12],
                subtitle="Import Options"
            )
        )
        
        disp.add_display_item(
            displayer.DisplayerItemAlert(
                "⚠️ Importing settings will update your configuration. Make sure to backup first!",
                displayer.BSstyle.WARNING
            ),
            0
        )
        
        disp.add_master_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.VERTICAL,
                [12]
            )
        )
        
        disp.add_display_item(
            displayer.DisplayerItemText(
                '<form method="post" enctype="multipart/form-data">'
                '<div class="mb-3">'
                '<label for="config_file" class="form-label">Select JSON file</label>'
                '<input type="file" class="form-control" id="config_file" name="config_file" accept=".json" required>'
                '</div>'
                '<div class="form-check mb-3">'
                '<input class="form-check-input" type="checkbox" id="merge" name="merge" value="true">'
                '<label class="form-check-label" for="merge">'
                'Merge with existing settings (instead of replacing)'
                '</label>'
                '</div>'
                '<button type="submit" class="btn btn-primary">Import</button>'
                '<a href="/settings_v2/" class="btn btn-secondary">Cancel</a>'
                '</form>'
            ),
            0
        )
        
        return render_template("base_content.j2", content=disp.display(), target="")
    
    else:  # POST
        manager = get_settings_manager()
        
        try:
            # Get uploaded file
            if 'config_file' not in request.files:
                flash("No file uploaded ❌", "error")
                return redirect(url_for("settings_v2.import_settings"))
            
            file = request.files['config_file']
            if file.filename == '':
                flash("No file selected ❌", "error")
                return redirect(url_for("settings_v2.import_settings"))
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json')
            file.save(temp_file.name)
            temp_file.close()
            
            # Import settings
            merge = 'merge' in request.form
            success = manager.import_settings(temp_file.name, merge=merge, validate=True)
            
            # Cleanup temp file
            os.unlink(temp_file.name)
            
            if success:
                mode = "merged" if merge else "replaced"
                flash(f"Settings {mode} successfully ✅", "success")
            else:
                flash("Failed to import settings (validation error) ❌", "error")
            
            return redirect(url_for("settings_v2.dashboard"))
            
        except Exception as e:
            flash(f"Error importing settings: {str(e)} ❌", "error")
            return redirect(url_for("settings_v2.import_settings"))


@bp.route("/search", methods=["GET"])
def search_settings():
    """Search settings by keyword."""
    if not access_manager.auth_object.authorize_group("admin"):
        return render_template("unauthorized.j2")
    
    manager = get_settings_manager()
    query = request.args.get('q', '')
    
    # Build displayer
    disp = displayer.Displayer()
    disp.add_generic("Search Settings", display=False)
    disp.set_title("Search Settings")
    
    # Search form
    disp.add_master_layout(
        displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL,
            [12]
        )
    )
    
    search_form = f'''
    <form method="get" action="/settings_v2/search" class="mb-4">
        <div class="input-group">
            <input type="text" class="form-control" name="q" placeholder="Search settings..." value="{query}">
            <button class="btn btn-primary" type="submit">Search</button>
        </div>
    </form>
    '''
    disp.add_display_item(displayer.DisplayerItemText(search_form), 0)
    
    if query:
        results = manager.search_settings(query)
        
        disp.add_master_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.TABLE,
                ["Setting", "Value", "Category"],
                f"Search Results ({len(results)} found)"
            )
        )
        
        for i, (key, value) in enumerate(results.items()):
            category = key.split('.')[0] if '.' in key else 'unknown'
            
            # Format value
            if isinstance(value, bool):
                value_str = "✓ Yes" if value else "✗ No"
            else:
                value_str = str(value)
            
            disp.add_display_item(
                displayer.DisplayerItemText(f"<strong>{key}</strong>"),
                0,
                line=i
            )
            disp.add_display_item(
                displayer.DisplayerItemText(f"<code>{value_str}</code>"),
                1,
                line=i
            )
            disp.add_display_item(
                displayer.DisplayerItemBadge(category, displayer.BSstyle.INFO),
                2,
                line=i
            )
    
    # Back button
    disp.add_master_layout(
        displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL,
            [12],
            alignment=[displayer.BSalign.L]
        )
    )
    disp.add_display_item(
        displayer.DisplayerItemButton(
            "back",
            "← Back to Dashboard",
            style=displayer.BSstyle.SECONDARY,
            link="/settings_v2/"
        ),
        0
    )
    
    return render_template("base_content.j2", content=disp.display(), target="")


@bp.route("/info/<path:setting_key>", methods=["GET"])
def setting_info(setting_key):
    """Display detailed information about a setting."""
    if not access_manager.auth_object.authorize_group("admin"):
        return render_template("unauthorized.j2")
    
    manager = get_settings_manager()
    
    try:
        info = manager.get_setting_info(setting_key)
        current_value = manager.get_setting(setting_key)
        
        # Build displayer
        disp = displayer.Displayer()
        disp.add_generic("Setting Info", display=False)
        disp.set_title(f"Setting Details: {setting_key}")
        
        disp.add_master_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.VERTICAL,
                [12]
            )
        )
        
        # Info card
        info_html = f'''
        <div class="card">
            <div class="card-header">
                <h5>{setting_key}</h5>
            </div>
            <div class="card-body">
                <dl class="row">
                    <dt class="col-sm-3">Current Value</dt>
                    <dd class="col-sm-9"><code>{current_value}</code></dd>
                    
                    <dt class="col-sm-3">Default Value</dt>
                    <dd class="col-sm-9"><code>{info['default']}</code></dd>
                    
                    <dt class="col-sm-3">Type</dt>
                    <dd class="col-sm-9"><span class="badge bg-info">{info['type']}</span></dd>
                    
                    <dt class="col-sm-3">Modified</dt>
                    <dd class="col-sm-9">
                        <span class="badge bg-{"warning" if info['modified'] else "secondary"}">
                            {"Yes" if info['modified'] else "No"}
                        </span>
                    </dd>
        '''
        
        if info.get('description'):
            info_html += f'''
                    <dt class="col-sm-3">Description</dt>
                    <dd class="col-sm-9">{info['description']}</dd>
            '''
        
        info_html += '''
                </dl>
            </div>
        </div>
        '''
        
        disp.add_display_item(displayer.DisplayerItemText(info_html), 0)
        
        # Action buttons
        disp.add_master_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.VERTICAL,
                [3, 9],
                alignment=[displayer.BSalign.L, displayer.BSalign.R]
            )
        )
        
        category = setting_key.split('.')[0] if '.' in setting_key else None
        edit_link = f"/settings_v2/edit?category={category}" if category else "/settings_v2/edit"
        
        disp.add_display_item(
            displayer.DisplayerItemButton(
                "back",
                "← Back",
                style=displayer.BSstyle.SECONDARY,
                link="/settings_v2/"
            ),
            0
        )
        disp.add_display_item(
            displayer.DisplayerItemButton(
                "edit",
                "Edit Setting",
                style=displayer.BSstyle.PRIMARY,
                link=edit_link
            ),
            1
        )
        
        return render_template("base_content.j2", content=disp.display(), target="")
        
    except KeyError:
        flash(f"Setting '{setting_key}' not found ❌", "error")
        return redirect(url_for("settings_v2.dashboard"))
