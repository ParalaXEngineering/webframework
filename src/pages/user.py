"""
User profile and preferences management blueprint.
User self-service for password, avatar, and personal settings.
"""

import os
import time

# Third-party
from flask import Blueprint, render_template, request, redirect, url_for, flash
from PIL import Image

try:
    # Local modules (relative import)
    from ..modules.displayer import (
        Displayer, DisplayerLayout, Layouts,
        DisplayerItemText, DisplayerItemButton, DisplayerItemInputString,
        DisplayerItemInputSelect, DisplayerItemFileUpload,
        DisplayerItemAlert, BSstyle
    )
    from ..modules.auth.auth_utils import verify_password, validate_password_strength
    from ..modules import utilities
    from ..modules.log.logger_factory import get_logger
    from ..modules.auth import auth_manager
except ImportError:
    # Local modules (fallback for some contexts)
    from modules.displayer import (
        Displayer, DisplayerLayout, Layouts,
        DisplayerItemText, DisplayerItemButton, DisplayerItemInputString,
        DisplayerItemInputSelect, DisplayerItemFileUpload,
        DisplayerItemAlert, BSstyle
    )
    from modules.auth.auth_utils import verify_password, validate_password_strength
    from modules import utilities
    from modules.log.logger_factory import get_logger
    from modules.auth import auth_manager

logger = get_logger("user_profile")

# Constants - Blueprint and URL routing
BLUEPRINT_NAME = "user_profile"
BLUEPRINT_PREFIX = "/user"
ROUTE_PROFILE = "/profile"
ROUTE_PREFERENCES = "/framework_preferences"

# Constants - UI text and labels
TEXT_ACCESS_RESTRICTED = "Access Restricted"
TEXT_GUEST_ACCESS = "Guest Access"
TEXT_PROFILE_NOT_AVAILABLE = "Profile Not Available for Guest Users"
TEXT_GUEST_CANNOT_ACCESS = "Guest users cannot access or modify profile settings."
TEXT_GUEST_LOGIN_MESSAGE = "Please log in with a registered account to access your profile."
TEXT_MY_PROFILE = "My Profile"
TEXT_PROFILE_BREADCRUMB = "Profile"
TEXT_PROFILE_INFO = "Profile Information"
TEXT_DISPLAY_NAME = "Display Name"
TEXT_EMAIL = "Email"
TEXT_UPDATE_PROFILE = "Update Profile"
TEXT_PROFILE_PICTURE = "Profile Picture"
TEXT_UPLOAD_NEW_AVATAR = "Upload New Avatar"
TEXT_AVATAR_HELP = "Allowed: JPEG, PNG, SVG. Max size: 1024x1024 (auto-resized for raster images)"
TEXT_CHANGE_PASSWORD = "Change Password"
TEXT_CURRENT_PASSWORD = "Current Password"
TEXT_NEW_PASSWORD = "New Password"
TEXT_CONFIRM_PASSWORD = "Confirm Password"
TEXT_CHANGE_PASSWORD_BTN = "Change Password"
TEXT_PASSWORD_REQUIREMENTS = "Password must be at least 5 characters with letters and numbers."
TEXT_PASSWORDLESS_ACCOUNT = "This is a passwordless account."
TEXT_ACCOUNT_INFO = "Account Information"
TEXT_USERNAME = "Username"
TEXT_GROUPS = "Groups"
TEXT_ACCOUNT_CREATED = "Account Created"
TEXT_LAST_LOGIN = "Last Login"
TEXT_UNKNOWN = "Unknown"
TEXT_NEVER = "Never"
TEXT_PROPERTY = "Property"
TEXT_VALUE = "Value"

# Constants - Message keys
MSG_PROFILE_UPDATED = "Profile updated successfully!"
MSG_DISPLAY_NAME_EMPTY = "Display name cannot be empty."
MSG_CURRENT_PASSWORD_INCORRECT = "Current password is incorrect."
MSG_PASSWORDS_NO_MATCH = "New passwords do not match."
MSG_PASSWORD_INVALID = "Invalid password"
MSG_PASSWORD_CHANGED = "Password changed successfully!"
MSG_USER_NOT_FOUND = "User not found."
MSG_ERROR_AUTH_NOT_INIT = "Authentication system not initialized"

