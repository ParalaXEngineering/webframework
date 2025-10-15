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
    
    return render_template("base_content.j2", content=disp.display())

@demo_bp.route('/threading-demo', methods=['GET', 'POST'])
@require_login
def threading_demo():
    """Threading demo with clear examples and code."""
    from demo_support.demo_threaded_complete import DemoThreadedAction
    from src.modules.threaded import threaded_manager
    
    disp = displayer.Displayer()
    disp.add_module(DemoThreadedAction)
    disp.set_title("Threading System Demo")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Threading Demo", "demo.threading_demo", [])
    
    # Handle POST requests (button clicks)
    message = None
    if request.method == 'POST':
        data_in = utilities.util_post_to_json(request.form.to_dict())
        
        if DemoThreadedAction.m_default_name in data_in:
            module_data = data_in[DemoThreadedAction.m_default_name]
            
            if 'btn_complete' in module_data:
                thread = DemoThreadedAction("complete")
                thread.start()
                message = ("✓ Started Complete Demo Thread", displayer.BSstyle.SUCCESS)
            elif 'btn_console' in module_data:
                thread = DemoThreadedAction("console")
                thread.start()
                message = ("✓ Started Console Demo Thread", displayer.BSstyle.SUCCESS)
            elif 'btn_logging' in module_data:
                thread = DemoThreadedAction("logging")
                thread.start()
                message = ("✓ Started Logging Demo Thread", displayer.BSstyle.SUCCESS)
            elif 'btn_process' in module_data:
                thread = DemoThreadedAction("process")
                thread.start()
                message = ("✓ Started Process Demo Thread", displayer.BSstyle.SUCCESS)
            elif 'btn_stop' in module_data:
                count = threaded_manager.thread_manager_obj.get_thread_count()
                threaded_manager.thread_manager_obj.kill_all_threads()
                message = (f"✓ Stopped {count} threads", displayer.BSstyle.WARNING)
    
    # Show message if any
    if message:
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [12]
        ))
        disp.add_display_item(displayer.DisplayerItemAlert(message[0], message[1]), 0)
    
    # Overview
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "<strong>Threading System Overview</strong><br>"
        "The framework's threading system provides background task execution with real-time monitoring, "
        "progress tracking, console output capture, and process management. "
        "Visit the <a href='/threads/' class='alert-link'>Threads Monitor</a> to see threads in action!",
        displayer.BSstyle.INFO
    ), 0)
    
    # Thread statistics
    stats = threaded_manager.thread_manager_obj.get_thread_stats()
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 3, 3, 3],
        subtitle="Current Status"
    ))
    
    disp.add_display_item(displayer.DisplayerItemText(
        f"<strong>Total Threads</strong><br><h3>{stats['total']}</h3>"
    ), 0)
    disp.add_display_item(displayer.DisplayerItemText(
        f"<strong>Running</strong><br><h3>{stats['running']}</h3>"
    ), 1)
    disp.add_display_item(displayer.DisplayerItemText(
        f"<strong>With Process</strong><br><h3>{stats['with_process']}</h3>"
    ), 2)
    disp.add_display_item(displayer.DisplayerItemText(
        f"<strong>With Errors</strong><br><h3>{stats['with_error']}</h3>"
    ), 3)
    
    # Quick Start
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Quick Start - Basic Thread"
    ))
    disp.add_display_item(displayer.DisplayerItemText(
        "<p>Create a thread by inheriting from <code>Threaded_action</code>:</p>"
    ), 0)
    
    code_basic = '''from src.modules.threaded.threaded_action import Threaded_action
import time

class MyThread(Threaded_action):
    """A simple background thread."""
    
    m_default_name = "MyThread"  # Unique identifier
    
    def __init__(self):
        super().__init__()
        self.m_name = self.m_default_name
    
    def run(self):
        """Main thread execution - runs in background."""
        self.m_logger.info("Thread started!")
        
        for i in range(5):
            # Update progress (0-100)
            self.m_running_state = (i + 1) * 20
            self.m_logger.info(f"Step {i+1}/5")
            time.sleep(1)
        
        self.m_logger.info("Thread completed!")
        self.m_running = False  # Mark as finished

# Start the thread
thread = MyThread()
thread.start()'''
    
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_basic_thread",
        code=code_basic,
        language="python",
        show_line_numbers=True
    ), 0)
    
    # Try It Section
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Try It - Demo Threads"
    ))
    disp.add_display_item(displayer.DisplayerItemText(
        "<p>Click a button to start a demo thread showcasing different features:</p>"
    ), 0)
    
    # Demo buttons
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [6, 6]
    ))
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_complete", "🤖 Complete Demo",
        tooltip="Shows all features: progress, console, logging, and process execution"
    ), 0)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_console", "📋 Console Demo",
        tooltip="Demonstrates console output capture"
    ), 0)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_logging", "📝 Logging Demo",
        tooltip="Shows structured logging integration"
    ), 1)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_process", "⚙️ Process Demo",
        tooltip="Demonstrates subprocess execution with output capture"
    ), 1)
    
    # Control buttons
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [6, 6]
    ))
    
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        "btn_monitor", "📊 Monitor Threads →", "monitor-eye",
        "/threads/", [], displayer.BSstyle.SECONDARY
    ), 0)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_stop", "🛑 Stop All Threads",
        color=displayer.BSstyle.WARNING
    ), 1)
    
    # Advanced Features
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Advanced Features"
    ))
    
    code_advanced = '''# Console Output Capture
self.m_process_results.append("Custom console output")

# Run External Process
self.run_process_command(
    "python script.py",
    cwd="/path/to/dir"
)

# Access captured stdout/stderr
stdout = self.m_process_stdout
stderr = self.m_process_stderr

# Background Mode (no monitoring)
self.m_background = True

# Error Handling
try:
    # Your code
    pass
except Exception as e:
    self.m_logger.error(f"Error: {e}")
    self.m_running = False'''
    
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_advanced_thread",
        code=code_advanced,
        language="python",
        show_line_numbers=True
    ), 0)
    
    # Key Properties
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Key Properties & Methods"
    ))
    
    table_id = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE,
        columns=["Property/Method", "Type", "Description"]
    ))
    
    properties = [
        ("m_running", "bool", "True while thread is running"),
        ("m_running_state", "int", "Progress percentage (0-100), or -1 for indeterminate"),
        ("m_process_results", "list", "Console output lines"),
        ("m_logger", "Logger", "Logger instance for structured logging"),
        ("m_background", "bool", "Set True to hide from monitoring UI"),
        ("run()", "method", "Main execution method (override this)"),
        ("start()", "method", "Start the thread"),
        ("run_process_command()", "method", "Execute external process with output capture"),
    ]
    
    for line, (prop, ptype, desc) in enumerate(properties):
        disp.add_display_item(displayer.DisplayerItemText(f"<code>{prop}</code>"), 
                             column=0, line=line, layout_id=table_id)
        disp.add_display_item(displayer.DisplayerItemBadge(ptype, displayer.BSstyle.INFO), 
                             column=1, line=line, layout_id=table_id)
        disp.add_display_item(displayer.DisplayerItemText(desc), 
                             column=2, line=line, layout_id=table_id)
    
    return render_template("base_content.j2", content=disp.display(), target="demo.threading_demo")


