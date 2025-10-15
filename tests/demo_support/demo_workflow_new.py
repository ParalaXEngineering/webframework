"""
Simplified Workflow Demo - Production Scanning Example

This demo shows:
- Basic form with code example
- Threaded action with progress tracking
- Redo functionality for batch operations
"""

import time
from src.modules.workflow import Workflow, WorkflowStep, StepActionType
from src.modules import displayer, scheduler
from src.modules.threaded import Threaded_action


class ScanProcessingAction(Threaded_action):
    """Simulates scanning and registering a product"""
    
    m_default_name = "Product Registration"
    
    def __init__(self, serial_number: str, batch_size: int = 1):
        super().__init__()
        self.serial_number = serial_number
        self.batch_size = batch_size
    
    def action(self):
        """Simulate scanning and registering products"""
        self.console_write(f"Starting registration for {self.batch_size} product(s)...")
        
        if self.m_scheduler:
            self.m_scheduler.emit_status(
                self.get_name(),
                f"Registering {self.batch_size} product(s)...",
                0,
                "Initializing scanner...",
                status_id="scan_progress"
            )
        
        time.sleep(1)
        
        for i in range(self.batch_size):
            if not self.m_running:
                break
            
            progress = int((i + 1) / self.batch_size * 100)
            self.m_running_state = progress
            
            msg = f"Registering product {i+1}/{self.batch_size}"
            self.console_write(msg)
            
            if self.m_scheduler:
                self.m_scheduler.emit_status(
                    self.get_name(),
                    msg,
                    progress,
                    f"Serial: {self.serial_number}-{i+1:03d} ({progress}%)",
                    status_id="scan_progress"
                )
            
            time.sleep(0.8)  # Simulate processing time
        
        self.console_write(f"✓ Registered {self.batch_size} product(s)!")
        self.m_running_state = 100