# Constants - Form field names
FORM_FIELD_DISPLAY_NAME = "input_display_name"
FORM_FIELD_EMAIL = "input_email"
FORM_FIELD_CURRENT_PASSWORD = "input_current_password"
FORM_FIELD_NEW_PASSWORD = "input_new_password"
FORM_FIELD_CONFIRM_PASSWORD = "input_confirm_password"
FORM_FIELD_AVATAR = "file_avatar"
BUTTON_UPDATE_INFO = "btn_update_info"
BUTTON_CHANGE_PASSWORD = "btn_change_password"

# Constants - Avatar and file upload
AVATAR_UPLOAD_PATH = "images/users"
AVATAR_RENAME_PATTERN = "{username}"
AVATAR_ACCEPT_TYPES = ["image/*"]
AVATAR_SIZE = (200, 200)
AVATAR_MAX_QUALITY = 95
IMAGE_MAX_SIZE = (1024, 1024)
DEFAULT_AVATAR_URL = "/common/assets/images/?filename=users/default.svg"

# Constants - User and authentication
USER_GUEST_NAME = "GUEST"
SESSION_GUEST = "guest"

# Constants - HTTP routes and redirects
ROUTE_LOGIN = "common.login"
ROUTE_SETTINGS_VIEW = "settings.user_view"

user_profile_bp = Blueprint(BLUEPRINT_NAME, __name__, url_prefix=BLUEPRINT_PREFIX)

# Export as 'bp' for framework auto-discovery
bp = user_profile_bp


def resize_image(image_path: str, max_size: tuple = IMAGE_MAX_SIZE):
    """
    Resize image to fit within max_size while maintaining aspect ratio.
    
    Args:
        image_path: Path to image file
        max_size: Maximum (width, height) tuple
    """
    img = Image.open(image_path)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    img.save(image_path, optimize=True, quality=AVATAR_MAX_QUALITY)


