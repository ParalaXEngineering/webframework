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
            # Button ID uses full module name with dot separator
            self.button_id = f"{workflow_name}.workflow_next"
        else:
            self.m_name = f"Processing_{item_name}"
            self.m_category = None
            self.button_id = "workflow_next"
    
    def action(self):
        """Simulate processing with progress updates"""
        # Change button to "Processing..." and disable it
        if self.m_scheduler:
            self.m_scheduler.emit_button(self.button_id, "", "⏳ Processing...", "primary")
            self.m_scheduler.disable_button(self.button_id)
        
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
        
        # Change button back to "Next →" and enable it
        if self.m_scheduler:
            self.m_scheduler.emit_button(self.button_id, "", "Next →", "primary")
            self.m_scheduler.enable_button(self.button_id)


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
        """Display simple completion message"""
        
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
                "This demonstrates a basic workflow with two steps: "
                "selection and completion."
            ),
            0
        )
        
        return disp
    
    # ===== Step 2b & 3b: Threaded Workflow =====
    
    def _display_threaded_process(self, disp, workflow_data):
        """Display threaded processing step"""
        
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
        )
        
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
                    "Click Next to start background processing. "
                    "The thread will run for approximately 2 seconds."
                ),
                0
            )
        
        return disp
    
    def _display_threaded_complete(self, disp, workflow_data):
        """Display threaded completion"""
        
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
                "This demonstrates a workflow with threaded action. "
                "The processing happened in the background without blocking the UI."
            ),
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
        """Display completion with redo option"""
        
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
                "This demonstrates the redo pattern. "
                "Use the 'Redo Last Step' button below to process another item."
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
        """Display completion with thread+redo"""
        
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
                "This combines threaded processing with the redo pattern. "
                "Enter a new item below and click 'Redo Last Step' to process it immediately."
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
        
        return disp
    
    # ===== Action Functions =====
    
    def _action_create_demo_thread(self, workflow, form_data):
        """Create demo processing thread"""
        item_name = workflow.m_workflow_data.get("item_name", "Item")
        # Pass workflow name to thread for unique identification
        return DemoProcessingThread(item_name, workflow.m_name)
