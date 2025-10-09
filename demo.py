"""
Displayer Demo Application

A Flask application to demonstrate and test all DisplayerItem types,
layouts, and features of the ParalaX Web Framework displayer system.

Run this script to start a local Flask server and view all displayer
components in action.

Usage:
    python demo.py
    
Or use VS Code launch configuration (F5)
"""

from flask import Flask, render_template, request, Blueprint
from flask_socketio import SocketIO
from src.modules import displayer
from src.modules import utilities, access_manager, site_conf
from src.modules.threaded import threaded_manager
from src.modules import scheduler
from src import pages as pages_module
from demo_scheduler_action import DemoSchedulerAction
from demo_thread import DemoBackgroundThread
import os
import threading
import importlib

# Create Flask app
app = Flask(__name__, 
            template_folder='templates',
            static_folder='webengine/assets',
            static_url_path='/assets')
app.secret_key = 'demo-secret-key-change-in-production'

# Configure session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development

# Initialize SocketIO for real-time communication
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize thread manager
threaded_manager.thread_manager_obj = threaded_manager.Threaded_manager()

# Initialize scheduler with SocketIO
scheduler_instance = scheduler.Scheduler(socket_obj=socketio)
scheduler.scheduler_obj = scheduler_instance
scheduler_instance.m_user_connected = True  # Enable scheduler for demo

# Start scheduler in background thread
scheduler_thread = threading.Thread(target=scheduler_instance.start, daemon=True)
scheduler_thread.start()

# Initialize access manager with a mock configuration
access_manager.auth_object = access_manager.Access_manager()
access_manager.auth_object.m_login = False
access_manager.auth_object.m_users = {"demo": {"password": "demo"}}
access_manager.auth_object.m_groups = ["demo_group"]
access_manager.auth_object.m_modules = {}
access_manager.auth_object.m_users_groups = {"demo": ["demo_group"]}

# Create a Site_conf instance for proper template context
class DemoSiteConf(site_conf.Site_conf):
    """Demo site configuration with minimal setup."""
    def __init__(self):
        super().__init__()
        # Configure app details
        self.app_details("Displayer Demo", "1.0", "test-tube", "2024 &copy; ParalaX", "Demo of Displayer System")
        
        # Add sidebar sections for demo
        self.add_sidebar_title("Demo Pages")
        self.add_sidebar_section("Demos", "test-tube", "demo")
        self.add_sidebar_submenu("Home", "demo.index")
        self.add_sidebar_submenu("Layouts", "demo.layouts")
        self.add_sidebar_submenu("Text & Display", "demo.text_display")
        self.add_sidebar_submenu("Inputs", "demo.inputs")
        self.add_sidebar_submenu("Scheduler Demo", "demo.scheduler_demo")
        self.add_sidebar_submenu("Complete Showcase", "demo.complete_showcase")
        self.add_sidebar_submenu("Settings Demo", "demo.settings_demo")
        
        # Add Framework Pages section
        self.add_sidebar_title("Framework Pages")
        self.add_sidebar_section("System", "cog", "framework")
        self.add_sidebar_submenu("Settings", "settings.index", endpoint="framework")
        self.add_sidebar_submenu("Thread Monitor", "threads.threads", endpoint="framework")
        self.add_sidebar_submenu("Bug Tracker", "bug.bugtracker", endpoint="framework")
        self.add_sidebar_submenu("Updater", "updater.update", endpoint="framework")
        self.add_sidebar_submenu("Packager", "packager.packager", endpoint="framework")

# Initialize site configuration
demo_conf = DemoSiteConf()
site_conf.site_conf_obj = demo_conf

# Register context processor to inject variables into all templates
@app.context_processor
def inject_template_context():
    """Inject site configuration context into all templates."""
    demo_conf.context_processor()  # Call the site_conf context processor
    return {
        'sidebarItems': demo_conf.m_sidebar,
        'topbarItems': demo_conf.m_topbar,
        'app': demo_conf.m_app,
        'javascript': demo_conf.m_javascripts,
        'title': demo_conf.m_app["name"],
        'footer': demo_conf.m_app["footer"],
        'filename': None,
        'endpoint': request.endpoint if request else None,
        'page_info': '',
        'user': None,
    }

@app.context_processor
def inject_resources():
    """Inject dynamic resources into all templates."""
    from src.modules.displayer import ResourceRegistry
    return {
        'required_css': ResourceRegistry.get_required_css(),
        'required_js': ResourceRegistry.get_required_js(),
        'required_cdn': ResourceRegistry.get_required_js_cdn()
    }

