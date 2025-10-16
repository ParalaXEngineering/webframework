"""
Comprehensive Workflow System Tests

This test file consolidates all workflow functionality tests:
- Basic workflow navigation and state management
- Thread completion and step advancement (thread_fix)
- Built-in redo functionality with allow_redo parameter
- Redo auto-execution for batch operations
- Batch scanning continuous loop pattern
- Conditional steps and visibility
- Action execution and data persistence

All tests use pytest conventions and can be run with: pytest tests/test_workflow.py
"""

import time
import json
from src.modules.workflow import Workflow, WorkflowStep, StepActionType
from src.modules import displayer
from src.modules.threaded.threaded_action import Threaded_action


# ===== Test Helper Classes =====

class QuickThread(Threaded_action):
    """Simple thread that completes quickly for testing"""
    m_default_name = "QuickThread"
    
    def __init__(self, data_id="test"):
        super().__init__()
        self.data_id = data_id
        self.completed = False
    
    def action(self):
        """Complete in 0.1 seconds"""
        self.m_running_state = 50
        time.sleep(0.1)
        self.completed = True
        self.m_running_state = 100


def simple_display(disp, data):
    """Minimal display function for testing"""
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemText("Test"), 0)
    return disp


def input_display(disp, data):
    """Display with input field"""
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    value = data.get("test_input", "")
    disp.add_display_item(
        displayer.DisplayerItemInputString("test_input", None, value),
        0
    )
    return disp


# ===== Basic Workflow Tests =====

def test_workflow_initialization():
    """Test basic workflow creation and initialization"""
    wf = Workflow("Test")
    
    # Add steps
    wf.add_step(WorkflowStep(name="Step1", display_func=simple_display))
    wf.add_step(WorkflowStep(name="Step2", display_func=simple_display))
    wf.add_step(WorkflowStep(name="Step3", display_func=simple_display))
    
    assert len(wf.m_steps) == 3, "Should have 3 steps"
    assert wf.m_name == "Test", "Name should be 'Test'"
    
    # Initialize
    wf.prepare_workflow(None)
    assert wf.m_current_step_index == 0, "Should start at step 0"
    assert wf.get_current_step().name == "Step1", "Current step should be Step1"
    

def test_workflow_navigation():
    """Test basic Next/Previous navigation"""
    wf = Workflow("Nav Test")
    wf.add_step(WorkflowStep(name="Step1", display_func=simple_display))
    wf.add_step(WorkflowStep(name="Step2", display_func=simple_display))
    wf.add_step(WorkflowStep(name="Step3", display_func=simple_display))
    
    wf.prepare_workflow(None)
    assert wf.m_current_step_index == 0
    
    # Go forward
    wf.prepare_workflow({
        "Nav Test": {
            "workflow_next": True,
            "current_step": "0",
            "workflow_state": json.dumps({})
        }
    })
    assert wf.m_current_step_index == 1, "Should be at step 1"
    
    # Go forward again
    wf.prepare_workflow({
        "Nav Test": {
            "workflow_next": True,
            "current_step": "1",
            "workflow_state": json.dumps(wf.m_workflow_data)
        }
    })
    assert wf.m_current_step_index == 2, "Should be at step 2 (last step)"


def test_workflow_data_persistence():
    """Test that form data persists across steps"""
    wf = Workflow("Data Test")
    wf.add_step(WorkflowStep(name="Input", display_func=input_display))
    wf.add_step(WorkflowStep(name="Display", display_func=simple_display))
    
    wf.prepare_workflow(None)
    
    # Submit data from step 1
    wf.prepare_workflow({
        "Data Test": {
            "test_input": "Hello World",
            "workflow_next": True,
            "current_step": "0",
            "workflow_state": json.dumps({})
        }
    })
    
    assert wf.m_workflow_data["test_input"] == "Hello World", "Data should be saved"
    assert wf.m_current_step_index == 1, "Should advance to step 2"


