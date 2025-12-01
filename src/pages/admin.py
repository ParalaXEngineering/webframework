"""
Admin authentication and authorization management blueprint.
Manage users, groups, and module permissions.
"""

# Third-party
from flask import Blueprint, render_template, request, flash

# Framework modules
from ..modules.auth import require_admin, auth_manager
from ..modules.auth.auth_utils import validate_username, validate_password_strength
from ..modules.auth.permission_registry import permission_registry
from ..modules.displayer import (
    BSstyle, Displayer, DisplayerItemButton, DisplayerItemInputBox,
    DisplayerItemInputMultiSelect, DisplayerItemInputPassword,
    DisplayerItemInputSelect, DisplayerItemInputString, DisplayerItemText,
    DisplayerLayout, Layouts, TableMode
)
from ..modules.log.logger_factory import get_logger
from ..modules import utilities

logger = get_logger("admin_auth")
admin_auth_bp = Blueprint('admin_auth', __name__, url_prefix='/admin')

# Export as 'bp' for framework auto-discovery
bp = admin_auth_bp

# Constants for permission/role names
SYSTEM_ADMIN_GROUP = "admin"
SYSTEM_GUEST_GROUP = "guest"
RESERVED_GROUPS = {SYSTEM_ADMIN_GROUP, SYSTEM_GUEST_GROUP}
RESERVED_USERS = {SYSTEM_ADMIN_GROUP, SYSTEM_GUEST_GROUP}

# Constants for form field/button names
BTN_CREATE_USER = "btn_create_user"
BTN_DELETE_USER = "btn_delete_user"
BTN_UPDATE_GROUPS = "btn_update_groups"
BTN_RESET_PASSWORD = "btn_reset_password"
BTN_CREATE_GROUP = "btn_create_group"
BTN_RENAME_GROUP = "btn_rename_group"
BTN_DELETE_GROUP = "btn_delete_group"
BTN_SAVE_PERMISSIONS = "btn_save_permissions"

# Constants for HTML/display
CHECKBOX_PREFIX = "checkbox_"
CHECKBOX_SEPARATOR = "|"