# Create blueprint for demo routes
demo_bp = Blueprint('demo', __name__)

# Common assets route (needed by templates)
common_bp = Blueprint('common', __name__, url_prefix='/common')

@common_bp.route('/assets/<asset_type>/<path:filename>')
def assets(asset_type, filename):
    """Serve assets from webengine directory."""
    from flask import send_from_directory
    asset_path = os.path.join('webengine', 'assets', asset_type)
    return send_from_directory(asset_path, filename)


@demo_bp.route('/')
def index():
    """Main index page with navigation to all demo pages."""
    disp = displayer.Displayer()
    disp.add_generic("Demo Navigation")
    disp.set_title("Displayer Component Demo")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    
    # Navigation cards
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 3, 3, 3]
    ))
    
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btn_layouts", "Layouts", "mdi-view-dashboard", "/layouts", [], displayer.BSstyle.PRIMARY
    ), 0)
    
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btn_text", "Text & Display", "mdi-text", "/text-display", [], displayer.BSstyle.SUCCESS
    ), 1)
    
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btn_inputs", "Inputs", "mdi-form-textbox", "/inputs", [], displayer.BSstyle.WARNING
    ), 2)
    
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btn_scheduler", "Scheduler", "mdi-clock-fast", "/scheduler-demo", [], displayer.BSstyle.INFO
    ), 3)
    
    # Complete showcase button
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btn_complete", "Complete Showcase", "mdi-star", "/complete-showcase", [], displayer.BSstyle.PRIMARY
    ), 0)
    
    return render_template("base_content.j2", content=disp.display())


@demo_bp.route('/layouts')
def layouts():
    """Demonstrate different layout types."""
    disp = displayer.Displayer()
    disp.add_generic("Layout Demos")
    disp.set_title("Layout Types")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Layouts", "demo.layouts", [])
    
    # Vertical layouts
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [4, 4, 4], subtitle="3 Equal Columns"
    ))
    disp.add_display_item(displayer.DisplayerItemText("Column 1"), 0)
    disp.add_display_item(displayer.DisplayerItemText("Column 2"), 1)
    disp.add_display_item(displayer.DisplayerItemText("Column 3"), 2)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemSeparator(), 0)
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 6, 3], subtitle="Variable Columns (3-6-3)"
    ))
    disp.add_display_item(displayer.DisplayerItemText("3"), 0)
    disp.add_display_item(displayer.DisplayerItemText("6"), 1)
    disp.add_display_item(displayer.DisplayerItemText("3"), 2)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemSeparator(), 0)
    
    # Horizontal Layout
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.HORIZONTAL, [6, 6], subtitle="Horizontal"
    ))
    disp.add_display_item(displayer.DisplayerItemText("Left"), 0)
    disp.add_display_item(displayer.DisplayerItemText("Right"), 1)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemSeparator(), 0)
    
    # Table Layout
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE, ["Name", "Status", "Actions"], subtitle="Table"
    ))
    disp.add_display_item(displayer.DisplayerItemText("Item 1"), column=0)
    disp.add_display_item(displayer.DisplayerItemBadge("Active", displayer.BSstyle.SUCCESS), column=1)
    disp.add_display_item(displayer.DisplayerItemButton("btn_action1", "View"), column=2)
    
    # Spacer
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.SPACER, [12]))
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="After Spacer"
    ))
    disp.add_display_item(displayer.DisplayerItemText("Content after spacer"), 0)
    
    return render_template("base_content.j2", content=disp.display())


