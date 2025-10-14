"""
Common Pages - Flask blueprint for common/shared routes.

This module contains HTTP route handlers for shared functionality like downloads,
assets, login, and help pages.
"""

from flask import Blueprint, render_template, request, send_file, redirect, url_for, flash, session
from functools import wraps

from ..modules import utilities
from ..modules import access_manager
from ..modules import displayer
from ..modules import site_conf
from ..modules import User_defined_module
from ..modules.auth.auth_manager import auth_manager

import os
import sys
import markdown
import bcrypt

bp = Blueprint("common", __name__, url_prefix="/common")


def require_admin(f):
    """Decorator to require admin group for accessing a page."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not auth_manager:
            # If no auth manager, allow access (backwards compatibility)
            return f(*args, **kwargs)
        
        current_user = session.get('username')
        if not current_user:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('common.login'))
        
        user = auth_manager.get_user(current_user)
        if not user or 'admin' not in user.groups:
            # Show access denied page
            disp = displayer.Displayer()
            disp.add_generic("Access Denied")
            disp.set_title("Access Denied - Admin Only")
            disp.add_breadcrumb("Home", "demo.index", [])
            
            disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
            disp.add_display_item(displayer.DisplayerItemAlert(
                "<h4><i class='bi bi-shield-lock'></i> Administrator Access Required</h4>"
                "<p>This page is restricted to administrators only.</p>"
                f"<p><strong>Current User:</strong> {current_user}</p>"
                f"<p><strong>Your Groups:</strong> {', '.join(user.groups) if user else 'None'}</p>"
                "<hr>"
                "<p>If you need access to this page, please contact your system administrator.</p>",
                displayer.BSstyle.WARNING
            ), column=0)
            
            disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
            disp.add_display_item(displayer.DisplayerItemButtonLink(
                "btn_back",
                "Return to Home",
                "home",
                link=url_for('demo.index'),
                color=displayer.BSstyle.PRIMARY
            ), column=0)
            
            return render_template("base_content.j2", content=disp.display())
        
        return f(*args, **kwargs)
    return decorated_function


@bp.route("/download", methods=["GET"])
def download():
    """Page that handles a download request by serving the file through Flask."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_path = os.path.join(
            os.path.dirname(sys.executable),
            "ressources",
            "downloads",
            request.args.to_dict()["file"],
        )
        send_path = base_path
    else:
        send_path = os.path.join("..", "..", "..", "ressources", "downloads", request.args.to_dict()["file"])
        base_path = os.path.join("ressources", "downloads", request.args.to_dict()["file"])

    if not os.path.exists(base_path):
        return render_template("404.j2")

    return send_file(send_path, as_attachment=True)


@bp.route("/assets/<asset_type>/", methods=["GET"])
def assets(asset_type):
    """Serve asset files based on type."""
    asset_paths = site_conf.site_conf_obj.get_statics(site_conf.site_conf_app_path)
    print(asset_paths)

    folder_path = None
    for path_info in asset_paths:
        if asset_type in path_info:
            folder_path = asset_paths[asset_type]
            break

    if folder_path is None:
        return "Invalid folder type", 404

    file_name = request.args.get("filename")
    if file_name[0] == ".":
        file_name = file_name[2:]
    file_path = os.path.join(folder_path, file_name)

    print(file_path)

    if not os.path.exists(file_path):
        return "", 200  # Return a blank page with status 200

    # Serve images inline for display, not as attachment downloads
    return send_file(file_path, as_attachment=False)


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page with user authentication."""
    # Logout current user
    if access_manager.auth_object:
        access_manager.auth_object.unlog()
    
    # Try to use new auth_manager if available
    try:
        from src.modules.auth.auth_manager import auth_manager as new_auth_manager
        if new_auth_manager:
            error_message = None
            
            # Get all users
            users = [u.username for u in new_auth_manager.get_all_users()]
            users.sort()
            
            if request.method == "POST":
                data_in = utilities.util_post_to_json(request.form.to_dict())
                username = data_in.get("user", "")
                password = data_in.get("password", "")
                
                # Use check_login_attempt for security features (lockout, attempt tracking)
                success, error_message = new_auth_manager.check_login_attempt(username, password)
                
                if success:
                    # Set old auth object for compatibility FIRST
                    if access_manager.auth_object:
                        access_manager.auth_object.set_user(username, True)
                    # Then set new session (this takes priority)
                    new_auth_manager.set_current_user(username)
                    return redirect("/")
                # else: error_message is already set by check_login_attempt
            
            return render_template("login.j2", target="common.login", users=users, message=error_message)
    except ImportError:
        pass
    
    # Fallback to old auth system (if config.json exists)
    try:
        config = utilities.util_read_parameters()
        users = config["access"]["users"]["value"]
        users_password = config["access"]["users_password"]["value"]

        error_message = None

        # Sort users
        users.sort()
        if "GUEST" not in users:
            users = ["GUEST"] + users

        if request.method == "POST":
            data_in = utilities.util_post_to_json(request.form.to_dict())

            username = data_in["user"]
            password_attempt = data_in["password"].encode('utf-8')

            redirect_path = config["core"]["redirect"]["value"] if "core" in config else "/"

            if username in users:
                if username not in users_password:
                    # No password is always allowed for now
                    access_manager.auth_object.set_user(username, True)
                    return redirect(redirect_path)
                else:
                    stored_password = users_password[username][0]
                    stored_hash = stored_password.encode('utf-8')

                    # Verify password with bcrypt
                    try:
                        if bcrypt.checkpw(password_attempt, stored_hash):
                            # Successful login
                            access_manager.auth_object.set_user(username, True)
                            return redirect(redirect_path)
                        else:
                            error_message = "Bad Password for this user"
                    except Exception:
                        access_manager.auth_object.set_user(username, True)
                        return redirect(redirect_path)
            else:
                error_message = "User does not exist"

        return render_template("login.j2", target="common.login", users=users, message=error_message)
    except Exception:
        # No auth configured - show empty login page
        return render_template("login.j2", target="common.login", users=["GUEST"], message=None)


@bp.route("/help", methods=["GET"])
def help():
    """Display help documentation from Markdown files."""
    data_in = request.args.to_dict()
    try:
        topic = data_in["topic"]

        # Open md file
        md_file_path = os.path.join("website", "help", topic + ".md")
        
        # Check if file exists to avoid FileNotFoundError
        if not os.path.exists(md_file_path):
            return "Fichier Markdown non trouvé.", 404
            
        with open(md_file_path, "r", encoding="utf-8") as text:
            text_data = text.read()

        content = markdown.markdown(text_data, extensions=["sane_lists", "toc", "tables"])
        
        disp = displayer.Displayer()
        User_defined_module.User_defined_module.m_default_name = "Help"
        disp.add_module(User_defined_module.User_defined_module, display=False)
        disp.set_title(f"Documentation: {topic.capitalize().replace('_', ' ').upper()}")
        
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle="")
        )

        disp.add_display_item(
            displayer.DisplayerItemAlert(content, displayer.BSstyle.NONE), 0
        )
        
        return render_template("base_content.j2", content=disp.display(), target="")
    except Exception:
        return render_template("base.j2")