@admin_auth_bp.route('/users', methods=['GET', 'POST'])
@require_admin()
def manage_users():
    """User management page - CRUD operations."""
    
    if not auth_manager:
        return "Authentication system not initialized", 500
    
    disp = Displayer()
    disp.add_generic("User Management")
    disp.add_breadcrumb("Admin", "admin_auth.manage_users", [])
    disp.add_breadcrumb("Users", "admin_auth.manage_users", [])
    
    if request.method == 'POST':
        data_in = utilities.util_post_to_json(request.form.to_dict())
        
        if "User Management" in data_in:
            module_data = data_in["User Management"]
            
            # Create new user
            if BTN_CREATE_USER in module_data:
                username = module_data.get("input_username", "").strip()
                password = module_data.get("input_password", "")
                display_name = module_data.get("input_display_name", "").strip()
                email = module_data.get("input_email", "").strip()
                groups_data = module_data.get("input_groups", "")
                
                # Handle both list (from multiselect) and comma-separated string
                if isinstance(groups_data, str):
                    groups = [g.strip() for g in groups_data.split(",")] if groups_data.strip() else []
                else:
                    groups = groups_data if isinstance(groups_data, list) else []
                
                # Validate
                is_valid_username, error_msg = validate_username(username)
                if not is_valid_username:
                    flash(error_msg or "Invalid username", "danger")
                elif auth_manager.get_user(username):
                    flash("Username already exists.", "danger")
                elif password:
                    is_valid_password, error_msg = validate_password_strength(password)
                    if not is_valid_password:
                        flash(error_msg or "Invalid password", "danger")
                    else:
                        auth_manager.create_user(username, password, groups, display_name or None, email or None)
                        flash(f"User '{username}' created successfully!", "success")
                else:
                    # Passwordless user
                    auth_manager.create_user(username, "", groups, display_name or None, email or None)
                    flash(f"Passwordless user '{username}' created successfully!", "success")
            
            # Delete user
            elif BTN_DELETE_USER in module_data:
                username = module_data.get("select_user_to_delete", "")
                if username and username not in RESERVED_USERS:
                    auth_manager.delete_user(username)
                    flash(f"User '{username}' deleted.", "success")
                else:
                    flash("Cannot delete admin or GUEST users.", "danger")
            
            # Update user groups
            elif BTN_UPDATE_GROUPS in module_data:
                username = module_data.get("select_user_to_update", "")
                groups_data = module_data.get("input_update_groups", "")
                
                # Handle both list and string formats
                if isinstance(groups_data, str):
                    groups = [g.strip() for g in groups_data.split(",")] if groups_data.strip() else []
                else:
                    groups = groups_data if isinstance(groups_data, list) else []
                
                if username:
                    auth_manager.update_user_groups(username, groups)
                    flash(f"Groups updated for '{username}'.", "success")
            
            # Reset password
            elif BTN_RESET_PASSWORD in module_data:
                username = module_data.get("select_user_to_reset", "")
                new_password = module_data.get("input_reset_password", "")
                
                if username and new_password:
                    is_valid, error_msg = validate_password_strength(new_password)
                    if not is_valid:
                        flash(error_msg or "Invalid password", "danger")
                    else:
                        auth_manager.update_user_password(username, new_password)
                        flash(f"Password reset for '{username}'.", "success")
    
    # User List Table
    users = auth_manager.get_all_users()
    user_data = []
    for user in users:  # type: ignore
        user_data.append({
            "Username": user.username,
            "Display Name": user.display_name,
            "Groups": ", ".join(user.groups),
            "Email": user.email or "N/A",
            "Last Login": user.last_login or "Never"
        })
    
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText("<h3>Current Users</h3>"), column=0)
    
    disp.add_master_layout(DisplayerLayout(
        Layouts.TABLE,
        columns=["Username", "Display Name", "Groups", "Email", "Last Login"],
        datatable_config={
            "table_id": "users_table",
            "mode": TableMode.BULK_DATA,
            "data": user_data,
            "columns": [
                {"data": "Username"},
                {"data": "Display Name"},
                {"data": "Groups"},
                {"data": "Email"},
                {"data": "Last Login"}
            ],
            "searchable_columns": [0, 1, 2]
        }
    ))
    
    # Create User Form
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText("<h3 class='mt-5'>Create New User</h3>"), column=0)
    
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [3, 3, 3, 3]))
    disp.add_display_item(DisplayerItemInputString("input_username", "Username"), column=0)
    disp.add_display_item(DisplayerItemInputPassword("input_password", "Password (empty for passwordless)"), column=1)
    disp.add_display_item(DisplayerItemInputString("input_display_name", "Display Name"), column=2)
    disp.add_display_item(DisplayerItemInputString("input_email", "Email"), column=3)
    
    all_groups = auth_manager.get_all_groups()
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [8, 4]))
    disp.add_display_item(DisplayerItemInputMultiSelect(
        "input_groups",
        "Groups",
        value=["guest"],
        choices=all_groups
    ), column=0)
    disp.add_display_item(DisplayerItemButton(BTN_CREATE_USER, "Create User", color=BSstyle.SUCCESS), column=1)
    
    # Update User Groups
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText("<h3 class='mt-5'>Update User Groups</h3>"), column=0)
    
    usernames = [u.username for u in users]  # type: ignore
    first_user_groups = users[0].groups if users else []
    
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [4, 6, 2]))
    disp.add_display_item(DisplayerItemInputSelect(
        "select_user_to_update",
        "Select User",
        value=usernames[0] if usernames else None,
        choices=usernames
    ), column=0)
    disp.add_display_item(DisplayerItemInputMultiSelect(
        "input_update_groups",
        "Groups",
        value=first_user_groups,
        choices=all_groups
    ), column=1)
    disp.add_display_item(DisplayerItemButton(BTN_UPDATE_GROUPS, "Update", color=BSstyle.PRIMARY), column=2)
    
    # Reset Password
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText("<h3 class='mt-5'>Reset User Password</h3>"), column=0)
    
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [4, 6, 2]))
    disp.add_display_item(DisplayerItemInputSelect(
        "select_user_to_reset",
        "Select User",
        value=usernames[0] if usernames else None,
        choices=usernames
    ), column=0)
    disp.add_display_item(DisplayerItemInputPassword("input_reset_password", "New Password"), column=1)
    disp.add_display_item(DisplayerItemButton(BTN_RESET_PASSWORD, "Reset", color=BSstyle.WARNING), column=2)
    
    # Delete User
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText("<h3 class='mt-5'>Delete User</h3>"), column=0)
    
    deletable_users = [u.username for u in users if u.username not in RESERVED_USERS]  # type: ignore
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [6, 6]))
    disp.add_display_item(DisplayerItemInputSelect(
        "select_user_to_delete",
        "Select User",
        value=deletable_users[0] if deletable_users else None,
        choices=deletable_users if deletable_users else ["(no deletable users)"]
    ), column=0)
    disp.add_display_item(DisplayerItemButton(BTN_DELETE_USER, "Delete User", color=BSstyle.ERROR), column=1)
    
    return render_template("base_content.j2", content=disp.display(), target="admin_auth.manage_users")