@demo_bp.route('/text-display')
def text_display():
    """Demonstrate text and display items."""
    disp = displayer.Displayer()
    disp.add_generic("Text & Display")
    disp.set_title("Text & Display Components")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Text & Display", "demo.text_display", [])
    
    # Text Items
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Text Items"
    ))
    disp.add_display_item(displayer.DisplayerItemText("Simple text"), 0)
    disp.add_display_item(displayer.DisplayerItemText("<b>Bold</b> and <i>italic</i>"), 0)
    disp.add_display_item(displayer.DisplayerItemText('<a href="https://example.com">Link</a>'), 0)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemSeparator(), 0)
    
    # Alerts
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Alerts"
    ))
    for style, name in [(displayer.BSstyle.PRIMARY, "Primary"),
                        (displayer.BSstyle.SUCCESS, "Success"),
                        (displayer.BSstyle.INFO, "Info"),
                        (displayer.BSstyle.WARNING, "Warning"),
                        (displayer.BSstyle.ERROR, "Error")]:
        disp.add_display_item(displayer.DisplayerItemAlert(f"{name} alert", style), 0)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemSeparator(), 0)
    
    # Badges
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [2, 2, 2, 2, 2, 2], subtitle="Badges"
    ))
    badges = [("Primary", displayer.BSstyle.PRIMARY), ("Success", displayer.BSstyle.SUCCESS),
              ("Info", displayer.BSstyle.INFO), ("Warning", displayer.BSstyle.WARNING),
              ("Danger", displayer.BSstyle.ERROR), ("Dark", displayer.BSstyle.DARK)]
    for idx, (text, style) in enumerate(badges):
        disp.add_display_item(displayer.DisplayerItemBadge(text, style), idx)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemSeparator(), 0)
    
    # Buttons
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 3, 3], subtitle="Buttons"
    ))
    disp.add_display_item(displayer.DisplayerItemButton("btn1", "Button"), 0)
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btnlink1", "Link Button", "mdi-link", "/", [], displayer.BSstyle.PRIMARY
    ), 1)
    disp.add_display_item(displayer.DisplayerItemIconLink(
        "iconlink1", "Icon Link", "mdi-home", "/", [], displayer.BSstyle.INFO
    ), 2)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemSeparator(), 0)
    
    # Placeholder
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Placeholder"
    ))
    disp.add_display_item(displayer.DisplayerItemPlaceholder("demo_placeholder", "Placeholder content"), 0)
    
    return render_template("base_content.j2", content=disp.display())


@demo_bp.route('/inputs', methods=['GET', 'POST'])
def inputs():
    """Demonstrate input items with form submission."""
    if request.method == 'POST':
        data = utilities.util_post_to_json(request.form.to_dict())
        return render_template("success.j2", message=f"Form submitted! Data: {data}")
    
    disp = displayer.Displayer()
    disp.add_generic("Inputs")
    disp.set_title("Input Components")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Inputs", "demo.inputs", [])
    
    # Basic Inputs
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 9], subtitle="Basic Inputs"
    ))
    disp.add_display_item(displayer.DisplayerItemText("String:"), 0)
    disp.add_display_item(displayer.DisplayerItemInputString("name", "Name", "John"), 1)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 9]))
    disp.add_display_item(displayer.DisplayerItemText("Text:"), 0)
    disp.add_display_item(displayer.DisplayerItemInputText("desc", "Description", "Text"), 1)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 9]))
    disp.add_display_item(displayer.DisplayerItemText("Numeric:"), 0)
    disp.add_display_item(displayer.DisplayerItemInputNumeric("age", "Age", 25), 1)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 9]))
    disp.add_display_item(displayer.DisplayerItemText("Date:"), 0)
    disp.add_display_item(displayer.DisplayerItemInputDate("date", "Date", "2024-01-01"), 1)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemSeparator(), 0)
    
    # Select Inputs
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 9], subtitle="Select"
    ))
    disp.add_display_item(displayer.DisplayerItemText("Select:"), 0)
    disp.add_display_item(displayer.DisplayerItemInputSelect(
        "country", "Country", "USA", ["USA", "Canada", "UK", "France"]
    ), 1)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 9]))
    disp.add_display_item(displayer.DisplayerItemText("Multi:"), 0)
    disp.add_display_item(displayer.DisplayerItemInputMultiSelect(
        "langs", "Languages", ["Python"], ["Python", "JavaScript", "Java", "C++"]
    ), 1)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemSeparator(), 0)
    
    # File Inputs
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 9], subtitle="File Inputs"
    ))
    disp.add_display_item(displayer.DisplayerItemText("File:"), 0)
    disp.add_display_item(displayer.DisplayerItemInputFile("file", "File"), 1)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 9]))
    disp.add_display_item(displayer.DisplayerItemText("Folder:"), 0)
    disp.add_display_item(displayer.DisplayerItemInputFolder("folder", "Folder"), 1)
    
    # Hidden + Submit
    disp.add_display_item(displayer.DisplayerItemHidden("hidden_id", "secret"), 0)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemButton("submit_form", "Submit"), 0)
    
    return render_template("base_content.j2", content=disp.display(), target="demo.inputs")


