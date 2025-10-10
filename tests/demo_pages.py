"""
Demo Pages Blueprint

All the demo routes for showcasing displayer components.
"""

from flask import Blueprint, render_template, request
from src.modules import displayer, utilities

# Create blueprint for demo routes
demo_bp = Blueprint('demo', __name__)


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
        "btn_threading", "Threading", "mdi-cog-sync", "/threading-demo", [], displayer.BSstyle.ERROR
    ), 3)
    
    # Second row
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [4, 4, 4]
    ))
    
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btn_scheduler", "Scheduler", "mdi-clock-fast", "/scheduler-demo", [], displayer.BSstyle.INFO
    ), 0)
    
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btn_settings", "Settings", "mdi-cog", "/settings/", [], displayer.BSstyle.SECONDARY
    ), 1)
    
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btn_logs", "Log Viewer", "mdi-file-document-multiple", "/logging/", [], displayer.BSstyle.DARK
    ), 2)
    
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
