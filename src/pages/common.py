"""
Common Pages - Flask blueprint for common/shared routes.

This module contains HTTP route handlers for shared functionality like downloads,
assets, login, and help pages.
"""

from flask import Blueprint, render_template, request, send_file, redirect, session
from typing import Dict, Any, cast
from ..modules import auth

from ..modules import utilities
from ..modules import displayer
from ..modules import site_conf
from ..modules import User_defined_module

import os
import sys
import markdown
from ..modules.log.logger_factory import get_logger

logger = get_logger(__name__)

bp = Blueprint("common", __name__, url_prefix="/common")


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
    if not site_conf.site_conf_obj:
        return "Site configuration not initialized", 500
        
    asset_paths = cast(Dict[str, Any], site_conf.site_conf_obj.get_statics(site_conf.site_conf_app_path))
    logger.debug(f"Asset paths: {asset_paths}")

    folder_path = None
    for path_info in asset_paths:
        if asset_type in path_info:
            folder_path = asset_paths[asset_type]
            break

    if folder_path is None:
        return "Invalid folder type", 404

    file_name = request.args.get("filename")
    if file_name and file_name[0] == ".":
        file_name = file_name[2:]
    
    if not file_name:
        return "Filename required", 400
        
    file_path = os.path.join(folder_path, file_name)

    logger.debug(f"Serving file: {file_path}")

    if not os.path.exists(file_path):
        # For user avatars, try alternative extensions (SVG if JPG requested, or vice versa)
        if file_name.startswith("users/"):
            # Try alternative file extensions for user avatars
            base_name = file_name.rsplit('.', 1)[0] if '.' in file_name else file_name
            alternative_extensions = ['.svg', '.jpg', '.jpeg', '.png']
            
            for ext in alternative_extensions:
                alt_path = os.path.join(folder_path, base_name + ext)
                if os.path.exists(alt_path):
                    logger.debug(f"Serving alternative avatar format: {alt_path}")
                    # Determine MIME type based on extension
                    mimetype = None
                    if ext == '.svg':
                        mimetype = 'image/svg+xml'
                    return send_file(alt_path, as_attachment=False, mimetype=mimetype)
        
        logger.warning(f"File not found: {file_path}")
        return "", 200  # Return empty response to avoid broken image icons

    # Serve images inline for display, not as attachment downloads
    # Set proper MIME type for SVG files
    mimetype = None
    if file_path.lower().endswith('.svg'):
        mimetype = 'image/svg+xml'
    
    return send_file(file_path, as_attachment=False, mimetype=mimetype)


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page with user authentication."""
    if not auth.auth_manager:
        return "Authentication system not initialized", 500
        
    # Logout current user
    auth.auth_manager.logout_current_user()
    
    error_message = None
    
    # Get all users
    users = [u.username for u in auth.auth_manager.get_all_users()]
    users.sort()
    
    if request.method == "POST":
        data_in = utilities.util_post_to_json(request.form.to_dict())
        username = data_in.get("user", "")
        password = data_in.get("password", "")
        
        # Use check_login_attempt for security features (lockout, attempt tracking)
        success, error_message = auth.auth_manager.check_login_attempt(username, password)
        
        if success:
            # Set user in session (set_current_user handles session.permanent)
            auth.auth_manager.set_current_user(username)
            return redirect("/")
        # else: error_message is already set by check_login_attempt
    
    return render_template("login.j2", target="common.login", users=users, message=error_message)


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
