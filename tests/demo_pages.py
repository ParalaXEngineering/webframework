"""
Demo Pages Blueprint

All the demo routes for showcasing displayer components.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session
from functools import wraps
from src.modules import displayer, utilities

# Create blueprint for demo routes
demo_bp = Blueprint('demo', __name__)


def require_login(f):
    """Decorator to require login for demo pages."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('common.login'))
        return f(*args, **kwargs)
    return decorated_function


@demo_bp.route('/')
@require_login
def index():
    """Main index page with gallery of demo pages."""
    disp = displayer.Displayer()
    disp.add_generic("Demo Gallery")
    disp.set_title("Displayer Component Showcase")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    
    # Info alert
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "<strong>ParalaX Web Framework Demo</strong> - Explore all displayer components and features",
        displayer.BSstyle.INFO
    ), 0)
    
    # Gallery - Row 1: Core Components
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 3, 3, 3]
    ))
    
    disp.add_display_item(displayer.DisplayerItemCard(
        id="card_layouts",
        title="Layouts",
        icon="mdi-view-dashboard",
        header_color=displayer.BSstyle.PRIMARY,
        body="Explore VERTICAL, HORIZONTAL, TABLE, TABS, and SPACER layouts",
        footer_buttons=[{"id": "btn_layouts", "text": "View Demos", "style": "primary"}]
    ), 0)
    
    disp.add_display_item(displayer.DisplayerItemCard(
        id="card_text",
        title="Text & Display",
        icon="mdi-text",
        header_color=displayer.BSstyle.SUCCESS,
        body="Text, alerts, badges, progress bars, and display components",
        footer_buttons=[{"id": "btn_text", "text": "View Demos", "style": "success"}]
    ), 1)
    
    disp.add_display_item(displayer.DisplayerItemCard(
        id="card_inputs",
        title="Input Components",
        icon="mdi-form-textbox",
        header_color=displayer.BSstyle.WARNING,
        body="Text inputs, dropdowns, checkboxes, file uploads, and more",
        footer_buttons=[{"id": "btn_inputs", "text": "View Demos", "style": "warning"}]
    ), 2)
    
    disp.add_display_item(displayer.DisplayerItemCard(
        id="card_tables",
        title="Table Modes (NEW)",
        icon="mdi-table",
        header_color=displayer.BSstyle.INFO,
        body="SIMPLE, INTERACTIVE, BULK_DATA, SERVER_SIDE table rendering modes",
        footer_buttons=[{"id": "btn_tables", "text": "View Demos", "style": "info"}]
    ), 3)
    
    # Gallery - Row 2: Advanced Features
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 3, 3, 3]
    ))
    
    disp.add_display_item(displayer.DisplayerItemCard(
        id="card_threading",
        title="Threading",
        icon="mdi-cog-sync",
        header_color=displayer.BSstyle.ERROR,
        body="Background tasks with progress tracking and real-time updates",
        footer_buttons=[{"id": "btn_threading", "text": "View Demos", "style": "danger"}]
    ), 0)
    
    disp.add_display_item(displayer.DisplayerItemCard(
        id="card_scheduler",
        title="Scheduler",
        icon="mdi-clock-fast",
        header_color=displayer.BSstyle.SECONDARY,
        body="Scheduled tasks, emit_status, popups, and dynamic reloading",
        footer_buttons=[{"id": "btn_scheduler", "text": "View Demos", "style": "secondary"}]
    ), 1)
    
    disp.add_display_item(displayer.DisplayerItemCard(
        id="card_settings",
        title="Settings",
        icon="mdi-cog",
        header_color=displayer.BSstyle.DARK,
        body="Framework settings and configuration management",
        footer_buttons=[{"id": "btn_settings", "text": "Open Settings", "style": "dark"}]
    ), 2)
    
    disp.add_display_item(displayer.DisplayerItemCard(
        id="card_logs",
        title="Log Viewer",
        icon="mdi-file-document-multiple",
        header_color=displayer.BSstyle.PRIMARY,
        body="Real-time log file monitoring with DataTables filtering",
        footer_buttons=[{"id": "btn_logs", "text": "View Logs", "style": "primary"}]
    ), 3)
    
    # Complete showcase button
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btn_complete", "🌟 Complete Component Showcase", "mdi-star", "/complete-showcase", [], displayer.BSstyle.SUCCESS
    ), 0)
    
    # Handle card button clicks
    if request.method == 'POST':
        data_in = utilities.util_post_to_json(request.form.to_dict())
        if "Demo Gallery" in data_in:
            module_data = data_in["Demo Gallery"]
            if "btn_layouts" in module_data:
                from flask import redirect, url_for
                return redirect(url_for('demo.layouts'))
            elif "btn_text" in module_data:
                from flask import redirect, url_for
                return redirect(url_for('demo.text_display'))
            elif "btn_inputs" in module_data:
                from flask import redirect, url_for
                return redirect(url_for('demo.inputs'))
            elif "btn_tables" in module_data:
                from flask import redirect, url_for
                return redirect(url_for('demo.table_modes'))
            elif "btn_threading" in module_data:
                from flask import redirect, url_for
                return redirect(url_for('demo.threading_demo'))
            elif "btn_scheduler" in module_data:
                from flask import redirect, url_for
                return redirect(url_for('demo.scheduler_demo'))
            elif "btn_settings" in module_data:
                from flask import redirect, url_for
                return redirect(url_for('settings.index'))
            elif "btn_logs" in module_data:
                from flask import redirect, url_for
                return redirect(url_for('logging.index'))
    
    return render_template("base_content.j2", content=disp.display())