@demo_bp.route('/scheduler-demo', methods=['GET', 'POST'])
@require_login
def scheduler_demo():
    """Demonstrate scheduler functionality with clear examples and code."""
    from demo_support.demo_scheduler_action import DemoSchedulerAction
    from src.modules.threaded import threaded_manager
    from src.modules.displayer import ResourceRegistry
    
    # Require jQuery for SocketIO functionality
    ResourceRegistry.require('jquery')
    
    # Handle form submission
    message = None
    if request.method == 'POST':
        data_in = utilities.util_post_to_json(request.form.to_dict())
        
        if DemoSchedulerAction.m_default_name in data_in:
            action_data = data_in[DemoSchedulerAction.m_default_name]
            
            # Check if an action is already running
            thread = threaded_manager.thread_manager_obj.get_thread(
                DemoSchedulerAction.m_default_name
            )
            
            if not thread:
                # Start new action based on button pressed
                demo_action = DemoSchedulerAction()
                
                if "simple_demo" in action_data:
                    demo_action.set_demo_type("simple")
                    demo_action.start()
                    message = ("✓ Started Simple Demo", displayer.BSstyle.SUCCESS)
                elif "complex_demo" in action_data:
                    demo_action.set_demo_type("complex")
                    demo_action.start()
                    message = ("✓ Started Complex Demo", displayer.BSstyle.SUCCESS)
                elif "error_demo" in action_data:
                    demo_action.set_demo_type("error")
                    demo_action.start()
                    message = ("✓ Started Error Demo", displayer.BSstyle.SUCCESS)
                elif "multi_step_demo" in action_data:
                    demo_action.set_demo_type("multi_step")
                    demo_action.start()
                    message = ("✓ Started Multi-Step Demo", displayer.BSstyle.SUCCESS)
                elif "all_features_demo" in action_data:
                    demo_action.set_demo_type("all_features")
                    demo_action.start()
                    message = ("✓ Started All Features Demo", displayer.BSstyle.SUCCESS)
            else:
                message = ("⚠ A demo action is already running", displayer.BSstyle.WARNING)
    
    disp = displayer.Displayer()
    disp.add_module(DemoSchedulerAction)
    disp.set_title("Scheduler & Action System Demo")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Scheduler", "demo.scheduler_demo", [])
    
    # Show message if any
    if message:
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [12]
        ))
        disp.add_display_item(displayer.DisplayerItemAlert(message[0], message[1]), 0)
    
    # Overview
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "<strong>Scheduler & Action System</strong><br>"
        "The scheduler system enables actions to communicate with the UI in real-time using SocketIO. "
        "Update progress bars, show popups, reload content, and control buttons - all from background threads!",
        displayer.BSstyle.INFO
    ), 0)
    
    # Quick Start
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Quick Start - Basic Action"
    ))
    disp.add_display_item(displayer.DisplayerItemText(
        "<p>Create an action by inheriting from <code>Action</code> and add it to a displayer:</p>"
    ), 0)
    
    code_basic = '''from src.modules.action import Action
from src.modules import displayer
import time

class MyAction(Action):
    """A simple scheduler action."""
    
    m_default_name = "MyAction"  # Unique identifier
    
    def __init__(self):
        super().__init__()
        self.m_name = self.m_default_name
    
    def run(self):
        """Main execution - runs when action is triggered."""
        # Update progress (0-100)
        for i in range(5):
            progress = (i + 1) * 20
            self.emit_status(
                category="progress",
                string=f"Step {i+1}/5",
                status=progress,
                supplement=f"{progress}%"
            )
            time.sleep(1)
        
        # Show completion popup
        self.emit_popup("success", "Task completed!")
        self.m_running = False

# Add to displayer
disp = displayer.Displayer()
disp.add_module(MyAction)  # Automatically creates UI and hooks up events'''
    
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_basic_action",
        code=code_basic,
        language="python",
        show_line_numbers=True
    ), 0)
    
    # Key Methods
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Real-Time UI Control Methods"
    ))
    
    table_id = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE,
        columns=["Method", "Purpose", "Example"]
    ))
    
    methods = [
        ("emit_status()", "Update progress bars and status text", "emit_status('progress', 'Loading', 50, '50%')"),
        ("emit_popup()", "Show toast notifications", "emit_popup('success', 'Task done!')"),
        ("emit_reload()", "Update page content dynamically", "emit_reload({'#div_id': '<p>New content</p>'})"),
        ("disable_button()", "Disable UI buttons", "disable_button('btn_start')"),
        ("enable_button()", "Re-enable UI buttons", "enable_button('btn_start')"),
    ]
    
    for line, (method, purpose, example) in enumerate(methods):
        disp.add_display_item(displayer.DisplayerItemText(f"<code>{method}</code>"), 
                             column=0, line=line, layout_id=table_id)
        disp.add_display_item(displayer.DisplayerItemText(purpose), 
                             column=1, line=line, layout_id=table_id)
        disp.add_display_item(displayer.DisplayerItemText(f"<code>{example}</code>"), 
                             column=2, line=line, layout_id=table_id)
    
    # Try It Section
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Try It - Demo Actions"
    ))
    disp.add_display_item(displayer.DisplayerItemText(
        "<p>Click buttons below to see different scheduler features in action:</p>"
    ), 0)
    
    # Status display (updated by SocketIO)
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(
        displayer.DisplayerItemAlert("No action running", displayer.BSstyle.NONE),
        0,
        id="scheduler_demo_status"
    )
    
    # Dynamic content area (updated by SocketIO)
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(
        displayer.DisplayerItemPlaceholder(
            "scheduler_demo_dynamic_content",
            '<div class="alert alert-secondary">Dynamic content area - will update when action runs</div>'
        ),
        0
    )
    
    # Demo buttons in a clean layout
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    
    demos = [
        ("simple_demo", "1. Single Progress", "Updates one progress bar"),
        ("multi_step_demo", "2. Parallel Progress", "Multiple concurrent progress bars"),
        ("error_demo", "3. Popup Notifications", "Success, warning, error, and info popups"),
        ("complex_demo", "4. Button Control", "Disable/enable buttons dynamically"),
        ("all_features_demo", "5. Dynamic Content", "Real-time page content updates"),
    ]
    
    for btn_id, title, description in demos:
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [9, 3]
        ))
        disp.add_display_item(
            displayer.DisplayerItemText(f"<strong>{title}</strong> - {description}"),
            0
        )
        disp.add_display_item(
            displayer.DisplayerItemButton(btn_id, "Run"),
            1,
            id=f"demo_action_btn_{btn_id}"
        )
    
    # Code Examples
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Code Examples"
    ))
    
    code_examples = '''# Progress Updates
self.emit_status(
    category="progress",      # Category identifier
    string="Processing...",   # Status text
    status=75,                # Progress value (0-100)
    supplement="75%",         # Additional info
    status_id="task_1"        # Optional: specific progress bar ID
)

# Popup Notifications
self.emit_popup("success", "Operation completed successfully!")
self.emit_popup("error", "Something went wrong!")
self.emit_popup("warning", "Please review settings")
self.emit_popup("info", "Processing started")

# Dynamic Content Updates
self.emit_reload({
    "#div_results": "<div>New results here</div>",
    "#status_text": "<span>Updated status</span>"
})

# Button Control
self.disable_button("btn_start")  # Prevent clicks during processing
# ... do work ...
self.enable_button("btn_start")   # Re-enable when done

# Multiple Progress Bars
self.emit_status("progress", "Task 1", 50, "50%", status_id="task1")
self.emit_status("progress", "Task 2", 75, "75%", status_id="task2")
self.emit_status("progress", "Task 3", 100, "Done", status_id="task3")'''
    
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_examples",
        code=code_examples,
        language="python",
        show_line_numbers=True
    ), 0)
    
    # Advanced: Dynamic Content Placeholder
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Advanced - Dynamic Content"
    ))
    disp.add_display_item(displayer.DisplayerItemText(
        "<p>Use <code>DisplayerItemDynamicContent</code> for content that updates in real-time:</p>"
    ), 0)
    
    code_dynamic = '''# In your page route:
disp.add_display_item(
    displayer.DisplayerItemDynamicContent(
        id="live_updates",
        initial_content='<div class="alert alert-secondary">Waiting...</div>',
        card=True  # Optional: wrap in card
    ),
    0
)

# In your action:
def run(self):
    # Update the content area
    new_html = '<div class="alert alert-success">Data loaded!</div>'
    self.emit_reload({"#live_updates": new_html})'''
    
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_dynamic_content",
        code=code_dynamic,
        language="python",
        show_line_numbers=True
    ), 0)
    
    return render_template("base_content.j2", content=disp.display(), target="demo.scheduler_demo")


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