@demo_bp.route('/complete-showcase')
def complete_showcase():
    """A comprehensive page showing ALL displayer features."""
    disp = displayer.Displayer()
    disp.add_generic("Complete Showcase")
    disp.set_title("Complete Showcase")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Showcase", "demo.complete_showcase", [])
    
    # All Alert Types
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Alerts"
    ))
    for style, name in [(displayer.BSstyle.PRIMARY, "Primary"),
                        (displayer.BSstyle.SUCCESS, "Success"),
                        (displayer.BSstyle.INFO, "Info"),
                        (displayer.BSstyle.WARNING, "Warning"),
                        (displayer.BSstyle.ERROR, "Error")]:
        disp.add_display_item(displayer.DisplayerItemAlert(f"{name} alert", style), 0)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemSeparator(), 0)
    
    # Layouts
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [6, 6], subtitle="2-Column"
    ))
    disp.add_display_item(displayer.DisplayerItemText("Left"), 0)
    disp.add_display_item(displayer.DisplayerItemText("Right"), 1)
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [4, 4, 4], subtitle="3-Column"
    ))
    disp.add_display_item(displayer.DisplayerItemBadge("Badge 1", displayer.BSstyle.PRIMARY), 0)
    disp.add_display_item(displayer.DisplayerItemBadge("Badge 2", displayer.BSstyle.SUCCESS), 1)
    disp.add_display_item(displayer.DisplayerItemBadge("Badge 3", displayer.BSstyle.INFO), 2)
    
    # Table
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE, ["Item", "Status", "Action"], subtitle="Table"
    ))
    disp.add_display_item(displayer.DisplayerItemText("Task 1"), column=0, line=0)
    disp.add_display_item(displayer.DisplayerItemBadge("Active", displayer.BSstyle.SUCCESS), column=1, line=0)
    disp.add_display_item(displayer.DisplayerItemButton("action1", "Edit"), column=2, line=0)
    
    disp.add_display_item(displayer.DisplayerItemText("Task 2"), column=0, line=1)
    disp.add_display_item(displayer.DisplayerItemBadge("Pending", displayer.BSstyle.WARNING), column=1, line=1)
    disp.add_display_item(displayer.DisplayerItemButton("action2", "View"), column=2, line=1)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemSeparator(), 0)
    
    # Buttons
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 3, 3], subtitle="Buttons"
    ))
    disp.add_display_item(displayer.DisplayerItemButton("btn_default", "Button"), 0)
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btn_link", "Link", "mdi-open-in-new", "/", [], displayer.BSstyle.SUCCESS
    ), 1)
    disp.add_display_item(displayer.DisplayerItemIconLink(
        "icon_link", "Icon", "mdi-information", "/", [], displayer.BSstyle.INFO
    ), 2)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemSeparator(), 0)
    
    # Text Formatting
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Text"
    ))
    disp.add_display_item(displayer.DisplayerItemText("Regular text"), 0)
    disp.add_display_item(displayer.DisplayerItemText("<b>Bold</b> <i>Italic</i> <u>Underline</u>"), 0)
    disp.add_display_item(displayer.DisplayerItemText('<a href="https://example.com">Link</a>'), 0)
    
    return render_template("base_content.j2", content=disp.display())