def test_workflow_progress_tracking():
    """Test progress percentage calculation"""
    wf = Workflow("Progress Test")
    wf.add_step(WorkflowStep(name="Step1", display_func=simple_display))
    wf.add_step(WorkflowStep(name="Step2", display_func=simple_display))
    wf.add_step(WorkflowStep(name="Step3", display_func=simple_display))
    wf.add_step(WorkflowStep(name="Step4", display_func=simple_display))
    
    wf.prepare_workflow(None)
    
    # Progress is (current_index + 1) / total * 100
    # Step 0 (1st of 4) = 25%
    assert wf.get_progress_percentage() == 25, "25% at first step"
    assert wf.is_first_step(), "Should be first step"
    assert not wf.is_last_step(), "Should not be last step"
    
    # Move to step 1 (2/4 = 50%)
    wf.prepare_workflow({
        "Progress Test": {
            "workflow_next": True,
            "current_step": "0",
            "workflow_state": json.dumps({})
        }
    })
    assert wf.get_progress_percentage() == 50, "50% at second step"
    
    # Move to last step (4/4 = 100%)
    wf.m_current_step_index = 3
    assert wf.is_last_step(), "Should be last step"
    assert wf.get_progress_percentage() == 100, "100% at last step"


def test_conditional_step_visibility():
    """Test that conditional steps are properly hidden/shown"""
    def is_visible(data):
        return data.get("show_extra", False)
    
    wf = Workflow("Conditional Test")
    wf.add_step(WorkflowStep(name="Step1", display_func=simple_display))
    wf.add_step(WorkflowStep(
        name="ConditionalStep",
        display_func=simple_display,
        condition_func=is_visible  # Correct parameter name
    ))
    wf.add_step(WorkflowStep(name="Step3", display_func=simple_display))
    
    wf.prepare_workflow(None)
    
    # Initially, conditional step should be hidden
    visible = wf._compute_visible_steps()
    assert len(visible) == 2, "Should have 2 visible steps (conditional hidden)"
    assert 1 not in visible, "Step index 1 should be hidden"
    
    # Enable the condition
    wf.m_workflow_data["show_extra"] = True
    visible = wf._compute_visible_steps()
    assert len(visible) == 3, "Should have 3 visible steps"
    assert 1 in visible, "Step index 1 should now be visible"


# ===== Thread-Related Tests =====

def test_thread_completion_and_advancement():
    """
    Test that workflow properly advances after thread completion (thread_fix)
    
    Bug fixed: Thread completing would loop back to progress display
    instead of advancing to next step.
    """
    wf = Workflow("Thread Test")
    
    def create_thread(workflow, data):
        return QuickThread()
    
    # Step 1: Normal step
    wf.add_step(WorkflowStep(name="Step1", display_func=simple_display))
    
    # Step 2: Threaded step
    wf.add_step(WorkflowStep(
        name="Threaded",
        display_func=simple_display,
        action_func=create_thread,
        action_type=StepActionType.THREADED
    ))
    
    # Step 3: Final step
    wf.add_step(WorkflowStep(name="Complete", display_func=simple_display))
    
    # Initialize
    wf.prepare_workflow(None)
    
    # Navigate to threaded step
    wf.prepare_workflow({
        "Thread Test": {
            "workflow_next": True,
            "current_step": "0",
            "workflow_state": json.dumps({})
        }
    })
    assert wf.m_current_step_index == 1, "Should be at threaded step"
    
    # Click Next - should start thread and stay on step 1
    wf.prepare_workflow({
        "Thread Test": {
            "workflow_next": True,
            "current_step": "1",
            "workflow_state": json.dumps(wf.m_workflow_data)
        }
    })
    assert wf.m_current_step_index == 1, "Should stay on step 1 while thread runs"
    assert wf.m_active_thread is not None, "Thread should be created"
    assert wf.m_active_thread.is_running(), "Thread should be running"
    
    # Wait for thread to complete
    time.sleep(0.15)
    assert not wf.m_active_thread.is_running(), "Thread should complete"
    
    # Click Next - should NOW advance to step 2
    wf.prepare_workflow({
        "Thread Test": {
            "workflow_next": True,
            "current_step": "1",
            "workflow_state": json.dumps(wf.m_workflow_data)
        }
    })
    assert wf.m_current_step_index == 2, "Should advance to Complete step"
    assert wf.m_active_thread is None, "Thread should be cleared"