@demo_bp.route('/layouts')
@require_login
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
@require_login
def text_display():
    """Demonstrate text and display items."""
    disp = displayer.Displayer()
    disp.add_generic("Text & Display")
    disp.set_title("Text & Display Components")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Text & Display", "demo.text_display", [])
    
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
    
    # Action Buttons
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Action Buttons (CRUD Operations)"
    ))
    disp.add_display_item(displayer.DisplayerItemText(
        "<p>Action buttons are commonly used in tables for quick CRUD operations. "
        "They provide View, Edit, Delete, and other actions in a compact format.</p>"
    ), 0)
    
    # Demo different styles
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE,
        columns=["Item", "Status", "Button Style", "Actions"]
    ))
    
    # Row 1: Default button style with all actions
    disp.add_display_item(displayer.DisplayerItemText("User #1234"), column=0)
    disp.add_display_item(displayer.DisplayerItemBadge("Active", displayer.BSstyle.SUCCESS), column=1)
    disp.add_display_item(displayer.DisplayerItemText("Buttons (default)"), column=2)
    disp.add_display_item(displayer.DisplayerItemActionButtons(
        id="actions_user_1234",
        view_url="https://www.google.com",
        edit_url="https://www.google.com",
        delete_url="https://www.google.com"
    ), column=3)
    
    # Row 2: Icon style (more compact)
    disp.add_display_item(displayer.DisplayerItemText("Product #5678"), column=0)
    disp.add_display_item(displayer.DisplayerItemBadge("Pending", displayer.BSstyle.WARNING), column=1)
    disp.add_display_item(displayer.DisplayerItemText("Icons only"), column=2)
    disp.add_display_item(displayer.DisplayerItemActionButtons(
        id="actions_product_5678",
        view_url="https://www.google.com",
        edit_url="https://www.google.com",
        delete_url="https://www.google.com",
        style="icons"
    ), column=3)
    
    # Row 3: Only edit and delete
    disp.add_display_item(displayer.DisplayerItemText("Comment #9012"), column=0)
    disp.add_display_item(displayer.DisplayerItemBadge("Flagged", displayer.BSstyle.ERROR), column=1)
    disp.add_display_item(displayer.DisplayerItemText("Edit & Delete only"), column=2)
    disp.add_display_item(displayer.DisplayerItemActionButtons(
        id="actions_comment_9012",
        edit_url="https://www.google.com",
        delete_url="https://www.google.com"
    ), column=3)
    
    # Row 4: Custom actions
    disp.add_display_item(displayer.DisplayerItemText("Report #3456"), column=0)
    disp.add_display_item(displayer.DisplayerItemBadge("Complete", displayer.BSstyle.INFO), column=1)
    disp.add_display_item(displayer.DisplayerItemText("Custom actions"), column=2)
    disp.add_display_item(displayer.DisplayerItemActionButtons(
        id="actions_report_3456",
        actions=[
            {"type": "view", "url": "https://www.google.com", "icon": "mdi mdi-eye", "style": "info", "tooltip": "View Report"},
            {"type": "download", "url": "https://www.google.com", "icon": "mdi mdi-download", "style": "success", "tooltip": "Download PDF"},
            {"type": "copy", "url": "https://www.google.com", "icon": "mdi mdi-content-copy", "style": "secondary", "tooltip": "Copy Link"}
        ]
    ), column=3)
    
    # Row 5: Large size buttons
    disp.add_display_item(displayer.DisplayerItemText("Project #7890"), column=0)
    disp.add_display_item(displayer.DisplayerItemBadge("Active", displayer.BSstyle.SUCCESS), column=1)
    disp.add_display_item(displayer.DisplayerItemText("Large size"), column=2)
    disp.add_display_item(displayer.DisplayerItemActionButtons(
        id="actions_project_7890",
        view_url="https://www.google.com",
        edit_url="https://www.google.com",
        delete_url="https://www.google.com",
        size="lg"
    ), column=3)
    
    return render_template("base_content.j2", content=disp.display())


