"""
Simplified Workflow Demo - Production Scanning Example

This demo shows:
- Basic form with code example
- Threaded action with progress tracking
- Redo functionality for batch operations
"""

import time
from src.modules.workflow import Workflow, WorkflowStep, StepActionType
from src.modules import displayer
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
        
        # Emit final status and re-enable navigation buttons
        if self.m_scheduler:
            self.m_scheduler.emit_status(
                self.get_name(),
                f"Complete! Registered {self.batch_size} product(s)",
                100,
                "✓ Registration complete",
                status_id="scan_progress"
            )
            # Re-enable workflow navigation buttons
            time.sleep(0.5)  # Brief delay to show completion
            self.m_scheduler.enable_button("Product Registration.workflow_next")
            self.m_scheduler.enable_button("Product Registration.workflow_prev")


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
        
        # Step 1: Scan Product - with immediate threaded processing
        self.add_step(WorkflowStep(
            name="Scan Product",
            display_func=self._display_scan,
            action_func=self._action_process_threaded,  # Thread starts immediately on Next
            action_type=StepActionType.THREADED,
            description="Scan product serial number"
        ))
        
        # Step 2: Complete with Redo Option
        self.add_step(WorkflowStep(
            name="Complete",
            display_func=self._display_complete,
            description="Registration complete",
            allow_redo=True  # Enable built-in redo button
        ))
    
    # ===== Step 1: Scan Product =====
    
    def _display_scan(self, disp, workflow_data):
        """Display product scanning form with code example"""
        
        # Check if there's an active thread (we're processing)
        if self.m_active_thread and self.m_active_thread.is_running():
            # Show processing status
            disp.add_master_layout(
                displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
            )
            
            serial = workflow_data.get("serial_number", "Unknown")
            batch = workflow_data.get("batch_size", "1")
            
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
            return disp
        
        # Main form section (when no thread running)
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
        )
        disp.add_display_item(
            displayer.DisplayerItemAlert(
                "<strong>📦 Product Registration System</strong><br>"
                "Scan or enter the product serial number. Click Next to start registration.",
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
        
        code_example = '''# Optimized 2-Step Workflow with Immediate Processing
# Step 1 - Scan (with threaded action that starts on Next)
def display_scan(disp, workflow_data):
    """Show form or thread progress"""
    # If thread is running, show progress
    if workflow.m_active_thread and workflow.m_active_thread.is_running():
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
        )
        serial = workflow_data.get("serial_number", "Unknown")
        disp.add_display_item(
            displayer.DisplayerItemAlert(
                f"⏳ Processing: {serial}",
                displayer.BSstyle.WARNING
            ), 0
        )
        disp.add_module(workflow.m_active_thread)  # Show progress bar
        return disp
    
    # Show scan form
    disp.add_master_layout(
        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
    )
    serial = workflow_data.get("serial_number", "")
    disp.add_display_item(
        displayer.DisplayerItemInputString("serial_number", None, serial), 0
    )
    return disp

def start_processing(workflow, form_data):
    """Create and return thread (started automatically)"""
    serial = workflow.m_workflow_data["serial_number"]
    return ProcessingThread(serial)

# Add step with THREADED action
workflow.add_step(WorkflowStep(
    name="Scan Product",
    display_func=display_scan,
    action_func=start_processing,
    action_type=StepActionType.THREADED  # Thread starts when leaving step
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
    
    def _action_process_threaded(self, workflow, form_data):
        """Create and return thread for processing"""
        serial = workflow.m_workflow_data.get("serial_number", "UNKNOWN")
        batch = int(workflow.m_workflow_data.get("batch_size", 1))
        
        thread = ScanProcessingAction(serial, batch)
        return thread  # Workflow will start it automatically
    
    # ===== Step 2: Complete =====

    
    def _display_complete(self, disp, workflow_data):
        """Display completion with scan input for next item"""
        
        serial = workflow_data.get("serial_number", "Unknown")
        batch = workflow_data.get("batch_size", "1")
        
        # Show completion message
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
        
        # Show registered data
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
        
        # Scan next product section - KEY FEATURE
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12],
                                     subtitle="🔄 Scan Next Product")
        )
        
        disp.add_display_item(
            displayer.DisplayerItemAlert(
                "<strong>Batch Scanning Mode</strong><br>"
                "Scan the next product barcode below. If your scanner has auto-enter, "
                "just scan and it will automatically process!",
                displayer.BSstyle.INFO
            ),
            0
        )
        
        # Serial number input - SAME FIELD NAME as step 1
        # This allows the redo to overwrite the previous value
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [6, 6])
        )
        disp.add_display_item(
            displayer.DisplayerItemText("<strong>Next Serial Number:</strong>"),
            0
        )
        # Clear the field for next scan (empty string)
        disp.add_display_item(
            displayer.DisplayerItemInputString("serial_number", None, "", focus=True),
            1
        )
        
        # Batch size input - SAME FIELD NAME
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [6, 6])
        )
        disp.add_display_item(
            displayer.DisplayerItemText("<strong>Batch Size:</strong>"),
            0
        )
        disp.add_display_item(
            displayer.DisplayerItemInputNumeric("batch_size", None, batch),
            1
        )
        
        # Code example for batch scanning
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12],
                                     subtitle="💡 Code Example: Batch Scanning Pattern")
        )
        
        code_example = '''# Batch Scanning Pattern - Continuous 2-Step Workflow
# Step 1: Scan (with immediate threaded processing)
# Step 2: Complete (with same field names for next scan)

def display_complete(disp, workflow_data):
    # Show what was just registered
    serial = workflow_data.get("serial_number", "Unknown")
    disp.add_display_item(
        DisplayerItemAlert(f"✓ Registered: {serial}", BSstyle.SUCCESS)
    )
    
    # Add scan inputs for NEXT item
    # CRITICAL: Use the SAME field names as Step 1
    # This overwrites previous values when "Redo Last Step" is clicked
    disp.add_display_item(
        DisplayerItemInputString("serial_number", None, "", focus=True)
    )
    disp.add_display_item(
        DisplayerItemInputNumeric("batch_size", None, "1")
    )
    return disp

# Define Complete step with allow_redo=True
workflow.add_step(WorkflowStep(
    name="Complete",
    display_func=display_complete,
    allow_redo=True  # Enables "Redo Last Step" button
))

# User workflow:
# 1. Scan → Enter serial & batch → Click Next
# 2. Thread processes immediately (still on Scan step during processing)
# 3. Auto-advances to Complete when thread finishes
# 4. Shows success + empty scan field
# 5. Scan next item → Click "Redo Last Step"
# 6. New values overwrite old values
# 7. Thread processes new item → Back to Complete
# 8. Repeat!

# Perfect for: warehouse scanning, batch registration, inventory management'''
        
        disp.add_display_item(
            displayer.DisplayerItemCode(
                "redo_code",
                code_example,
                language="python",
                title="Continuous Batch Scanning",
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
                            <li>Built-in redo for batch operations</li>
                            <li>Easy integration</li>
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