@admin_auth_bp.route('/permissions', methods=['GET', 'POST'])
@require_admin()
def manage_permissions():
    """Module permissions matrix management."""
    
    if not auth_manager:
        return "Authentication system not initialized", 500
    
    disp = Displayer()
    disp.add_generic("Permission Management")
    disp.set_title("Module Permissions")
    disp.add_breadcrumb("Admin", "admin_auth.manage_users", [])
    disp.add_breadcrumb("Permissions", "admin_auth.manage_permissions", [])
    
    if request.method == 'POST':
        data_in = utilities.util_post_to_json(request.form.to_dict())
        
        if "Permission Management" in data_in:
            module_data = data_in["Permission Management"]
            
            if BTN_SAVE_PERMISSIONS in module_data:
                logger.debug("Received form data for permission save")
                
                # Get all modules and groups to rebuild permissions
                all_modules = permission_registry.get_all_modules()
                all_groups = auth_manager.get_all_groups()
                
                # Build new permissions from form data
                new_permissions = {}
                for module_name in all_modules:
                    new_permissions[module_name] = {group: [] for group in all_groups}  # type: ignore
                
                # Parse checkbox format: checkbox_{module}|{group}|{action}
                for key, value in module_data.items():
                    if key.startswith(CHECKBOX_PREFIX):
                        # Remove prefix and split by separator
                        checkbox_data = key[len(CHECKBOX_PREFIX):]
                        parts = checkbox_data.split(CHECKBOX_SEPARATOR)
                        if len(parts) == 3:
                            module_name, group, action = parts
                            
                            # Check if checkbox is checked
                            is_checked = str(value) in ["on", "true", "True", "1"] or value in [True, 1]
                            
                            logger.debug(f"Processing {module_name}.{group}.{action}: checked={is_checked}")
                            
                            if is_checked and module_name in new_permissions and group in new_permissions[module_name]:
                                new_permissions[module_name][group].append(action)
                
                # Apply all new permissions
                for module_name, group_perms in new_permissions.items():
                    for group, actions in group_perms.items():
                        auth_manager.set_module_permissions(module_name, group, actions)
                
                flash("Permissions saved successfully!", "success")
    
    # Get all modules and groups (excluding admin)
    all_modules = permission_registry.get_all_modules()
    all_groups = [g for g in auth_manager.get_all_groups() if g != SYSTEM_ADMIN_GROUP]  # type: ignore
    
    if not all_modules:
        disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
        disp.add_display_item(DisplayerItemText(
            "<div class='alert alert-warning'>No modules have registered permissions yet. "
            "Modules must call <code>permission_registry.register_module()</code> to appear here.</div>"
        ), column=0)
        return render_template("base_content.j2", content=disp.display(), target="admin_auth.manage_permissions")
    
    # Permission Matrix
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText("<h3>Module Permission Matrix</h3>"), column=0)
    disp.add_display_item(DisplayerItemText(
        "<p>Check boxes to grant permissions to groups for each module action.</p>"
        "<div class='alert alert-info'><i class='mdi mdi-information'></i> "
        "The <strong>admin</strong> group has full access to all modules and is not shown here.</div>"
    ), column=0)
    
    # Create table with modules as rows
    for module_name in all_modules:
        disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
        disp.add_display_item(DisplayerItemText(f"<h4 class='mt-4'>{module_name}</h4>"), column=0)
        
        actions = permission_registry.get_module_actions(module_name)
        current_perms = auth_manager.get_module_permissions(module_name)
        
        # Create table: rows=actions, cols=groups
        header = ["Action"] + all_groups
        layout_id = disp.add_master_layout(DisplayerLayout(Layouts.TABLE, header))
        
        for action_idx, action in enumerate(actions):
            row: list = [DisplayerItemText(f"<strong>{action}</strong>")]
            
            for group in all_groups:
                # Check if group has this action
                is_checked = action in current_perms.get(group, [])
                checkbox = DisplayerItemInputBox(
                    f"{CHECKBOX_PREFIX}{module_name}{CHECKBOX_SEPARATOR}{group}{CHECKBOX_SEPARATOR}{action}",
                    "",
                    value=is_checked
                )
                row.append(checkbox)
            
            # Add row items using add_display_item
            for col_idx, item in enumerate(row):
                disp.add_display_item(item, col_idx, line=action_idx, layout_id=layout_id)
    
    # Save button
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemButton(
        BTN_SAVE_PERMISSIONS,
        "Save All Permissions",
        color=BSstyle.PRIMARY
    ), column=0)
    
    return render_template("base_content.j2", content=disp.display(), target="admin_auth.manage_permissions")