@demo_bp.route('/inputs', methods=['GET', 'POST'])
@require_login
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
    disp.add_display_item(displayer.DisplayerItemText("Numeric:"), 0)
    disp.add_display_item(displayer.DisplayerItemInputNumeric("age", "Age", 25), 1)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 9]))
    disp.add_display_item(displayer.DisplayerItemText("Select:"), 0)
    disp.add_display_item(displayer.DisplayerItemInputSelect(
        "country", "Country", "USA", ["USA", "Canada", "UK", "France"]
    ), 1)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemButton("submit_form", "Submit"), 0)
    
    return render_template("base_content.j2", content=disp.display(), target="demo.inputs")


@demo_bp.route('/complete-showcase')
@require_login
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
    
    # Table
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE, ["Item", "Status", "Action"], subtitle="Table"
    ))
    disp.add_display_item(displayer.DisplayerItemText("Task 1"), column=0, line=0)
    disp.add_display_item(displayer.DisplayerItemBadge("Active", displayer.BSstyle.SUCCESS), column=1, line=0)
    disp.add_display_item(displayer.DisplayerItemButton("action1", "Edit"), column=2, line=0)
    
    return render_template("base_content.j2", content=disp.display())


@demo_bp.route('/threading-demo', methods=['GET', 'POST'])
@require_login
def threading_demo():
    """Threading demo with buttons to start various thread types."""
    from demo_support.demo_threaded_complete import DemoThreadedAction
    from src.modules.threaded import threaded_manager
    
    disp = displayer.Displayer()
    disp.add_module(DemoThreadedAction)
    disp.set_title("Threading System Demo")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Threading Demo", "demo.threading_demo", [])
    
    # Handle POST requests (button clicks)
    if request.method == 'POST':
        # Parse form data using util_post_to_json
        data_in = utilities.util_post_to_json(request.form.to_dict())
        
        # Check if our module is in the data
        if DemoThreadedAction.m_default_name in data_in:
            module_data = data_in[DemoThreadedAction.m_default_name]
            
            # Check which button was clicked
            if 'btn_complete' in module_data:
                thread = DemoThreadedAction("complete")
                thread.start()
                disp.add_display_item(displayer.DisplayerItemAlert("✓ Started Complete Demo Thread", displayer.BSstyle.SUCCESS), 0)
            elif 'btn_console' in module_data:
                thread = DemoThreadedAction("console")
                thread.start()
                disp.add_display_item(displayer.DisplayerItemAlert("✓ Started Console Demo Thread", displayer.BSstyle.SUCCESS), 0)
            elif 'btn_logging' in module_data:
                thread = DemoThreadedAction("logging")
                thread.start()
                disp.add_display_item(displayer.DisplayerItemAlert("✓ Started Logging Demo Thread", displayer.BSstyle.SUCCESS), 0)
            elif 'btn_process' in module_data:
                thread = DemoThreadedAction("process")
                thread.start()
                disp.add_display_item(displayer.DisplayerItemAlert("✓ Started Process Demo Thread", displayer.BSstyle.SUCCESS), 0)
            elif 'btn_stop' in module_data:
                count = threaded_manager.thread_manager_obj.get_thread_count()
                threaded_manager.thread_manager_obj.kill_all_threads()
                disp.add_display_item(displayer.DisplayerItemAlert("✓ Stopped {} threads".format(count), displayer.BSstyle.WARNING), 0)
    
    # Description
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemText(
        """<h3>Threading Demo</h3>
        <p>Start different types of demo threads to see all features of the threading system.
        Each thread demonstrates console output, logging, progress tracking, and more.
        Visit the <a href='/threads/'>Threads Monitor</a> page to see them in action!</p>"""
    ), 0)
    
    # Thread statistics
    stats = threaded_manager.thread_manager_obj.get_thread_stats()
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 3, 3, 3]
    ))
    
    disp.add_display_item(displayer.DisplayerItemText(
        "<strong>Total Threads</strong><br><h3>{}</h3>".format(stats['total'])
    ), 0)
    disp.add_display_item(displayer.DisplayerItemText(
        "<strong>Running</strong><br><h3>{}</h3>".format(stats['running'])
    ), 1)
    disp.add_display_item(displayer.DisplayerItemText(
        "<strong>With Process</strong><br><h3>{}</h3>".format(stats['with_process'])
    ), 2)
    disp.add_display_item(displayer.DisplayerItemText(
        "<strong>With Errors</strong><br><h3>{}</h3>".format(stats['with_error'])
    ), 3)
    
    # Separator and section title
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemSeparator(), 0)
    disp.add_display_item(displayer.DisplayerItemText(
        "<h4>🚀 Start Demo Threads</h4><p>Click a button below to start a demo thread that showcases different features.</p>"
    ), 0)
    
    # Demo buttons
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [6, 6]
    ))
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_complete", "🤖 Complete Demo"
    ), 0)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_console", "📋 Console Demo"
    ), 0)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_logging", "📝 Logging Demo"
    ), 1)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_process", "⚙️ Process Demo"
    ), 1)
    
    # Monitor and control buttons
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [6, 6]
    ))
    
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btn_monitor", "📊 Monitor Threads →", "monitor-eye",
        "/threads/", [], displayer.BSstyle.SECONDARY
    ), 0)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_stop", "🛑 Stop All Threads"
    ), 1)
    
    return render_template("base_content.j2", content=disp.display(), target="demo.threading_demo")


