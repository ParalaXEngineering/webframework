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
from ..modules.constants import STATUS_SERVER_ERROR
from ..modules.displayer import (
    BSstyle, Displayer, DisplayerItemButton, DisplayerItemInputBox,
    DisplayerItemInputMultiSelect, DisplayerItemInputPassword,
    DisplayerItemInputSelect, DisplayerItemInputString, DisplayerItemText,
    DisplayerLayout, Layouts, TableMode
)
from ..modules.i18n.messages import (
    # Page Titles and Headings
    TEXT_USER_MANAGEMENT, TEXT_PERMISSION_MANAGEMENT, TEXT_GROUP_MANAGEMENT,
    TEXT_MODULE_PERMISSIONS, TEXT_CURRENT_USERS, TEXT_CREATE_NEW_USER,
    TEXT_UPDATE_USER_GROUPS, TEXT_RESET_USER_PASSWORD, TEXT_DELETE_USER,
    TEXT_CURRENT_GROUPS, TEXT_CREATE_NEW_GROUP, TEXT_RENAME_GROUP,
    TEXT_DELETE_GROUP, TEXT_MODULE_PERMISSION_MATRIX,
    # Breadcrumbs
    TEXT_BREADCRUMB_ADMIN, TEXT_BREADCRUMB_USERS, TEXT_BREADCRUMB_PERMISSIONS,
    TEXT_BREADCRUMB_GROUPS,
    # Buttons
    BUTTON_CREATE_USER, BUTTON_DELETE_USER, BUTTON_UPDATE, BUTTON_RESET,
    BUTTON_CREATE_GROUP, BUTTON_RENAME, BUTTON_DELETE_GROUP,
    BUTTON_SAVE_ALL_PERMISSIONS,
    # Input Labels
    LABEL_USERNAME, LABEL_PASSWORD, LABEL_DISPLAY_NAME, LABEL_EMAIL,
    LABEL_GROUPS_ADMIN, LABEL_SELECT_USER, LABEL_NEW_PASSWORD,
    LABEL_GROUP_NAME, LABEL_SELECT_GROUP, LABEL_NEW_GROUP_NAME,
    LABEL_ACTION,
    # Table Headers and Column Names
    TABLE_HEADER_GROUP_NAME, TABLE_HEADER_NUM_USERS,
    TEXT_USERNAME, TEXT_DISPLAY_NAME, TEXT_GROUPS, TEXT_EMAIL, TEXT_LAST_LOGIN,
    TEXT_NA, TEXT_NEVER,
    # Flash Messages - Errors
    ERROR_INVALID_USERNAME, ERROR_USERNAME_EXISTS, ERROR_INVALID_PASSWORD,
    ERROR_CANNOT_DELETE_SYSTEM_USERS, ERROR_GROUP_NAME_EMPTY, ERROR_GROUP_EXISTS,
    ERROR_CANNOT_RENAME_SYSTEM_GROUPS, ERROR_CANNOT_DELETE_SYSTEM_GROUPS,
    ERROR_AUTH_NOT_INIT,
    # Flash Messages - Success
    MSG_USER_CREATED, MSG_PASSWORDLESS_USER_CREATED, MSG_USER_DELETED,
    MSG_GROUPS_UPDATED, MSG_PASSWORD_RESET, MSG_PERMISSIONS_SAVED,
    MSG_GROUP_CREATED, MSG_GROUP_RENAMED, MSG_GROUP_DELETED,
    # Info Messages
    INFO_NO_MODULES_REGISTERED, INFO_PERMISSION_MATRIX_HELP,
    INFO_DELETE_GROUP_WARNING, INFO_GROUP_AUTO_CREATE,
    # Default/Placeholder values
    TEXT_NO_DELETABLE_USERS, TEXT_NO_CUSTOM_GROUPS,
    # HTML Section Headers
    HTML_CURRENT_USERS, HTML_CREATE_NEW_USER, HTML_UPDATE_USER_GROUPS,
    HTML_RESET_USER_PASSWORD, HTML_DELETE_USER, HTML_MODULE_PERMISSION_MATRIX,
    HTML_CURRENT_GROUPS, HTML_CREATE_NEW_GROUP, HTML_RENAME_GROUP,
    HTML_DELETE_GROUP,
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
        return ERROR_AUTH_NOT_INIT, STATUS_SERVER_ERROR
    
    disp = Displayer()
    disp.add_generic(TEXT_USER_MANAGEMENT)
    disp.add_breadcrumb(TEXT_BREADCRUMB_ADMIN, "admin_auth.manage_users", [])
    disp.add_breadcrumb(TEXT_BREADCRUMB_USERS, "admin_auth.manage_users", [])
    
    if request.method == 'POST':
        data_in = utilities.util_post_to_json(request.form.to_dict())
        
        if str(TEXT_USER_MANAGEMENT) in data_in:
            module_data = data_in[str(TEXT_USER_MANAGEMENT)]
            
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
                    flash(error_msg or ERROR_INVALID_USERNAME, "danger")
                elif auth_manager.get_user(username):
                    flash(ERROR_USERNAME_EXISTS, "danger")
                elif password:
                    is_valid_password, error_msg = validate_password_strength(password)
                    if not is_valid_password:
                        flash(error_msg or ERROR_INVALID_PASSWORD, "danger")
                    else:
                        auth_manager.create_user(username, password, groups, display_name or None, email or None)
                        flash(MSG_USER_CREATED.format(username=username), "success")
                else:
                    # Passwordless user
                    auth_manager.create_user(username, "", groups, display_name or None, email or None)
                    flash(MSG_PASSWORDLESS_USER_CREATED.format(username=username), "success")
            
            # Delete user
            elif BTN_DELETE_USER in module_data:
                username = module_data.get("select_user_to_delete", "")
                if username and username not in RESERVED_USERS:
                    auth_manager.delete_user(username)
                    flash(MSG_USER_DELETED.format(username=username), "success")
                else:
                    flash(ERROR_CANNOT_DELETE_SYSTEM_USERS, "danger")
            
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
                    flash(MSG_GROUPS_UPDATED.format(username=username), "success")
            
            # Reset password
            elif BTN_RESET_PASSWORD in module_data:
                username = module_data.get("select_user_to_reset", "")
                new_password = module_data.get("input_reset_password", "")
                
                if username and new_password:
                    is_valid, error_msg = validate_password_strength(new_password)
                    if not is_valid:
                        flash(error_msg or ERROR_INVALID_PASSWORD, "danger")
                    else:
                        auth_manager.update_user_password(username, new_password)
                        flash(MSG_PASSWORD_RESET.format(username=username), "success")
    
    # User List Table
    users = auth_manager.get_all_users()
    user_data = []
    for user in users:  # type: ignore
        user_data.append({
            "Username": user.username,
            "Display Name": user.display_name,
            "Groups": ", ".join(user.groups),
            "Email": user.email or TEXT_NA,
            "Last Login": user.last_login or TEXT_NEVER
        })
    
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText(HTML_CURRENT_USERS), column=0)
    
    disp.add_master_layout(DisplayerLayout(
        Layouts.TABLE,
        columns=[TEXT_USERNAME, TEXT_DISPLAY_NAME, TEXT_GROUPS, TEXT_EMAIL, TEXT_LAST_LOGIN],
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
    disp.add_display_item(DisplayerItemText(HTML_CREATE_NEW_USER), column=0)
    
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [3, 3, 3, 3]))
    disp.add_display_item(DisplayerItemInputString("input_username", LABEL_USERNAME), column=0)
    disp.add_display_item(DisplayerItemInputPassword("input_password", LABEL_PASSWORD), column=1)
    disp.add_display_item(DisplayerItemInputString("input_display_name", LABEL_DISPLAY_NAME), column=2)
    disp.add_display_item(DisplayerItemInputString("input_email", LABEL_EMAIL), column=3)
    
    all_groups = auth_manager.get_all_groups()
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [8, 4]))
    disp.add_display_item(DisplayerItemInputMultiSelect(
        "input_groups",
        LABEL_GROUPS_ADMIN,
        value=["guest"],
        choices=all_groups
    ), column=0)
    disp.add_display_item(DisplayerItemButton(BTN_CREATE_USER, BUTTON_CREATE_USER, color=BSstyle.SUCCESS), column=1)
    
    # Update User Groups
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText(HTML_UPDATE_USER_GROUPS), column=0)
    
    usernames = [u.username for u in users]  # type: ignore
    first_user_groups = users[0].groups if users else []
    
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [4, 6, 2]))
    disp.add_display_item(DisplayerItemInputSelect(
        "select_user_to_update",
        LABEL_SELECT_USER,
        value=usernames[0] if usernames else None,
        choices=usernames
    ), column=0)
    disp.add_display_item(DisplayerItemInputMultiSelect(
        "input_update_groups",
        LABEL_GROUPS_ADMIN,
        value=first_user_groups,
        choices=all_groups
    ), column=1)
    disp.add_display_item(DisplayerItemButton(BTN_UPDATE_GROUPS, BUTTON_UPDATE, color=BSstyle.PRIMARY), column=2)
    
    # Reset Password
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText(HTML_RESET_USER_PASSWORD), column=0)
    
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [4, 6, 2]))
    disp.add_display_item(DisplayerItemInputSelect(
        "select_user_to_reset",
        LABEL_SELECT_USER,
        value=usernames[0] if usernames else None,
        choices=usernames
    ), column=0)
    disp.add_display_item(DisplayerItemInputPassword("input_reset_password", LABEL_NEW_PASSWORD), column=1)
    disp.add_display_item(DisplayerItemButton(BTN_RESET_PASSWORD, BUTTON_RESET, color=BSstyle.WARNING), column=2)
    
    # Delete User
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText(HTML_DELETE_USER), column=0)
    
    deletable_users = [u.username for u in users if u.username not in RESERVED_USERS]  # type: ignore
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [6, 6]))
    disp.add_display_item(DisplayerItemInputSelect(
        "select_user_to_delete",
        LABEL_SELECT_USER,
        value=deletable_users[0] if deletable_users else None,
        choices=deletable_users if deletable_users else [TEXT_NO_DELETABLE_USERS]
    ), column=0)
    disp.add_display_item(DisplayerItemButton(BTN_DELETE_USER, BUTTON_DELETE_USER, color=BSstyle.ERROR), column=1)
    
    return render_template("base_content.j2", content=disp.display(), target="admin_auth.manage_users")