@admin_auth_bp.route('/groups', methods=['GET', 'POST'])
@require_admin()
def manage_groups():
    """Group management page."""
    
    if not auth_manager:
        return "Authentication system not initialized", 500
    
    disp = Displayer()
    disp.add_generic("Group Management")
    disp.set_title("Group Management")
    disp.add_breadcrumb("Admin", "admin_auth.manage_users", [])
    disp.add_breadcrumb("Groups", "admin_auth.manage_groups", [])
    
    if request.method == 'POST':
        data_in = utilities.util_post_to_json(request.form.to_dict())
        
        if "Group Management" in data_in:
            module_data = data_in["Group Management"]
            
            # Create new group
            if BTN_CREATE_GROUP in module_data:
                group_name = module_data.get("input_new_group", "").strip()
                
                if not group_name:
                    flash("Group name cannot be empty.", "danger")
                elif group_name in auth_manager.get_all_groups():
                    flash(f"Group '{group_name}' already exists.", "danger")
                else:
                    auth_manager.create_group(group_name)
                    flash(f"Group '{group_name}' created successfully!", "success")
            
            # Rename group
            elif BTN_RENAME_GROUP in module_data:
                old_name = module_data.get("select_group_to_rename", "")
                new_name = module_data.get("input_new_group_name", "").strip()
                
                if old_name and new_name:
                    if old_name in RESERVED_GROUPS:
                        flash("Cannot rename system groups (admin, guest).", "danger")
                    elif new_name in auth_manager.get_all_groups():
                        flash(f"Group '{new_name}' already exists.", "danger")
                    else:
                        auth_manager.rename_group(old_name, new_name)
                        flash(f"Group '{old_name}' renamed to '{new_name}'.", "success")
            
            # Delete group
            elif BTN_DELETE_GROUP in module_data:
                group_name = module_data.get("select_group_to_delete", "")
                
                if group_name in RESERVED_GROUPS:
                    flash("Cannot delete system groups (admin, guest).", "danger")
                elif group_name:
                    auth_manager.delete_group(group_name)
                    flash(f"Group '{group_name}' deleted.", "success")
    
    # Current Groups
    groups = auth_manager.get_all_groups()
    
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText("<h3>Current Groups</h3>"), column=0)
    
    layout_id = disp.add_master_layout(DisplayerLayout(Layouts.TABLE, ["Group Name", "# Users"]))
    users = auth_manager.get_all_users()
    for line_idx, group in enumerate(groups):
        user_count = sum(1 for u in users if group in u.groups)  # type: ignore
        disp.add_display_item(DisplayerItemText(group), 0, line=line_idx, layout_id=layout_id)
        disp.add_display_item(DisplayerItemText(str(user_count)), 1, line=line_idx, layout_id=layout_id)
    
    # Create New Group
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText("<h3 class='mt-5'>Create New Group</h3>"), column=0)
    
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [8, 4]))
    disp.add_display_item(DisplayerItemInputString("input_new_group", "Group Name"), column=0)
    disp.add_display_item(DisplayerItemButton(BTN_CREATE_GROUP, "Create Group", color=BSstyle.SUCCESS), column=1)
    
    # Rename Group
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText("<h3 class='mt-5'>Rename Group</h3>"), column=0)
    
    renameable_groups = [g for g in groups if g not in RESERVED_GROUPS]  # type: ignore
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [4, 6, 2]))
    disp.add_display_item(DisplayerItemInputSelect(
        "select_group_to_rename",
        "Select Group",
        value=renameable_groups[0] if renameable_groups else None,
        choices=renameable_groups if renameable_groups else ["(no custom groups)"]
    ), column=0)
    disp.add_display_item(DisplayerItemInputString("input_new_group_name", "New Group Name"), column=1)
    disp.add_display_item(DisplayerItemButton(BTN_RENAME_GROUP, "Rename", color=BSstyle.PRIMARY), column=2)
    
    # Delete Group
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText("<h3 class='mt-5'>Delete Group</h3>"), column=0)
    disp.add_display_item(DisplayerItemText(
        "<div class='alert alert-warning'>Deleting a group removes it from all users and permissions.</div>"
    ), column=0)
    
    deletable_groups = [g for g in groups if g not in RESERVED_GROUPS]  # type: ignore
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [6, 6]))
    disp.add_display_item(DisplayerItemInputSelect(
        "select_group_to_delete",
        "Select Group",
        value=deletable_groups[0] if deletable_groups else None,
        choices=deletable_groups if deletable_groups else ["(no custom groups)"]
    ), column=0)
    disp.add_display_item(DisplayerItemButton(BTN_DELETE_GROUP, "Delete Group", color=BSstyle.ERROR), column=1)
    
    # Info about creating groups
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText(
        "<div class='alert alert-info mt-5'><strong>Note:</strong> Groups are created automatically when "
        "you assign them to users or in the permissions matrix.</div>"
    ), column=0)
    
    return render_template("base_content.j2", content=disp.display(), target="admin_auth.manage_groups")