def test_thread_flag_persistence():
    """Test that thread flags are properly set and cleared"""
    wf = Workflow("Flag Test")
    
    def create_thread(workflow, data):
        return QuickThread()
    
    wf.add_step(WorkflowStep(
        name="Threaded",
        display_func=simple_display,
        action_func=create_thread,
        action_type=StepActionType.THREADED
    ))
    wf.add_step(WorkflowStep(name="Next", display_func=simple_display))
    
    wf.prepare_workflow(None)
    
    # Start thread
    wf.prepare_workflow({
        "Flag Test": {
            "workflow_next": True,
            "current_step": "0",
            "workflow_state": json.dumps({})
        }
    })
    
    # Check flag is set
    assert "_thread_on_step_0" in wf.m_workflow_data, "Thread flag should be set"
    assert wf.m_workflow_data["_thread_on_step_0"], "Flag should be True"
    
    # Wait and advance
    time.sleep(0.15)
    wf.prepare_workflow({
        "Flag Test": {
            "workflow_next": True,
            "current_step": "0",
            "workflow_state": json.dumps(wf.m_workflow_data)
        }
    })
    
    # Check flag is cleared
    assert "_thread_on_step_0" not in wf.m_workflow_data, "Thread flag should be cleared"


# ===== Redo Functionality Tests =====

def test_builtin_redo_button():
    """
    Test built-in allow_redo parameter creates Redo Last Step button
    """
    wf = Workflow("Redo Test")
    
    def create_thread(workflow, data):
        item_id = workflow.m_workflow_data.get("item_id", "default")
        return QuickThread(item_id)
    
    wf.add_step(WorkflowStep(
        name="Input",
        display_func=input_display,
        action_func=create_thread,
        action_type=StepActionType.THREADED
    ))
    wf.add_step(WorkflowStep(
        name="Complete",
        display_func=simple_display,
        allow_redo=True  # Enable redo button
    ))
    
    wf.prepare_workflow(None)
    
    # Submit first item
    wf.prepare_workflow({
        "Redo Test": {
            "test_input": "ITEM-001",
            "workflow_next": True,
            "current_step": "0",
            "workflow_state": json.dumps({})
        }
    })
    assert wf.m_active_thread is not None, "Thread should start"
    
    # Wait and advance
    time.sleep(0.15)
    wf.prepare_workflow({
        "Redo Test": {
            "workflow_next": True,
            "current_step": "0",
            "workflow_state": json.dumps(wf.m_workflow_data)
        }
    })
    assert wf.m_current_step_index == 1, "Should be at Complete"
    
    # Click Redo Last Step
    wf.prepare_workflow({
        "Redo Test": {
            "workflow_redo_last": True,
            "current_step": "1",
            "workflow_state": json.dumps(wf.m_workflow_data)
        }
    })
    assert wf.m_current_step_index == 0, "Should go back to Input step"


def test_redo_preserves_data():
    """Test that redo preserves workflow data"""
    wf = Workflow("Redo Data Test")
    wf.add_step(WorkflowStep(name="Step1", display_func=input_display))
    wf.add_step(WorkflowStep(
        name="Step2",
        display_func=simple_display,
        allow_redo=True
    ))
    
    wf.prepare_workflow(None)
    
    # Submit data
    wf.prepare_workflow({
        "Redo Data Test": {
            "test_input": "Original Value",
            "workflow_next": True,
            "current_step": "0",
            "workflow_state": json.dumps({})
        }
    })
    assert wf.m_workflow_data["test_input"] == "Original Value"
    
    # Redo
    wf.prepare_workflow({
        "Redo Data Test": {
            "workflow_redo_last": True,
            "current_step": "1",
            "workflow_state": json.dumps(wf.m_workflow_data)
        }
    })
    
    # Data should still be there
    assert wf.m_workflow_data["test_input"] == "Original Value", "Data should be preserved"


def test_redo_auto_execution():
    """
    Test that redo automatically executes action for batch operations
    
    Enhancement: When clicking Redo Last Step with new data, the action
    (thread) should start automatically instead of showing the form again.
    """
    wf = Workflow("Auto Exec Test")
    thread_count = {"count": 0}  # Use dict to avoid closure issues
    
    def create_thread(workflow, data):
        thread_count["count"] += 1
        item_id = workflow.m_workflow_data.get("test_input", "default")
        return QuickThread(item_id)
    
    wf.add_step(WorkflowStep(
        name="Scan",
        display_func=input_display,
        action_func=create_thread,
        action_type=StepActionType.THREADED
    ))
    wf.add_step(WorkflowStep(
        name="Complete",
        display_func=input_display,  # Has input for next scan
        allow_redo=True
    ))
    
    wf.prepare_workflow(None)
    
    # First scan
    wf.prepare_workflow({
        "Auto Exec Test": {
            "test_input": "ITEM-001",
            "workflow_next": True,
            "current_step": "0",
            "workflow_state": json.dumps({})
        }
    })
    assert thread_count["count"] == 1, "First thread created"
    
    # Wait and advance
    time.sleep(0.15)
    wf.prepare_workflow({
        "Auto Exec Test": {
            "workflow_next": True,
            "current_step": "0",
            "workflow_state": json.dumps(wf.m_workflow_data)
        }
    })
    assert wf.m_current_step_index == 1, "At Complete"
    
    # Enter new data and click Redo Last Step
    wf.prepare_workflow({
        "Auto Exec Test": {
            "test_input": "ITEM-002",  # New data
            "workflow_redo_last": True,
            "current_step": "1",
            "workflow_state": json.dumps(wf.m_workflow_data)
        }
    })
    
    # KEY ASSERTION: Thread should auto-start
    assert wf.m_current_step_index == 0, "Back to Scan step"
    assert wf.m_active_thread is not None, "Thread should auto-start"
    assert thread_count["count"] == 2, "Second thread created automatically"
    assert wf.m_workflow_data["test_input"] == "ITEM-002", "New data saved"


