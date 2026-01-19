"""
Common Pages - Flask blueprint for common/shared routes.

This module contains HTTP route handlers for shared functionality like downloads,
assets, login, and help pages.
"""

# Standard library
import os
import sys
from typing import Dict, Any, cast

# Third-party
from flask import Blueprint, render_template, request, send_file, redirect, session
import markdown

# Framework modules - constants and i18n
from ..modules.constants import (
    STATUS_OK,
    STATUS_BAD_REQUEST,
    STATUS_NOT_FOUND,
    STATUS_SERVER_ERROR,
    METHOD_GET,
    METHOD_POST,
    GET_POST,
    PARAM_FILE,
    PARAM_FILENAME,
    PARAM_USER,
    PARAM_PASSWORD
)
from ..modules.i18n.messages import (
    ERROR_CONFIG_NOT_INIT,
    ERROR_INVALID_FOLDER,
    ERROR_FILENAME_REQUIRED,
    ERROR_FILE_NOT_FOUND,
    DEFAULT_HELP_TITLE,
    TEXT_404_TEMPLATE,
    TEXT_HELP,
    TEXT_LOGIN_TEMPLATE,
    TEXT_TEMPLATE_BASE,
    TEXT_TEMPLATE_BASE_CONTENT
)

# Framework modules - core functionality
from ..modules import auth, displayer, User_defined_module, utilities
from ..modules.app_context import app_context
from ..modules.log.logger_factory import get_logger

logger = get_logger(__name__)

# =============================================================================
# Domain-Specific Constants (Common Pages)
# =============================================================================

# Blueprint Configuration
BP_NAME = "common"
BP_URL_PREFIX = "/common"
bp = Blueprint(BP_NAME, __name__, url_prefix=BP_URL_PREFIX)

# Route Paths
ROUTE_DOWNLOAD = "/download"
ROUTE_ASSETS = "/assets/<asset_type>/"
ROUTE_LOGIN = "/login"
ROUTE_HELP = "/help"

# Resource Paths
RESOURCES_DIR = "ressources"
DOWNLOADS_DIR = "downloads"
WEBSITE_DIR = "website"
HELP_DIR = "help"
MEIPASS_RESOURCES = "ressources"

# File Handling
FILE_EXTENSION_SVG = ".svg"
FILE_EXTENSION_JPG = ".jpg"
FILE_EXTENSION_JPEG = ".jpeg"
FILE_EXTENSION_PNG = ".png"
MIME_TYPE_SVG = "image/svg+xml"

# Query Parameters (domain-specific)
PARAM_TOPIC = "topic"

# Form Field Names (domain-specific)
FIELD_USER = "user"
FIELD_PASSWORD = "password"

# Markdown Configuration
MARKDOWN_EXTENSIONS = ["sane_lists", "toc", "tables"]

# Avatar Configuration
AVATAR_PREFIX = "users/"
AVATAR_EXTENSIONS = [FILE_EXTENSION_SVG, FILE_EXTENSION_JPG, FILE_EXTENSION_JPEG, FILE_EXTENSION_PNG]