@admin_auth_bp.route('/permissions', methods=['GET', 'POST'])
@require_admin()
def manage_permissions():
    """Module permissions matrix management."""
    
    if not auth_manager:
        return ERROR_AUTH_NOT_INIT, STATUS_SERVER_ERROR
    
    disp = Displayer()
    disp.add_generic(TEXT_PERMISSION_MANAGEMENT)
    disp.set_title(TEXT_MODULE_PERMISSIONS)
    disp.add_breadcrumb(TEXT_BREADCRUMB_ADMIN, "admin_auth.manage_users", [])
    disp.add_breadcrumb(TEXT_BREADCRUMB_PERMISSIONS, "admin_auth.manage_permissions", [])
    
    if request.method == 'POST':
        data_in = utilities.util_post_to_json(request.form.to_dict())
        
        if str(TEXT_PERMISSION_MANAGEMENT) in data_in:
            module_data = data_in[str(TEXT_PERMISSION_MANAGEMENT)]
            
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
                
                flash(MSG_PERMISSIONS_SAVED, "success")
    
    # Get all modules and groups (excluding admin)
    all_modules = permission_registry.get_all_modules()
    all_groups = [g for g in auth_manager.get_all_groups() if g != SYSTEM_ADMIN_GROUP]  # type: ignore
    
    if not all_modules:
        disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
        disp.add_display_item(DisplayerItemText(INFO_NO_MODULES_REGISTERED), column=0)
        return render_template("base_content.j2", content=disp.display(), target="admin_auth.manage_permissions")
    
    # Permission Matrix
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText(HTML_MODULE_PERMISSION_MATRIX), column=0)
    disp.add_display_item(DisplayerItemText(INFO_PERMISSION_MATRIX_HELP), column=0)
    
    # Create table with modules as rows
    for module_name in all_modules:
        disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
        disp.add_display_item(DisplayerItemText(f"<h4 class='mt-4'>{module_name}</h4>"), column=0)
        
        actions = permission_registry.get_module_actions(module_name)
        current_perms = auth_manager.get_module_permissions(module_name)
        
        # Create table: rows=actions, cols=groups
        header = [LABEL_ACTION] + all_groups
        layout_id = disp.add_master_layout(DisplayerLayout(Layouts.TABLE, header))
        
        for action_idx, action in enumerate(actions):
            row: list = [DisplayerItemText("<strong>{}</strong>".format(action))]
            
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
        BUTTON_SAVE_ALL_PERMISSIONS,
        color=BSstyle.PRIMARY
    ), column=0)
    
    return render_template("base_content.j2", content=disp.display(), target="admin_auth.manage_permissions")


