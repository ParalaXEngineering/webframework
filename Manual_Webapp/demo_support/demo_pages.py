"""
Demo Pages Blueprint

All the demo routes for showcasing displayer components.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session
from src.modules import displayer, utilities
from src.modules.auth import require_login

# Import website-specific i18n messages (includes framework messages too)
from website.i18n.messages import (
    TEXT_SIMPLE_FORM_DEMO, TEXT_SIMPLE_FORM_EXAMPLE,
    TEXT_THREADING_DEMO, TEXT_SCHEDULER_DEMO, TEXT_WORKFLOW_DEMO
)

# Create blueprint for demo routes
demo_bp = Blueprint('demo', __name__)

@demo_bp.route('/simple-form-demo', methods=['GET', 'POST']) 
@require_login()
def simple_form_demo():
    """Simple form demo - basic text input and display."""
    disp = displayer.Displayer()
    disp.add_generic(TEXT_SIMPLE_FORM_DEMO)
    disp.set_title(TEXT_SIMPLE_FORM_EXAMPLE)
    
    disp.add_breadcrumb("Simple Form", "demo.simple_form_demo", [])
    
    # Handle POST - display submitted data
    if request.method == 'POST':
        # Parse form data using util_post_to_json
        data_in = utilities.util_post_to_json(request.form.to_dict())
        
        # Extract data from the module
        if "Simple Form Demo" in data_in:
            form_data = data_in["Simple Form Demo"]
            user_text = form_data.get("input_text", "")
            
            # Show success message with submitted text
            disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
            disp.add_display_item(displayer.DisplayerItemAlert(
                f"<strong>Form Submitted!</strong><br>You entered: <em>{user_text}</em>",
                displayer.BSstyle.SUCCESS
            ), 0)
    
    # Show form
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemText(
        "<p>This is a simple form example. Enter some text and click submit.</p>"
    ), 0)
    
    disp.add_display_item(displayer.DisplayerItemInputString(
        "input_text",
        "Enter Text",
        value=""
    ), 0)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_submit",
        "Submit",
        color=displayer.BSstyle.PRIMARY
    ), 0)
    
    return render_template("base_content.j2", content=disp.display(), target="demo.simple_form_demo")


@demo_bp.route('/threading-demo', methods=['GET', 'POST'])
@require_login()
def threading_demo():
    """Threading demo with table of examples and code."""
    from demo_support.demo_threaded_complete import DemoThreadedAction
    from src.modules.threaded import threaded_manager
    
    disp = displayer.Displayer()
    disp.add_module(DemoThreadedAction)
    disp.set_title(TEXT_THREADING_DEMO)
    
    disp.add_breadcrumb("Threading Demo", "demo.threading_demo", [])
    
    # Handle POST requests
    message = None
    if request.method == 'POST':
        data_in = utilities.util_post_to_json(request.form.to_dict())
        
        if DemoThreadedAction.m_default_name in data_in:
            module_data = data_in[DemoThreadedAction.m_default_name]
            
            if 'btn_console' in module_data:
                thread = DemoThreadedAction("console")
                thread.start()
                message = ("✓ Console Demo Started", displayer.BSstyle.SUCCESS)
            elif 'btn_logging' in module_data:
                thread = DemoThreadedAction("logging")
                thread.start()
                message = ("✓ Logging Demo Started", displayer.BSstyle.SUCCESS)
            elif 'btn_process' in module_data:
                thread = DemoThreadedAction("process")
                thread.start()
                message = ("✓ Process Demo Started", displayer.BSstyle.SUCCESS)
            elif 'btn_stop' in module_data:
                if threaded_manager.thread_manager_obj:
                    count = threaded_manager.thread_manager_obj.get_thread_count()
                    threaded_manager.thread_manager_obj.kill_all_threads()
                    message = (f"✓ Stopped {count} threads", displayer.BSstyle.WARNING)
                else:
                    message = ("Thread manager not available", displayer.BSstyle.ERROR)
    
    if message:
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        disp.add_display_item(displayer.DisplayerItemAlert(message[0], message[1]), 0)
    
    # Overview
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "<strong>Threading System</strong><br>"
        "Background task execution with real-time monitoring. "
        "Visit <a href='/threads/' class='alert-link'>Threads Monitor</a> to see running threads.",
        displayer.BSstyle.INFO
    ), 0)
    
    # Thread statistics
    if threaded_manager.thread_manager_obj:
        stats = threaded_manager.thread_manager_obj.get_thread_stats()
    else:
        stats = {'total': 0, 'running': 0, 'sleeping': 0, 'error': 0}
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 3, 3, 3],
        subtitle="Current Status"
    ))
    disp.add_display_item(displayer.DisplayerItemText(
        f"<strong>Total</strong><br><h3>{stats['total']}</h3>"), 0)
    disp.add_display_item(displayer.DisplayerItemText(
        f"<strong>Running</strong><br><h3>{stats['running']}</h3>"), 1)
    disp.add_display_item(displayer.DisplayerItemText(
        f"<strong>With Process</strong><br><h3>{stats['with_process']}</h3>"), 2)
    disp.add_display_item(displayer.DisplayerItemText(
        f"<strong>Errors</strong><br><h3>{stats['with_error']}</h3>"), 3)
    
    # Demo table with examples
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Try Demo Threads"
    ))
    
    table_id = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE,
        columns=["Demo", "Action", "Code Example"]
    ))
    
    # Console Demo
    disp.add_display_item(displayer.DisplayerItemText(
        "<strong>Console Output</strong><br>Capture custom console messages"
    ), column=0, line=0, layout_id=table_id)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_console", "", icon="console"
    ), column=1, line=0, layout_id=table_id)
    
    code_console = '''def run(self):
    self.m_process_results.append("Custom console output")
    self.m_process_results.append("Another line")
    self.m_running = False'''
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_console",
        code=code_console,
        language="python",
        show_line_numbers=False
    ), column=2, line=0, layout_id=table_id)
    
    # Logging Demo
    disp.add_display_item(displayer.DisplayerItemText(
        "<strong>Structured Logging</strong><br>Use logger for tracked messages"
    ), column=0, line=1, layout_id=table_id)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_logging", "", icon="text-box"
    ), column=1, line=1, layout_id=table_id)
    
    code_logging = '''def run(self):
    self.m_logger.info("Thread started")
    self.m_logger.warning("A warning")
    self.m_logger.error("An error")
    self.m_running = False'''
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_logging",
        code=code_logging,
        language="python",
        show_line_numbers=False
    ), column=2, line=1, layout_id=table_id)
    
    # Process Demo
    disp.add_display_item(displayer.DisplayerItemText(
        "<strong>External Process</strong><br>Run subprocess with output capture"
    ), column=0, line=2, layout_id=table_id)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_process", "", icon="cog"
    ), column=1, line=2, layout_id=table_id)
    
    code_process = '''def run(self):
    self.run_process_command(
        "python --version",
        cwd=os.getcwd()
    )
    # Access output
    print(self.m_process_stdout)
    self.m_running = False'''
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_process",
        code=code_process,
        language="python",
        show_line_numbers=False
    ), column=2, line=2, layout_id=table_id)
    
    # Control buttons
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [6, 6]
    ))
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_monitor", "Monitor Threads", icon="monitor-eye",
        link="/threads/", color=displayer.BSstyle.SECONDARY
    ), 0)
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_stop", "Stop All Threads", icon="stop-circle", color=displayer.BSstyle.WARNING
    ), 1)
    
    # API Reference
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Key Properties & Methods"
    ))
    
    api_table = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE,
        columns=["Property/Method", "Type", "Description"]
    ))
    
    properties = [
        ("m_running", "bool", "True while thread is running"),
        ("m_running_state", "int", "Progress (0-100), or -1 for indeterminate"),
        ("m_process_results", "list", "Console output lines"),
        ("m_logger", "Logger", "Logger for structured logging"),
        ("m_background", "bool", "Hide from monitoring UI"),
        ("run()", "method", "Main execution (override this)"),
        ("run_process_command()", "method", "Execute subprocess"),
    ]
    
    for line, (prop, ptype, desc) in enumerate(properties):
        disp.add_display_item(displayer.DisplayerItemText(f"<code>{prop}</code>"), 
                             column=0, line=line, layout_id=api_table)
        disp.add_display_item(displayer.DisplayerItemBadge(ptype, displayer.BSstyle.INFO), 
                             column=1, line=line, layout_id=api_table)
        disp.add_display_item(displayer.DisplayerItemText(desc), 
                             column=2, line=line, layout_id=api_table)
    
    return render_template("base_content.j2", content=disp.display(), target="demo.threading_demo")


@demo_bp.route('/scheduler-demo', methods=['GET', 'POST'])
@require_login()
def scheduler_demo():
    """Scheduler/Action system demo with real-time UI updates."""
    from demo_support.demo_scheduler_action import DemoSchedulerAction
    from src.modules.threaded import threaded_manager
    from src.modules.displayer import ResourceRegistry
    
    # Require jQuery for SocketIO
    ResourceRegistry.require('jquery')
    
    # Handle POST
    message = None
    if request.method == 'POST':
        data_in = utilities.util_post_to_json(request.form.to_dict())
        
        if DemoSchedulerAction.m_default_name in data_in:
            action_data = data_in[DemoSchedulerAction.m_default_name]
            thread = threaded_manager.thread_manager_obj.get_thread(DemoSchedulerAction.m_default_name) if threaded_manager.thread_manager_obj else None
            
            if not thread:
                demo_action = DemoSchedulerAction()
                
                if "btn_single" in action_data:
                    demo_action.set_demo_type("single_progress")
                    demo_action.start()
                    message = ("✓ Single Progress Started", displayer.BSstyle.SUCCESS)
                elif "btn_parallel" in action_data:
                    demo_action.set_demo_type("parallel_progress")
                    demo_action.start()
                    message = ("✓ Parallel Progress Started", displayer.BSstyle.SUCCESS)
                elif "btn_popup" in action_data:
                    demo_action.set_demo_type("popup_demo")
                    demo_action.start()
                    message = ("✓ Popup Demo Started", displayer.BSstyle.SUCCESS)
                elif "btn_alert" in action_data:
                    demo_action.set_demo_type("status_codes")
                    demo_action.start()
                    message = ("✓ Status Codes Demo Started", displayer.BSstyle.SUCCESS)
                elif "btn_button_control" in action_data:
                    demo_action.set_demo_type("button_control")
                    demo_action.start()
                    message = ("✓ Button Control Started", displayer.BSstyle.SUCCESS)
                elif "btn_dynamic" in action_data:
                    demo_action.set_demo_type("dynamic_content")
                    demo_action.start()
                    message = ("✓ Dynamic Content Started", displayer.BSstyle.SUCCESS)
                elif "btn_all_features" in action_data:
                    demo_action.set_demo_type("all_features")
                    demo_action.start()
                    message = ("✓ All Features Demo Started", displayer.BSstyle.SUCCESS)
            else:
                message = ("⚠ Demo already running", displayer.BSstyle.WARNING)
    
    disp = displayer.Displayer()
    disp.add_module(DemoSchedulerAction)
    disp.set_title("Scheduler & Action System Demo")
    
    disp.add_breadcrumb("Scheduler", "demo.scheduler_demo", [])
    
    if message:
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        disp.add_display_item(displayer.DisplayerItemAlert(message[0], message[1]), 0)
    
    # Overview
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "<strong>Scheduler & Action System</strong><br>"
        "Real-time UI updates via SocketIO. Update progress, show popups, reload content, control buttons!",
        displayer.BSstyle.INFO
    ), 0)
    
    # Demo table
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Real-Time UI Demos"
    ))
    
    table_id = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE,
        columns=["Demo", "Action", "Code Example"]
    ))
        
    # 1. Single Progress
    disp.add_display_item(displayer.DisplayerItemText(
        "<strong>Single Progress</strong><br>Simple progress bar update"
    ), column=0, line=1, layout_id=table_id)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_single", "", icon="progress-check"
    ), column=1, line=1, layout_id=table_id)
    
    code_single = '''for i in range(10):
    self.emit_status(
        category="progress",
        string=f"Processing {i+1}/10",
        status=(i+1) * 10,
        supplement=f"{(i+1)*10}%"
    )
    time.sleep(0.5)'''
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_single", code=code_single, language="python", show_line_numbers=False
    ), column=2, line=1, layout_id=table_id)
    
    # 2. Parallel Progress
    disp.add_display_item(displayer.DisplayerItemText(
        "<strong>Parallel Progress</strong><br>Multiple concurrent progress bars"
    ), column=0, line=2, layout_id=table_id)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_parallel", "", icon="progress-star"
    ), column=1, line=2, layout_id=table_id)
    
    code_parallel = '''# Update multiple progress bars
self.emit_status("progress", "Task 1", 33, 
    "33%", status_id="task1")
self.emit_status("progress", "Task 2", 67, 
    "67%", status_id="task2")
self.emit_status("progress", "Task 3", 100, 
    "Done", status_id="task3")'''
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_parallel", code=code_parallel, language="python", show_line_numbers=False
    ), column=2, line=2, layout_id=table_id)
    
    # 3. Popup Demo
    disp.add_display_item(displayer.DisplayerItemText(
        "<strong>Popup Notifications</strong><br>Toast messages: success, error, warning, info"
    ), column=0, line=3, layout_id=table_id)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_popup", "", icon="bell-ring"
    ), column=1, line=3, layout_id=table_id)
    
    code_popup = '''self.emit_popup("info", "Starting process")
time.sleep(1)
self.emit_popup("success", "Task completed!")
time.sleep(1)
self.emit_popup("warning", "Check settings")
time.sleep(1)
self.emit_popup("error", "Error occurred")'''
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_popup", code=code_popup, language="python", show_line_numbers=False
    ), column=2, line=3, layout_id=table_id)
    
    # 4. Special Status Codes
    disp.add_display_item(displayer.DisplayerItemText(
        "<strong>Special Status Codes</strong><br>Status codes >100 show special icons in action progress"
    ), column=0, line=4, layout_id=table_id)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_alert", "", icon="alert-circle"
    ), column=1, line=4, layout_id=table_id)
    
    code_alert = '''# Special status codes:
# 100 = Done (green check)
# 101 = Failed (red X)
# 102 = Readme (info icon)
# 103 = In progress (spinner)
# 104 = (empty)
# 105 = Not needed (minus icon)
# 106 = Pending (hourglass)
self.emit_status("progress", 
    "Task description", 103, 
    "In progress...")'''
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_alert", code=code_alert, language="python", show_line_numbers=False
    ), column=2, line=4, layout_id=table_id)
    
    # 5. Button Control
    disp.add_display_item(displayer.DisplayerItemText(
        "<strong>Button Control</strong><br>Disable/enable buttons dynamically"
    ), column=0, line=5, layout_id=table_id)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_button_control", "", icon="toggle-switch"
    ), column=1, line=5, layout_id=table_id)
    
    code_button = '''# Disable button during processing
self.disable_button("btn_button_control")
for i in range(5):
    self.emit_status("progress", 
        f"Working {i+1}/5", (i+1)*20)
    time.sleep(0.5)
# Re-enable when done
self.enable_button("btn_button_control")'''
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_button", code=code_button, language="python", show_line_numbers=False
    ), column=2, line=5, layout_id=table_id)
    
    # 6. Dynamic Content
    disp.add_display_item(displayer.DisplayerItemText(
        "<strong>Dynamic Content</strong><br>Update page content in real-time"
    ), column=0, line=6, layout_id=table_id)

    # Row 0: Dynamic content area (spans all columns)
    disp.add_display_item(displayer.DisplayerItemPlaceholder(
        "scheduler_demo_dynamic_content",
        '<div class="alert alert-secondary"><i class="mdi mdi-information-outline"></i> <strong>Dynamic Content Area</strong> - Will update in real-time during demos (no page refresh needed!)</div>'
    ), column=0, line=6, layout_id=table_id)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_dynamic", "", icon="refresh"
    ), column=1, line=6, layout_id=table_id)
    
    code_dynamic = '''for i in range(5):
    html = f\'\'\'<div class="alert 
        alert-info">Update {i+1}/5 
        - {time.strftime("%H:%M:%S")}
        </div>\'\'\'
    self.emit_reload({
        "#scheduler_demo_dynamic_content": html
    })
    time.sleep(1)'''
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_dynamic", code=code_dynamic, language="python", show_line_numbers=False
    ), column=2, line=6, layout_id=table_id)
    
    # 7. All Features
    disp.add_display_item(displayer.DisplayerItemText(
        "<strong>All Features Combined</strong><br>Progress + popup + button control + dynamic content"
    ), column=0, line=7, layout_id=table_id)
    
    disp.add_display_item(displayer.DisplayerItemButton(
        "btn_all_features", "", icon="star-circle", color=displayer.BSstyle.PRIMARY
    ), column=1, line=7, layout_id=table_id)
    
    code_all = '''# Comprehensive example
self.disable_button("btn_all_features")
self.emit_popup("info", "Starting...")

for i in range(5):
    # Update progress
    self.emit_status("progress", 
        f"Step {i+1}/5", (i+1)*20, 
        f"{(i+1)*20}%")
    
    # Update content
    html = f"<div>Processing step {i+1}</div>"
    self.emit_reload({"#scheduler_demo_dynamic_content": html})
    
    time.sleep(1)

self.emit_popup("success", "Complete!")
self.enable_button("btn_all_features")'''
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_all", code=code_all, language="python", show_line_numbers=False
    ), column=2, line=7, layout_id=table_id)
    
    # API Reference
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Key Methods"
    ))
    
    api_table = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE,
        columns=["Method", "Parameters", "Description"]
    ))
    
    methods = [
        ("emit_status()", "category, string, status, supplement, status_id", "Update progress bars"),
        ("emit_popup()", "type, message", "Show toast notification"),
        ("emit_reload()", "dict of {selector: html}", "Update page content"),
        ("disable_button()", "button_id", "Disable UI button"),
        ("enable_button()", "button_id", "Enable UI button"),
    ]
    
    # Add special status codes info
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Special Status Codes (>100)"
    ))
    
    status_codes_table = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE,
        columns=["Code", "Icon", "Meaning"]
    ))
    
    status_codes = [
        ("100", '<i class="mdi mdi-check text-success mx-1"></i>', "Done / Success"),
        ("101", '<i class="mdi mdi-close text-danger mx-1"></i>', "Failed / Error"),
        ("102", '<i class="mdi mdi-information-outline text-info mx-1"></i>', "Information / Readme"),
        ("103", '<div class="spinner-border spinner-border-sm text-primary" role="status"></div>', "In Progress"),
        ("104", "", "Hidden status"),
        ("105", '<i class="mdi mdi-minus-circle-outline text-secondary mx-1"></i>', "Not needed / Skipped"),
        ("106", '<i class="mdi mdi-timer-sand text-primary mx-1"></i>', "Pending / Waiting"),
    ]
    
    for line, (code, icon, meaning) in enumerate(status_codes):
        disp.add_display_item(displayer.DisplayerItemText(f"<code>{code}</code>"), 
                             column=0, line=line, layout_id=status_codes_table)
        disp.add_display_item(displayer.DisplayerItemText(icon), 
                             column=1, line=line, layout_id=status_codes_table)
        disp.add_display_item(displayer.DisplayerItemText(meaning), 
                             column=2, line=line, layout_id=status_codes_table)
    
    for line, (method, params, desc) in enumerate(methods):
        disp.add_display_item(displayer.DisplayerItemText(f"<code>{method}</code>"), 
                             column=0, line=line, layout_id=api_table)
        disp.add_display_item(displayer.DisplayerItemText(f"<small>{params}</small>"), 
                             column=1, line=line, layout_id=api_table)
        disp.add_display_item(displayer.DisplayerItemText(desc), 
                             column=2, line=line, layout_id=api_table)
    
    return render_template("base_content.j2", content=disp.display(), target="demo.scheduler_demo")


# ============================================================================
# AUTHORIZATION DEMO - Redirect to new comprehensive demo
# ============================================================================

@demo_bp.route('/authorization')
def authorization_demo():
    """Redirect to the new comprehensive authorization showcase."""
    from flask import redirect
    return redirect(url_for('demo_auth.index'))


@demo_bp.route('/workflow-demo', methods=['GET', 'POST'])
@require_login()
def workflow_demo():
    """
    Workflow system demo - Product registration with batch operations.
    
    Demonstrates:
    - Multi-step forms with data persistence
    - Threaded actions with progress
    - Redo functionality for batch operations
    - Code examples alongside each step
    """
    from demo_support.demo_workflow_new import WorkflowDemo
    import pickle
    
    disp = displayer.Displayer()
    disp.set_title("Workflow System Demo")
    
    # Get or create workflow instance from session
    if 'workflow_demo_instance' in session and request.method == 'POST':
        try:
            workflow = pickle.loads(session['workflow_demo_instance'])
        except Exception:
            workflow = WorkflowDemo()
    else:
        workflow = WorkflowDemo()
    
    # Handle POST requests
    if request.method == 'POST':
        data_in = utilities.util_post_to_json(request.form.to_dict())
        # Redo is now handled automatically in workflow.prepare_workflow()
        workflow.prepare_workflow(data_in)
    else:
        workflow.prepare_workflow(None)
    
    # Generate display (this may start a NEW thread if action creates one)
    workflow.add_display(disp)
    
    # Save workflow to session
    # Store which step had a finished thread (for next POST request)
    if workflow.m_active_thread and not workflow.m_active_thread.is_running():
        workflow.m_workflow_data['_thread_finished_step'] = workflow.m_current_step_index
    
    # Clear thread reference before pickling (threads can't be pickled)
    active_thread = workflow.m_active_thread
    workflow.m_active_thread = None
    session['workflow_demo_instance'] = pickle.dumps(workflow)
    workflow.m_active_thread = active_thread  # Restore for current response
    
    return render_template("base_content.j2", content=disp.display(), target="demo.workflow_demo")

