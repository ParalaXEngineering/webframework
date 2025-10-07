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

from flask import Flask, render_template, request, session, Blueprint
from src.modules import displayer
from src.modules import utilities, access_manager, site_conf
import os

# Create Flask app
app = Flask(__name__, 
            template_folder='templates',
            static_folder='webengine/assets',
            static_url_path='/assets')
app.secret_key = 'demo-secret-key-change-in-production'

# Configure session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development

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
        self.add_sidebar_submenu("Complete Showcase", "demo.complete_showcase")
        self.add_sidebar_submenu("Settings Demo", "demo.settings_demo")

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
    
    # Add breadcrumbs
    disp.add_breadcrumb("Home", "demo.index", [])
    
    # Introduction
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Welcome"
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "This demo application showcases all DisplayerItem types and layouts available in the ParalaX Web Framework.",
        displayer.BSstyle.INFO
    ), 0)
    
    # Navigation cards
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [4, 4, 4], subtitle="Choose a Demo Category"
    ))
    
    # Layout demos
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btn_layouts", "Layout Demos", "mdi-view-dashboard", "/layouts", [], displayer.BSstyle.PRIMARY
    ), 0)
    disp.add_display_item(displayer.DisplayerItemText(
        "Explore different layout types: Vertical, Horizontal, Table, and Tabs"
    ), 0)
    
    # Text & Display demos
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btn_text", "Text & Display Items", "mdi-text", "/text-display", [], displayer.BSstyle.SUCCESS
    ), 1)
    disp.add_display_item(displayer.DisplayerItemText(
        "View text, alerts, badges, and other display elements"
    ), 1)
    
    # Input demos
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btn_inputs", "Input Items", "mdi-form-textbox", "/inputs", [], displayer.BSstyle.WARNING
    ), 2)
    disp.add_display_item(displayer.DisplayerItemText(
        "Test all input types with working form submission"
    ), 2)
    
    # Settings Demo
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="New: Settings Management Demo"
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "✨ <strong>Featured:</strong> Explore the new SettingsManager API - a clean, three-layer architecture "
        "for configuration management with full CRUD operations, validation, import/export, and search!",
        displayer.BSstyle.SUCCESS
    ), 0)
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btn_settings", "Settings Manager Demo", "mdi-cog", "/settings-demo", [], displayer.BSstyle.SUCCESS
    ), 0)
    disp.add_display_item(displayer.DisplayerItemText(
        "Interactive demonstration of the SettingsManager API with live examples and full UI"
    ), 0)
    
    # Interactive demo
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Interactive Demo"
    ))
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btn_complete", "Complete Showcase", "mdi-star", "/complete-showcase", [], displayer.BSstyle.PRIMARY
    ), 0)
    disp.add_display_item(displayer.DisplayerItemText(
        "View a comprehensive page with ALL displayer features in one place"
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
    
    # Vertical Layout Demo
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Vertical Layout Example"
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "Vertical layouts stack content vertically with customizable column widths.",
        displayer.BSstyle.INFO
    ), 0)
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [4, 4, 4], subtitle="Three Equal Columns"
    ))
    disp.add_display_item(displayer.DisplayerItemText("Column 1 content"), 0)
    disp.add_display_item(displayer.DisplayerItemText("Column 2 content"), 1)
    disp.add_display_item(displayer.DisplayerItemText("Column 3 content"), 2)
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 6, 3], subtitle="Variable Width Columns"
    ))
    disp.add_display_item(displayer.DisplayerItemText("Small (3)"), 0)
    disp.add_display_item(displayer.DisplayerItemText("Medium (6)"), 1)
    disp.add_display_item(displayer.DisplayerItemText("Small (3)"), 2)
    
    # Horizontal Layout Demo
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.HORIZONTAL, [6, 6], subtitle="Horizontal Layout Example"
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "Horizontal layouts arrange content side by side.",
        displayer.BSstyle.SUCCESS
    ), 0)
    disp.add_display_item(displayer.DisplayerItemText("Second column"), 1)
    
    # Table Layout Demo
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE, ["Name", "Status", "Actions"], subtitle="Table Layout Example"
    ))
    disp.add_display_item(displayer.DisplayerItemText("Item 1"), column=0)
    disp.add_display_item(displayer.DisplayerItemBadge("Active", displayer.BSstyle.SUCCESS), column=1)
    disp.add_display_item(displayer.DisplayerItemButton("btn_action1", "View"), column=2)
    
    # Spacer Demo
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.SPACER, [12]
    ))
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="After Spacer"
    ))
    disp.add_display_item(displayer.DisplayerItemText("Content after a spacer layout"), 0)
    
    return render_template("base_content.j2", content=disp.display())


