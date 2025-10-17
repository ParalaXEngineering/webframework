"""
User profile and preferences management blueprint.
User self-service for password, avatar, and personal settings.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from PIL import Image
import os

try:
    from ..modules.displayer import (
        Displayer, DisplayerLayout, Layouts,
        DisplayerItemText, DisplayerItemButton, DisplayerItemInputString,
        DisplayerItemInputSelect, DisplayerItemImage, DisplayerItemInputFile,
        DisplayerItemAlert, BSstyle
    )
    from ..modules.auth.auth_utils import verify_password, validate_password_strength
    from ..modules import utilities
    from ..modules.log.logger_factory import get_logger
except ImportError:
    from modules.displayer import (
        Displayer, DisplayerLayout, Layouts,
        DisplayerItemText, DisplayerItemButton, DisplayerItemInputString,
        DisplayerItemInputSelect, DisplayerItemImage, DisplayerItemInputFile,
        DisplayerItemAlert, BSstyle
    )
    from modules.auth.auth_utils import verify_password, validate_password_strength
    from modules import utilities
    from modules.log.logger_factory import get_logger

logger = get_logger("user_profile")
user_profile_bp = Blueprint('user_profile', __name__, url_prefix='/user')

# Export as 'bp' for framework auto-discovery
bp = user_profile_bp


def _get_auth_manager():
    """Get the auth_manager instance. Import at runtime to avoid circular imports."""
    try:
        from ..modules.auth.auth_manager import auth_manager
    except ImportError:
        from modules.auth.auth_manager import auth_manager
    return auth_manager


def resize_image(image_path: str, max_size: tuple = (1024, 1024)):
    """
    Resize image to fit within max_size while maintaining aspect ratio.
    
    Args:
        image_path: Path to image file
        max_size: Maximum (width, height) tuple
    """
    img = Image.open(image_path)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    img.save(image_path, optimize=True, quality=95)


@user_profile_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    """User profile page - password, avatar, display name, email."""
    auth_manager = _get_auth_manager()
    
    # Get current user
    current_user = auth_manager.get_current_user()
    if not current_user:
        return redirect(url_for('common.login'))
    
    user = auth_manager.get_user(current_user)
    if not user:
        return redirect(url_for('common.login'))
    
    # Create displayer
    disp = Displayer()
    disp.add_generic("User Profile")
    disp.set_title("My Profile")
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Profile", "user_profile.profile", [])
    
    # Handle POST
    if request.method == 'POST':
        data_in = utilities.util_post_to_json(request.form.to_dict())
        
        if "User Profile" in data_in:
            module_data = data_in["User Profile"]
            
            # Update profile info
            if "btn_update_info" in module_data:
                display_name = module_data.get("input_display_name", "").strip()
                email = module_data.get("input_email", "").strip()
                
                if display_name:
                    auth_manager.update_user_info(current_user, display_name=display_name, email=email or None)
                    flash("Profile updated successfully!", "success")
                else:
                    flash("Display name cannot be empty.", "danger")
            
            # Change password
            elif "btn_change_password" in module_data:
                current_password = module_data.get("input_current_password", "")
                new_password = module_data.get("input_new_password", "")
                confirm_password = module_data.get("input_confirm_password", "")
                
                # Verify current password
                if not verify_password(current_password, user.password_hash):
                    flash("Current password is incorrect.", "danger")
                elif new_password != confirm_password:
                    flash("New passwords do not match.", "danger")
                else:
                    # Validate password strength
                    is_valid, error_msg = validate_password_strength(new_password)
                    if not is_valid:
                        flash(error_msg, "danger")
                    else:
                        auth_manager.update_user_password(current_user, new_password)
                        flash("Password changed successfully!", "success")
            
            # Upload avatar
            elif "btn_upload_avatar" in module_data:
                if 'User Profile.file_avatar' not in request.files:
                    flash("No file uploaded.", "danger")
                else:
                    file = request.files['User Profile.file_avatar']
                    if not file or not file.filename:
                        flash("No file selected.", "danger")
                    else:
                        # Validate file type
                        allowed_extensions = {'jpg', 'jpeg', 'png'}
                        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                        
                        if file_ext not in allowed_extensions:
                            flash("Only JPEG and PNG images are allowed.", "danger")
                        else:
                            # Save with username as filename
                            filename = f"{current_user}.jpg"
                            
                            # Use standard framework path: tests/website/assets/images/users/
                            avatar_dir = 'tests/website/assets/images/users'
                            os.makedirs(avatar_dir, exist_ok=True)
                            filepath = os.path.join(avatar_dir, filename)
                            
                            # Save and resize
                            try:
                                file.save(filepath)
                                resize_image(filepath, max_size=(1024, 1024))
                                auth_manager.update_user_avatar(current_user, filename)
                                flash("Avatar updated successfully!", "success")
                            except Exception as e:
                                flash(f"Error processing image: {str(e)}", "danger")
                                if os.path.exists(filepath):
                                    os.remove(filepath)
        
        # Reload user data
        user = auth_manager.get_user(current_user)
    
    # Profile Information Section
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText("<h3>Profile Information</h3>"), column=0)
    
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [6, 6]))
    disp.add_display_item(DisplayerItemInputString(
        "input_display_name",
        "Display Name",
        value=user.display_name
    ), column=0)
    disp.add_display_item(DisplayerItemInputString(
        "input_email",
        "Email",
        value=user.email or ""
    ), column=1)
    
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemButton(
        "btn_update_info",
        "Update Profile",
        BSstyle.PRIMARY
    ), column=0)
    
    # Avatar Section
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText("<h3 class='mt-5'>Profile Picture</h3>"), column=0)
    
    # Determine avatar URL with cache-busting timestamp
    import time
    timestamp = int(time.time())
    # Avatar is served through the standard /common/assets/images/ route with users/ subdirectory
    avatar_url = f'/common/assets/images/?filename=users/{user.avatar}&t={timestamp}'
    
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [4, 8]))
    disp.add_display_item(DisplayerItemImage(
        height="200px",
        link=avatar_url
    ), column=0)
    
    disp.add_display_item(DisplayerItemInputFile(
        "file_avatar",
        "Upload New Avatar"
    ), column=1)
    disp.add_display_item(DisplayerItemButton(
        "btn_upload_avatar",
        "Upload Avatar",
        BSstyle.PRIMARY
    ), column=1)
    disp.add_display_item(DisplayerItemText(
        "<small class='text-muted'>Allowed: JPEG, PNG. Max size: 1024x1024 (auto-resized)</small>"
    ), column=1)
    
    # Password Change Section (only if user has password)
    if user.password_hash:
        disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
        disp.add_display_item(DisplayerItemText("<h3 class='mt-5'>Change Password</h3>"), column=0)
        
        disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [4, 4, 4]))
        # TODO: Replace with proper password input type when DisplayerItemInputPassword is available
        disp.add_display_item(DisplayerItemText(
            '<div class="mb-3"><label for="input_current_password" class="form-label">Current Password</label>'
            '<input type="password" class="form-control" id="input_current_password" name="input_current_password"></div>'
        ), column=0)
        disp.add_display_item(DisplayerItemText(
            '<div class="mb-3"><label for="input_new_password" class="form-label">New Password</label>'
            '<input type="password" class="form-control" id="input_new_password" name="input_new_password"></div>'
        ), column=1)
        disp.add_display_item(DisplayerItemText(
            '<div class="mb-3"><label for="input_confirm_password" class="form-label">Confirm Password</label>'
            '<input type="password" class="form-control" id="input_confirm_password" name="input_confirm_password"></div>'
        ), column=2)
        
        disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
        disp.add_display_item(DisplayerItemButton(
            "btn_change_password",
            "Change Password",
            BSstyle.WARNING
        ), column=0)
        disp.add_display_item(DisplayerItemText(
            "<small class='text-muted'>Password must be at least 6 characters with letters and numbers.</small>"
        ), column=0)
    else:
        disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
        disp.add_display_item(DisplayerItemText(
            "<div class='alert alert-info mt-5'>This is a passwordless account.</div>"
        ), column=0)
    
    # Account Info
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText("<h3 class='mt-5'>Account Information</h3>"), column=0)
    
    table_layout_id = disp.add_master_layout(DisplayerLayout(Layouts.TABLE, ["Property", "Value"]))
    disp.add_display_item(DisplayerItemText("Username"), column=0, layout_id=table_layout_id)
    disp.add_display_item(DisplayerItemText(user.username), column=1, layout_id=table_layout_id)
    
    disp.add_display_item(DisplayerItemText("Groups"), column=0, layout_id=table_layout_id)
    disp.add_display_item(DisplayerItemText(", ".join(user.groups)), column=1, layout_id=table_layout_id)
    
    disp.add_display_item(DisplayerItemText("Account Created"), column=0, layout_id=table_layout_id)
    disp.add_display_item(DisplayerItemText(user.created_at or "Unknown"), column=1, layout_id=table_layout_id)
    
    disp.add_display_item(DisplayerItemText("Last Login"), column=0, layout_id=table_layout_id)
    disp.add_display_item(DisplayerItemText(user.last_login or "Never"), column=1, layout_id=table_layout_id)
    
    return render_template("base_content.j2", content=disp.display(), target="user_profile.profile")


@user_profile_bp.route('/preferences', methods=['GET', 'POST'])
def preferences():
    """User preferences page - theme, notifications, module settings."""
    auth_manager = _get_auth_manager()
    
    # Get current user
    current_user = auth_manager.get_current_user()
    if not current_user:
        return redirect(url_for('common.login'))
    
    user_prefs = auth_manager.get_user_prefs(current_user)
    is_guest = current_user.upper() == 'GUEST'
    
    # Create displayer
    disp = Displayer()
    disp.add_generic("User Preferences")
    disp.set_title("My Preferences")
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Preferences", "user_profile.preferences", [])
    
    # Show info for GUEST users
    if is_guest:
        disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
        disp.add_display_item(DisplayerItemAlert(
            "<strong>Guest Mode:</strong> You are viewing in read-only mode. GUEST users cannot modify preferences.",
            BSstyle.INFO
        ), column=0)
    
    # Handle POST (only for non-guest users)
    if request.method == 'POST' and not is_guest:
        data_in = utilities.util_post_to_json(request.form.to_dict())
        
        if "User Preferences" in data_in:
            module_data = data_in["User Preferences"]
            
            if "btn_save_prefs" in module_data:
                # Update preferences
                user_prefs["theme"] = module_data.get("select_theme", "light")
                user_prefs["dashboard_layout"] = module_data.get("select_layout", "default")
                
                # Save
                auth_manager.save_user_prefs(current_user, user_prefs)
                flash("Preferences saved successfully!", "success")
    
    # General Preferences
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText("<h3>General Preferences</h3>"), column=0)
    
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [6, 6]))
    disp.add_display_item(DisplayerItemInputSelect(
        "select_theme",
        "Theme",
        value=user_prefs.get("theme", "light"),
        choices=["light", "dark"]
    ), column=0)
    disp.add_display_item(DisplayerItemInputSelect(
        "select_layout",
        "Dashboard Layout",
        value=user_prefs.get("dashboard_layout", "default"),
        choices=["default", "compact", "wide"]
    ), column=1)
    
    # Only show save button for non-guest users
    if not is_guest:
        disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
        disp.add_display_item(DisplayerItemButton(
            "btn_save_prefs",
            "Save Preferences",
            BSstyle.PRIMARY
        ), column=0)
    
    # Module Settings (display as JSON)
    disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
    disp.add_display_item(DisplayerItemText("<h3 class='mt-5'>Module Settings</h3>"), column=0)
    
    import json
    module_settings_json = json.dumps(user_prefs.get("module_settings", {}), indent=2)
    disp.add_display_item(DisplayerItemText(
        f"<pre style='background: #f5f5f5; padding: 1rem; border-radius: 4px;'>{module_settings_json}</pre>"
    ), column=0)
    disp.add_display_item(DisplayerItemText(
        "<small class='text-muted'>Module settings are configured automatically by each module.</small>"
    ), column=0)
    
    return render_template("base_content.j2", content=disp.display(), target="user_profile.preferences")
