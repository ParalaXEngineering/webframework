"""
Modern Workflow System for Multi-Step Processes

This module provides a flexible workflow system with:
- Declarative step-based API
- Automatic form state persistence
- Conditional step visibility
- Support for sync and threaded actions
- Automatic breadcrumb generation
- Visual progress tracking
"""

import traceback
import json
from typing import Optional, Callable, Any, Dict, List
from enum import Enum

try:
    from . import scheduler
    from . import displayer
    from .threaded import Threaded_action
    from .log.logger_factory import get_logger
except ImportError:
    import scheduler
    import displayer
    from threaded import Threaded_action
    from log.logger_factory import get_logger


class StepActionType(Enum):
    """Type of action to execute for a workflow step"""
    NONE = "none"  # No action
    FUNCTION = "function"  # Simple synchronous function
    THREADED = "threaded"  # Threaded action


class WorkflowStep:
    """
    Represents a single step in a workflow.
    
    This class encapsulates all aspects of a workflow step:
    - Display logic (what to show the user)
    - Action logic (what to do when proceeding)
    - Skip logic (what to do when skipping)
    - Conditional visibility (when to show this step)
    
    Example:
        >>> def show_form(disp, data):
        ...     disp.add_display_item(DisplayerItemText("Hello"))
        ...     return disp
        >>> 
        >>> def process_data(workflow, data):
        ...     print(f"Processing: {data}")
        >>> 
        >>> step = WorkflowStep(
        ...     name="Welcome",
        ...     display_func=show_form,
        ...     action_func=process_data,
        ...     description="Welcome to the wizard"
        ... )
    """
    
    def __init__(
        self,
        name: str,
        display_func: Callable,
        action_func: Optional[Callable] = None,
        skip_func: Optional[Callable] = None,
        condition_func: Optional[Callable[[Dict], bool]] = None,
        action_type: StepActionType = StepActionType.FUNCTION,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        allow_redo: bool = False
    ):
        """
        Initialize a workflow step.
        
        Args:
            name: Display name for this step (shown in breadcrumbs)
            display_func: Function to generate the display. Signature: (displayer, workflow_data) -> displayer
            action_func: Function to execute on "Next". Signature: (workflow, form_data) -> None
            skip_func: Function to execute on "Skip". Signature: (workflow, form_data) -> None
            condition_func: Function to determine if step should be shown. Signature: (workflow_data) -> bool
            action_type: Type of action (NONE, FUNCTION, THREADED)
            description: Optional description for this step
            icon: Optional icon class for breadcrumbs
            allow_redo: If True, shows a "Redo" button on this step to repeat the previous step
        """
        self.name = name
        self.display_func = display_func
        self.action_func = action_func
        self.skip_func = skip_func
        self.condition_func = condition_func
        self.action_type = action_type
        self.description = description
        self.icon = icon or "bi-circle"
        self.allow_redo = allow_redo
        
    def is_visible(self, workflow_data: Dict) -> bool:
        """
        Check if this step should be visible based on workflow data.
        
        Args:
            workflow_data: All data collected from previous steps
            
        Returns:
            True if step should be shown, False otherwise
        """
        if self.condition_func is None:
            return True
        return self.condition_func(workflow_data)
    
    def execute_action(self, workflow: 'Workflow', form_data: Dict) -> None:
        """
        Execute this step's action.
        
        Args:
            workflow: The parent workflow instance
            form_data: Data from the current step's form
        """
        if not self.action_func:
            return
            
        if self.action_type == StepActionType.FUNCTION:
            # Simple synchronous function
            self.action_func(workflow, form_data)
        elif self.action_type == StepActionType.THREADED:
            # Threaded action - expect action_func to return a Threaded_action instance
            thread = self.action_func(workflow, form_data)
            if isinstance(thread, Threaded_action):
                thread.start()
                # Store reference so we can check status
                workflow.m_active_thread = thread
    
    def execute_skip(self, workflow: 'Workflow', form_data: Dict) -> None:
        """
        Execute this step's skip logic.
        
        Args:
            workflow: The parent workflow instance
            form_data: Data from the current step's form
        """
        if self.skip_func:
            self.skip_func(workflow, form_data)