@demo_bp.route('/text-display')
def text_display():
    """Demonstrate text and display items."""
    disp = displayer.Displayer()
    disp.add_generic("Text & Display Items")
    disp.set_title("Text & Display Components")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Text & Display", "demo.text_display", [])
    
    # Text Items
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Text Items"
    ))
    disp.add_display_item(displayer.DisplayerItemText("Simple text item"), 0)
    disp.add_display_item(displayer.DisplayerItemText("<b>Bold HTML text</b> with <i>formatting</i>"), 0)
    disp.add_display_item(displayer.DisplayerItemText(
        '<a href="https://example.com">Link in text</a>'
    ), 0)
    
    # Alerts
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Alert Styles"
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "Primary alert message", displayer.BSstyle.PRIMARY
    ), 0)
    disp.add_display_item(displayer.DisplayerItemAlert(
        "Success alert message", displayer.BSstyle.SUCCESS
    ), 0)
    disp.add_display_item(displayer.DisplayerItemAlert(
        "Info alert message", displayer.BSstyle.INFO
    ), 0)
    disp.add_display_item(displayer.DisplayerItemAlert(
        "Warning alert message", displayer.BSstyle.WARNING
    ), 0)
    disp.add_display_item(displayer.DisplayerItemAlert(
        "Error/Danger alert message", displayer.BSstyle.ERROR
    ), 0)
    
    # Badges
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [2, 2, 2, 2, 2, 2], subtitle="Badge Styles"
    ))
    disp.add_display_item(displayer.DisplayerItemBadge("Primary", displayer.BSstyle.PRIMARY), 0)
    disp.add_display_item(displayer.DisplayerItemBadge("Success", displayer.BSstyle.SUCCESS), 1)
    disp.add_display_item(displayer.DisplayerItemBadge("Info", displayer.BSstyle.INFO), 2)
    disp.add_display_item(displayer.DisplayerItemBadge("Warning", displayer.BSstyle.WARNING), 3)
    disp.add_display_item(displayer.DisplayerItemBadge("Danger", displayer.BSstyle.ERROR), 4)
    disp.add_display_item(displayer.DisplayerItemBadge("Dark", displayer.BSstyle.DARK), 5)
    
    # Buttons and Links
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 3, 3, 3], subtitle="Buttons & Links"
    ))
    disp.add_display_item(displayer.DisplayerItemButton("btn1", "Button"), 0)
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btnlink1", "Button Link", "mdi-link", "/", [], displayer.BSstyle.PRIMARY
    ), 1)
    disp.add_display_item(displayer.DisplayerItemIconLink(
        "iconlink1", "Icon Link", "mdi-home", "/", [], displayer.BSstyle.INFO
    ), 2)
    
    # Placeholder demo
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Placeholder Example"
    ))
    disp.add_display_item(displayer.DisplayerItemText("Content before placeholder"), 0)
    disp.add_display_item(displayer.DisplayerItemPlaceholder("demo_placeholder", "Placeholder content here"), 0)
    disp.add_display_item(displayer.DisplayerItemText("Content after placeholder"), 0)
    
    return render_template("base_content.j2", content=disp.display())


@demo_bp.route('/inputs', methods=['GET', 'POST'])
def inputs():
    """Demonstrate input items with form submission."""
    if request.method == 'POST':
        # Process form data
        data = utilities.util_post_to_json(request.form.to_dict())
        return render_template("success.j2", message=f"Form submitted successfully! Data: {data}")
    
    disp = displayer.Displayer()
    disp.add_generic("Input Items Demo")
    disp.set_title("Input Components")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Inputs", "demo.inputs", [])
    
    # Basic Inputs
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 9], subtitle="Basic Text Inputs"
    ))
    disp.add_display_item(displayer.DisplayerItemText("String Input:"), 0)
    disp.add_display_item(displayer.DisplayerItemInputString(
        "name", "Enter your name", "John Doe"
    ), 1)
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 9]
    ))
    disp.add_display_item(displayer.DisplayerItemText("Text Area:"), 0)
    disp.add_display_item(displayer.DisplayerItemInputText(
        "description", "Enter description", "Default text"
    ), 1)
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 9]
    ))
    disp.add_display_item(displayer.DisplayerItemText("Numeric Input:"), 0)
    disp.add_display_item(displayer.DisplayerItemInputNumeric(
        "age", "Enter age", 25
    ), 1)
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 9]
    ))
    disp.add_display_item(displayer.DisplayerItemText("Date Input:"), 0)
    disp.add_display_item(displayer.DisplayerItemInputDate(
        "date", "Select date", "2024-01-01"
    ), 1)
    
    # Select Inputs
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 9], subtitle="Select Inputs"
    ))
    disp.add_display_item(displayer.DisplayerItemText("Select:"), 0)
    disp.add_display_item(displayer.DisplayerItemInputSelect(
        "country", "Select country", "USA", ["USA", "Canada", "UK", "France", "Germany"]
    ), 1)
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 9]
    ))
    disp.add_display_item(displayer.DisplayerItemText("Multi-Select:"), 0)
    disp.add_display_item(displayer.DisplayerItemInputMultiSelect(
        "languages", "Select languages", ["Python", "JavaScript"], 
        ["Python", "JavaScript", "Java", "C++", "Ruby", "Go"]
    ), 1)
    
    # File Inputs
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 9], subtitle="File & Path Inputs"
    ))
    disp.add_display_item(displayer.DisplayerItemText("File Input:"), 0)
    disp.add_display_item(displayer.DisplayerItemInputFile(
        "upload_file", "Select file"
    ), 1)
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 9]
    ))
    disp.add_display_item(displayer.DisplayerItemText("Folder Input:"), 0)
    disp.add_display_item(displayer.DisplayerItemInputFolder(
        "folder_path", "Select folder"
    ), 1)
    
    # Hidden field
    disp.add_display_item(displayer.DisplayerItemHidden("hidden_id", "secret_value"), 0)
    
    # Submit button
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemButton("submit_form", "Submit Form"), 0)
    
    return render_template("base_content.j2", content=disp.display(), target="demo.inputs")


