"""ParalaX Web Framework - Main application initialization and routing.

Handles Flask app setup, blueprint registration, feature flag initialization,
SocketIO setup for real-time features, and context processors for templates.
"""

import importlib
import os
import shutil
import sys
import threading
import time
import traceback
import uuid
import webbrowser

try:
    from flask import Flask, g, render_template, request, session
    from flask_session import Session
    from flask_socketio import SocketIO
    FLASK_AVAILABLE = True
except ImportError:
    # Flask not available - create dummy classes for import testing
    Flask = None  # type: ignore
    g = None  # type: ignore
    render_template = None  # type: ignore
    request = None  # type: ignore
    session = None  # type: ignore
    Session = None  # type: ignore
    SocketIO = None  # type: ignore
    FLASK_AVAILABLE = False

from .modules import scheduler
from .modules.app_context import app_context
from .modules.log.logger_factory import format_exception_html, get_logger
from .modules.socketio_manager import initialize_socketio_manager
from .modules.threaded import threaded_manager

# Framework modules - constants
from .modules.constants import USER_GUEST_NAME

# Domain-specific constants for main application setup
COOKIE_SAMESITE = "Lax"
SESSION_TYPE = "filesystem"
SESSION_FILE_DIR = "flask_session"
SESSION_FILE_THRESHOLD = 100  # Max sessions before cleanup
SESSION_PERMANENT_LIFETIME_HOURS = 24  # Session expiry in hours
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5000
DEFAULT_USER = USER_GUEST_NAME  # Use framework constant for consistency
ANONYMOUS_USER = "anonymous"
STARTUP_URL = "http://127.0.0.1:5000/common/login"
WEBSITE_PAGES_PATH = "website/pages"
WEBSITE_AUTH_PATH = "website/auth"
WEBSITE_CONFIG_PATH = "website/config.json"
WEBSITE_SCHEDULER_PATH = "website/scheduler.py"
WEBSITE_SITE_CONF_PATH = "website.site_conf"
LOGS_DIR_NAME = "logs"
FAVICON_INSTANCE_PATH = "website/assets/images/logo/favicon.png"
FAVICON_FRAMEWORK_PATH = "webengine/assets/images/logo/favicon.png"
DEFAULT_AVATAR_INSTANCE_PATH = "website/assets/images/users/default.svg"
DEFAULT_AVATAR_FRAMEWORK_PATH = "webengine/assets/images/users/default.svg"
IGNORED_404_PATHS = [
    "/.well-known/appspecific/com.chrome.devtools.json",
    "/favicon.ico",
    "/.well-known/",
]
LOG_EMITTER_INTERVAL = 2.0
THREAD_EMITTER_INTERVAL = 0.5

# Module-level auth_manager variable (initialized in setup_app)
auth_manager = None

# Middleware to support reverse proxy with URL prefix
class PrefixMiddleware:
    """
    Middleware to handle X-Forwarded-Prefix header from reverse proxies.
    
    When nginx (or other reverse proxy) sends X-Forwarded-Prefix header,
    this middleware sets SCRIPT_NAME so Flask's url_for() generates correct URLs.
    """
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # Read X-Forwarded-Prefix header (set by nginx)
        prefix = environ.get('HTTP_X_FORWARDED_PREFIX', '')
        if prefix:
            # Remove trailing slash to avoid double slashes
            prefix = prefix.rstrip('/')
            # Set SCRIPT_NAME so Flask knows about the prefix
            environ['SCRIPT_NAME'] = prefix
            # Adjust PATH_INFO by removing the prefix if it's there
            path_info = environ.get('PATH_INFO', '')
            if path_info.startswith(prefix):
                environ['PATH_INFO'] = path_info[len(prefix):]
        
        return self.app(environ, start_response)


# Create Flask app only if Flask is available
if FLASK_AVAILABLE:
    app = Flask(  # type: ignore
        __name__,
        instance_relative_config=True,
        static_folder=os.path.join("..", "webengine", "assets"),
        template_folder=os.path.join("..", "templates")
    )
    # Apply prefix middleware to handle reverse proxy URL prefixes
    app.wsgi_app = PrefixMiddleware(app.wsgi_app)  # type: ignore
else:
    app = None  # Placeholder when Flask is not available

def authorize_refresh(f):
    f._disable_csrf = True  # Ajouter un attribut personnalisé
    return f