def test_redo_without_action_func():
    """Test redo works normally for steps without action_func"""
    wf = Workflow("Simple Redo")
    wf.add_step(WorkflowStep(name="Step1", display_func=simple_display))
    wf.add_step(WorkflowStep(
        name="Step2",
        display_func=simple_display,
        allow_redo=True
    ))
    
    wf.prepare_workflow(None)
    wf.prepare_workflow({
        "Simple Redo": {
            "workflow_next": True,
            "current_step": "0",
            "workflow_state": json.dumps({})
        }
    })
    assert wf.m_current_step_index == 1
    
    # Redo
    wf.prepare_workflow({
        "Simple Redo": {
            "workflow_redo_last": True,
            "current_step": "1",
            "workflow_state": json.dumps(wf.m_workflow_data)
        }
    })
    
    assert wf.m_current_step_index == 0, "Should go back"
    assert wf.m_active_thread is None, "No thread created"


# ===== Batch Scanning Pattern Tests =====

def test_batch_scanning_continuous_loop():
    """
    Test continuous scanning loop pattern using same field names
    
    Pattern: Scan → Process → Complete (with scan input) → Redo → Scan → ...
    The Complete step has the same field name as Scan, allowing values to overwrite.
    """
    wf = Workflow("Batch Scan")
    
    def create_thread(workflow, data):
        serial = workflow.m_workflow_data.get("serial_number", "?")
        return QuickThread(serial)
    
    def display_scan(disp, data):
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        serial = data.get("serial_number", "")
        disp.add_display_item(
            displayer.DisplayerItemInputString("serial_number", None, serial),
            0
        )
        return disp
    
    def display_complete(disp, data):
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        # Show what was scanned
        serial = data.get("serial_number", "?")
        disp.add_display_item(displayer.DisplayerItemText(f"Registered: {serial}"), 0)
        # IMPORTANT: Same field name for next scan
        disp.add_display_item(
            displayer.DisplayerItemInputString("serial_number", None, ""),
            0
        )
        return disp
    
    wf.add_step(WorkflowStep(
        name="Scan",
        display_func=display_scan,
        action_func=create_thread,
        action_type=StepActionType.THREADED
    ))
    wf.add_step(WorkflowStep(
        name="Complete",
        display_func=display_complete,
        allow_redo=True
    ))
    
    wf.prepare_workflow(None)
    
    # Scan first item
    wf.prepare_workflow({
        "Batch Scan": {
            "serial_number": "ITEM-001",
            "workflow_next": True,
            "current_step": "0",
            "workflow_state": json.dumps({})
        }
    })
    time.sleep(0.15)
    wf.prepare_workflow({
        "Batch Scan": {
            "workflow_next": True,
            "current_step": "0",
            "workflow_state": json.dumps(wf.m_workflow_data)
        }
    })
    assert wf.m_current_step_index == 1
    assert wf.m_workflow_data["serial_number"] == "ITEM-001"
    
    # Scan second item (overwrites first)
    wf.prepare_workflow({
        "Batch Scan": {
            "serial_number": "ITEM-002",  # Same field name
            "workflow_redo_last": True,
            "current_step": "1",
            "workflow_state": json.dumps(wf.m_workflow_data)
        }
    })
    assert wf.m_workflow_data["serial_number"] == "ITEM-002", "New value overwrites old"
    
    # Thread should auto-start
    assert wf.m_active_thread is not None
    time.sleep(0.15)
    wf.prepare_workflow({
        "Batch Scan": {
            "workflow_next": True,
            "current_step": "0",
            "workflow_state": json.dumps(wf.m_workflow_data)
        }
    })
    
    # Scan third item
    wf.prepare_workflow({
        "Batch Scan": {
            "serial_number": "ITEM-003",
            "workflow_redo_last": True,
            "current_step": "1",
            "workflow_state": json.dumps(wf.m_workflow_data)
        }
    })
    assert wf.m_workflow_data["serial_number"] == "ITEM-003", "Third value overwrites"
    