@demo_bp.route('/scheduler-demo', methods=['GET', 'POST'])
def scheduler_demo():
    """Demonstrate scheduler functionality with threaded actions."""
    
    # Require jQuery for SocketIO functionality in site.js
    from src.modules.displayer import ResourceRegistry
    ResourceRegistry.require('jquery')
    
    # Handle form submission
    if request.method == 'POST':
        data_in = utilities.util_post_to_json(request.form.to_dict())
        
        if DemoSchedulerAction.m_default_name in data_in:
            action_data = data_in[DemoSchedulerAction.m_default_name]
            
            # Check if an action is already running
            thread = threaded_manager.thread_manager_obj.get_thread(
                DemoSchedulerAction.m_default_name
            )
            
            if thread:
                # Action already running
                pass  # The scheduler will show the status
            else:
                # Start new action based on button pressed
                demo_action = DemoSchedulerAction()
                
                if "simple_demo" in action_data:
                    demo_action.set_demo_type("simple")
                    demo_action.start()
                elif "complex_demo" in action_data:
                    demo_action.set_demo_type("complex")
                    demo_action.start()
                elif "error_demo" in action_data:
                    demo_action.set_demo_type("error")
                    demo_action.start()
                elif "multi_step_demo" in action_data:
                    demo_action.set_demo_type("multi_step")
                    demo_action.start()
                elif "all_features_demo" in action_data:
                    demo_action.set_demo_type("all_features")
                    demo_action.start()
    
    disp = displayer.Displayer()
    disp.add_module(DemoSchedulerAction)
    disp.set_title("Scheduler Demo")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Scheduler", "demo.scheduler_demo", [])
    
    # Status display
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Status"
    ))
    disp.add_display_item(
        displayer.DisplayerItemAlert("No action running", displayer.BSstyle.NONE),
        0,
        id="scheduler_demo_status"
    )
    
    # Dynamic content area
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Dynamic Content"
    ))
    disp.add_display_item(
        displayer.DisplayerItemPlaceholder(
            "scheduler_demo_dynamic_content",
            '<div class="alert alert-secondary">Dynamic content area</div>'
        ),
        0
    )
    
    # Demo buttons
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Demos"
    ))
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [9, 3]
    ))
    disp.add_display_item(
        displayer.DisplayerItemText("<strong>1. Single Progress</strong> - Updates one line"),
        0
    )
    disp.add_display_item(
        displayer.DisplayerItemButton("simple_demo", "Run"),
        1,
        id="demo_action_btn"
    )
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [9, 3]
    ))
    disp.add_display_item(
        displayer.DisplayerItemText("<strong>2. Parallel Progress</strong> - Multiple concurrent bars"),
        0
    )
    disp.add_display_item(
        displayer.DisplayerItemButton("multi_step_demo", "Run"),
        1
    )
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [9, 3]
    ))
    disp.add_display_item(
        displayer.DisplayerItemText("<strong>3. Popups</strong> - All popup types"),
        0
    )
    disp.add_display_item(
        displayer.DisplayerItemButton("error_demo", "Run"),
        1
    )
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [9, 3]
    ))
    disp.add_display_item(
        displayer.DisplayerItemText("<strong>4. Button Control</strong> - Disable/enable buttons"),
        0
    )
    disp.add_display_item(
        displayer.DisplayerItemButton("complex_demo", "Run"),
        1
    )
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [9, 3]
    ))
    disp.add_display_item(
        displayer.DisplayerItemText("<strong>5. Content Reload</strong> - Dynamic page updates"),
        0
    )
    disp.add_display_item(
        displayer.DisplayerItemButton("all_features_demo", "Run"),
        1
    )
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemSeparator(), 0)
    
    # Quick reference
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="API Quick Reference"
    ))
    disp.add_display_item(
        displayer.DisplayerItemText(
            "<strong>emit_status(category, string, status, supplement, status_id)</strong> - Progress updates<br>"
            "<strong>emit_popup(level, string)</strong> - Toast notifications<br>"
            "<strong>emit_reload(content)</strong> - Update page elements<br>"
            "<strong>disable_button(id)</strong> / <strong>enable_button(id)</strong> - Button control"
        ),
        0
    )
    
    disp.add_display_item(
        displayer.DisplayerItemDynamicContent(
            id="dynamic_content_demo",
            initial_content='<div class="alert alert-secondary">Dynamic content area</div>',
            card=False
        ),
        0
    )
    
    return render_template("base_content.j2", content=disp.display(), target="demo.scheduler_demo")


@demo_bp.route('/settings-demo')
def settings_demo():
    """Redirect to settings interface."""
    from flask import redirect
    return redirect('/settings/')


# Register blueprints
app.register_blueprint(demo_bp)
app.register_blueprint(common_bp)

# Auto-discover and register framework internal pages
pages_dir = os.path.dirname(os.path.abspath(pages_module.__file__))
framework_pages = [f[:-3] for f in os.listdir(pages_dir) 
                   if f.endswith('.py') and f != '__init__.py']

for page_name in framework_pages:
    try:
        page_module = importlib.import_module(f"src.pages.{page_name}")
        if hasattr(page_module, 'bp'):
            app.register_blueprint(page_module.bp)
            print(f"✓ Registered framework page: {page_name}")
    except ImportError as e:
        print(f"✗ Failed to import {page_name}: {e}")
    except Exception as e:
        print(f"✗ Failed to register {page_name}: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("  Displayer Demo Application")
    print("=" * 60)
    
    # Start demo background thread for testing threads UI
    print("  Starting demo background thread...")
    demo_thread = DemoBackgroundThread()
    demo_thread.start()
    print("  ✓ Demo thread started - visit /threads/ to monitor")
    print()
    
    print("  Starting Flask server with SocketIO...")
    print("  Open your browser to: http://localhost:5001")
    print("  Press CTRL+C to stop the server")
    print("=" * 60)
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5001, allow_unsafe_werkzeug=True)
