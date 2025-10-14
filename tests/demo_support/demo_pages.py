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
    """Main index page - demo landing page."""
    disp = displayer.Displayer()
    disp.add_generic("Demo Landing")
    disp.set_title("ParalaX Framework Demos")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    
    # Welcome message
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "<strong>Welcome to the ParalaX Web Framework Demo Application</strong><br><br>"
        "This application demonstrates key features of the ParalaX Framework:<br><br>"
        "<ul>"
        "<li><strong>Component Showcase:</strong> Auto-generated catalog of all DisplayerItem components</li>"
        "<li><strong>Demo Pages:</strong> Examples of layouts, inputs, threading, scheduling, and more</li>"
        "<li><strong>Authorization:</strong> Permission-based page access examples</li>"
        "<li><strong>Framework Features:</strong> Settings, logging, thread monitoring, and more</li>"
        "</ul><br>"
        "Use the sidebar to navigate through different sections.",
        displayer.BSstyle.INFO
    ), 0)
    
    # Quick Links Section
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Quick Links"
    ))
    
    # Table of quick links
    layout_id = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE,
        columns=["Section", "Description", "Link"]
    ))
    
    quick_links = [
        ("Component Showcase", "Browse all auto-discovered DisplayerItem components", "showcase.index"),
        ("Layouts Demo", "Examples of VERTICAL, HORIZONTAL, TABLE, TABS layouts", "demo.layouts"),
        ("Text & Display", "Alerts, badges, text, and display components", "demo.text_display"),
        ("Input Components", "Forms, inputs, file uploads, and more", "demo.inputs"),
        ("Table Modes", "SIMPLE, INTERACTIVE, BULK_DATA, SERVER_SIDE examples", "demo.table_modes"),
        ("Threading Demo", "Background tasks with progress tracking", "demo.threading_demo"),
        ("Scheduler Demo", "Scheduled tasks and dynamic reloading", "demo.scheduler_demo"),
    ]
    
    for line, (name, desc, url) in enumerate(quick_links):
        disp.add_display_item(
            displayer.DisplayerItemText(f"<strong>{name}</strong>"),
            column=0, layout_id=layout_id, line=line
        )
        disp.add_display_item(
            displayer.DisplayerItemText(desc),
            column=1, layout_id=layout_id, line=line
        )
        disp.add_display_item(
            displayer.DisplayerItemButtonLink(
                id=f"link_{line}",
                text="Open",
                icon="arrow-right",
                link=url,
                color=displayer.BSstyle.PRIMARY
            ),
            column=2, layout_id=layout_id, line=line
        )
    
    return render_template("base_content.j2", content=disp.display())


@demo_bp.route('/layouts')
@require_login
def layouts():
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

@demo_bp.route('/threading-demo', methods=['GET', 'POST'])
@require_login
def threading_demo():
    """Threading demo with buttons to start various thread types."""
    from demo_support.demo_threaded_complete import DemoThreadedAction
    from src.modules.threaded import threaded_manager
    
    username = session.get('username')
    
    # No need to manually check permissions anymore - the framework handles it!
    # When we add the module, if the user doesn't have permission,
    # an access denied message will be displayed automatically.
    
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
    
    username = session.get('username')
    
    # No need to manually check permissions anymore - the framework handles it!
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
    
    disp = displayer.Displayer()
    disp.add_generic("Table Modes Showcase")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Table Modes", "demo.table_modes", [])
        
    # 1. Simple HTML Table (no DataTables)
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="1. TableMode.SIMPLE - Plain HTML Table"
    ))
    disp.add_display_item(displayer.DisplayerItemText(
        "Use basic displayer items to render. Can be slow for large datasets (50+ rows). No search or pagination."
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
        "Use Datatable for rendering, while DisplayerItem is used for population. Can be slow for large datasets (50+ rows). Search and pagination enabled."
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

    # 4. Server-Side Mode
    # TODO: Implement a real API endpoint for demo, and present the code here
    
    # 4. Code examples
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Code Examples"
    ))
    
    # TODO: create displayer item for code with syntax highlighting
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


# ============================================================================
# AUTHORIZATION DEMOS
# ============================================================================