def _ensure_default_assets(app_path, framework_root, logger):
    """
    Ensure required default assets exist in the instance.
    
    Checks for favicon and default user avatar, copying from framework 
    defaults if missing. Skips copying if files already exist.
    
    Args:
        app_path: Path to the instance (e.g., Manual_Webapp root)
        framework_root: Path to the framework root
        logger: Logger instance for messages
    """
    # Define required assets: (instance_path, framework_source_path, description)
    required_assets = [
        (
            os.path.join(app_path, FAVICON_INSTANCE_PATH),
            os.path.join(framework_root, FAVICON_FRAMEWORK_PATH),
            "favicon"
        ),
        (
            os.path.join(app_path, DEFAULT_AVATAR_INSTANCE_PATH),
            os.path.join(framework_root, DEFAULT_AVATAR_FRAMEWORK_PATH),
            "default user avatar"
        ),
    ]
    
    for instance_path, framework_path, description in required_assets:
        # Skip if already exists in instance
        if os.path.exists(instance_path):
            logger.debug("%s already exists: %s", description.capitalize(), instance_path)
            continue
        
        # Check if framework default exists
        if not os.path.exists(framework_path):
            logger.warning("Framework default %s not found: %s", description, framework_path)
            continue
        
        # Create directory if needed
        instance_dir = os.path.dirname(instance_path)
        if not os.path.exists(instance_dir):
            os.makedirs(instance_dir)
            logger.debug("Created directory: %s", instance_dir)
        
        # Copy from framework to instance
        try:
            shutil.copy2(framework_path, instance_path)
            logger.debug("Copied %s from framework defaults: %s", description, os.path.basename(instance_path))
        except Exception as e:
            logger.error("Failed to copy %s: %s", description, e)