@demo_bp.route('/scheduler-demo', methods=['GET', 'POST'])
@require_login
def scheduler_demo():
    """Demonstrate scheduler functionality with threaded actions."""
    from demo_support.demo_scheduler_action import DemoSchedulerAction
    from src.modules.threaded import threaded_manager
    
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


@demo_bp.route('/table-modes')
@require_login
def table_modes():
    """Showcase new TABLE layout modes with TableMode enum."""
    disp = displayer.Displayer()
    disp.add_generic("Table Modes Showcase")
    disp.set_title("New TABLE Layout API - TableMode Examples")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Table Modes", "demo.table_modes", [])
    
    # Info
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "<strong>NEW API:</strong> Use <code>datatable_config</code> with <code>TableMode</code> enum instead of confusing 'basic/advanced/ajax' strings!",
        displayer.BSstyle.INFO
    ), 0)
    
    # 1. Simple HTML Table (no DataTables)
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="1. TableMode.SIMPLE - Plain HTML Table"
    ))
    disp.add_display_item(displayer.DisplayerItemText(
        "No DataTables JavaScript - just plain HTML. Fastest rendering, no features."
    ), 0)
    
    layout_id = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE,
        columns=["Name", "Email", "Role"]
        # No datatable_config = plain HTML
    ))
    disp.add_display_item(displayer.DisplayerItemText("Alice Smith"), 0, line=0, layout_id=layout_id)
    disp.add_display_item(displayer.DisplayerItemText("alice@example.com"), 1, line=0, layout_id=layout_id)
    disp.add_display_item(displayer.DisplayerItemBadge("Admin", displayer.BSstyle.PRIMARY), 2, line=0, layout_id=layout_id)
    
    disp.add_display_item(displayer.DisplayerItemText("Bob Johnson"), 0, line=1, layout_id=layout_id)
    disp.add_display_item(displayer.DisplayerItemText("bob@example.com"), 1, line=1, layout_id=layout_id)
    disp.add_display_item(displayer.DisplayerItemBadge("User", displayer.BSstyle.SUCCESS), 2, line=1, layout_id=layout_id)
    
    # 2. Interactive Mode
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="2. TableMode.INTERACTIVE - Manual Row Population"
    ))
    disp.add_display_item(displayer.DisplayerItemText(
        "DataTables with manual item population. Flexible - can use any DisplayerItem. Searchable columns enabled."
    ), 0)
    
    layout_id = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE,
        columns=["Product", "Price", "Actions"],
        datatable_config={
            "table_id": "interactive_demo",
            "mode": displayer.TableMode.INTERACTIVE,
            "searchable_columns": [0]  # Enable search on Product column
        }
    ))
    
    products = [
        ("Laptop", "$1,299", "primary"),
        ("Mouse", "$29", "success"),
        ("Keyboard", "$89", "info")
    ]
    
    for line, (product, price, style) in enumerate(products):
        disp.add_display_item(displayer.DisplayerItemText(product), 0, line=line, layout_id=layout_id)
        disp.add_display_item(displayer.DisplayerItemBadge(price, getattr(displayer.BSstyle, style.upper())), 1, line=line, layout_id=layout_id)
        disp.add_display_item(displayer.DisplayerItemButton(f"buy_{line}", "Buy"), 2, line=line, layout_id=layout_id)
    
    # 3. Bulk Data Mode
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="3. TableMode.BULK_DATA - Pre-loaded JSON"
    ))
    disp.add_display_item(displayer.DisplayerItemText(
        "Most efficient for large datasets (100s-1000s of rows). Data loaded as JSON with search panes on selected columns."
    ), 0)
    
    bulk_data = [
        {"User": "Alice Cooper", "Department": "Engineering", "Status": "Active", "Projects": 5},
        {"User": "Bob Dylan", "Department": "Marketing", "Status": "Active", "Projects": 3},
        {"User": "Charlie Brown", "Department": "Engineering", "Status": "On Leave", "Projects": 2},
        {"User": "Diana Ross", "Department": "Sales", "Status": "Active", "Projects": 8},
        {"User": "Eddie Vedder", "Department": "Engineering", "Status": "Active", "Projects": 4},
        {"User": "Frank Sinatra", "Department": "Sales", "Status": "Active", "Projects": 6},
    ]
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE,
        columns=["User", "Department", "Status", "Projects"],
        datatable_config={
            "table_id": "bulk_demo",
            "mode": displayer.TableMode.BULK_DATA,
            "data": bulk_data,
            "columns": [
                {"data": "User"},
                {"data": "Department"},
                {"data": "Status"},
                {"data": "Projects"}
            ],
            "searchable_columns": [1, 2]  # Search panes on Department (col 1) and Status (col 2)
        }
    ))
    
    # 4. Code examples
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Code Examples"
    ))
    
    code_example = '''# NEW API - Clear and explicit
from src.modules.displayer import DisplayerLayout, Layouts, TableMode

# 1. SIMPLE - Plain HTML table (no DataTables JavaScript)
layout = DisplayerLayout(
    Layouts.TABLE, 
    columns=["Name", "Status"]
    # No datatable_config = plain HTML table
)

# 2. INTERACTIVE - Manual row population with DisplayerItems
layout_id = disp.add_master_layout(DisplayerLayout(
    Layouts.TABLE,
    columns=["Product", "Price", "Actions"],
    datatable_config={
        "table_id": "interactive_demo",
        "mode": TableMode.INTERACTIVE,
        "searchable_columns": [0]  # Search pane on Product column
    }
))
# Then add items with add_display_item(item, column, line, layout_id)

# 3. BULK_DATA - Pre-loaded JSON (most efficient for large datasets)
bulk_data = [
    {"User": "Alice", "Department": "Engineering", "Status": "Active"},
    {"User": "Bob", "Department": "Marketing", "Status": "Active"}
]
layout = DisplayerLayout(
    Layouts.TABLE,
    columns=["User", "Department", "Status"],
    datatable_config={
        "table_id": "bulk_demo",
        "mode": TableMode.BULK_DATA,
        "data": bulk_data,
        "columns": [
            {"data": "User"},
            {"data": "Department"}, 
            {"data": "Status"}
        ],
        "searchable_columns": [1, 2]  # Search panes on columns 1 & 2
    }
)

# 4. SERVER_SIDE - AJAX endpoint (for dynamic/real-time data)
layout = DisplayerLayout(
    Layouts.TABLE,
    columns=["Name", "Status"],
    datatable_config={
        "table_id": "ajax_demo",
        "mode": TableMode.SERVER_SIDE,
        "api_endpoint": "api.get_users",  # Flask route name
        "columns": [{"data": "Name"}, {"data": "Status"}],
        "refresh_interval": 3000  # Auto-refresh every 3s
    }
)

# OLD API (deprecated - shows warning)
layout = DisplayerLayout(
    Layouts.TABLE,
    columns=["Name"],
    responsive={"table1": {"type": "advanced", ...}}
)'''
    
    disp.add_display_item(displayer.DisplayerItemText(f"<pre><code>{code_example}</code></pre>"), 0)
    
    return render_template("base_content.j2", content=disp.display())
