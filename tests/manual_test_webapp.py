"""
Manual Test Web Application

A Flask application for manual testing of the ParalaX Web Framework.
Uses the framework's main.py setup_app() function properly.

Usage:
    python tests/manual_test_webapp.py
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

# Import framework setup
from src.main import app, setup_app, FLASK_AVAILABLE
from src.modules.logger_factory import get_logger
from src.modules import site_conf

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
        self.add_sidebar_submenu("Home", "demo.index")
        self.add_sidebar_submenu("Layouts", "demo.layouts")
        self.add_sidebar_submenu("Text & Display", "demo.text_display")
        self.add_sidebar_submenu("Inputs", "demo.inputs")
        self.add_sidebar_submenu("Threading Demo", "demo.threading_demo")
        self.add_sidebar_submenu("Scheduler Demo", "demo.scheduler_demo")
        self.add_sidebar_submenu("Complete Showcase", "demo.complete_showcase")
        
        # Add Framework Pages section
        self.add_sidebar_title("Framework Pages")
        self.add_sidebar_section("System", "cog", "framework")
        self.add_sidebar_submenu("Settings", "settings.index", endpoint="framework")
        self.add_sidebar_submenu("Thread Monitor", "threads.threads", endpoint="framework")
        self.add_sidebar_submenu("Log Viewer", "logging.logs", endpoint="framework")
        self.add_sidebar_submenu("Bug Tracker", "bug.bugtracker", endpoint="framework")
        self.add_sidebar_submenu("Updater", "updater.update", endpoint="framework")
        self.add_sidebar_submenu("Packager", "packager.packager", endpoint="framework")
        
        # Configure topbar
        self.m_topbar = {"display": False, "left": [], "center": [], "right": [], "login": False}
        self.m_javascripts = []
        self.m_enable_easter_eggs = False
    
    def context_processor(self):
        """Return context for templates"""
        return {
            "enable_easter_eggs": self.m_enable_easter_eggs
        }

# Setup the application using framework's setup_app
logger.info("Initializing manual test application using framework setup")

# Create and inject the test site_conf BEFORE calling setup_app
site_conf.site_conf_obj = TestSiteConf()

socketio = setup_app(app)

# Register demo pages blueprint
from demo_pages import demo_bp
app.register_blueprint(demo_bp)
logger.info("Registered demo pages blueprint")

if __name__ == "__main__":
    print("=" * 60)
    print("  ParalaX Web Framework - Manual Test Application")
    print("=" * 60)
    print("  Starting Flask server with SocketIO...")
    print("  Open your browser to: http://localhost:5001")
    print("  Press CTRL+C to stop the server")
    print("=" * 60)
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5001, allow_unsafe_werkzeug=True)