# ===== Action Execution Tests =====

def test_action_execution():
    """Test that action functions are properly called"""
    execution_log = []
    
    def action1(workflow, data):
        execution_log.append("action1")
    
    def action2(workflow, data):
        execution_log.append("action2")
    
    wf = Workflow("Action Test")
    wf.add_step(WorkflowStep(
        name="Step1",
        display_func=simple_display,
        action_func=action1
    ))
    wf.add_step(WorkflowStep(
        name="Step2",
        display_func=simple_display,
        action_func=action2
    ))
    
    wf.prepare_workflow(None)
    
    # Move to step 2 - should execute action1
    wf.prepare_workflow({
        "Action Test": {
            "workflow_next": True,
            "current_step": "0",
            "workflow_state": json.dumps({})
        }
    })
    
    assert "action1" in execution_log, "Action1 should be executed"
    assert wf.m_current_step_index == 1


# ===== Edge Cases and Error Handling =====

def test_empty_workflow():
    """Test workflow with no steps"""
    wf = Workflow("Empty")
    wf.prepare_workflow(None)
    assert len(wf.m_steps) == 0
    assert wf.get_current_step() is None


def test_single_step_workflow():
    """Test workflow with only one step"""
    wf = Workflow("Single")
    wf.add_step(WorkflowStep(name="Only", display_func=simple_display))
    
    wf.prepare_workflow(None)
    assert wf.is_first_step()
    assert wf.is_last_step()
    assert wf.get_progress_percentage() == 100


def test_workflow_state_serialization():
    """Test that workflow state properly serializes and deserializes"""
    wf = Workflow("Serialize Test")
    wf.add_step(WorkflowStep(name="Step1", display_func=input_display))
    wf.add_step(WorkflowStep(name="Step2", display_func=simple_display))
    
    wf.prepare_workflow(None)
    
    # Add some data
    wf.prepare_workflow({
        "Serialize Test": {
            "test_input": "Test Value",
            "workflow_next": True,
            "current_step": "0",
            "workflow_state": json.dumps({})
        }
    })
    
    # Serialize state
    state_json = json.dumps(wf.m_workflow_data)
    
    # Create new workflow and restore state
    wf2 = Workflow("Serialize Test")
    wf2.add_step(WorkflowStep(name="Step1", display_func=input_display))
    wf2.add_step(WorkflowStep(name="Step2", display_func=simple_display))
    
    wf2.prepare_workflow({
        "Serialize Test": {
            "current_step": "1",
            "workflow_state": state_json
        }
    })
    
    assert wf2.m_workflow_data["test_input"] == "Test Value", "State should be restored"
    assert wf2.m_current_step_index == 1, "Step should be restored"


# Run all tests if executed directly
if __name__ == "__main__":
    print("\n" + "="*70)
    print("Running Comprehensive Workflow Tests")
    print("="*70 + "\n")
    
    test_functions = [
        ("Basic Initialization", test_workflow_initialization),
        ("Navigation", test_workflow_navigation),
        ("Data Persistence", test_workflow_data_persistence),
        ("Progress Tracking", test_workflow_progress_tracking),
        ("Conditional Visibility", test_conditional_step_visibility),
        ("Thread Completion", test_thread_completion_and_advancement),
        ("Thread Flags", test_thread_flag_persistence),
        ("Built-in Redo", test_builtin_redo_button),
        ("Redo Data Preservation", test_redo_preserves_data),
        ("Redo Auto-Execution", test_redo_auto_execution),
        ("Redo Without Action", test_redo_without_action_func),
        ("Batch Scanning Loop", test_batch_scanning_continuous_loop),
        ("Action Execution", test_action_execution),
        ("Empty Workflow", test_empty_workflow),
        ("Single Step", test_single_step_workflow),
        ("State Serialization", test_workflow_state_serialization),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in test_functions:
        try:
            test_func()
            print(f"✓ {name}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {name}: ERROR - {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70)
    
    if failed == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ {failed} test(s) failed")