def setup_app(app):
    """Setup Flask app. Only call when FLASK_AVAILABLE is True."""
    import sys
    if not FLASK_AVAILABLE:
        return None
    
    # Validate SECRET_KEY was set by caller application
    if 'SECRET_KEY' not in app.config or not app.config['SECRET_KEY']:
        error_msg = (
            "\n" + "="*80 + "\n"
            "ERROR: SECRET_KEY not configured!\n"
            "\n"
            "The SECRET_KEY must be set by the calling application BEFORE calling setup_app().\n"
            "\n"
            "Recommended approach:\n"
            "  1. Create a .secret_key file in your application root with a random key\n"
            "  2. Add .secret_key to your .gitignore\n"
            "  3. Set app.config['SECRET_KEY'] before calling setup_app()\n"
            "\n"
            "Quick setup commands:\n"
            "  python -c \"import secrets; print(secrets.token_hex(32))\" > .secret_key\n"
            "  echo '.secret_key' >> .gitignore\n"
            "\n"
            "Then in your main.py:\n"
            "  from pathlib import Path\n"
            "  app.config['SECRET_KEY'] = Path('.secret_key').read_text().strip()\n"
            "\n"
            "="*80 + "\n"
        )
        raise RuntimeError(error_msg)
    
    # Session configuration with expiration and cleanup
    from datetime import timedelta
    app.config["SESSION_TYPE"] = SESSION_TYPE  # type: ignore
    app.config["SESSION_FILE_DIR"] = SESSION_FILE_DIR  # type: ignore
    app.config["SESSION_FILE_THRESHOLD"] = SESSION_FILE_THRESHOLD  # type: ignore
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=SESSION_PERMANENT_LIFETIME_HOURS)  # type: ignore
    app.config['TEMPLATES_AUTO_RELOAD'] = False  # type: ignore
    app.config["PROPAGATE_EXCEPTIONS"] = False  # type: ignore
    app.config["SESSION_PERMANENT"] = True  # type: ignore
    app.config["SESSION_COOKIE_SAMESITE"] = COOKIE_SAMESITE  # type: ignore
    app.config.from_object(__name__)  # type: ignore
    Session(app)  # type: ignore

    socketio_obj = SocketIO(app)  # type: ignore
    
    # Initialize Babel for i18n support
    from .modules.i18n import init_babel
    init_babel(app)
    
    # Initialize logger using centralized factory and log application start
    logger = get_logger("main")
    logger.info("Application starting up")
    
    # Initialize SocketIO manager for user isolation
    socketio_manager_obj = initialize_socketio_manager(socketio_obj)
    logger.info("SocketIO manager initialized for multi-user support")

    # Detect if we're running from exe
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        app_path = sys._MEIPASS  # type: ignore
    else:
        # Go up 2 levels from src/main.py to get framework root
        # src/main.py -> src/ -> webframework/
        app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Ensure required default assets exist (favicon, default avatar)
    # Use app_path from app_context if set (instance path), otherwise use local app_path
    instance_path = app_context.app_path if app_context.app_path else app_path
    _ensure_default_assets(instance_path, app_path, logger)

    # Get all Python files in the website pages directory (if it exists)
    website_pages_path = os.path.join(app_path, WEBSITE_PAGES_PATH)
    if os.path.exists(website_pages_path):
        files = [f for f in os.listdir(website_pages_path) if f.endswith(".py") and not f.startswith("__")]
        
        # Import each module and register its blueprint
        for file in files:
            module_name = file[:-3]  # Remove the ".py" extension
            
            try:
                # Import the module
                page_module = importlib.import_module(f"website.pages.{module_name}")
                
                # Register the blueprint if it exists
                if hasattr(page_module, 'bp'):
                    app.register_blueprint(page_module.bp)
                    logger.debug("Registered website page blueprint: %s", module_name)
            except ImportError as e:
                logger.debug("Failed to import website page %s: %s", module_name, e)
            except Exception as e:
                logger.debug("Failed to register blueprint for %s: %s", module_name, e)

    # Import site_conf FIRST (before any feature-dependent initialization)
    # Only set if not already configured (e.g., by test setup)
    from .modules.site_conf import Site_conf
    if app_context.site_conf is None:
        try:
            app_context.site_conf = importlib.import_module(WEBSITE_SITE_CONF_PATH).ExampleSiteConf()
            app_context.app_path = app_path
            logger.debug("Loaded website.site_conf")
        except (ModuleNotFoundError, AttributeError) as e:
            logger.debug("No website.site_conf found - using default Site_conf: %s", e)
            app_context.site_conf = Site_conf()
    else:
        logger.debug("Using pre-configured site_conf: %s", type(app_context.site_conf).__name__)
    
    # Get site configuration for feature flags
    site_config = app_context.site_conf

    # Auto-discover and register framework internal pages
    from src import pages as pages_module
    
    # Map of page names to required feature flags
    # Note: 'common' is always registered as it provides essential assets serving
    PAGE_FEATURE_REQUIREMENTS = {
        'threads': 'm_enable_threads',
        # 'common': Always registered - provides assets serving for all pages
        'logging': 'm_enable_log_viewer',
        'bug_tracker': 'm_enable_bug_tracker',
        'settings': 'm_enable_settings',
        'updater': 'm_enable_updater',
        'packager': 'm_enable_packager',
        'user': 'm_enable_authentication',
        'admin': 'm_enable_authentication',
        'file_handler': 'm_enable_file_manager',
        'file_manager_admin': 'm_file_manager_admin',
    }
    
    # Get the pages directory path
    pages_dir = os.path.dirname(os.path.abspath(pages_module.__file__))
    
    # Get all Python files in the pages directory
    # Exclude 'help' since it's registered conditionally via m_enable_help feature flag
    framework_pages = [f[:-3] for f in os.listdir(pages_dir) 
                       if f.endswith('.py') and f != '__init__.py' and f != 'help.py']
    
    # Import and register each framework page blueprint
    for page_name in framework_pages:
        # Check if page requires a feature flag
        required_feature = PAGE_FEATURE_REQUIREMENTS.get(page_name)
        if required_feature:
            if not getattr(site_config, required_feature, False):
                logger.debug("Skipping framework page '%s' - feature '%s' is disabled", page_name, required_feature)
                continue
        
        try:
            # Determine the correct package path based on how pages_module was imported
            pages_package = pages_module.__package__
            if pages_package:  # Running as package
                page_module = importlib.import_module(f".{page_name}", package=pages_package)
            else:  # Running directly
                page_module = importlib.import_module(f"pages.{page_name}")
            
            # Register the blueprint if it exists
            if hasattr(page_module, 'bp'):
                app.register_blueprint(page_module.bp)
                logger.debug("Registered framework page blueprint: %s", page_name)
        except ImportError as e:
            logger.debug("Failed to import framework page %s: %s", page_name, e)
        except Exception as e:
            logger.debug("Failed to register blueprint for %s: %s", page_name, e)

    # Initialize auth manager conditionally based on feature flag
    from .modules.auth.auth_manager import AuthManager
    
    if site_config.m_enable_authentication:
        # Check if auth_manager was already configured by the calling application
        if app_context.auth_manager is None:
            # Use app_path from app_context if set, otherwise fall back to app_path
            auth_base_path = app_context.app_path if app_context.app_path else app_path
            auth_manager_instance = AuthManager(auth_dir=os.path.join(auth_base_path, WEBSITE_AUTH_PATH))
            app_context.auth_manager = auth_manager_instance
            
            # Also update the local module reference for backward compatibility
            globals()['auth_manager'] = auth_manager_instance
            
            logger.debug("Auth manager initialized")
        else:
            # Auth manager was pre-configured by calling application
            globals()['auth_manager'] = app_context.auth_manager
            logger.debug("Auth manager already configured, using existing instance")
    else:
        app_context.auth_manager = None
        globals()['auth_manager'] = None
        logger.debug("Auth manager disabled")
    
    # Initialize settings manager (always enabled, needed for framework config)
    from .modules.settings import SettingsManager
    
    # Use app_path from app_context if set, otherwise fall back to local app_path
    config_base_path = app_context.app_path if app_context.app_path else app_path
    config_path = os.path.join(config_base_path, WEBSITE_CONFIG_PATH)
    settings_manager_instance = SettingsManager(config_path)
    settings_manager_instance.load()
    
    # Merge optional configurations based on enabled features
    if site_config:
        settings_manager_instance.merge_optional_configs(site_config)
    
    app_context.settings_manager = settings_manager_instance
    globals()['settings_manager'] = settings_manager_instance
    logger.debug("Settings manager initialized with config: %s", config_path)

    # Conditionally initialize file manager based on feature flag
    if site_config.m_enable_file_manager:
        from .modules.file_manager import FileManager
        from .pages import file_handler, file_manager_admin
        
        # Create FileManager instance and inject into route modules
        file_manager_instance = FileManager(settings_manager_instance)
        file_handler.file_manager = file_manager_instance
        if site_config.m_file_manager_admin:
            file_manager_admin.file_manager = file_manager_instance
        
        logger.debug("File manager initialized")
    else:
        logger.debug("File manager disabled")
    
    # Conditionally initialize tooltip manager based on feature flag
    if site_config.m_enable_tooltip_manager:
        from .modules.tooltip_manager import TooltipManager
        from .modules.tooltip_manager import routes as tooltip_routes
        
        # Create TooltipManager instance and register blueprint
        tooltip_manager_instance = TooltipManager(settings_manager_instance)
        app_context.tooltip_manager = tooltip_manager_instance
        app.register_blueprint(tooltip_routes.bp)
        
        logger.info(f"Tooltip manager initialized and registered")
    else:
        app_context.tooltip_manager = None
        logger.info("Tooltip manager disabled (feature flag off)")

    # -------------------------------------------------------------------------
    # Help System - Initialize help manager and register blueprint
    # -------------------------------------------------------------------------
    if getattr(site_config, 'm_enable_help', False):
        from .modules.help_manager import HelpManager
        from .pages import help as help_pages
        
        # Create HelpManager instance using app_context.app_path (project root)
        # instead of local app_path (framework root) for correct path resolution
        help_app_path = app_context.app_path if app_context.app_path else app_path
        help_manager_instance = HelpManager(help_app_path, settings_manager_instance)
        help_manager_instance.set_site_conf(site_config)
        help_manager_instance.discover_content()
        
        app_context.help_manager = help_manager_instance
        app.register_blueprint(help_pages.bp)
        
        logger.info(f"Help system initialized with {len(help_manager_instance.sections)} sections")
    else:
        app_context.help_manager = None
        logger.info("Help system disabled (feature flag off)")

    # -------------------------------------------------------------------------
    # Plugin System - Load and register enabled plugins from submodules
    # -------------------------------------------------------------------------
    if hasattr(site_config, 'm_enabled_plugins') and site_config.m_enabled_plugins:
        from .modules.plugin_base import PluginBase
        
        # Load plugin config from settings (config.json)
        all_settings = settings_manager_instance.get_all_settings()
        plugin_configs = all_settings.get("plugins", {})
        
        for plugin_name in site_config.m_enabled_plugins:
            try:
                # Import the plugin from submodules/{name}/web/
                plugin_module = importlib.import_module(f"submodules.{plugin_name}.web")
                
                # Find the plugin class (must inherit from PluginBase)
                plugin_class = None
                for attr_name in dir(plugin_module):
                    attr = getattr(plugin_module, attr_name)
                    if (isinstance(attr, type) 
                        and issubclass(attr, PluginBase) 
                        and attr is not PluginBase):
                        plugin_class = attr
                        break
                
                if plugin_class is None:
                    raise RuntimeError(f"No PluginBase subclass found in submodules.{plugin_name}.web")
                
                # Instantiate and validate dependencies
                plugin_instance = plugin_class()
                plugin_instance.validate_dependencies(site_config)
                
                # Get plugin-specific config
                plugin_config = plugin_configs.get(plugin_name, {})
                
                # Register the plugin
                plugin_instance.on_register(app, app_context, plugin_config)
                
                # Build sidebar items
                plugin_instance.build_sidebar(site_config)
                
                # Register plugin help content if help system is enabled
                if app_context.help_manager:
                    help_content = plugin_instance.get_help_content()
                    app_context.help_manager.register_plugin_help(plugin_name, help_content)
                
                logger.info(f"Plugin '{plugin_name}' loaded and registered successfully")
                
            except ImportError as e:
                error_msg = (
                    f"\n{'='*80}\n"
                    f"ERROR: Failed to import plugin '{plugin_name}'\n\n"
                    f"Make sure the plugin exists at: submodules/{plugin_name}/web/__init__.py\n"
                    f"Import error: {e}\n"
                    f"{'='*80}\n"
                )
                raise RuntimeError(error_msg) from e
            except Exception as e:
                error_msg = (
                    f"\n{'='*80}\n"
                    f"ERROR: Failed to load plugin '{plugin_name}'\n\n"
                    f"Error: {e}\n"
                    f"{'='*80}\n"
                )
                raise RuntimeError(error_msg) from e
    
    # Conditionally initialize scheduler based on feature flag
    if site_config.m_enable_scheduler:
        if os.path.isfile(os.path.join(app_path, WEBSITE_SCHEDULER_PATH)):
            scheduler_obj = importlib.import_module("website.scheduler").Scheduler(socket_obj=socketio_obj)
        else:
            scheduler_obj = scheduler.Scheduler(socket_obj=socketio_obj)

        scheduler_thread = threading.Thread(target=scheduler_obj.start, daemon=True)
        scheduler_thread.start()

        app_context.scheduler = scheduler_obj
        logger.debug("Scheduler initialized")
    else:
        app_context.scheduler = None
        logger.debug("Scheduler disabled")

    # Conditionally initialize long term scheduler based on feature flag
    if site_config.m_enable_long_term_scheduler:
        scheduler_lt = scheduler.Scheduler_LongTerm()
        scheduler_lt.start()
        app_context.scheduler_lt = scheduler_lt
        logger.debug("Long-term scheduler initialized")
    else:
        app_context.scheduler_lt = None
        logger.debug("Long-term scheduler disabled")

    # Conditionally initialize thread manager based on feature flag
    if site_config.m_enable_threads:
        app_context.thread_manager = threaded_manager.Threaded_manager()
        logger.debug("Thread manager initialized")
    else:
        app_context.thread_manager = None
        logger.debug("Thread manager disabled")

    # Conditionally initialize log emitter for real-time log viewing
    if site_config.m_enable_log_viewer:
        from .modules.log import log_emitter
        
        logs_dir = os.path.join(app_path, LOGS_DIR_NAME)
        log_emitter.initialize_log_emitter(socketio_obj, logs_dir, interval=LOG_EMITTER_INTERVAL)
        logger.debug("Log emitter initialized")
    else:
        logger.debug("Log emitter disabled")

    # Conditionally initialize thread emitter for real-time thread updates
    if site_config.m_enable_threads:
        from .modules.threaded import thread_emitter
        
        thread_emitter.thread_emitter_obj = thread_emitter.ThreadEmitter(socketio_obj, interval=THREAD_EMITTER_INTERVAL)
        thread_emitter.thread_emitter_obj.start()
        logger.debug("Thread emitter initialized")
    else:
        logger.debug("Thread emitter disabled")

    # Register SocketIO connection handlers for user rooms
    @socketio_obj.on("connect")  # type: ignore
    def handle_connect():
        """Handle client connection - join user-specific room"""
        try:
            room = socketio_manager_obj.join_user_room()
            username = session.get('user', ANONYMOUS_USER)  # type: ignore
            logger.debug("Client connected: %s in room %s", username, room)
        except Exception as e:
            logger.error("Error in handle_connect: %s", e)
    
    @socketio_obj.on("disconnect")  # type: ignore
    def handle_disconnect():
        """Handle client disconnection - leave user room"""
        try:
            username = session.get('user', ANONYMOUS_USER)  # type: ignore
            socketio_manager_obj.leave_user_room()
            logger.debug("Client disconnected: %s", username)
        except Exception as e:
            logger.error("Error in handle_disconnect: %s", e)

    # Register user_connected handler (conditionally based on scheduler)
    if site_config.m_enable_scheduler:
        @socketio_obj.on("user_connected")  # type: ignore
        def connect():
            if app_context.scheduler:
                app_context.scheduler.m_user_connected = True  # type: ignore

    # Set scheduler_obj and register functions (site_conf already loaded earlier)
    # Only set scheduler_obj if scheduler is enabled
    if site_config.m_enable_scheduler and app_context.scheduler:
        app_context.site_conf.m_scheduler_obj = app_context.scheduler

    # Register long term functions from the site config (if LT scheduler is enabled)
    if site_config.m_enable_long_term_scheduler:
        app_context.site_conf.register_scheduler_lt_functions()

    @socketio_obj.server.on("*")  # type: ignore
    def catch_all(event, sid, *args):
        app_context.site_conf.socketio_event(event, args)  # type: ignore

    @app.context_processor  # type: ignore
    def inject_bar():
        custom_context = app_context.site_conf.context_processor()  # type: ignore
        
        # Get current user for applying overrides
        user = session.get('user')  # type: ignore
        if not user and auth_manager is not None:
            user = auth_manager.get_current_user()
        
        # Apply user overrides to topbar if needed
        # Deep copy topbar to avoid modifying the original
        topbar_items = {
            "display": app_context.site_conf.m_topbar["display"],  # type: ignore
            "login": app_context.site_conf.m_topbar["login"],  # type: ignore
            "left": app_context.site_conf.m_topbar["left"].copy(),  # type: ignore
            "center": app_context.site_conf.m_topbar["center"].copy(),  # type: ignore
            "right": app_context.site_conf.m_topbar["right"].copy()  # type: ignore
        }
        
        # Only apply overrides if user is logged in with auth enabled
        if user and auth_manager is not None:
            # Check if thread status should be enabled/disabled
            thread_enabled_override = auth_manager.get_user_framework_override(user, "framework_ui.thread_status_enabled")
            thread_icon_override = auth_manager.get_user_framework_override(user, "framework_ui.thread_status_icon")
            thread_pos_override = auth_manager.get_user_framework_override(user, "framework_ui.thread_status_position")
            
            # If user has any overrides for thread status, apply them
            if thread_enabled_override is not None or thread_icon_override is not None or thread_pos_override is not None:
                # Find and remove all thread items first
                thread_item = None
                for area in ["left", "center", "right"]:
                    for item in topbar_items[area]:
                        if item.get("type") == "thread":
                            thread_item = item.copy()  # Keep a copy of the original
                            break
                    # Remove thread items from all positions
                    topbar_items[area] = [item for item in topbar_items[area] if item.get("type") != "thread"]
                
                # Re-add thread item if enabled (or if no override exists)
                if thread_enabled_override is not False:  # True or None (no override) = show it
                    if thread_item:
                        # Apply icon override if present
                        if thread_icon_override is not None:
                            thread_item["icon"] = thread_icon_override
                        
                        # Determine which position to add to
                        target_position = thread_pos_override if thread_pos_override in ["left", "center", "right"] else "right"
                        topbar_items[target_position].append(thread_item)
        
        # Filter sidebar items based on user permissions
        sidebar_items = app_context.site_conf.m_sidebar.copy()  # type: ignore
        is_guest = user and user.upper() == 'GUEST'
        
        # Check if user is admin
        is_admin = False
        if auth_manager is not None and user and user.upper() != 'GUEST':
            user_obj = auth_manager.get_user(user)
            is_admin = user_obj and 'admin' in user_obj.groups
        
        if auth_manager is not None:
            # Filter sidebar based on user type
            filtered_sidebar = []
            skip_until_next_title = False
            
            for item in sidebar_items:
                # Check if this is a title
                if item.get('isTitle'):
                    # Skip "User Management" title for guests
                    if item.get('name') == 'User Management' and is_guest:
                        skip_until_next_title = True
                        continue
                    skip_until_next_title = False
                    filtered_sidebar.append(item)
                # Check if this is the Account section
                elif item.get('name') == 'Account':
                    # Skip Account section for guests
                    if is_guest:
                        skip_until_next_title = True
                    else:
                        filtered_sidebar.append(item)
                # Check if this is the Admin section
                elif item.get('name') == 'Admin':
                    # Only show Admin section to admin users
                    if is_admin:
                        filtered_sidebar.append(item)
                    else:
                        skip_until_next_title = True
                elif not skip_until_next_title:
                    filtered_sidebar.append(item)
            
            sidebar_items = filtered_sidebar
        
        base_context = dict(
            sidebarItems=sidebar_items,
            topbarItems=topbar_items,
            app=app_context.site_conf.m_app,  # type: ignore
            javascript=app_context.site_conf.m_javascripts,  # type: ignore
            filename=None,
            title=app_context.site_conf.m_app["name"],  # type: ignore
            footer=app_context.site_conf.m_app["footer"]  # type: ignore
        )
        # Merge custom context from site_conf (like enable_easter_eggs) with base context
        if custom_context:
            base_context.update(custom_context)
        return base_context

    @app.context_processor  # type: ignore
    def inject_endpoint():
        if "page_info" not in session:  # type: ignore
            session["page_info"] = ""  # type: ignore

        # Get current user from session
        # Use auth_manager only if it's initialized
        user = session.get('user')  # type: ignore
        if not user and auth_manager is not None:
            user = auth_manager.get_current_user()
        
        return dict(
            endpoint=request.endpoint, page_info=session["page_info"], user=user  # type: ignore
        )

    
    @app.context_processor  # type: ignore
    def inject_csrf_token():
        """Inject CSRF token into templates.
        
        Token is generated once per session and persists across requests.
        This allows multi-tab usage and prevents token invalidation issues.
        """
        def generate_csrf_token():
            # Only generate new token if not already in session
            if 'csrf_token' not in session:
                session['csrf_token'] = str(uuid.uuid4())  # type: ignore
            return session['csrf_token']  # type: ignore
        
        return dict(csrf_token=generate_csrf_token())

    @app.before_request
    def reset_resources():
        """Reset ResourceRegistry at the start of each request.
        
        This ensures resources from previous requests don't leak into new ones.
        The registry uses Flask's g object for request-scoped storage.
        """
        from .modules.displayer import ResourceRegistry
        ResourceRegistry.reset()

    @app.context_processor
    def inject_resources():
        """Inject required CSS/JS resources into all templates.
        
        Resources are accumulated during page rendering via ResourceRegistry.require() calls,
        then injected here so templates can include the necessary files.
        """
        from .modules.displayer import ResourceRegistry
        resources = dict(
            required_css=ResourceRegistry.get_required_css(),
            required_js=ResourceRegistry.get_required_js(),
            required_cdn=ResourceRegistry.get_required_js_cdn()
        )
        return resources
    
    @app.context_processor
    def inject_user_theme():
        """Inject user's theme preference into all templates."""
        from .modules.auth import auth_manager
        user_theme = "light"  # Default
        
        if auth_manager:
            try:
                current_user = auth_manager.get_current_user()
                if current_user:
                    user_prefs = auth_manager.get_user_prefs(current_user)
                    user_theme = user_prefs.get("theme", "light")
            except Exception:
                pass  # Silently fall back to default
        
        return dict(user_theme=user_theme)

    # Custom Jinja2 filter for url_for with dict parameters
    @app.template_filter('url_for_with_params')
    def url_for_with_params_filter(endpoint, params=None):
        """
        Generate a URL for an endpoint with optional parameters.
        
        Args:
            endpoint: Flask endpoint name (e.g., 'logging.api_log_data')
            params: Dictionary of URL parameters (e.g., {'log_file': 'test.log'})
        
        Returns:
            Generated URL string
        """
        from flask import url_for
        if params:
            return url_for(endpoint, **params)
        return url_for(endpoint)

    # Index page (Framework default home page)
    @app.route("/")  # type: ignore
    def framework_index():
        session["page_info"] = "index"  # type: ignore
        return render_template("index.j2", title=app_context.site_conf.m_app["name"], content=app_context.site_conf.m_index)  # type: ignore

    # Handle Chrome DevTools and browser-specific requests to avoid 404 logs
    @app.route('/.well-known/appspecific/com.chrome.devtools.json')  # type: ignore
    def chrome_devtools():
        """Return empty response for Chrome DevTools request."""
        return {}, 204  # 204 No Content
    
    @app.route('/.well-known/<path:path>')  # type: ignore
    def well_known(path):
        """Handle other .well-known requests."""
        return {}, 204  # 204 No Content

    # Error handling to log errors
    @app.errorhandler(Exception)  # type: ignore
    def handle_exception(e):
        
        if hasattr(e, 'code') and e.code == 404:    
            requested_url = request.path  # type: ignore
            query_parameters = request.args.to_dict()  # type: ignore
            
            # Check if this is a path we should ignore
            should_log = not any(requested_url.startswith(path) for path in IGNORED_404_PATHS)
            
            if should_log:
                logger.error("A 404 was generated at the following path: %s. Get arguments: %s", requested_url, query_parameters)
            
            return render_template("404.j2", requested=requested_url)  # type: ignore

        # Gather detailed error context
        error_context = {
            'error': str(e),
            'traceback': str(traceback.format_exc()),
            'method': request.method,  # GET, POST, etc.
            'url': request.url,  # Full URL with query string
            'endpoint': request.endpoint,  # Flask endpoint name
            'remote_addr': request.remote_addr,  # Client IP
        }
        
        # Add GET parameters if present
        if request.args:
            error_context['get_params'] = dict(request.args)
        
        # Add POST parameters if present (be careful with sensitive data)
        if request.method == 'POST' and request.form:
            # Don't log passwords or sensitive fields
            safe_form = {k: v for k, v in request.form.items() 
                        if 'password' not in k.lower() and 'token' not in k.lower()}
            if safe_form:
                error_context['post_params'] = safe_form
        
        # Store error details in session for bug reporting
        session['last_error'] = {
            'error': str(e),
            'traceback': str(traceback.format_exc()),
            'method': request.method,
            'url': request.url,
            'endpoint': request.endpoint,
            'remote_addr': request.remote_addr,
            'get_params': dict(request.args) if request.args else None,
            'post_params': safe_form if request.method == 'POST' and request.form else None,
        }
        
        # Log as single-line HTML for log viewer
        logger.error("An error occurred: %s", format_exception_html(e))
        return render_template("error.j2", **error_context)  # type: ignore

    @app.before_request  # type: ignore
    def before_request():            
        g.start_time = time.time()  # type: ignore

        # Only update scheduler if it's enabled
        if app_context.scheduler is not None:
            app_context.scheduler.m_user_connected = False  # type: ignore
        
        if request.endpoint == "static":  # type: ignore
            return

        # Ensure session['user'] is always set for consistent authentication
        # This is critical for SocketIO room management and thread isolation
        if 'user' not in session:
            # Don't set GUEST during authentication flow to avoid race condition
            # The login route will set session['user'] properly
            if request.endpoint not in ['common.login', 'admin_auth.api_login']:
                session.permanent = True
                # Check if login is enabled
                if app_context.site_conf and hasattr(app_context.site_conf, 'm_topbar'):
                    if app_context.site_conf.m_topbar.get('login', False):
                        # Login enabled: default to GUEST if not logged in
                        session['user'] = DEFAULT_USER
                    else:
                        # No login: use anonymous (all users share same session)
                        session['user'] = ANONYMOUS_USER
                else:
                    # Fallback if site_conf not available
                    session['user'] = DEFAULT_USER

        # Note: config reading migrated to settings engine in src/modules/settings
        
        inject_bar()

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        webbrowser.open(STARTUP_URL)
    
    return socketio_obj


def run_app(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, debug: bool = False) -> None:
    """
    Run the ParalaX Web Framework application.
    
    Args:
        host: Host to bind to (default: 0.0.0.0)
        port: Port to bind to (default: 5000)
        debug: Enable debug mode (default: False)
    """
    if not FLASK_AVAILABLE:
        raise RuntimeError("Flask is not installed. Please install it with: pip install flask")
    
    if not app:
        raise RuntimeError("Flask app is not initialized")
    
    socketio_obj = setup_app(app)
    if socketio_obj is None:
        raise RuntimeError("Failed to initialize SocketIO")
    
    socketio_obj.run(app, host=host, port=port, debug=debug)


# Only setup the app if we're running as main, not during import for testing
if __name__ == "__main__":
    run_app()
