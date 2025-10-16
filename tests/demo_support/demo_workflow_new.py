"""
Workflow Demo - Interactive Examples

Demonstrates different workflow patterns:
- Simple: Basic two-step workflow
- Threaded: Workflow with background processing
- Redo: Continuous input loop with redo button
- Threaded + Redo: Combined threaded processing with redo
"""

import time
from src.modules.workflow import Workflow, WorkflowStep, StepActionType
from src.modules import displayer
from src.modules.threaded import Threaded_action


class DemoProcessingThread(Threaded_action):
    """Simple demo thread that simulates processing"""
    
    m_default_name = "Processing"
    
    def __init__(self, item_name: str, workflow_name: str = None):
        super().__init__()
        self.item_name = item_name
        # Set a unique name that includes the workflow name for thread restoration
        if workflow_name:
            self.m_name = f"{workflow_name}_thread"
            # Set the category for status reporting (workflow name with underscores for HTML IDs)
            self.m_category = workflow_name.replace(" ", "_")
            # Button IDs must include module name prefix (matches HTML name attribute)
            self.button_id = f"{workflow_name}.workflow_next"
            self.prev_button_id = f"{workflow_name}.workflow_prev"
        else:
            self.m_name = f"Processing_{item_name}"
            self.m_category = None
            self.button_id = "workflow_next"
            self.prev_button_id = "workflow_prev"
    
    def action(self):
        """Simulate processing with progress updates"""
        # Change button to "Processing..." and disable both navigation buttons
        if self.m_scheduler:
            self.m_scheduler.emit_button(self.button_id, "", "Processing...", "primary")
            self.m_scheduler.disable_button(self.button_id)
            self.m_scheduler.disable_button(self.prev_button_id)
        
        steps = 10
        for i in range(steps):
            if not self.m_running:
                break
            
            progress = int((i + 1) / steps * 100)
            self.m_running_state = progress
            self.console_write(f"Processing {self.item_name}: {progress}%")
            
            # Emit status to the correct workflow table if category is set
            # Category uses underscores for HTML table ID
            if self.m_scheduler and self.m_category:
                self.m_scheduler.emit_status(
                    self.m_category,
                    f"Processing {self.item_name}",
                    progress,
                    f"{progress}%",
                    status_id="workflow_processing"
                )
            
            time.sleep(0.2)  # 2 seconds total
        
        self.m_running_state = 100
        self.console_write(f"Completed: {self.item_name}")
        
        # Change button back to "Next" and enable both navigation buttons
        if self.m_scheduler:
            self.m_scheduler.emit_button(self.button_id, "", "Next", "primary")
            self.m_scheduler.enable_button(self.button_id)
            self.m_scheduler.enable_button(self.prev_button_id)
            # Reload page so buttons are rendered properly without disabled attribute
            self.m_scheduler.emit_reload()