class Workflow:
    """
    Modern workflow system for multi-step processes.
    
    This class manages a sequence of steps, handles form state persistence,
    supports conditional step visibility, and provides automatic UI generation.
    
    Features:
    - Declarative step definition
    - Automatic form state saving/restoration
    - Conditional step visibility
    - Progress tracking with breadcrumbs
    - Support for sync and threaded actions
    
    Example:
        >>> workflow = Workflow("Registration Wizard")
        >>> 
        >>> # Define steps
        >>> workflow.add_step(WorkflowStep(
        ...     name="Personal Info",
        ...     display_func=show_personal_form,
        ...     action_func=save_personal_info
        ... ))
        >>> 
        >>> workflow.add_step(WorkflowStep(
        ...     name="Account Setup",
        ...     display_func=show_account_form,
        ...     action_func=create_account,
        ...     condition_func=lambda data: data.get('create_account') == True
        ... ))
    """
    
    m_type = "workflow"
    m_default_name = "Workflow Instance"
    
    def __init__(self, name: Optional[str] = None):
        """
        Initialize a workflow.
        
        Args:
            name: Optional name for this workflow instance
        """
        self.m_name = name or self.m_default_name
        self.m_steps: List[WorkflowStep] = []
        self.m_current_step_index = 0
        self.m_workflow_data: Dict[str, Any] = {}  # All data collected from all steps
        self.m_active_thread: Optional[Threaded_action] = None
        self.m_logger = get_logger(f"workflow.{self.m_name}")
        
        # Track which steps are visible (computed based on conditions)
        self.m_visible_steps: List[int] = []

    def get_name(self) -> str:
        """Get the name of this workflow instance."""
        return self.m_name
    
    def change_name(self, name: str) -> None:
        """Change the name of this workflow instance."""
        self.m_name = name
        self.m_logger = get_logger(f"workflow.{self.m_name}")
    
    def add_step(self, step: WorkflowStep) -> None:
        """
        Add a step to the workflow.
        
        Args:
            step: The WorkflowStep to add
        """
        self.m_steps.append(step)
        self.m_logger.debug(f"Added step '{step.name}' to workflow")
    
    def _compute_visible_steps(self) -> List[int]:
        """
        Compute which steps should be visible based on current workflow data.
        
        Returns:
            List of step indices that should be visible
        """
        visible = []
        for i, step in enumerate(self.m_steps):
            if step.is_visible(self.m_workflow_data):
                visible.append(i)
        return visible
    
    def _get_visible_step_index(self, absolute_index: int) -> int:
        """
        Convert an absolute step index to a visible step index.
        
        Args:
            absolute_index: Index in the full step list
            
        Returns:
            Index in the visible steps list, or -1 if not visible
        """
        try:
            return self.m_visible_steps.index(absolute_index)
        except ValueError:
            return -1
    
    def get_current_step(self) -> Optional[WorkflowStep]:
        """Get the current workflow step."""
        if 0 <= self.m_current_step_index < len(self.m_steps):
            return self.m_steps[self.m_current_step_index]
        return None
    
    def prepare_workflow(self, data_in: Optional[Dict]) -> bool:
        """
        Process incoming POST data and determine next step.
        
        Args:
            data_in: Data from POST request (from util_post_to_json)
            
        Returns:
            True if workflow should proceed, False otherwise
        """
        # First time - start at step 0
        if not data_in:
            self.m_current_step_index = 0
            self.m_visible_steps = self._compute_visible_steps()
            return True
        
        # Check if this POST is for our workflow
        if self.m_name not in data_in:
            return False
        
        workflow_data = data_in[self.m_name]
        
        # DEBUG: Log what we received
        self.m_logger.info(f"POST received for workflow. Keys in workflow_data: {list(workflow_data.keys())}")
        
        # Restore workflow state
        if "workflow_state" in workflow_data:
            try:
                state_json = workflow_data["workflow_state"]
                self.m_logger.debug(f"Raw workflow_state received: {repr(state_json)[:200]}")
                self.m_workflow_data = json.loads(state_json)
                self.m_logger.debug(f"Restored workflow state: {len(self.m_workflow_data)} keys")
            except Exception as e:
                self.m_logger.error(f"Failed to restore workflow state: {e}")
                self.m_logger.error(f"Invalid JSON was: {repr(workflow_data.get('workflow_state', ''))[:200]}")
        
        if "current_step" in workflow_data:
            self.m_current_step_index = int(workflow_data["current_step"])
        
        # Compute visible steps based on current data
        self.m_visible_steps = self._compute_visible_steps()
        
        # Try to restore thread reference if one was running on this step
        self._restore_thread_reference()
        
        # Handle button actions
        if "workflow_prev" in workflow_data:
            self._go_previous()
            return True
        elif "workflow_skip" in workflow_data:
            self._execute_skip(workflow_data)
            self._go_next()
            return True
        elif "workflow_redo_last" in workflow_data:
            # Redo last step button clicked - go back to previous step and preserve data
            # First save the form data (which may include new scan input)
            self._save_step_data(workflow_data)
            self._redo_last_step()
            
            # Auto-execute the action if the step has one (for batch operations)
            current_step = self.m_steps[self.m_current_step_index]
            if current_step.action_func is not None:
                self.m_logger.info(f"Auto-executing action after redo on step {self.m_current_step_index}")
                self._execute_action(workflow_data)
                
                # If a thread was created, mark it
                if self.m_active_thread:
                    thread_step_flag = f'_thread_on_step_{self.m_current_step_index}'
                    self.m_workflow_data[thread_step_flag] = True
                    self.m_logger.info(f"Thread created on redo, staying on step {self.m_current_step_index}")
            
            return True
        elif "workflow_redo" in workflow_data:
            # Redo button clicked - handle redo with workflow data
            # Redo configuration should be in workflow_data as:
            # - redo_target_step: which step to jump back to
            # - other fields: new data to update
            target_step = int(workflow_data.get("redo_target_step", 0))
            
            # Extract data to update (exclude workflow control fields)
            exclude_keys = {"workflow_redo", "workflow_state", "current_step", "redo_target_step"}
            update_data = {k: v for k, v in workflow_data.items() if k not in exclude_keys}
            
            self.redo(target_step, update_data)
            return True
        elif "workflow_next" in workflow_data:
            self._save_step_data(workflow_data)
            
            # Get current step info before potential navigation
            current_step = self.get_current_step()
            thread_step_flag = f'_thread_on_step_{self.m_current_step_index}'
            thread_was_started = self.m_workflow_data.get(thread_step_flag, False)
            
            self.m_logger.info(f"Current step: {self.m_current_step_index}, Thread flag: {thread_was_started}, Active thread: {self.m_active_thread is not None}")
            
            # Check if current step has a THREADED action
            is_threaded_step = current_step and current_step.action_type == StepActionType.THREADED
            
            if is_threaded_step and thread_was_started:
                # Thread was already started on this THREADED step
                if self.m_active_thread and self.m_active_thread.is_running():
                    # Thread still running - stay on step
                    self.m_logger.info(f"Thread still running on step {self.m_current_step_index}, staying")
                else:
                    # Thread completed (or lost reference) - advance to next step
                    self.m_logger.info(f"Thread completed/finished on step {self.m_current_step_index}, advancing")
                    self.m_workflow_data.pop(thread_step_flag, None)
                    self.m_active_thread = None
                    self._go_next()
            elif is_threaded_step and not thread_was_started:
                # First time on THREADED step - start the thread
                self.m_logger.info(f"Starting thread on THREADED step {self.m_current_step_index}")
                self._execute_action(workflow_data)
                if self.m_active_thread:
                    self.m_workflow_data[thread_step_flag] = True
                    self.m_logger.info(f"Thread created on step {self.m_current_step_index}, staying")
            else:
                # Non-threaded step - execute action (if any) and advance
                self.m_logger.info(f"Non-threaded step {self.m_current_step_index}, executing action and advancing")
                self._execute_action(workflow_data)
                self._go_next()
                
                # Check if we landed on a THREADED step after advancing
                new_step = self.get_current_step()
                if new_step and new_step.action_type == StepActionType.THREADED:
                    new_thread_flag = f'_thread_on_step_{self.m_current_step_index}'
                    if not self.m_workflow_data.get(new_thread_flag, False):
                        # Auto-start thread on the new THREADED step
                        self.m_logger.info(f"Auto-starting thread on new THREADED step {self.m_current_step_index}")
                        self._execute_action(self.m_workflow_data)
                        if self.m_active_thread:
                            self.m_workflow_data[new_thread_flag] = True
            
            return True
        
        return False
    
    def _save_step_data(self, form_data: Dict) -> None:
        """
        Save data from the current step's form into workflow data.
        
        Args:
            form_data: Data from the form
        """
        current_step = self.get_current_step()
        if not current_step:
            return
        
        # Save all form data except workflow control fields
        exclude_keys = {"workflow_next", "workflow_prev", "workflow_skip", 
                       "workflow_state", "current_step"}
        
        for key, value in form_data.items():
            if key not in exclude_keys:
                self.m_workflow_data[key] = value
        
        self.m_logger.debug(f"Saved step data: {list(form_data.keys())}")
    
    def _execute_action(self, form_data: Dict) -> None:
        """Execute the current step's action."""
        current_step = self.get_current_step()
        if current_step:
            try:
                current_step.execute_action(self, form_data)
            except Exception as e:
                self.m_logger.error(f"Step action failed: {e}\n{traceback.format_exc()}")
                if scheduler.scheduler_obj:
                    scheduler.scheduler_obj.emit_popup(
                        scheduler.logLevel.error,
                        f"Step action failed: {e}"
                    )
    
    def _execute_skip(self, form_data: Dict) -> None:
        """Execute the current step's skip logic."""
        current_step = self.get_current_step()
        if current_step:
            try:
                current_step.execute_skip(self, form_data)
            except Exception as e:
                self.m_logger.error(f"Step skip failed: {e}\n{traceback.format_exc()}")
    
    def _go_next(self) -> None:
        """Move to the next visible step."""
        # Recompute visible steps in case conditions changed
        self.m_visible_steps = self._compute_visible_steps()
        
        # Find next visible step
        for i in range(self.m_current_step_index + 1, len(self.m_steps)):
            if i in self.m_visible_steps:
                self.m_current_step_index = i
                self.m_logger.debug(f"Moving to step {i}: {self.m_steps[i].name}")
                return
        
        # No more visible steps - stay at last step
        self.m_logger.debug("No more visible steps")
    
    def _go_previous(self) -> None:
        """Move to the previous visible step."""
        # Clear thread flag for current step when going back
        thread_step_flag = f'_thread_on_step_{self.m_current_step_index}'
        self.m_workflow_data.pop(thread_step_flag, None)
        self.m_active_thread = None
        
        # Find previous visible step
        for i in range(self.m_current_step_index - 1, -1, -1):
            if i in self.m_visible_steps:
                self.m_current_step_index = i
                self.m_logger.debug(f"Moving back to step {i}: {self.m_steps[i].name}")
                return
    
    def _redo_last_step(self) -> None:
        """
        Redo the last step - go back to previous step while preserving workflow data.
        
        This is called when the "Redo Last Step" button is clicked on the last step.
        Unlike _go_previous(), this doesn't clear the thread flag immediately,
        allowing the previous step to be re-executed with the same or updated data.
        """
        # Find previous visible step
        for i in range(self.m_current_step_index - 1, -1, -1):
            if i in self.m_visible_steps:
                # Clear only the thread flag for the target step to allow re-execution
                target_thread_flag = f'_thread_on_step_{i}'
                self.m_workflow_data.pop(target_thread_flag, None)
                
                self.m_current_step_index = i
                self.m_active_thread = None
                self.m_logger.info(f"Redo: Moving back to step {i}: {self.m_steps[i].name}")
                return
        
        self.m_logger.warning("Cannot redo - no previous step available")
    
    def _clear_all_thread_flags(self) -> None:
        """Clear all thread flags from workflow data."""
        keys_to_remove = [k for k in self.m_workflow_data.keys() if k.startswith('_thread_on_step_')]
        for key in keys_to_remove:
            self.m_workflow_data.pop(key, None)
        self.m_logger.debug(f"Cleared {len(keys_to_remove)} thread flags")
    
    def _restore_thread_reference(self) -> None:
        """
        Try to restore the thread reference from the thread manager.
        
        This is called when restoring workflow state from a POST request.
        If a thread was started on the current step, we try to find it
        in the thread manager to restore the reference.
        """
        thread_step_flag = f'_thread_on_step_{self.m_current_step_index}'
        if not self.m_workflow_data.get(thread_step_flag, False):
            # No thread flag for this step
            return
        
        # Check if there's a running thread with our workflow name
        try:
            from . import threaded
            if threaded.threaded_manager.thread_manager_obj:
                manager = threaded.threaded_manager.thread_manager_obj
                # Look for a thread with our workflow name (threads should set m_name to include workflow name)
                thread_name_pattern = f"{self.m_name}_thread"
                running_threads = getattr(manager, 'm_running_threads', [])
                for thread in running_threads:
                    if hasattr(thread, 'm_name') and thread.m_name == thread_name_pattern:
                        self.m_active_thread = thread
                        self.m_logger.debug(f"Restored thread reference: {thread.m_name}")
                        return
                    # Fallback: check get_name() method
                    elif hasattr(thread, 'get_name') and thread.get_name() == thread_name_pattern:
                        self.m_active_thread = thread
                        self.m_logger.debug(f"Restored thread reference: {thread.get_name()}")
                        return
                
                # Thread not found in running threads - it might have completed
                self.m_logger.debug(f"Thread flag set but no running thread found for '{thread_name_pattern}'")
        except Exception as e:
            self.m_logger.warning(f"Failed to restore thread reference: {e}")
    
    def is_first_step(self) -> bool:
        """Check if we're on the first visible step."""
        if not self.m_visible_steps:
            return True
        return self.m_current_step_index == self.m_visible_steps[0]
    
    def is_last_step(self) -> bool:
        """Check if we're on the last visible step."""
        if not self.m_visible_steps:
            return True
        return self.m_current_step_index == self.m_visible_steps[-1]
    
    def get_progress_percentage(self) -> int:
        """Get workflow progress as a percentage."""
        if not self.m_visible_steps:
            return 0
        
        try:
            visible_index = self.m_visible_steps.index(self.m_current_step_index)
            return int((visible_index + 1) / len(self.m_visible_steps) * 100)
        except ValueError:
            return 0
    
    def redo(self, target_step_index: int, update_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Redo functionality - jump back to a specific step with updated data.
        
        This is useful for batch operations where you want to repeat a workflow
        with different parameters (e.g., scanning multiple products).
        
        Args:
            target_step_index: The step index to jump back to (0-based)
            update_data: Optional dictionary of data to update in workflow_data
        
        Example:
            ::
            
                # After completing workflow, redo from step 1 with new serial
                workflow.redo(
                    target_step_index=1,
                    update_data={"serial_number": "NEW-123", "batch": "5"}
                )
        """
        if target_step_index < 0 or target_step_index >= len(self.m_steps):
            self.m_logger.error(f"Invalid target step index: {target_step_index}")
            return
        
        # Update workflow data if provided
        if update_data:
            self.m_workflow_data.update(update_data)
            self.m_logger.debug(f"Updated workflow data with: {list(update_data.keys())}")
        
        # Jump to target step
        self.m_current_step_index = target_step_index
        self.m_visible_steps = self._compute_visible_steps()
        
        # Clear any active thread and thread flags for all steps
        self.m_active_thread = None
        self._clear_all_thread_flags()
        
        self.m_logger.info(f"Redo: Jumped to step {target_step_index} ({self.m_steps[target_step_index].name})")
    
    def add_display(self, disp: 'displayer.Displayer') -> 'displayer.Displayer':
        """
        Generate the display for the current workflow step.
        
        This method:
        1. Adds the module to the displayer
        2. Generates automatic breadcrumbs
        3. Calls the step's display function
        4. Adds navigation buttons
        5. Includes hidden fields for state management
        
        Args:
            disp: The Displayer instance
            
        Returns:
            The updated Displayer instance
        """
        if not disp:
            return disp
        
        current_step = self.get_current_step()
        if not current_step:
            self.m_logger.error("No current step available")
            return disp
        
        # Add breadcrumbs BEFORE add_module (they're part of page structure)
        self._add_breadcrumbs(disp)
        
        # Add module with step name as subtitle
        disp.add_module(self, current_step.name)
        
        # Add progress indicator
        self._add_progress_indicator(disp)
        
        # Call the step's display function with workflow data
        try:
            disp = current_step.display_func(disp, self.m_workflow_data)
        except Exception as e:
            self.m_logger.error(f"Display function failed: {e}\n{traceback.format_exc()}")
            disp.add_master_layout(
                displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
            )
            disp.add_display_item(
                displayer.DisplayerItemAlert(
                    f"Error displaying step: {e}",
                    displayer.BSstyle.ERROR
                ),
                0
            )
        
        # Add navigation buttons and hidden state
        self._add_navigation(disp)
        
        return disp
    
    def _add_breadcrumbs(self, disp: 'displayer.Displayer') -> None:
        """Add breadcrumbs showing all visible steps."""
        # Add breadcrumbs for each visible step
        for i, step_idx in enumerate(self.m_visible_steps):
            step = self.m_steps[step_idx]
            # Mark only the current step with primary color
            is_active = (step_idx == self.m_current_step_index)
            
            # For now, breadcrumbs are just visual (no navigation)
            # You could add URL parameters here if you want clickable breadcrumbs
            disp.add_breadcrumb(
                name=f"{i+1}. {step.name}",
                url="",  # Current page
                parameters=[],
                style="primary" if is_active else None
            )
    
    def _add_progress_indicator(self, disp: 'displayer.Displayer') -> None:
        """Add a visual progress indicator."""
        progress = self.get_progress_percentage()
        visible_idx = self._get_visible_step_index(self.m_current_step_index) + 1
        total_visible = len(self.m_visible_steps)
        
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
        )
        
        # Progress info
        info_text = f"<strong>Step {visible_idx} of {total_visible}</strong> ({progress}% complete)"
        disp.add_display_item(
            displayer.DisplayerItemText(info_text),
            0
        )
        
        # Progress bar using DisplayerItemProgressBar
        disp.add_display_item(
            displayer.DisplayerItemProgressBar(
                id="workflow_progress",
                value=progress,
                label=None,
                style=displayer.BSstyle.PRIMARY,
                striped=True,
                animated=True,
                height=25,
                show_percentage=True
            ),

            0
        )
    
    def _add_navigation(self, disp: 'displayer.Displayer') -> None:
        """Add navigation buttons and hidden state fields."""
        disp.add_master_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.VERTICAL,
                [12],
                subtitle="",
                alignment=[displayer.BSalign.R],
            )
        )
        
        # Hidden fields for state management
        disp.add_display_item(
            displayer.DisplayerItemHidden("current_step", str(self.m_current_step_index))
        )
        
        # Serialize workflow data to JSON and store in hidden field
        workflow_state_json = json.dumps(self.m_workflow_data)
        disp.add_display_item(
            displayer.DisplayerItemHidden("workflow_state", workflow_state_json)
        )
        
        # Check if there's an active thread running
        thread_running = bool(self.m_active_thread and self.m_active_thread.is_running())
        
        # Navigation buttons
        if not self.is_first_step():
            disp.add_display_item(
                displayer.DisplayerItemButton("workflow_prev", "Previous"),
                0,
                disabled=thread_running,  # Disable during thread
            )
        
        if not self.is_last_step():
            current_step = self.get_current_step()
            
            # Determine button label based on thread state
            if thread_running:
                next_label = "Processing..."
            else:
                next_label = "Next"
            
            skip_enabled = current_step and current_step.skip_func is not None
            
            # Always show Next button, disabled during thread execution
            disp.add_display_item(
                displayer.DisplayerItemButton("workflow_next", next_label),
                0,
                disabled=thread_running,
            )
            
            if skip_enabled:
                disp.add_display_item(
                    displayer.DisplayerItemButton("workflow_skip", "Skip"),
                    0,
                    disabled=thread_running,  # Disable during thread
                )
        else:
            # Last step - show finish button and optional redo button
            current_step = self.get_current_step()
            
            # Show redo button first if enabled
            if current_step and current_step.allow_redo:
                disp.add_display_item(
                    displayer.DisplayerItemButton("workflow_redo_last", "Redo Last Step"),
                    0,
                    disabled=False,
                )
            
            # Then show finish button
            disp.add_display_item(
                displayer.DisplayerItemButton("workflow_next", "Finish"),
                0,
                disabled=False,
            )
    
    def add_redo_button(
        self,
        disp: 'displayer.Displayer',
        button_text: str = "🔄 Redo",
        target_step_index: int = 0,
        button_id: Optional[str] = None
    ) -> None:
        """
        Add a redo button to the current display.
        
        Call this from your step's display function if you want a redo button.
        Typically used on the last step for batch operations.
        
        Args:
            disp: The Displayer instance
            button_text: Text to display on the button
            target_step_index: Which step to jump back to when redo is clicked
            button_id: Optional custom button ID (defaults to workflow_redo)
        
        Example:
            def display_complete(disp, workflow_data):
                disp.add_display_item(...)
                # Add redo button that jumps back to step 1
                workflow.add_redo_button(disp, "Register Another", target_step_index=1)
                return disp
        """
        # Create a layout for the redo button
        disp.add_master_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.VERTICAL,
                [12],
                subtitle="",
                alignment=[displayer.BSalign.C]
            )
        )
        
        # Add hidden field with target step
        disp.add_display_item(
            displayer.DisplayerItemHidden("redo_target_step", str(target_step_index))
        )
        
        # Add the redo button
        btn_id = button_id or "workflow_redo"
        disp.add_display_item(
            displayer.DisplayerItemButton(btn_id, button_text),
            0
        )
        
        self.m_logger.debug(f"Added redo button targeting step {target_step_index}")
    
    def prepare_worker(self) -> None:
        """
        Legacy method for compatibility.
        
        In the new system, actions are executed immediately in prepare_workflow.
        This method is kept for compatibility but does nothing.
        """
        pass