@demo_bp.route('/complete-showcase')
def complete_showcase():
    """A comprehensive page showing ALL displayer features."""
    disp = displayer.Displayer()
    disp.add_generic("Complete Showcase")
    disp.set_title("Complete Displayer Showcase")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Complete Showcase", "demo.complete_showcase", [])
    
    # Section 1: All Alert Types
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Section 1: Alert Styles", 
        spacing=3, background=displayer.BSstyle.LIGHT
    ))
    for style_name, style in [
        ("Primary", displayer.BSstyle.PRIMARY),
        ("Success", displayer.BSstyle.SUCCESS),
        ("Info", displayer.BSstyle.INFO),
        ("Warning", displayer.BSstyle.WARNING),
        ("Error", displayer.BSstyle.ERROR),
        ("Dark", displayer.BSstyle.DARK),
    ]:
        disp.add_display_item(displayer.DisplayerItemAlert(
            f"{style_name} alert - This demonstrates the {style_name.lower()} style",
            style
        ), 0)
    
    # Section 2: Layout Variety
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Section 2: Layout Examples", spacing=3
    ))
    
    # 2-column layout
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [6, 6], subtitle="Two Column Layout"
    ))
    disp.add_display_item(displayer.DisplayerItemText("Left column content with some text"), 0)
    disp.add_display_item(displayer.DisplayerItemText("Right column content with different text"), 1)
    
    # 3-column layout
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [4, 4, 4], subtitle="Three Column Layout"
    ))
    disp.add_display_item(displayer.DisplayerItemBadge("Badge 1", displayer.BSstyle.PRIMARY), 0)
    disp.add_display_item(displayer.DisplayerItemBadge("Badge 2", displayer.BSstyle.SUCCESS), 1)
    disp.add_display_item(displayer.DisplayerItemBadge("Badge 3", displayer.BSstyle.INFO), 2)
    
    # Table layout
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE, ["Item", "Status", "Priority", "Action"], 
        subtitle="Table Layout"
    ))
    disp.add_display_item(displayer.DisplayerItemText("Task 1"), column=0, line=0)
    disp.add_display_item(displayer.DisplayerItemBadge("Active", displayer.BSstyle.SUCCESS), column=1, line=0)
    disp.add_display_item(displayer.DisplayerItemBadge("High", displayer.BSstyle.ERROR), column=2, line=0)
    disp.add_display_item(displayer.DisplayerItemButton("action1", "Edit"), column=3, line=0)
    
    disp.add_display_item(displayer.DisplayerItemText("Task 2"), column=0, line=1)
    disp.add_display_item(displayer.DisplayerItemBadge("Pending", displayer.BSstyle.WARNING), column=1, line=1)
    disp.add_display_item(displayer.DisplayerItemBadge("Medium", displayer.BSstyle.WARNING), column=2, line=1)
    disp.add_display_item(displayer.DisplayerItemButton("action2", "View"), column=3, line=1)
    
    # Section 3: Button Variety
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Section 3: Buttons & Links", spacing=3
    ))
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 3, 3, 3]
    ))
    disp.add_display_item(displayer.DisplayerItemButton("btn_default", "Default Button"), 0)
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btn_link", "Link Button", "mdi-open-in-new", "/", [], displayer.BSstyle.SUCCESS
    ), 1)
    disp.add_display_item(displayer.DisplayerItemIconLink(
        "icon_link", "Icon Link", "mdi-information", "/", [], displayer.BSstyle.INFO
    ), 2)
    # Removed DisplayerItemDownload with placeholder "#" link
    
    # Section 4: Text Formatting
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Section 4: Text Formatting", spacing=3
    ))
    disp.add_display_item(displayer.DisplayerItemText("Regular text"), 0)
    disp.add_display_item(displayer.DisplayerItemText("<b>Bold text</b>"), 0)
    disp.add_display_item(displayer.DisplayerItemText("<i>Italic text</i>"), 0)
    disp.add_display_item(displayer.DisplayerItemText("<u>Underlined text</u>"), 0)
    disp.add_display_item(displayer.DisplayerItemText(
        '<span style="color: red;">Colored text</span>'
    ), 0)
    disp.add_display_item(displayer.DisplayerItemText(
        '<a href="https://example.com" target="_blank">External Link</a>'
    ), 0)
    
    # Summary section
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Summary", 
        spacing=3, background=displayer.BSstyle.LIGHT
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "This page demonstrates the key features of the Displayer system. "
        "Each section showcases different components and layouts. "
        "Use this as a visual reference for building your own pages.",
        displayer.BSstyle.SUCCESS
    ), 0)
    
    return render_template("base_content.j2", content=disp.display())