@demo_bp.route('/auth/accessible')
@require_login
def auth_accessible():
    """A page anyone logged in can access."""
    from src.modules.auth.auth_manager import auth_manager
    
    username = session.get('username')
    user = auth_manager.get_user(username)
    
    disp = displayer.Displayer()
    disp.add_generic("Accessible Page")
    disp.set_title("Public Demo Page")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Accessible Page", "demo.auth_accessible", [])
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemAlert(
        f"<h4>✓ Welcome {username}!</h4>"
        "<p>This page is accessible to any logged-in user.</p>"
        "<p><strong>No special permissions required.</strong></p>",
        displayer.BSstyle.SUCCESS
    ), 0)
    
    disp.add_display_item(displayer.DisplayerItemText(
        "<h5>Your Account Info:</h5>"
        f"<ul>"
        f"<li><strong>Username:</strong> {user.username}</li>"
        f"<li><strong>Groups:</strong> {', '.join(user.groups) if user.groups else 'None'}</li>"
        f"<li><strong>Is Admin:</strong> {'Yes' if 'admin' in user.groups else 'No'}</li>"
        f"</ul>"
    ), 0)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.HORIZONTAL, [6, 6]))
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btn_home", "Back to Demos", "mdi-home", url_for('demo.index'), [], displayer.BSstyle.SECONDARY
    ), 0)
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btn_restricted", "Try Restricted Page", "mdi-lock", url_for('demo.auth_restricted'), [], displayer.BSstyle.WARNING
    ), 1)
    
    return render_template("base_content.j2", content=disp.display())


@demo_bp.route('/auth/restricted')
@require_login
def auth_restricted():
    """A page that requires specific permission."""
    from demo_support.demo_auth_action import DemoAuthorizationAction
    
    username = session.get('username')
    
    # No need to manually check permissions anymore - the framework handles it!
    
    disp = displayer.Displayer()
    disp.add_module(DemoAuthorizationAction)
    disp.set_title("Protected Demo Page")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Restricted Page", "demo.auth_restricted", [])
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    
    # If the user has permission (module not denied), show success message
    # The framework will automatically show access denied if permission is missing
    disp.add_display_item(displayer.DisplayerItemAlert(
        f"<h4>🔓 Access Granted!</h4>"
        f"<p>Welcome {username}! You have the required permission.</p>"
        "<p><strong>Required:</strong> 'view' permission in 'Demo_Authorization' module</p>",
        displayer.BSstyle.SUCCESS
    ), 0)
    
    disp.add_display_item(displayer.DisplayerItemText(
        "<h5>Protected Content:</h5>"
        "<p>This is secret information only visible to authorized users!</p>"
        "<ul>"
        "<li>Sensitive data 1</li>"
        "<li>Sensitive data 2</li>"
        "<li>Sensitive data 3</li>"
        "</ul>"
    ), 0)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.HORIZONTAL, [6, 6]))
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btn_home", "Back to Demos", "mdi-home", url_for('demo.index'), [], displayer.BSstyle.SECONDARY
    ), 0)
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btn_admin", "Try Admin Page", "mdi-shield-crown", url_for('demo.auth_admin'), [], displayer.BSstyle.ERROR
    ), 1)
    
    return render_template("base_content.j2", content=disp.display())


@demo_bp.route('/auth/admin')
@require_login
def auth_admin():
    """A page that requires admin role."""
    from src.modules.auth.auth_manager import auth_manager
    
    username = session.get('username')
    user = auth_manager.get_user(username)
    
    # Check if user is admin
    is_admin = 'admin' in user.groups
    
    disp = displayer.Displayer()
    disp.add_generic("Admin Page")
    disp.set_title("Administrator Only")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Admin Page", "demo.auth_admin", [])
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    
    if is_admin:
        disp.add_display_item(displayer.DisplayerItemAlert(
            f"<h4>👑 Admin Access Granted!</h4>"
            f"<p>Welcome {username}! You have administrator privileges.</p>"
            "<p><strong>Required:</strong> 'admin' group membership</p>",
            displayer.BSstyle.SUCCESS
        ), 0)
        
        # Show all users
        all_users = auth_manager.get_all_users()
        
        disp.add_display_item(displayer.DisplayerItemText(
            f"<h5>System Users ({len(all_users)}):</h5>"
        ), 0)
        
        table_layout = disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.TABLE,
            ["Username", "Groups", "Last Login"]
        ))
        
        for u in all_users:
            disp.add_display_item(displayer.DisplayerItemText(u.username), 0, layout_id=table_layout)
            
            groups_text = ', '.join(u.groups) if u.groups else 'None'
            disp.add_display_item(displayer.DisplayerItemText(groups_text), 1, layout_id=table_layout)
            disp.add_display_item(displayer.DisplayerItemText(u.last_login or 'Never'), 2, layout_id=table_layout)
    else:
        disp.add_display_item(displayer.DisplayerItemAlert(
            f"<h4>⛔ Admin Access Required</h4>"
            f"<p>Sorry {username}, this page is for administrators only.</p>"
            "<p><strong>Required:</strong> 'admin' group membership</p>"
            "<p><em>You need to be in the 'admin' group to access this page.</em></p>",
            displayer.BSstyle.ERROR
        ), 0)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.HORIZONTAL, [6, 6]))
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btn_home", "Back to Demos", "mdi-home", url_for('demo.index'), [], displayer.BSstyle.SECONDARY
    ), 0)
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btn_accessible", "Back to Accessible Page", "mdi-check", url_for('demo.auth_accessible'), [], displayer.BSstyle.SUCCESS
    ), 1)
    
    return render_template("base_content.j2", content=disp.display())