class SimplifiedDemoWorkflow(Workflow):
    """
    Simplified workflow demo - Product Registration System
    
    Simulates scanning products with serial numbers and registering them.
    Shows threaded actions and redo functionality.
    """
    
    m_default_name = "Product Registration"
    
    def __init__(self):
        super().__init__("Product Registration")
        self._setup_steps()
    
    def _setup_steps(self):
        """Define workflow steps"""
        
        # Step 1: Scan Product
        self.add_step(WorkflowStep(
            name="Scan Product",
            display_func=self._display_scan,
            action_func=self._action_scan,
            description="Scan product serial number"
        ))
        
        # Step 2: Process Registration (threaded)
        self.add_step(WorkflowStep(
            name="Register",
            display_func=self._display_process,
            action_func=self._action_process_threaded,
            action_type=StepActionType.THREADED,
            description="Processing registration..."
        ))
        
        # Step 3: Complete with Redo Option
        self.add_step(WorkflowStep(
            name="Complete",
            display_func=self._display_complete,
            description="Registration complete"
        ))
    
    # ===== Step 1: Scan Product =====
    
    def _display_scan(self, disp, workflow_data):
        """Display product scanning form with code example"""
        
        # Main form section
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
        )
        disp.add_display_item(
            displayer.DisplayerItemAlert(
                "<strong>📦 Product Registration System</strong><br>"
                "Scan or enter the product serial number to register it in the system.",
                displayer.BSstyle.INFO
            ),
            0
        )
        
        # Serial number input
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [6, 6])
        )
        disp.add_display_item(
            displayer.DisplayerItemText("<strong>Serial Number:</strong>"),
            0
        )
        serial = workflow_data.get("serial_number", "")
        disp.add_display_item(
            displayer.DisplayerItemInputString("serial_number", None, serial, focus=True),
            1
        )
        
        # Batch size input
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [6, 6])
        )
        disp.add_display_item(
            displayer.DisplayerItemText("<strong>Batch Size:</strong>"),
            0
        )
        batch = workflow_data.get("batch_size", "1")
        disp.add_display_item(
            displayer.DisplayerItemInputNumeric("batch_size", None, batch),
            1
        )
        
        # Code example
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12],
                                     subtitle="💡 Code Example")
        )
        
        code_example = '''# Step 1: Define display function
def display_scan(disp, workflow_data):
    """Show the form"""
    disp.add_master_layout(
        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
    )
    
    # Restore previous value if exists
    serial = workflow_data.get("serial_number", "")
    disp.add_display_item(
        displayer.DisplayerItemInputString("serial_number", None, serial),
        0
    )
    return disp

# Step 2: Add validation action (optional)
def validate_scan(workflow, form_data):
    """Validate before moving to next step"""
    serial = form_data.get("serial_number", "").strip()
    if not serial:
        scheduler.scheduler_obj.emit_popup(
            scheduler.logLevel.warning,
            "Please enter a serial number"
        )

# Step 3: Create workflow step
workflow.add_step(WorkflowStep(
    name="Scan Product",
    display_func=display_scan,
    action_func=validate_scan  # Optional validation
))'''
        
        disp.add_display_item(
            displayer.DisplayerItemCode(
                "scan_code",
                code_example,
                language="python",
                title="Creating a Form Step",
                show_line_numbers=True
            ),
            0
        )
        
        return disp
    
    def _action_scan(self, workflow, form_data):
        """Validate serial number"""
        serial = form_data.get("serial_number", "").strip()
        
        if not serial:
            if scheduler.scheduler_obj:
                scheduler.scheduler_obj.emit_popup(
                    scheduler.logLevel.warning,
                    "Please enter a serial number"
                )
        else:
            self.m_logger.info(f"Scanned serial: {serial}")
    
    # ===== Step 2: Process Registration =====
    
    def _display_process(self, disp, workflow_data):
        """Display processing status with thread module"""
        
        serial = workflow_data.get("serial_number", "Unknown")
        batch = workflow_data.get("batch_size", "1")
        
        # If there's an active thread, show it as a module
        if self.m_active_thread and self.m_active_thread.is_running():
            disp.add_master_layout(
                displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
            )
            disp.add_display_item(
                displayer.DisplayerItemAlert(
                    f"<strong>⏳ Processing Registration</strong><br>"
                    f"Serial: <code>{serial}</code> | Batch: {batch} unit(s)<br>"
                    f"<small>Please wait for processing to complete...</small>",
                    displayer.BSstyle.WARNING
                ),
                0
            )
            
            # Add the thread as a module to show progress
            disp.add_module(self.m_active_thread)
        else:
            # No active thread - show info about starting
            disp.add_master_layout(
                displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
            )
            disp.add_display_item(
                displayer.DisplayerItemAlert(
                    f"<strong>Ready to Process</strong><br>"
                    f"Serial: <code>{serial}</code> | Batch: {batch} unit(s)<br>"
                    f"<small>Click Next to start registration.</small>",
                    displayer.BSstyle.INFO
                ),
                0
            )
        
        # Code example for threaded action
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12],
                                     subtitle="💡 Code Example: Threaded Actions")
        )
        
        code_example = '''# Step 1: Create a Threaded_action class
from src.modules.threaded import Threaded_action
import time

class ScanProcessingAction(Threaded_action):
    m_default_name = "Product Registration"
    
    def __init__(self, serial_number: str, batch_size: int):
        super().__init__()
        self.serial_number = serial_number
        self.batch_size = batch_size
    
    def action(self):
        """Main thread action - override this method"""
        for i in range(self.batch_size):
            if not self.m_running:  # Check if cancelled
                break
            
            # Update progress percentage
            progress = int((i + 1) / self.batch_size * 100)
            self.m_running_state = progress
            
            # Emit status via scheduler (optional)
            if self.m_scheduler:
                self.m_scheduler.emit_status(
                    self.get_name(),
                    f"Processing {i+1}/{self.batch_size}",
                    progress,
                    f"{progress}%",
                    status_id="my_progress"
                )
            
            time.sleep(1)  # Simulate work

# Step 2: Create action function that returns thread
def start_processing(workflow, form_data):
    """Return a Threaded_action instance"""
    serial = workflow.m_workflow_data["serial_number"]
    batch = int(workflow.m_workflow_data.get("batch_size", 1))
    
    thread = ScanProcessingAction(serial, batch)
    return thread  # Workflow starts it automatically

# Step 3: Add step with THREADED action type
workflow.add_step(WorkflowStep(
    name="Register",
    display_func=display_process,
    action_func=start_processing,
    action_type=StepActionType.THREADED  # Important!
))'''
        
        disp.add_display_item(
            displayer.DisplayerItemCode(
                "thread_code",
                code_example,
                language="python",
                title="Creating Threaded Actions",
                show_line_numbers=True
            ),
            0
        )
        
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
        )
        disp.add_display_item(
            displayer.DisplayerItemAlert(
                "<strong>ℹ️ Key Points:</strong><ul>"
                "<li>Thread runs in background - UI stays responsive</li>"
                "<li>Override <code>action()</code> method with your logic</li>"
                "<li>Set <code>self.m_running_state</code> (0-100) to show progress</li>"
                "<li>Check <code>self.m_running</code> for cancellation</li>"
                "<li>Use <code>self.console_write()</code> to output to thread console</li>"
                "<li>Next button auto-disabled while thread runs</li>"
                "</ul>",
                displayer.BSstyle.INFO
            ),
            0
        )
        
        return disp
    
    def _action_process_threaded(self, workflow, form_data):
        """Start threaded processing"""
        serial = workflow.m_workflow_data.get("serial_number", "UNKNOWN")
        batch = int(workflow.m_workflow_data.get("batch_size", 1))
        
        thread = ScanProcessingAction(serial, batch)
        return thread  # Workflow will start it
    
    # ===== Step 3: Complete =====
    
    def _display_complete(self, disp, workflow_data):
        """Display completion with redo option"""
        
        serial = workflow_data.get("serial_number", "Unknown")
        batch = workflow_data.get("batch_size", "1")
        
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
        )
        disp.add_display_item(
            displayer.DisplayerItemAlert(
                f"<strong>✓ Registration Complete!</strong><br>"
                f"Successfully registered {batch} product(s) with serial: <code>{serial}</code>",
                displayer.BSstyle.SUCCESS
            ),
            0
        )
        
        # Show all registered data
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12],
                                     subtitle="📋 Registration Details")
        )
        
        details_html = '<div class="card"><div class="card-body">'
        details_html += f'<p><strong>Serial Number:</strong> {serial}</p>'
        details_html += f'<p><strong>Batch Size:</strong> {batch} unit(s)</p>'
        details_html += '<p><strong>Status:</strong> <span class="badge bg-success">Registered</span></p>'
        details_html += '</div></div>'
        
        disp.add_display_item(
            displayer.DisplayerItemText(details_html),
            0
        )
        
        # Redo section
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12],
                                     subtitle="🔄 Scan Another Product")
        )
        
        disp.add_display_item(
            displayer.DisplayerItemAlert(
                "<strong>Batch Operation Mode</strong><br>"
                "You can register another product with a different serial number. "
                "Enter the new serial below and click Redo to process it.",
                displayer.BSstyle.INFO
            ),
            0
        )
        
        # New serial input for redo
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [6, 6])
        )
        disp.add_display_item(
            displayer.DisplayerItemText("<strong>Next Serial Number:</strong>"),
            0
        )
        next_serial = workflow_data.get("next_serial", "")
        disp.add_display_item(
            displayer.DisplayerItemInputString("next_serial", None, next_serial, focus=True),
            1
        )
        
        # Batch size for redo
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [6, 6])
        )
        disp.add_display_item(
            displayer.DisplayerItemText("<strong>Batch Size:</strong>"),
            0
        )
        next_batch = workflow_data.get("next_batch", batch)
        disp.add_display_item(
            displayer.DisplayerItemInputNumeric("next_batch", None, next_batch),
            1
        )
        
        # Add redo button using the workflow's built-in method
        # This will jump back to step 1 (the Processing step) with the new data
        self.add_redo_button(disp, "🔄 Register Another Product", target_step_index=1)
        
        # Code example for redo
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12],
                                     subtitle="💡 Code Example: Redo Functionality")
        )
        
        code_example = '''# NEW: Using built-in redo functionality
# In your step's display function:
def display_complete(disp, workflow_data):
    # ... show completion info ...
    
    # Add input fields for new parameters
    disp.add_display_item(
        displayer.DisplayerItemInputString("next_serial", None, "")
    )
    
    # Add redo button (workflow method)
    # This creates a button that automatically handles redo logic
    self.add_redo_button(
        disp,
        button_text="Register Another",
        target_step_index=1  # Jump back to step 1 (Processing)
    )
    
    return disp

# That's it! The workflow handles:
# - Saving the new form data
# - Jumping back to the specified step
# - Clearing the active thread
# - Recomputing visible steps

# OLD WAY (manual in route):
@app.route('/workflow', methods=['GET', 'POST'])
def my_workflow():
    if request.method == 'POST':
        data_in = utilities.util_post_to_json(request.form.to_dict())
        workflow_data = data_in.get(workflow.m_name, {})
        
        # Manual redo handling (no longer needed)
        if "workflow_redo" in workflow_data:
            workflow.m_workflow_data["serial_number"] = workflow_data.get("next_serial", "")
            workflow.m_current_step_index = 1
    
    # Now it's automatic! Just call prepare_workflow
    workflow.prepare_workflow(data_in)'''
        workflow_data = data_in.get(workflow.m_name, {})
        if "workflow_redo" in workflow_data:
            # Update parameters from form
            workflow.m_workflow_data["serial_number"] = workflow_data.get("next_serial", "")
            workflow.m_workflow_data["batch_size"] = workflow_data.get("next_batch", "1")
            
            # Jump back to processing step (step index 1)
            workflow.m_current_step_index = 1
            workflow.prepare_workflow(None)  # Reset for display
        else:
            workflow.prepare_workflow(data_in)
    
    # ... render ...'''
        
        disp.add_display_item(
            displayer.DisplayerItemCode(
                "redo_code",
                code_example,
                language="python",
                title="Implementing Redo Button",
                show_line_numbers=True
            ),
            0
        )
        
        # Summary of all features
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12],
                                     subtitle="🎯 Workflow System Features")
        )
        
        features = '''<div class="row">
            <div class="col-md-6">
                <div class="card bg-light">
                    <div class="card-body">
                        <h6 class="card-title">✨ Core Features</h6>
                        <ul class="mb-0">
                            <li>Automatic state persistence</li>
                            <li>Breadcrumb navigation</li>
                            <li>Progress tracking</li>
                            <li>Go back to any step</li>
                            <li>Form validation</li>
                        </ul>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card bg-light">
                    <div class="card-body">
                        <h6 class="card-title">🚀 Advanced Features</h6>
                        <ul class="mb-0">
                            <li>Conditional steps</li>
                            <li>Skippable steps</li>
                            <li>Threaded actions</li>
                            <li>Custom buttons (redo, cancel, etc.)</li>
                            <li>Batch operations</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>'''
        
        disp.add_display_item(
            displayer.DisplayerItemText(features),
            0
        )
        
        return disp