@admin_auth_bp.route('/groups', methods=['GET', 'POST'])
@require_admin()
def manage_groups():
    """Group management page."""
    
    if not auth_manager:
        return ERROR_AUTH_NOT_INIT, STATUS_SERVER_ERROR
    
    disp = Displayer()
    disp.add_generic(TEXT_GROUP_MANAGEMENT)
    disp.set_title(TEXT_GROUP_MANAGEMENT)
    disp.add_breadcrumb(TEXT_BREADCRUMB_ADMIN, "admin_auth.manage_users", [])
    disp.add_breadcrumb(TEXT_BREADCRUMB_GROUPS, "admin_auth.manage_groups", [])
    
    if request.method == 'POST':
        data_in = utilities.util_post_to_json(request.form.to_dict())
        
        if str(TEXT_GROUP_MANAGEMENT) in data_in:
            module_data = data_in[str(TEXT_GROUP_MANAGEMENT)]
            
            # Create new group
            if BTN_CREATE_GROUP in module_data:
                group_name = module_data.get("input_new_group", "").strip()
                
                if not group_name:
                    flash(ERROR_GROUP_NAME_EMPTY, "danger")
                elif group_name in auth_manager.get_all_groups():
                    flash(ERROR_GROUP_EXISTS.format(group_name=group_name), "danger")
                else:
                    auth_manager.create_group(group_name)
                    flash(MSG_GROUP_CREATED.format(group_name=group_name), "success")
            
            # Rename group
            elif BTN_RENAME_GROUP in module_data:
                old_name = module_data.get("select_group_to_rename", "")
                new_name = module_data.get("input_new_group_name", "").strip()
                
                if old_name and new_name:
                    if old_name in RESERVED_GROUPS:
                        flash(ERROR_CANNOT_RENAME_SYSTEM_GROUPS, "danger")
                    elif new_name in auth_manager.get_all_groups():
                        flash(ERROR_GROUP_EXISTS.format(group_name=new_name), "danger")
                    else:
                        auth_manager.rename_group(old_name, new_name)
                        flash(MSG_GROUP_RENAMED.format(old_name=old_name, new_name=new_name), "success")
            
            # Delete group
            elif BTN_DELETE_GROUP in module_data:
                group_name = module_data.get("select_group_to_delete", "")
                
                if group_name in RESERVED_GROUPS:
                    flash(ERROR_CANNOT_DELETE_SYSTEM_GROUPS, "danger")
                elif group_name:
                    auth_manager.delete_group(group_name)
                    flash(MSG_GROUP_DELETED.format(group_name=group_name), "success")
    
    # Current Groups
    groups = auth_manager.get_all_groups()
    
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText(HTML_CURRENT_GROUPS), column=0)
    
    layout_id = disp.add_master_layout(DisplayerLayout(Layouts.TABLE, [TABLE_HEADER_GROUP_NAME, TABLE_HEADER_NUM_USERS]))
    users = auth_manager.get_all_users()
    for line_idx, group in enumerate(groups):
        user_count = sum(1 for u in users if group in u.groups)  # type: ignore
        disp.add_display_item(DisplayerItemText(group), 0, line=line_idx, layout_id=layout_id)
        disp.add_display_item(DisplayerItemText(str(user_count)), 1, line=line_idx, layout_id=layout_id)
    
    # Create New Group
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText(HTML_CREATE_NEW_GROUP), column=0)
    
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [8, 4]))
    disp.add_display_item(DisplayerItemInputString("input_new_group", LABEL_GROUP_NAME), column=0)
    disp.add_display_item(DisplayerItemButton(BTN_CREATE_GROUP, BUTTON_CREATE_GROUP, color=BSstyle.SUCCESS), column=1)
    
    # Rename Group
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText(HTML_RENAME_GROUP), column=0)
    
    renameable_groups = [g for g in groups if g not in RESERVED_GROUPS]  # type: ignore
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [4, 6, 2]))
    disp.add_display_item(DisplayerItemInputSelect(
        "select_group_to_rename",
        LABEL_SELECT_GROUP,
        value=renameable_groups[0] if renameable_groups else None,
        choices=renameable_groups if renameable_groups else [TEXT_NO_CUSTOM_GROUPS]
    ), column=0)
    disp.add_display_item(DisplayerItemInputString("input_new_group_name", LABEL_NEW_GROUP_NAME), column=1)
    disp.add_display_item(DisplayerItemButton(BTN_RENAME_GROUP, BUTTON_RENAME, color=BSstyle.PRIMARY), column=2)
    
    # Delete Group
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText(HTML_DELETE_GROUP), column=0)
    disp.add_display_item(DisplayerItemText(INFO_DELETE_GROUP_WARNING), column=0)
    
    deletable_groups = [g for g in groups if g not in RESERVED_GROUPS]  # type: ignore
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [6, 6]))
    disp.add_display_item(DisplayerItemInputSelect(
        "select_group_to_delete",
        LABEL_SELECT_GROUP,
        value=deletable_groups[0] if deletable_groups else None,
        choices=deletable_groups if deletable_groups else [TEXT_NO_CUSTOM_GROUPS]
    ), column=0)
    disp.add_display_item(DisplayerItemButton(BTN_DELETE_GROUP, BUTTON_DELETE_GROUP, color=BSstyle.ERROR), column=1)
    
    # Info about creating groups
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText(INFO_GROUP_AUTO_CREATE), column=0)
    
    return render_template("base_content.j2", content=disp.display(), target="admin_auth.manage_groups")