@demo_bp.route('/settings-demo')
def settings_demo():
    """Interactive demo of the SettingsManager functionality."""
    from src.modules.settings_manager import SettingsManager
    import tempfile
    import json
    
    disp = displayer.Displayer()
    disp.add_generic("Settings Demo")
    disp.set_title("SettingsManager API Demo")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Settings Demo", "demo.settings_demo", [])
    
    # Create a temporary settings manager for demonstration
    temp_config = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    temp_path = temp_config.name
    temp_config.close()
    
    manager = SettingsManager(temp_path, create_backup=False)
    manager.load()
    
    # Introduction
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Overview"
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "This demo showcases the SettingsManager API - a clean, three-layer architecture for "
        "managing application configuration. The system provides data persistence, business logic, "
        "and presentation layers with complete separation of concerns.",
        displayer.BSstyle.INFO
    ), 0)
    
    # Architecture Diagram
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Three-Layer Architecture"
    ))
    architecture_html = """
    <div class="card">
        <div class="card-body">
            <h5>Clean Architecture Layers</h5>
            <div style="font-family: monospace; background: #f8f9fa; padding: 20px; border-radius: 5px;">
                <div style="border: 2px solid #0d6efd; padding: 10px; margin-bottom: 10px; border-radius: 5px;">
                    <strong>📱 Presentation Layer</strong> (settings_v2.py)<br>
                    Flask routes, request/response handling, UI rendering
                </div>
                <div style="text-align: center; margin: 10px 0;">⬇️ delegates to ⬇️</div>
                <div style="border: 2px solid #198754; padding: 10px; margin-bottom: 10px; border-radius: 5px;">
                    <strong>💼 Business Logic Layer</strong> (SettingsManager)<br>
                    Categories, validation, import/export, search
                </div>
                <div style="text-align: center; margin: 10px 0;">⬇️ delegates to ⬇️</div>
                <div style="border: 2px solid #dc3545; padding: 10px; border-radius: 5px;">
                    <strong>💾 Data Layer</strong> (SettingsStorage)<br>
                    JSON file persistence, schema validation, backups
                </div>
            </div>
        </div>
    </div>
    """
    disp.add_display_item(displayer.DisplayerItemText(architecture_html), 0)
    
    # Live Demo Section at top
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Live Settings Interface"
    ))
    
    live_demo_html = """
    <div class="card border-primary">
        <div class="card-header bg-primary text-white">
            <h5 class="mb-0">🚀 Try the Live Settings Interface</h5>
        </div>
        <div class="card-body">
            <p>Experience the complete settings management interface with all features:</p>
            <ul>
                <li>Dashboard with overview and quick actions</li>
                <li>View all settings grouped by category</li>
                <li>Edit settings with type-appropriate inputs</li>
                <li>Import/Export configurations</li>
                <li>Search functionality</li>
            </ul>
            <div class="d-grid gap-2 mt-3">
                <a href="/settings_v2/" class="btn btn-primary btn-lg">
                    <i class="mdi mdi-cog"></i> Open Settings Interface
                </a>
            </div>
        </div>
    </div>
    """
    disp.add_display_item(displayer.DisplayerItemText(live_demo_html), 0)
    
    # Cleanup temp files
    import os
    try:
        os.unlink(temp_path)
    except:
        pass
    
    return render_template("base_content.j2", content=disp.display())


# Register blueprints
app.register_blueprint(demo_bp)
app.register_blueprint(common_bp)

if __name__ == '__main__':
    print("=" * 60)
    print("  Displayer Demo Application")
    print("=" * 60)
    print(f"  Starting Flask server...")
    print(f"  Open your browser to: http://localhost:5001")
    print(f"  Press CTRL+C to stop the server")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5001)
