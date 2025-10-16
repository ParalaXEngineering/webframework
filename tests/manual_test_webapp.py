"""
Manual Test Web Application

A Flask application for manual testing of the ParalaX Web Framework.
Uses the framework's main.py setup_app() function properly.

Usage:
    python tests/manual_test_webapp.py
"""

import sys
import os
import logging

# Import framework setup
from src.main import app, setup_app, FLASK_AVAILABLE
from src.modules.log.logger_factory import get_logger
from src.modules import site_conf
from src.modules.auth.auth_manager import AuthManager

import src.modules.auth.auth_manager as auth_module
from demo_support.demo_pages import demo_bp
from demo_support.component_showcase import showcase_bp
from demo_support.layout_showcase import layout_bp
from demo_support.demo_user_defined_layout import user_defined_bp
from website.pages.user_profile_bp import user_profile_bp
from website.pages.admin_auth_bp import admin_auth_bp
from src.modules.auth.permission_registry import permission_registry

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))
sys.path.insert(0, os.path.join(project_root, 'tests'))  # Add tests to path for website module

# Initialize auth manager BEFORE creating app
auth_manager_instance = AuthManager(auth_dir="tests/website/auth")

if not FLASK_AVAILABLE:
    print("ERROR: Flask is not available. Please install dependencies.")
    sys.exit(1)

# Get logger
logger = get_logger("manual_test")

# Create a full Site_conf for the test application with demo pages
class TestSiteConf(site_conf.Site_conf):
    """Site configuration for manual testing with demo pages"""
    
    def __init__(self):
        super().__init__()
        
        # Configure app details
        self.m_app = {
            "name": "ParalaX Framework - Manual Test",
            "version": "0.1.0",
            "icon": "flask",
            "footer": "2025 &copy; ParalaX Engineering"
        }
        self.m_index = "Welcome to the ParalaX Web Framework manual test application"
        
        # Configure sidebar with demo pages
        self.add_sidebar_title("Demo Pages")
        self.add_sidebar_section("Demos", "test-tube", "demo")
        self.add_sidebar_submenu("Threading Demo", "demo.threading_demo")
        self.add_sidebar_submenu("Scheduler Demo", "demo.scheduler_demo")
        self.add_sidebar_submenu("Workflow Demo", "demo.workflow_demo")
        
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
        
        # Authorization demos
        self.add_sidebar_section("Authorization Demos", "shield-check", "auth")
        self.add_sidebar_submenu("Accessible Page", "demo.auth_accessible", endpoint="auth")
        self.add_sidebar_submenu("Restricted Page", "demo.auth_restricted", endpoint="auth")
        self.add_sidebar_submenu("Admin Only", "demo.auth_admin", endpoint="auth")
        
        # Add User Management section
        self.add_sidebar_title("User Management")
        self.add_sidebar_section("Account", "account-circle", "user")
        self.add_sidebar_submenu("My Profile", "user_profile.profile", endpoint="user")
        self.add_sidebar_submenu("My Preferences", "user_profile.preferences", endpoint="user")
        
        # Add Admin section
        self.add_sidebar_section("Admin", "shield-lock", "admin")
        self.add_sidebar_submenu("Users", "admin_auth.manage_users", endpoint="admin")
        self.add_sidebar_submenu("Permissions", "admin_auth.manage_permissions", endpoint="admin")
        self.add_sidebar_submenu("Groups", "admin_auth.manage_groups", endpoint="admin")
        
        # Add Framework Pages section
        self.add_sidebar_title("Framework Pages")
        self.add_sidebar_section("System", "cog", "framework")
        self.add_sidebar_submenu("Settings", "settings.index", endpoint="framework")
        self.add_sidebar_submenu("Thread Monitor", "threads.threads", endpoint="framework")
        self.add_sidebar_submenu("Log Viewer", "logging.logs", endpoint="framework")
        self.add_sidebar_submenu("Bug Tracker", "bug.bugtracker", endpoint="framework")
        self.add_sidebar_submenu("Updater", "updater.update", endpoint="framework")
        self.add_sidebar_submenu("Packager", "packager.packager", endpoint="framework")
        
        # Configure topbar with login display
        self.m_topbar = {"display": True, "left": [], "center": [], "right": [], "login": True}
        self.m_javascripts = []
        self.m_enable_easter_eggs = False
    
    def get_statics(self, app_path: str) -> dict:
        """Override get_statics to point to test website location."""
        # For test app, website is at tests/website/ instead of website/
        return {
            "images": os.path.join(app_path, "tests", "website", "assets", "images"),
            "js": os.path.join(app_path, "tests", "website", "assets", "js")
        }
    
    def context_processor(self):
        """Return context for templates"""
        return {
            "enable_easter_eggs": self.m_enable_easter_eggs
        }

# Setup the application using framework's setup_app
logger.info("Initializing manual test application using framework setup")

# Create and inject the test site_conf BEFORE calling setup_app
site_conf.site_conf_obj = TestSiteConf()
# Set app_path so get_statics() works correctly
site_conf.site_conf_app_path = project_root

# Inject auth_manager into auth module
auth_module.auth_manager = auth_manager_instance

socketio = setup_app(app)

# Register demo pages blueprint

app.register_blueprint(demo_bp)
app.register_blueprint(showcase_bp)
app.register_blueprint(layout_bp)
app.register_blueprint(user_defined_bp)
app.register_blueprint(admin_auth_bp)
logger.info("Registered demo pages, component showcase, layout showcase, and user-defined layout blueprints")

# Register user profile and admin blueprints

app.register_blueprint(user_profile_bp)
logger.info("Registered auth management blueprints")

# Register real demo modules with appropriate permissions
permission_registry.register_module("Demo_Layouts", ["view", "edit"])
permission_registry.register_module("Demo_Components", ["view", "edit"])
permission_registry.register_module("Demo_Threading", ["view", "execute"])
permission_registry.register_module("Demo_Scheduler", ["view", "execute", "configure"])
permission_registry.register_module("Demo_Authorization", ["view"])

logger.info("Registered demo module permissions")

if __name__ == "__main__":
    print("=" * 60)
    print("  ParalaX Web Framework - Manual Test Application")
    print("=" * 60)
    print("  Starting Flask server with SocketIO...")
    print("  Open your browser to: http://localhost:5001")
    print("  ")
    print("  Default Credentials:")
    print("  - Admin: username='admin', password='admin'")
    print("  - Guest: username='GUEST', password='' (passwordless)")
    print("  ")
    print("  Demo Features:")
    print("  - Component showcase (layouts, inputs, tables, etc.)")
    print("  - Authorization demos in Demo Gallery:")
    print("    • Accessible Page (anyone can view)")
    print("    • Restricted Page (requires permission)")
    print("    • Admin Only (requires admin role)")
    print("  ")
    print("  Press CTRL+C to stop the server")
    print("=" * 60)
    
    # Disable Flask/Werkzeug HTTP request logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    socketio.run(app, debug=False, host='0.0.0.0', port=5001, allow_unsafe_werkzeug=True, log_output=False)

