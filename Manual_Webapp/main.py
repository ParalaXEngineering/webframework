"""
Manual Test Web Application

A Flask application for manual testing of the ParalaX Web Framework.
This demonstrates how to properly use the framework as an external application.

Usage:
    python Manual_Webapp/main.py
"""

import sys
import os
import logging
import secrets
from pathlib import Path

# Get the Manual_Webapp directory (where this file is located)
manual_webapp_root = os.path.dirname(os.path.abspath(__file__))

# Get the framework root (parent of Manual_Webapp)
framework_root = os.path.dirname(manual_webapp_root)

# Load or create secret key
def get_or_create_secret_key(app_root):
    """Get secret key from file or create new one.
    
    Priority:
    1. PARALAX_SECRET_KEY environment variable
    2. .secret_key file in app root
    3. Generate new key and save to file
    """
    # 1. Check environment variable
    env_key = os.environ.get('PARALAX_SECRET_KEY')
    if env_key:
        return env_key
    
    # 2. Check .secret_key file
    key_file = Path(app_root) / '.secret_key'
    if key_file.exists():
        return key_file.read_text().strip()
    
    # 3. Generate new key and save
    new_key = secrets.token_hex(32)
    try:
        key_file.write_text(new_key)
        # Try to set restrictive permissions (owner read/write only)
        try:
            key_file.chmod(0o600)
        except Exception:
            pass  # Not critical if chmod fails
        print(f"Generated new secret key in {key_file}")
        print("Add .secret_key to .gitignore to keep it secret!")
    except OSError as e:
        print(f"Warning: Could not save secret key to file: {e}")
        print("Key will work for this session only.")
    
    return new_key

# Add framework root to path so we can import src modules
sys.path.insert(0, framework_root)
sys.path.insert(0, os.path.join(framework_root, 'src'))

# Add Manual_Webapp to path for demo_support and website imports
sys.path.insert(0, manual_webapp_root)

# Initialize logging using framework's unified system (console-only for Manual_Webapp)
from src.modules.log.logger_factory import initialize_logging
initialize_logging(Path(manual_webapp_root), config_file=None)  # No config file = use defaults

# Import framework setup
from src.main import app, setup_app, FLASK_AVAILABLE
from src.modules.log.logger_factory import get_logger
from src.modules import site_conf
from src.modules.app_context import app_context
from src.modules.auth.auth_manager import AuthManager
from src.modules.auth.permission_registry import permission_registry
import src.modules.auth as auth_module

from demo_support.demo_pages import demo_bp
from demo_support.component_showcase import showcase_bp
from demo_support.layout_showcase import layout_bp
from demo_support.demo_grid_layout import grid_layout_bp
from demo_support.demo_file_manager import demo_file_bp
from demo_support.demo_authorization import demo_auth_bp

# Initialize auth manager BEFORE creating app
# Auth dir is now relative to Manual_Webapp
auth_manager_instance = AuthManager(auth_dir=os.path.join(manual_webapp_root, "website", "auth"))

if not FLASK_AVAILABLE or app is None:
    print("ERROR: Flask is not available. Please install dependencies.")
    sys.exit(1)

# Configure secret key BEFORE calling setup_app()
app.config['SECRET_KEY'] = get_or_create_secret_key(manual_webapp_root)

# Get logger
logger = get_logger("manual_test")