@bp.route(ROUTE_DOWNLOAD, methods=[METHOD_GET])
def download():
    """Page that handles a download request by serving the file through Flask."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_path = os.path.join(
            os.path.dirname(sys.executable),
            MEIPASS_RESOURCES,
            DOWNLOADS_DIR,
            request.args.to_dict()[PARAM_FILE],
        )
        send_path = base_path
    else:
        send_path = os.path.join("..", "..", "..", RESOURCES_DIR, DOWNLOADS_DIR, request.args.to_dict()[PARAM_FILE])
        base_path = os.path.join(RESOURCES_DIR, DOWNLOADS_DIR, request.args.to_dict()[PARAM_FILE])

    if not os.path.exists(base_path):
        return render_template(TEXT_404_TEMPLATE)

    return send_file(send_path, as_attachment=True)


@bp.route(ROUTE_ASSETS, methods=[METHOD_GET])
def assets(asset_type):
    """Serve asset files based on type."""
    if not app_context.site_conf:
        return ERROR_CONFIG_NOT_INIT, STATUS_SERVER_ERROR
        
    asset_paths = cast(Dict[str, Any], app_context.site_conf.get_statics(app_context.app_path))
    logger.debug(f"Asset paths: {asset_paths}")

    folder_path = None
    for path_info in asset_paths:
        if asset_type in path_info:
            folder_path = asset_paths[asset_type]
            break

    # Handle plugin asset types (e.g., "tracker_js", "tracker_css")
    # Format: {plugin_name}_{asset_subtype} -> submodules/{plugin_name}/web/assets/{asset_subtype}/
    if folder_path is None and '_' in asset_type:
        plugin_name, asset_subtype = asset_type.rsplit('_', 1)
        if hasattr(app_context, 'plugins') and plugin_name in app_context.plugins:
            plugin = app_context.plugins[plugin_name]
            if hasattr(plugin, 'get_assets_path'):
                plugin_assets = plugin.get_assets_path()
                if plugin_assets:
                    folder_path = os.path.join(plugin_assets, asset_subtype)
                    logger.debug(f"Plugin asset path for {asset_type}: {folder_path}")

    if folder_path is None:
        return ERROR_INVALID_FOLDER, STATUS_NOT_FOUND

    file_name = request.args.get(PARAM_FILENAME)
    if file_name and file_name[0] == ".":
        file_name = file_name[2:]
    
    if not file_name:
        return ERROR_FILENAME_REQUIRED, STATUS_BAD_REQUEST
        
    file_path = os.path.join(folder_path, file_name)

    logger.debug(f"Serving file: {file_path}")

    if not os.path.exists(file_path):
        # For user avatars, try alternative extensions (SVG if JPG requested, or vice versa)
        if file_name.startswith(AVATAR_PREFIX):
            # Try alternative file extensions for user avatars
            base_name = file_name.rsplit('.', 1)[0] if '.' in file_name else file_name
            
            for ext in AVATAR_EXTENSIONS:
                alt_path = os.path.join(folder_path, base_name + ext)
                if os.path.exists(alt_path):
                    logger.debug(f"Serving alternative avatar format: {alt_path}")
                    # Determine MIME type based on extension
                    mimetype = None
                    if ext == FILE_EXTENSION_SVG:
                        mimetype = MIME_TYPE_SVG
                    return send_file(alt_path, as_attachment=False, mimetype=mimetype)
        
        logger.warning(f"File not found: {file_path}")
        return "", STATUS_OK  # Return empty response to avoid broken image icons

    # Serve images inline for display, not as attachment downloads
    # Set proper MIME type for SVG files
    mimetype = None
    if file_path.lower().endswith(FILE_EXTENSION_SVG):
        mimetype = MIME_TYPE_SVG
    
    return send_file(file_path, as_attachment=False, mimetype=mimetype)


@bp.route(ROUTE_LOGIN, methods=GET_POST)
def login():
    """Login page with user authentication."""
    if not app_context.auth_manager:
        return ERROR_CONFIG_NOT_INIT, STATUS_SERVER_ERROR
        
    # Logout current user
    app_context.auth_manager.logout_current_user()
    
    error_message = None
    
    # Get next URL from query parameter (where to redirect after login)
    next_url = request.args.get('next', '/')
    
    # Get all users
    users = [u.username for u in app_context.auth_manager.get_all_users()]  # type: ignore
    users.sort()
    
    if request.method == METHOD_POST:
        # Check IP-based rate limit BEFORE processing login
        ip_address = request.remote_addr or "unknown"
        rate_allowed, rate_message = auth.login_rate_limiter.check(ip_address)
        
        if not rate_allowed:
            # IP is rate limited - show message and don't process login
            return render_template(TEXT_LOGIN_TEMPLATE, target=f"{BP_NAME}.login", users=users, message=rate_message, next_url=next_url)
        
        data_in = utilities.util_post_to_json(request.form.to_dict())
        username = data_in.get(FIELD_USER, "")
        password = data_in.get(FIELD_PASSWORD, "")
        
        # Get next URL from POST data (hidden field) if not in query string
        if 'next' in data_in:
            next_url = data_in['next']
        
        # Use check_login_attempt for security features (lockout, attempt tracking)
        success, error_message = cast(Any, app_context.auth_manager).check_login_attempt(username, password)  # type: ignore
        
        # Record IP-based attempt outcome for rate limiting
        auth.login_rate_limiter.record_attempt(ip_address, success)
        
        if success:
            # Set user in session (set_current_user handles session.permanent)
            app_context.auth_manager.set_current_user(username)
            
            # Validate and redirect to next URL (prevent open redirect attacks)
            if auth.is_safe_redirect_url(next_url):
                return redirect(next_url)
            else:
                # Invalid next URL - go to home
                logger.warning(f"Blocked unsafe redirect to: {next_url}")
                return redirect("/")
        # else: error_message is already set by check_login_attempt
    
    return render_template(TEXT_LOGIN_TEMPLATE, target=f"{BP_NAME}.login", users=users, message=error_message, next_url=next_url)


@bp.route(ROUTE_HELP, methods=[METHOD_GET])
def help_legacy():
    """Display help documentation from Markdown files (legacy system)."""
    data_in = request.args.to_dict()
    try:
        topic = data_in[PARAM_TOPIC]

        # Open md file
        md_file_path = os.path.join(WEBSITE_DIR, HELP_DIR, topic + ".md")
        
        # Check if file exists to avoid FileNotFoundError
        if not os.path.exists(md_file_path):
            return ERROR_FILE_NOT_FOUND, STATUS_NOT_FOUND
            
        with open(md_file_path, "r", encoding="utf-8") as text:
            text_data = text.read()

        content = markdown.markdown(text_data, extensions=MARKDOWN_EXTENSIONS)
        
        disp = displayer.Displayer()
        User_defined_module.User_defined_module.m_default_name = TEXT_HELP
        disp.add_module(User_defined_module.User_defined_module, display=False)
        disp.set_title(DEFAULT_HELP_TITLE.format(topic.capitalize().replace('_', ' ').upper()))
        
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle="")
        )

        disp.add_display_item(
            displayer.DisplayerItemAlert(content, displayer.BSstyle.NONE), 0
        )
        
        return render_template(TEXT_TEMPLATE_BASE_CONTENT, content=disp.display(), target="")
    except Exception:
        return render_template(TEXT_TEMPLATE_BASE)