class WorkflowDemo(Workflow):
    """
    Interactive workflow demonstration with multiple workflow patterns
    """
    
    def __init__(self):
        super().__init__("Workflow Demo")
        # Initialize with default workflow type so conditional steps are visible
        self.m_workflow_data["workflow_type"] = "simple"
        self._setup_steps()
    
    # Condition functions (picklable methods instead of lambdas)
    def _condition_simple(self, data):
        result = data.get("workflow_type") == "simple"
        self.m_logger.debug(f"_condition_simple: workflow_type={data.get('workflow_type')}, result={result}")
        return result
    
    def _condition_threaded(self, data):
        result = data.get("workflow_type") == "threaded"
        self.m_logger.debug(f"_condition_threaded: workflow_type={data.get('workflow_type')}, result={result}")
        return result
    
    def _condition_redo(self, data):
        result = data.get("workflow_type") == "redo"
        self.m_logger.debug(f"_condition_redo: workflow_type={data.get('workflow_type')}, result={result}")
        return result
    
    def _condition_threaded_redo(self, data):
        result = data.get("workflow_type") == "threaded_redo"
        self.m_logger.debug(f"_condition_threaded_redo: workflow_type={data.get('workflow_type')}, result={result}")
        return result
    
    def _setup_steps(self):
        """Define all workflow steps with conditional visibility"""
        
        # Step 1: Select workflow type (always visible)
        self.add_step(WorkflowStep(
            name="Select Type",
            display_func=self._display_select_type,
            description="Choose workflow pattern"
        ))
        
        # Step 2a: Simple - Done (visible if type == "simple")
        self.add_step(WorkflowStep(
            name="Done",
            display_func=self._display_simple_done,
            condition_func=self._condition_simple,
            description="Workflow complete"
        ))
        
        # Step 2b: Threaded - Processing (visible if type == "threaded")
        self.add_step(WorkflowStep(
            name="Processing",
            display_func=self._display_threaded_process,
            action_func=self._action_create_demo_thread,
            action_type=StepActionType.THREADED,
            condition_func=self._condition_threaded,
            description="Background processing"
        ))
        
        # Step 3b: Threaded - Complete (visible if type == "threaded")
        self.add_step(WorkflowStep(
            name="Complete",
            display_func=self._display_threaded_complete,
            condition_func=self._condition_threaded,
            description="Processing finished"
        ))
        
        # Step 2c: Redo - Input (visible if type == "redo")
        self.add_step(WorkflowStep(
            name="Input",
            display_func=self._display_redo_input,
            condition_func=self._condition_redo,
            description="Enter data"
        ))
        
        # Step 3c: Redo - Complete (visible if type == "redo")
        self.add_step(WorkflowStep(
            name="Complete",
            display_func=self._display_redo_complete,
            condition_func=self._condition_redo,
            allow_redo=True,
            description="Scan complete"
        ))
        
        # Step 2d: Threaded+Redo - Input with Thread (visible if type == "threaded_redo")
        self.add_step(WorkflowStep(
            name="Scan",
            display_func=self._display_threaded_redo_input,
            action_func=self._action_create_demo_thread,
            action_type=StepActionType.THREADED,
            condition_func=self._condition_threaded_redo,
            description="Scan and process"
        ))
        
        # Step 3d: Threaded+Redo - Complete (visible if type == "threaded_redo")
        self.add_step(WorkflowStep(
            name="Complete",
            display_func=self._display_threaded_redo_complete,
            condition_func=self._condition_threaded_redo,
            allow_redo=True,
            description="Processing complete"
        ))
    
    # ===== Step 1: Select Workflow Type =====
    
    def _display_select_type(self, disp, workflow_data):
        """Display workflow type selection"""
        
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
        )
        
        disp.add_display_item(
            displayer.DisplayerItemText("<h4>Workflow Demo</h4>"),
            0
        )
        
        disp.add_display_item(
            displayer.DisplayerItemText("Select a workflow pattern to demonstrate:"),
            0
        )
        
        # Workflow type selection
        workflow_types = [
            ("simple", "Simple - Basic two-step workflow"),
            ("threaded", "Threaded - Workflow with background processing"),
            ("redo", "Redo - Continuous input loop"),
            ("threaded_redo", "Threaded + Redo - Combined pattern")
        ]
        
        current_type = workflow_data.get("workflow_type", "simple")
        
        disp.add_display_item(
            displayer.DisplayerItemInputSelect(
                "workflow_type",
                "Workflow Type",
                current_type,
                [t[0] for t in workflow_types],
                [t[1] for t in workflow_types]
            ),
            0
        )
        
        return disp
    
    # ===== Step 2a: Simple - Done =====
    
    def _display_simple_done(self, disp, workflow_data):
        """Display simple completion with documentation"""
        
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
        )
        
        disp.add_display_item(
            displayer.DisplayerItemAlert(
                "Workflow complete!",
                displayer.BSstyle.SUCCESS
            ),
            0
        )
        
        disp.add_display_item(
            displayer.DisplayerItemText(
                "<strong>Simple Workflow Pattern</strong><br>"
                "This demonstrates the most basic workflow: linear navigation through steps "
                "with form data collection."
            ),
            0
        )
        
        # Add documentation section
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12],
                                     subtitle="Implementation Guide")
        )
        
        disp.add_display_item(
            displayer.DisplayerItemText("<h5>1. Define Workflow Steps</h5>"),
            0
        )
        
        workflow_code = '''# Create a simple two-step workflow
workflow = Workflow(name="Simple Demo")

# Step 1: Selection
workflow.add_step(WorkflowStep(
    name="Select Type",
    display_func=display_selection,
    description="Choose workflow pattern"
))

# Step 2: Completion
workflow.add_step(WorkflowStep(
    name="Done",
    display_func=display_done,
    description="Workflow complete"
))

def display_selection(disp, workflow_data):
    """Display selection form"""
    disp.add_display_item(
        DisplayerItemRadioButton(
            "workflow_type",
            "Select Pattern",
            ["simple", "threaded", "redo"],
            workflow_data.get("workflow_type", "simple")
        )
    )
    return disp

def display_done(disp, workflow_data):
    """Display completion message"""
    selected_type = workflow_data.get("workflow_type", "unknown")
    disp.add_display_item(
        DisplayerItemAlert(f"Selected: {selected_type}", BSstyle.SUCCESS)
    )
    return disp'''
        
        disp.add_display_item(
            displayer.DisplayerItemCode(
                "simple_workflow",
                workflow_code,
                language="python",
                title="Simple Workflow Definition",
                show_line_numbers=True
            ),
            0
        )
        
        # Key concepts
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12],
                                     subtitle="Key Concepts")
        )
        
        concepts_html = '''<div class="row">
    <div class="col-md-6">
        <div class="card bg-light mb-3">
            <div class="card-body">
                <h6 class="card-title">Step Navigation</h6>
                <ul class="mb-0">
                    <li>Linear flow: Step 1 → Step 2 → Done</li>
                    <li>Previous/Next buttons auto-generated</li>
                    <li>Finish button on last step</li>
                    <li>Navigation buttons disabled when needed</li>
                </ul>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card bg-light mb-3">
            <div class="card-body">
                <h6 class="card-title">Data Collection</h6>
                <ul class="mb-0">
                    <li>Form fields stored in <code>workflow_data</code></li>
                    <li>Field names persist across steps</li>
                    <li>Access via <code>workflow_data.get("field_name")</code></li>
                    <li>Data preserved during navigation</li>
                </ul>
            </div>
        </div>
    </div>
</div>
<div class="row">
    <div class="col-md-12">
        <div class="card bg-light mb-3">
            <div class="card-body">
                <h6 class="card-title">Display Functions</h6>
                <ul class="mb-0">
                    <li>Called with <code>(disp, workflow_data)</code> parameters</li>
                    <li>Build UI using DisplayerItem components</li>
                    <li>Add layouts with <code>add_master_layout()</code></li>
                    <li>Add items with <code>add_display_item(item, layout_index)</code></li>
                    <li>Must return the displayer object</li>
                </ul>
            </div>
        </div>
    </div>
</div>'''
        
        disp.add_display_item(
            displayer.DisplayerItemText(concepts_html),
            0
        )
        
        return disp
    
    # ===== Step 2b & 3b: Threaded Workflow =====
    
    def _display_threaded_process(self, disp, workflow_data):
        """Display threaded processing step"""
        
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
        )
        
        # DEBUG: Show current state
        self.m_logger.info(f"[DISPLAY] Step {self.m_current_step_index}, Thread: {self.m_active_thread}, Running: {self.m_active_thread.is_running() if self.m_active_thread else False}")
        
        # If thread is running, show progress
        if self.m_active_thread and self.m_active_thread.is_running():
            disp.add_display_item(
                displayer.DisplayerItemAlert(
                    "Processing in background...",
                    displayer.BSstyle.INFO
                ),
                0
            )
            # Don't add thread as separate module - it will be displayed in the workflow's progress table
            # The thread progress is automatically updated via Socket.IO
        else:
            disp.add_display_item(
                displayer.DisplayerItemText(
                    f"[DEBUG: Step {self.m_current_step_index}] Click Next to start background processing. "
                    "The thread will run for approximately 2 seconds."
                ),
                0
            )
        
        return disp
    
    def _display_threaded_complete(self, disp, workflow_data):
        """Display threaded completion with documentation"""
        
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
        )
        
        disp.add_display_item(
            displayer.DisplayerItemAlert(
                "Background processing complete!",
                displayer.BSstyle.SUCCESS
            ),
            0
        )
        
        disp.add_display_item(
            displayer.DisplayerItemText(
                "<strong>Threaded Workflow Pattern</strong><br>"
                "This demonstrates a workflow with background thread execution. "
                "The processing happened asynchronously without blocking the UI."
            ),
            0
        )
        
        # Add documentation section
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12],
                                     subtitle="Implementation Guide")
        )
        
        # Step 1: Define the thread class
        disp.add_display_item(
            displayer.DisplayerItemText("<h5>1. Create a Threaded Action Class</h5>"),
            0
        )
        
        thread_code = '''class DemoProcessingThread(Threaded_action):
    """Thread that performs background processing with progress updates"""
    
    def __init__(self, item_name: str, workflow_name: str):
        super().__init__()
        self.item_name = item_name
        # Set unique name with workflow prefix for thread restoration
        self.m_name = f"{workflow_name}_thread"
        # Category for progress display (sanitized for HTML IDs)
        self.m_category = workflow_name.replace(" ", "_")
        # Button IDs must include module name prefix
        self.button_id = f"{workflow_name}.workflow_next"
        self.prev_button_id = f"{workflow_name}.workflow_prev"
    
    def action(self):
        """Execute background processing with real-time updates"""
        # Disable navigation and update button text
        if self.m_scheduler:
            self.m_scheduler.emit_button(self.button_id, "", "Processing...", "primary")
            self.m_scheduler.disable_button(self.button_id)
            self.m_scheduler.disable_button(self.prev_button_id)
        
        # Perform work with progress updates
        for i in range(10):
            progress = int((i + 1) / 10 * 100)
            self.m_running_state = progress
            
            # Emit status to workflow progress table
            if self.m_scheduler and self.m_category:
                self.m_scheduler.emit_status(
                    self.m_category,
                    f"Processing {self.item_name}",
                    progress,
                    f"{progress}%",
                    status_id="workflow_processing"
                )
            
            time.sleep(0.2)
        
        # Re-enable navigation and trigger page reload
        if self.m_scheduler:
            self.m_scheduler.emit_button(self.button_id, "", "Next", "primary")
            self.m_scheduler.enable_button(self.button_id)
            self.m_scheduler.enable_button(self.prev_button_id)
            self.m_scheduler.emit_reload()  # Reload to advance workflow'''
        
        disp.add_display_item(
            displayer.DisplayerItemCode(
                "thread_class",
                thread_code,
                language="python",
                title="Thread Class Implementation",
                show_line_numbers=True
            ),
            0
        )
        
        # Step 2: Define workflow step
        disp.add_display_item(
            displayer.DisplayerItemText("<h5>2. Define the Workflow Step</h5>"),
            0
        )
        
        step_code = '''# Add a THREADED workflow step
workflow.add_step(WorkflowStep(
    name="Processing",
    display_func=display_processing,
    action_func=create_thread,  # Returns Threaded_action instance
    action_type=StepActionType.THREADED,  # Mark as threaded
    description="Background processing"
))

def display_processing(disp, workflow_data):
    """Display function shows thread status"""
    if workflow.m_active_thread and workflow.m_active_thread.is_running():
        disp.add_display_item(
            DisplayerItemAlert("Processing in background...", BSstyle.INFO)
        )
    else:
        disp.add_display_item(
            DisplayerItemText("Click Next to start processing.")
        )
    return disp

def create_thread(workflow, form_data):
    """Action function creates and returns the thread"""
    item_name = workflow.m_workflow_data.get("item_name", "Item")
    return DemoProcessingThread(item_name, workflow.m_name)'''
        
        disp.add_display_item(
            displayer.DisplayerItemCode(
                "step_definition",
                step_code,
                language="python",
                title="Workflow Step Definition",
                show_line_numbers=True
            ),
            0
        )
        
        # Key concepts
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12],
                                     subtitle="Key Concepts")
        )
        
        concepts_html = '''<div class="row">
    <div class="col-md-6">
        <div class="card bg-light mb-3">
            <div class="card-body">
                <h6 class="card-title">Thread Integration</h6>
                <ul class="mb-0">
                    <li><code>action_type=StepActionType.THREADED</code></li>
                    <li>Action function returns <code>Threaded_action</code></li>
                    <li>Thread auto-starts on step entry</li>
                    <li>Workflow stays on step until thread completes</li>
                    <li>Page auto-reloads on completion</li>
                </ul>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card bg-light mb-3">
            <div class="card-body">
                <h6 class="card-title">Button Control</h6>
                <ul class="mb-0">
                    <li><code>emit_button(id, icon, text, style)</code></li>
                    <li><code>disable_button(id)</code></li>
                    <li><code>enable_button(id)</code></li>
                    <li>Button IDs include module name prefix</li>
                    <li><code>emit_reload()</code> refreshes page</li>
                </ul>
            </div>
        </div>
    </div>
</div>
<div class="row">
    <div class="col-md-6">
        <div class="card bg-light mb-3">
            <div class="card-body">
                <h6 class="card-title">Progress Display</h6>
                <ul class="mb-0">
                    <li><code>emit_status(category, msg, progress, supplement)</code></li>
                    <li>Category = sanitized module name</li>
                    <li>Updates workflow progress table via Socket.IO</li>
                    <li>Real-time UI updates without page reload</li>
                </ul>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card bg-light mb-3">
            <div class="card-body">
                <h6 class="card-title">Thread State Management</h6>
                <ul class="mb-0">
                    <li>Thread flag: <code>_thread_on_step_N</code></li>
                    <li>Tracks thread execution per step</li>
                    <li>Prevents duplicate execution</li>
                    <li>Thread restoration via name pattern</li>
                </ul>
            </div>
        </div>
    </div>
</div>'''
        
        disp.add_display_item(
            displayer.DisplayerItemText(concepts_html),
            0
        )
        
        return disp
    
    # ===== Step 2c & 3c: Redo Workflow =====
    
    def _display_redo_input(self, disp, workflow_data):
        """Display input form for redo demo"""
        
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
        )
        
        disp.add_display_item(
            displayer.DisplayerItemText(
                "Enter an item name to process:"
            ),
            0
        )
        
        item_name = workflow_data.get("item_name", "")
        
        disp.add_display_item(
            displayer.DisplayerItemInputString(
                "item_name",
                "Item Name",
                item_name,
                focus=True
            ),
            0
        )
        
        return disp
    
    def _display_redo_complete(self, disp, workflow_data):
        """Display completion with redo option and documentation"""
        
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
        )
        
        item_name = workflow_data.get("item_name", "Unknown")
        
        disp.add_display_item(
            displayer.DisplayerItemAlert(
                f"Item processed: {item_name}",
                displayer.BSstyle.SUCCESS
            ),
            0
        )
        
        disp.add_display_item(
            displayer.DisplayerItemText(
                "<strong>Redo Workflow Pattern</strong><br>"
                "This demonstrates repeating a step without restarting the entire workflow. "
                "The Redo button returns to a previous step while preserving workflow state."
            ),
            0
        )
        
        # Input for next item (same field name = overwrites previous)
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12],
                                     subtitle="Process Another Item")
        )
        
        disp.add_display_item(
            displayer.DisplayerItemInputString(
                "item_name",
                "Next Item Name",
                "",
                focus=True
            ),
            0
        )
        
        # Add documentation section
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12],
                                     subtitle="Implementation Guide")
        )
        
        disp.add_display_item(
            displayer.DisplayerItemText("<h5>1. Enable Redo on a Step</h5>"),
            0
        )
        
        redo_code = '''# Define step with allow_redo=True
workflow.add_step(WorkflowStep(
    name="Input",
    display_func=display_input,
    description="Enter data"
))

workflow.add_step(WorkflowStep(
    name="Complete",
    display_func=display_complete,
    allow_redo=True,  # Enable the Redo button on this step
    description="Scan complete"
))

def display_input(disp, workflow_data):
    """Display input form"""
    item_name = workflow_data.get("item_name", "")
    disp.add_display_item(
        DisplayerItemInputString("item_name", "Item Name", item_name)
    )
    return disp

def display_complete(disp, workflow_data):
    """Display completion with redo input"""
    item_name = workflow_data.get("item_name", "Unknown")
    
    # Show result
    disp.add_display_item(
        DisplayerItemAlert(f"Processed: {item_name}", BSstyle.SUCCESS)
    )
    
    # Add input for next iteration (overwrites previous value)
    disp.add_display_item(
        DisplayerItemInputString("item_name", "Next Item", "", focus=True)
    )
    
    return disp'''
        
        disp.add_display_item(
            displayer.DisplayerItemCode(
                "redo_workflow",
                redo_code,
                language="python",
                title="Redo Workflow Definition",
                show_line_numbers=True
            ),
            0
        )
        
        # Key concepts
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12],
                                     subtitle="Key Concepts")
        )
        
        concepts_html = '''<div class="row">
    <div class="col-md-6">
        <div class="card bg-light mb-3">
            <div class="card-body">
                <h6 class="card-title">Redo Mechanism</h6>
                <ul class="mb-0">
                    <li><code>allow_redo=True</code> on WorkflowStep</li>
                    <li>Shows "Redo Last Step" button</li>
                    <li>Returns to previous step with state intact</li>
                    <li>Workflow state preserved across redo</li>
                    <li>Can redo multiple times</li>
                </ul>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card bg-light mb-3">
            <div class="card-body">
                <h6 class="card-title">Data Handling</h6>
                <ul class="mb-0">
                    <li>Same field name overwrites previous value</li>
                    <li>New data submitted via Redo button</li>
                    <li>workflow_data updated with new values</li>
                    <li>Step counter decrements on redo</li>
                    <li>No data loss during redo operation</li>
                </ul>
            </div>
        </div>
    </div>
</div>
<div class="row">
    <div class="col-md-12">
        <div class="card bg-light mb-3">
            <div class="card-body">
                <h6 class="card-title">Use Cases</h6>
                <ul class="mb-0">
                    <li><strong>Batch Processing</strong>: Process multiple items one at a time</li>
                    <li><strong>Iterative Input</strong>: Collect multiple records in sequence</li>
                    <li><strong>Error Correction</strong>: Allow user to retry with different input</li>
                    <li><strong>Incremental Work</strong>: Complete similar tasks repeatedly</li>
                </ul>
            </div>
        </div>
    </div>
</div>'''
        
        disp.add_display_item(
            displayer.DisplayerItemText(concepts_html),
            0
        )
        
        return disp
    
    # ===== Step 2d & 3d: Threaded + Redo Workflow =====
    
    def _display_threaded_redo_input(self, disp, workflow_data):
        """Display input with thread processing"""
        
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
        )
        
        # If thread is running, show progress
        if self.m_active_thread and self.m_active_thread.is_running():
            item_name = workflow_data.get("item_name", "Unknown")
            disp.add_display_item(
                displayer.DisplayerItemAlert(
                    f"Processing: {item_name}",
                    displayer.BSstyle.INFO
                ),
                0
            )
            # Don't add thread as separate module - it will be displayed in the workflow's progress table
        else:
            # Show input form
            disp.add_display_item(
                displayer.DisplayerItemText(
                    "Enter an item name. Processing will start automatically when you click Next."
                ),
                0
            )
            
            item_name = workflow_data.get("item_name", "")
            
            disp.add_display_item(
                displayer.DisplayerItemInputString(
                    "item_name",
                    "Item Name",
                    item_name,
                    focus=True
                ),
                0
            )
        
        return disp
    
    def _display_threaded_redo_complete(self, disp, workflow_data):
        """Display completion with thread+redo and documentation"""
        
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
        )
        
        item_name = workflow_data.get("item_name", "Unknown")
        
        disp.add_display_item(
            displayer.DisplayerItemAlert(
                f"Processing complete: {item_name}",
                displayer.BSstyle.SUCCESS
            ),
            0
        )
        
        disp.add_display_item(
            displayer.DisplayerItemText(
                "<strong>Threaded + Redo Pattern</strong><br>"
                "This combines background thread processing with the redo pattern. "
                "Each iteration processes asynchronously, allowing repeated batch operations."
            ),
            0
        )
        
        # Input for next item
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12],
                                     subtitle="Process Another Item")
        )
        
        disp.add_display_item(
            displayer.DisplayerItemInputString(
                "item_name",
                "Next Item Name",
                "",
                focus=True
            ),
            0
        )
        
        # Add documentation section
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12],
                                     subtitle="Implementation Guide")
        )
        
        disp.add_display_item(
            displayer.DisplayerItemText("<h5>1. Combine Threading and Redo</h5>"),
            0
        )
        
        combined_code = '''# Define workflow with threaded redo step
workflow.add_step(WorkflowStep(
    name="Scan",
    display_func=display_scan,
    action_func=create_scan_thread,
    action_type=StepActionType.THREADED,  # Background processing
    description="Scan and process"
))

workflow.add_step(WorkflowStep(
    name="Complete",
    display_func=display_complete,
    allow_redo=True,  # Enable redo to previous step
    description="Processing finished"
))

def display_scan(disp, workflow_data):
    """Display scan status or input form"""
    if workflow.m_active_thread and workflow.m_active_thread.is_running():
        # Thread is running - show progress
        item_name = workflow_data.get("item_name", "Unknown")
        disp.add_display_item(
            DisplayerItemAlert(f"Processing: {item_name}", BSstyle.INFO)
        )
    else:
        # Show input form
        disp.add_display_item(
            DisplayerItemInputString("item_name", "Item Name", 
                                    workflow_data.get("item_name", ""))
        )
    return disp

def display_complete(disp, workflow_data):
    """Display completion with input for next iteration"""
    item_name = workflow_data.get("item_name", "Unknown")
    
    # Show result
    disp.add_display_item(
        DisplayerItemAlert(f"Completed: {item_name}", BSstyle.SUCCESS)
    )
    
    # Input for next iteration
    disp.add_display_item(
        DisplayerItemInputString("item_name", "Next Item", "", focus=True)
    )
    
    return disp

def create_scan_thread(workflow, form_data):
    """Create processing thread"""
    item_name = workflow.m_workflow_data.get("item_name", "Item")
    return ScanThread(item_name, workflow.m_name)'''
        
        disp.add_display_item(
            displayer.DisplayerItemCode(
                "threaded_redo_workflow",
                combined_code,
                language="python",
                title="Threaded + Redo Workflow Definition",
                show_line_numbers=True
            ),
            0
        )
        
        disp.add_display_item(
            displayer.DisplayerItemText("<h5>2. Workflow Flow</h5>"),
            0
        )
        
        flow_html = '''<div class="alert alert-info">
    <strong>Execution Flow:</strong>
    <ol class="mb-0">
        <li>User enters item name and clicks Next</li>
        <li>Thread auto-starts on Scan step</li>
        <li>Background processing with progress updates</li>
        <li>Thread completes → page auto-reloads</li>
        <li>Workflow advances to Complete step automatically</li>
        <li>User enters new item name</li>
        <li>Clicks "Redo Last Step" → returns to Scan step</li>
        <li>Thread auto-starts again with new data</li>
        <li>Cycle repeats for batch processing</li>
    </ol>
</div>'''
        
        disp.add_display_item(
            displayer.DisplayerItemText(flow_html),
            0
        )
        
        # Key concepts
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12],
                                     subtitle="Key Concepts")
        )
        
        concepts_html = '''<div class="row">
    <div class="col-md-6">
        <div class="card bg-light mb-3">
            <div class="card-body">
                <h6 class="card-title">Pattern Combination</h6>
                <ul class="mb-0">
                    <li><code>action_type=StepActionType.THREADED</code></li>
                    <li><code>allow_redo=True</code> on next step</li>
                    <li>Thread auto-starts each iteration</li>
                    <li>Redo returns to threaded step</li>
                    <li>New thread created for each redo</li>
                </ul>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card bg-light mb-3">
            <div class="card-body">
                <h6 class="card-title">Thread Management</h6>
                <ul class="mb-0">
                    <li>Thread flag cleared before redo</li>
                    <li>New thread instance created</li>
                    <li>Previous thread properly cleaned up</li>
                    <li>Progress table updated per iteration</li>
                    <li>Button state managed per iteration</li>
                </ul>
            </div>
        </div>
    </div>
</div>
<div class="row">
    <div class="col-md-12">
        <div class="card bg-light mb-3">
            <div class="card-body">
                <h6 class="card-title">Use Cases</h6>
                <ul class="mb-0">
                    <li><strong>Batch File Processing</strong>: Process multiple files with individual progress</li>
                    <li><strong>Sequential Scans</strong>: Scan multiple items one at a time with feedback</li>
                    <li><strong>Iterative Analysis</strong>: Run analysis on multiple datasets consecutively</li>
                    <li><strong>Queue Processing</strong>: Handle work items from queue with visual progress</li>
                    <li><strong>Repetitive Operations</strong>: Execute same background task with different inputs</li>
                </ul>
            </div>
        </div>
    </div>
</div>'''
        
        disp.add_display_item(
            displayer.DisplayerItemText(concepts_html),
            0
        )
        
        return disp
    
    # ===== Action Functions =====
    
    def _action_create_demo_thread(self, workflow, form_data):
        """Create demo processing thread"""
        item_name = workflow.m_workflow_data.get("item_name", "Item")
        # Pass workflow name to thread for unique identification
        return DemoProcessingThread(item_name, workflow.m_name)