# Create a full Site_conf for the test application with demo pages
class TestSiteConf(site_conf.Site_conf):
    """Site configuration for manual testing with demo pages"""
    
    def __init__(self):
        super().__init__()
        
        # Configure app details
        self.m_app = {
            "name": "ParalaX FRAMEWORK Demo",
            "version": "1.0.0",
            "icon": "flask",
            "footer": "2025 &copy; ParalaX Engineering"
        }
        self.m_index = "Welcome to the ParalaX Web Framework manual test application"
        
        # Configure sidebar with demo pages
        self.add_sidebar_title("Demo Pages")
        self.add_sidebar_section("Demos", "test-tube", "demo")
        self.add_sidebar_submenu("Simple Form", "demo.simple_form_demo", endpoint="demo")
        self.add_sidebar_submenu("Threading Demo", "demo.threading_demo", endpoint="demo")
        self.add_sidebar_submenu("Scheduler Demo", "demo.scheduler_demo", endpoint="demo")
        self.add_sidebar_submenu("Workflow Demo", "demo.workflow_demo", endpoint="demo")
        self.add_sidebar_submenu("FileManager demo", "demo_files.file_manager_demo", endpoint="demo")
        self.add_sidebar_submenu("Authorization Demo", "demo_auth.index", endpoint="demo")

        # Component Showcase - Auto-generated from DisplayerCategory
        self.add_sidebar_title("Displayer Showcase")
        self.add_sidebar_section("Components", "palette", "showcase_main")
        self.add_sidebar_submenu("Overview", "showcase.index", endpoint="showcase_main")
        
        # Add categories dynamically
        from demo_support.component_showcase import get_all_components_for_sidebar
        categories = get_all_components_for_sidebar()
        for category_name, category_key, count in categories:
            self.add_sidebar_submenu(
                f"{category_name} ({count})", 
                "showcase.category",
                parameter=f"category={category_key}",
                endpoint="showcase_main"
            )
        
        # Layout Showcase
        self.add_sidebar_section("All Layouts", "view-dashboard", "layout_main")
        self.add_sidebar_submenu("Overview", "layouts.index", endpoint="layout_main")
        
        # Add layout types dynamically
        from demo_support.layout_showcase import get_all_layouts_for_sidebar
        layout_types = get_all_layouts_for_sidebar()
        for layout_name, layout_key in layout_types:
            self.add_sidebar_submenu(
                layout_name,
                "layouts.layout_detail",
                parameter=f"layout={layout_key}",
                endpoint="layout_main"
            )
        
        # Tooltip Demo
        self.add_sidebar_page("Tooltips Demo", "help-circle", "demo.tooltips_demo")

        
        
        # Enable all framework features - this will add sidebar items automatically
        # This includes: Authentication (User Management + Admin), Threads, Logs, 
        # Bug Tracker, Settings, Updater, Packager
        self.enable_all_features(add_to_sidebar=True)
        
        # Enable File Manager separately (not in enable_all_features yet)
        self.enable_file_manager(add_to_sidebar=True, enable_admin_page=True)
        
        # Enable Tooltip Manager
        self.enable_tooltip_manager(add_to_sidebar=True)
        
        # Configure topbar login display (don't overwrite m_topbar, just update it)
        # The enable_all_features() already configured the topbar with thread status
        self.m_topbar["login"] = True
        self.m_javascripts = []
        self.m_enable_easter_eggs = False
    
    def get_statics(self, app_path: str) -> dict:
        """Override get_statics to point to Manual_Webapp website location."""
        # For Manual_Webapp, website is at Manual_Webapp/website/
        return {
            "images": os.path.join(app_path, "website", "assets", "images"),
            "js": os.path.join(app_path, "website", "assets", "js")
        }
    
    def context_processor(self):
        """Return context for templates"""
        # Call parent to get base context (includes enable_bug_tracker, etc.)
        context = super().context_processor()
        # Add any custom overrides here if needed
        return context

# Setup the application using framework's setup_app
logger.info("Initializing manual test application using framework setup")

# CRITICAL: Set app_path to Manual_Webapp root so config.json is loaded from Manual_Webapp/website/config.json
app_context.site_conf = TestSiteConf()
app_context.app_path = manual_webapp_root

# IMPORTANT: Change working directory to framework root for templates/static/translations resolution
# The framework's Flask app is configured to use framework_root/templates, framework_root/webengine,
# and framework_root/translations. We only override the config path via site_conf_app_path.
os.chdir(framework_root)
print(f"[Manual_Webapp] ✓ Changed working directory to: {framework_root}")
logger.info(f"Changed working directory to framework root: {framework_root}")

# Inject auth_manager into auth module
auth_module.auth_manager = auth_manager_instance

socketio = setup_app(app)

# Inject file_manager instance into demo blueprint
try:
    from src.pages import file_handler
    if hasattr(file_handler, 'file_manager') and file_handler.file_manager:
        import demo_support.demo_file_manager as demo_file_module
        demo_file_module.file_manager = file_handler.file_manager
        logger.info("Injected file_manager instance into demo blueprint")
except Exception as e:
    logger.warning(f"Could not inject file_manager into demo: {e}")

# Register demo pages blueprint
app.register_blueprint(demo_bp)
app.register_blueprint(showcase_bp)
app.register_blueprint(layout_bp)
app.register_blueprint(grid_layout_bp)
app.register_blueprint(demo_file_bp)
app.register_blueprint(demo_auth_bp)
logger.info("Registered demo pages, component showcase, layout showcase, grid layout, and file manager demo blueprints")

# Register user profile and admin blueprints
logger.info("Registered auth management blueprints")

# Register demo modules with custom permissions (view is implicit)
# NOTE: Demo_Layouts and Demo_Components are registered in their respective blueprint files
# This keeps permission registration close to the code that uses them
permission_registry.register_module("Demo_Threading", [])  # Threaded actions check their own permission
permission_registry.register_module("Demo_Scheduler", [])  # Threaded actions check their own permission
# Demo_Auth module is registered in demo_authorization.py
permission_registry.register_module("FileManager", ["upload", "download", "delete", "edit"])

logger.info("Registered demo module permissions")

# Validate permission configuration at startup
try:
    from src.modules.auth.permission_validator import validate_and_log
    validate_and_log()
except Exception as e:
    logger.warning(f"Permission validation failed: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("  ParalaX Web Framework - Manual Test Application")
    print("=" * 60)
    print("  Starting Flask server with SocketIO...")
    print("  Open your browser to: http://localhost:5001")
    print("  ")
    print("  Default Credentials:")
    print("  - Admin: username='admin', password='admin123'")
    print("  - Guest: username='GUEST', password='' (passwordless)")
    print("  ")
    print("  Demo Features:")
    print("  - Component showcase (layouts, inputs, tables, etc.)")
    print("  - Authorization Showcase (interactive permission demo)")
    print("  - File Manager with upload/download/versioning")
    print("  ")
    print("  Press CTRL+C to stop the server")
    print("=" * 60)
    
    socketio.run(app, debug=False, host='0.0.0.0', port=5001, allow_unsafe_werkzeug=True, log_output=False)  # type: ignore