@user_profile_bp.route(ROUTE_PROFILE, methods=['GET', 'POST'])
def profile():
    """User profile page - password, avatar, display name, email."""
    # Auth manager is required for this page
    # NOTE: This check should never fail in normal operation since this page
    # is only added to sidebar when authentication is enabled via site_conf
    if not auth_manager:
        logger.error(f"{MSG_ERROR_AUTH_NOT_INIT} - this should not happen")
        return MSG_ERROR_AUTH_NOT_INIT, 500
    
    # Get current user
    current_user = auth_manager.get_current_user()
    if not current_user:
        return redirect(url_for(ROUTE_LOGIN))
    
    # Check if user is guest - redirect with message
    if current_user.upper() == USER_GUEST_NAME:
        disp = Displayer()
        disp.add_generic(TEXT_ACCESS_RESTRICTED)
        disp.set_title(TEXT_GUEST_ACCESS)
        disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
        disp.add_display_item(DisplayerItemAlert(
            f"<h4><i class='mdi mdi-account-alert'></i> {TEXT_PROFILE_NOT_AVAILABLE}</h4>"
            f"<p>{TEXT_GUEST_CANNOT_ACCESS}</p>"
            f"<p>{TEXT_GUEST_LOGIN_MESSAGE}</p>",
            BSstyle.WARNING,
            icon="account-alert"
        ), column=0)
        return render_template("base_content.j2", content=disp.display())
    
    user = auth_manager.get_user(current_user)
    if not user:
        return redirect(url_for(ROUTE_LOGIN))
    
    # Create displayer
    disp = Displayer()
    disp.add_generic(TEXT_MY_PROFILE, display=False)
    disp.set_title(TEXT_MY_PROFILE)
    disp.add_breadcrumb(TEXT_PROFILE_BREADCRUMB, f"{BLUEPRINT_NAME}.profile", [])
    
    # Handle POST
    if request.method == 'POST':
        data_in = utilities.util_post_to_json(request.form.to_dict())
        
        if TEXT_MY_PROFILE in data_in:
            module_data = data_in[TEXT_MY_PROFILE]
            
            # Update profile info
            if BUTTON_UPDATE_INFO in module_data:
                display_name = module_data.get(FORM_FIELD_DISPLAY_NAME, "").strip()
                email = module_data.get(FORM_FIELD_EMAIL, "").strip()
                
                if display_name:
                    auth_manager.update_user_info(current_user, display_name=display_name, email=email or None)
                    flash(MSG_PROFILE_UPDATED, "success")
                else:
                    flash(MSG_DISPLAY_NAME_EMPTY, "danger")
            
            # Change password
            elif BUTTON_CHANGE_PASSWORD in module_data:
                current_password = module_data.get(FORM_FIELD_CURRENT_PASSWORD, "")
                new_password = module_data.get(FORM_FIELD_NEW_PASSWORD, "")
                confirm_password = module_data.get(FORM_FIELD_CONFIRM_PASSWORD, "")
                
                # Verify current password
                if not verify_password(current_password, user.password_hash):
                    flash(MSG_CURRENT_PASSWORD_INCORRECT, "danger")
                elif new_password != confirm_password:
                    flash(MSG_PASSWORDS_NO_MATCH, "danger")
                else:
                    # Validate password strength
                    is_valid, error_msg = validate_password_strength(new_password)
                    if not is_valid:
                        flash(error_msg or MSG_PASSWORD_INVALID, "danger")
                    else:
                        auth_manager.update_user_password(current_user, new_password)
                        flash(MSG_PASSWORD_CHANGED, "success")
            
            # Note: Avatar upload is now handled by simple-upload endpoint via FilePond
            # The file is saved directly to website/assets/images/users/{username}.ext
        
        # Reload user data
        user = auth_manager.get_user(current_user)
    
    if not user:
        flash(MSG_USER_NOT_FOUND, "danger")
        return redirect(url_for(ROUTE_LOGIN))
    
    # Profile Information Section
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText(f"<h3>{TEXT_PROFILE_INFO}</h3>"), column=0)
    
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [6, 6]))
    disp.add_display_item(DisplayerItemInputString(
        FORM_FIELD_DISPLAY_NAME,
        TEXT_DISPLAY_NAME,
        value=user.display_name
    ), column=0)
    disp.add_display_item(DisplayerItemInputString(
        FORM_FIELD_EMAIL,
        TEXT_EMAIL,
        value=user.email or ""
    ), column=1)
    
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemButton(
        BUTTON_UPDATE_INFO,
        TEXT_UPDATE_PROFILE,
        color=BSstyle.PRIMARY
    ), column=0)
    
    # Avatar Section
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText(f"<h3 class='mt-5'>{TEXT_PROFILE_PICTURE}</h3>"), column=0)
    
    # Determine avatar URL with cache-busting timestamp
    timestamp = int(time.time())
    # Avatar is served through the standard /common/assets/images/ route with users/ subdirectory
    avatar_url = f'/common/assets/images/?filename=users/{user.avatar}&t={timestamp}'
    
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [4, 8]))
    # Create avatar display with default.svg fallback
    avatar_html = f'''
    <img id="profile-avatar" src="{avatar_url}" 
         class="rounded-circle" 
         style="width: {AVATAR_SIZE[0]}px; height: {AVATAR_SIZE[1]}px; object-fit: cover;"
         onerror="this.onerror=null; this.src='{DEFAULT_AVATAR_URL}';">
    '''
    disp.add_display_item(DisplayerItemText(avatar_html), column=0)
    
    disp.add_display_item(DisplayerItemFileUpload(
        FORM_FIELD_AVATAR,
        TEXT_UPLOAD_NEW_AVATAR,
        simple=True,
        upload_path=AVATAR_UPLOAD_PATH,
        rename_to=AVATAR_RENAME_PATTERN,
        accept_types=AVATAR_ACCEPT_TYPES,
        multiple=False
    ), column=1)
    disp.add_display_item(DisplayerItemText(
        f"<small class='text-muted'>{TEXT_AVATAR_HELP}</small>"
    ), column=1)
    
    # Password Change Section (only if user has password)
    if user.password_hash:
        disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
        disp.add_display_item(DisplayerItemText(f"<h3 class='mt-5'>{TEXT_CHANGE_PASSWORD}</h3>"), column=0)
        
        disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [4, 4, 4]))
        # TODO: Replace with proper password input type when DisplayerItemInputPassword is available
        # Note: Raw HTML inputs must use module-prefixed names for proper form submission
        disp.add_display_item(DisplayerItemText(
            f'<div class="mb-3"><label for="{FORM_FIELD_CURRENT_PASSWORD}" class="form-label">{TEXT_CURRENT_PASSWORD}</label>'
            f'<input type="password" class="form-control" id="{FORM_FIELD_CURRENT_PASSWORD}" name="{TEXT_MY_PROFILE}.{FORM_FIELD_CURRENT_PASSWORD}"></div>'
        ), column=0)
        disp.add_display_item(DisplayerItemText(
            f'<div class="mb-3"><label for="{FORM_FIELD_NEW_PASSWORD}" class="form-label">{TEXT_NEW_PASSWORD}</label>'
            f'<input type="password" class="form-control" id="{FORM_FIELD_NEW_PASSWORD}" name="{TEXT_MY_PROFILE}.{FORM_FIELD_NEW_PASSWORD}"></div>'
        ), column=1)
        disp.add_display_item(DisplayerItemText(
            f'<div class="mb-3"><label for="{FORM_FIELD_CONFIRM_PASSWORD}" class="form-label">{TEXT_CONFIRM_PASSWORD}</label>'
            f'<input type="password" class="form-control" id="{FORM_FIELD_CONFIRM_PASSWORD}" name="{TEXT_MY_PROFILE}.{FORM_FIELD_CONFIRM_PASSWORD}"></div>'
        ), column=2)
        
        disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
        disp.add_display_item(DisplayerItemButton(
            BUTTON_CHANGE_PASSWORD,
            TEXT_CHANGE_PASSWORD_BTN,
            color=BSstyle.WARNING
        ), column=0)
        disp.add_display_item(DisplayerItemText(
            f"<small class='text-muted'>{TEXT_PASSWORD_REQUIREMENTS}</small>"
        ), column=0)
    else:
        disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
        disp.add_display_item(DisplayerItemText(
            f"<div class='alert alert-info mt-5'>{TEXT_PASSWORDLESS_ACCOUNT}</div>"
        ), column=0)
    
    # Account Info
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText(f"<h3 class='mt-5'>{TEXT_ACCOUNT_INFO}</h3>"), column=0)
    
    table_layout_id = disp.add_master_layout(DisplayerLayout(Layouts.TABLE, [TEXT_PROPERTY, TEXT_VALUE]))
    disp.add_display_item(DisplayerItemText(TEXT_USERNAME), column=0, layout_id=table_layout_id)
    disp.add_display_item(DisplayerItemText(user.username), column=1, layout_id=table_layout_id)
    
    disp.add_display_item(DisplayerItemText(TEXT_GROUPS), column=0, layout_id=table_layout_id)
    disp.add_display_item(DisplayerItemText(", ".join(user.groups)), column=1, layout_id=table_layout_id)
    
    disp.add_display_item(DisplayerItemText(TEXT_ACCOUNT_CREATED), column=0, layout_id=table_layout_id)
    disp.add_display_item(DisplayerItemText(user.created_at or TEXT_UNKNOWN), column=1, layout_id=table_layout_id)
    
    disp.add_display_item(DisplayerItemText(TEXT_LAST_LOGIN), column=0, layout_id=table_layout_id)
    disp.add_display_item(DisplayerItemText(user.last_login or TEXT_NEVER), column=1, layout_id=table_layout_id)
    
    return render_template("base_content.j2", content=disp.display(), target=f"{BLUEPRINT_NAME}.profile")


@user_profile_bp.route(ROUTE_PREFERENCES, methods=['GET', 'POST'])
def framework_preferences():
    """Framework preferences page - redirect to unified settings page."""
    return redirect(url_for(ROUTE_SETTINGS_VIEW))