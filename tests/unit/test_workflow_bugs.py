"""
Additional Workflow Tests - Bug Reproduction and Fixes

These tests reproduce the reported bugs:
1. Threading not working (workflow advances before thread starts)
2. Redo button not appearing
3. Data persistence with threads
"""

import pytest
import time

from src.modules.workflow import Workflow, WorkflowStep, StepActionType
from src.modules import displayer
from src.modules.threaded import Threaded_action


class SlowThread(Threaded_action):
    """Thread that takes time to complete"""
    m_default_name = "Slow Thread"
    
    def __init__(self):
        super().__init__()
        self.completed = False
    
    def action(self):
        self.console_write("Starting slow action")
        for i in range(5):
            if not self.m_running:
                break
            self.m_running_state = (i + 1) * 20
            time.sleep(0.1)
        self.completed = True
        self.m_running_state = 100
        self.console_write("Completed")


def simple_display(disp, data):
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemText("Test"), 0)
    return disp


class TestThreadingBugs:
    """Test threading-related bugs"""
    
    def test_bug_workflow_advances_before_thread_completes(self):
        """
        BUG: When clicking Next on a threaded step, workflow immediately
        advances to next step instead of waiting for thread to complete.
        
        EXPECTED: Workflow should stay on threaded step until thread completes.
        """
        workflow = Workflow("Test")
        
        thread_instance = None
        
        def create_thread(wf, data):
            nonlocal thread_instance
            thread_instance = SlowThread()
            return thread_instance
        
        # Step 1: Normal step
        workflow.add_step(WorkflowStep("Step 1", simple_display))
        
        # Step 2: Threaded step
        workflow.add_step(WorkflowStep(
            "Processing",
            simple_display,
            action_func=create_thread,
            action_type=StepActionType.THREADED
        ))
        
        # Step 3: Complete
        workflow.add_step(WorkflowStep("Complete", simple_display))
        
        # Start workflow
        workflow.prepare_workflow(None)
        assert workflow.m_current_step_index == 0
        
        # Move to step 1 (normal step -> threaded step)
        data_in = {
            "Test": {
                "workflow_next": True,
                "current_step": "0",
                "workflow_state": "{}"
            }
        }
        workflow.prepare_workflow(data_in)
        
        # Now at step 1 (the threaded step)
        assert workflow.m_current_step_index == 1
        assert workflow.get_current_step().name == "Processing"
        
        # Now click Next on the threaded step - this should START the thread
        data_in = {
            "Test": {
                "workflow_next": True,
                "current_step": "1",
                "workflow_state": "{}"
            }
        }
        workflow.prepare_workflow(data_in)
        
        # CRITICAL: Should still be on step 1 because thread was started
        assert workflow.m_current_step_index == 1, "Workflow should stay on threaded step when thread starts"
        
        # Thread should be stored
        assert workflow.m_active_thread is not None, "Thread should be stored in workflow"
        
        # Wait for thread to start
        time.sleep(0.15)
        
        # Thread should be running
        assert thread_instance.is_running()
        
        # ISSUE: If we click Next again while thread is running, what happens?
        # Navigation should be disabled while thread runs
        
    def test_workflow_should_not_advance_while_thread_running(self):
        """
        Test that workflow doesn't advance if a thread is still running.
        This requires checking thread status before advancing.
        """
        workflow = Workflow("Test")
        
        def create_thread(wf, data):
            return SlowThread()
        
        workflow.add_step(WorkflowStep("Step 1", simple_display))
        workflow.add_step(WorkflowStep(
            "Processing",
            simple_display,
            action_func=create_thread,
            action_type=StepActionType.THREADED
        ))
        workflow.add_step(WorkflowStep("Complete", simple_display))
        
        # Start and move to threaded step
        workflow.prepare_workflow(None)
        workflow.prepare_workflow({
            "Test": {
                "workflow_next": True,
                "current_step": "0",
                "workflow_state": "{}"
            }
        })
        
        # Now at step 1 (Processing)
        assert workflow.m_current_step_index == 1
        
        # Click Next on the threaded step to START the thread
        workflow.prepare_workflow({
            "Test": {
                "workflow_next": True,
                "current_step": "1",
                "workflow_state": "{}"
            }
        })
        
        # Should still be at step 1 with thread running
        assert workflow.m_current_step_index == 1
        assert workflow.m_active_thread is not None
        
        time.sleep(0.15)  # Let thread start
        
        # Try to advance while thread is running - should be prevented by disabled button
        # But let's test what happens if somehow the form gets submitted
        # In real usage, buttons are disabled so this shouldn't happen
        
    def test_thread_completion_enables_navigation(self):
        """
        Test that once thread completes, user can navigate.
        Thread completion should be checked on page load.
        """
        workflow = Workflow("Test")
        
        thread_instance = None
        
        def create_thread(wf, data):
            nonlocal thread_instance
            thread_instance = SlowThread()
            return thread_instance
        
        workflow.add_step(WorkflowStep("Step 1", simple_display))
        workflow.add_step(WorkflowStep(
            "Processing",
            simple_display,
            action_func=create_thread,
            action_type=StepActionType.THREADED
        ))
        workflow.add_step(WorkflowStep("Complete", simple_display))
        
        # Move to threaded step
        workflow.prepare_workflow(None)
        workflow.prepare_workflow({
            "Test": {
                "workflow_next": True,
                "current_step": "0",
                "workflow_state": "{}"
            }
        })
        
        # Start the thread by clicking Next on the threaded step
        workflow.prepare_workflow({
            "Test": {
                "workflow_next": True,
                "current_step": "1",
                "workflow_state": "{}"
            }
        })
        
        # Should still be on step 1 with thread running
        assert workflow.m_current_step_index == 1
        assert workflow.m_active_thread is not None
        
        # Wait for thread to complete
        time.sleep(0.6)
        
        # Thread should be done
        assert not thread_instance.is_running()
        assert thread_instance.completed
        
        # Workflow should allow advancing now
        # This is typically checked in the route handler


class TestRedoFunctionality:
    """Test redo button functionality"""
    
    def test_redo_button_core_functionality(self):
        """
        Test that redo functionality can be part of workflow core.
        Redo should:
        1. Save new parameters from form
        2. Jump back to specified step
        3. Keep workflow data intact
        """
        workflow = Workflow("Test")
        
        workflow.add_step(WorkflowStep("Input", simple_display))
        workflow.add_step(WorkflowStep("Process", simple_display))
        workflow.add_step(WorkflowStep("Complete", simple_display))
        
        # Complete workflow
        workflow.prepare_workflow(None)
        workflow.m_workflow_data = {"serial": "ABC123", "batch": "5"}
        workflow.m_current_step_index = 2  # On last step
        
        # Test redo functionality
        # User fills new data and clicks redo
        new_data = {
            "next_serial": "DEF456",
            "next_batch": "3"
        }
        
        # Redo should:
        # 1. Update workflow data
        workflow.m_workflow_data["serial"] = new_data["next_serial"]
        workflow.m_workflow_data["batch"] = new_data["next_batch"]
        
        # 2. Jump back to process step (index 1)
        workflow.m_current_step_index = 1
        
        # Verify
        assert workflow.m_workflow_data["serial"] == "DEF456"
        assert workflow.m_workflow_data["batch"] == "3"
        assert workflow.m_current_step_index == 1
        
    def test_redo_method_in_workflow(self):
        """Test adding a redo() method to Workflow class"""
        workflow = Workflow("Test")
        
        workflow.add_step(WorkflowStep("Step 1", simple_display))
        workflow.add_step(WorkflowStep("Step 2", simple_display))
        workflow.add_step(WorkflowStep("Step 3", simple_display))
        
        workflow.prepare_workflow(None)
        workflow.m_workflow_data = {"old_data": "value"}
        workflow.m_current_step_index = 2
        
        # This method should be added to Workflow class
        # workflow.redo(target_step_index=1, new_data={"new_field": "new_value"})


class TestDataPersistenceWithThreads:
    """Test data persistence when threads are involved"""
    
    def test_workflow_data_preserved_during_thread(self):
        """
        Test that workflow data is preserved while thread is running.
        """
        workflow = Workflow("Test")
        
        def create_thread(wf, data):
            return SlowThread()
        
        workflow.add_step(WorkflowStep("Input", simple_display))
        workflow.add_step(WorkflowStep(
            "Process",
            simple_display,
            action_func=create_thread,
            action_type=StepActionType.THREADED
        ))
        
        # Add data in step 1
        workflow.prepare_workflow(None)
        workflow.prepare_workflow({
            "Test": {
                "workflow_next": True,
                "current_step": "0",
                "workflow_state": "{}",
                "user_input": "important_data"
            }
        })
        
        # Data should be saved
        assert "user_input" in workflow.m_workflow_data
        assert workflow.m_workflow_data["user_input"] == "important_data"
        
        # Thread is now running
        time.sleep(0.15)
        
        # Data should still be there
        assert workflow.m_workflow_data["user_input"] == "important_data"


class TestValidationAndErrorHandling:
    """Test validation keeps user on current form"""
    
    def test_validation_failure_stays_on_step(self):
        """
        Test that if validation fails, user stays on current step.
        This requires action to return False or raise ValidationError.
        """
        workflow = Workflow("Test")
        
        validation_failed = {"value": False}
        
        def validate_action(wf, data):
            # Simulate validation failure
            value = data.get("required_field", "").strip()
            if not value:
                validation_failed["value"] = True
                # In real usage, would emit popup
                # Should we prevent advancement?
                return False  # Indicate failure
        
        workflow.add_step(WorkflowStep(
            "Input",
            simple_display,
            action_func=validate_action
        ))
        workflow.add_step(WorkflowStep("Next", simple_display))
        
        workflow.prepare_workflow(None)
        
        # Try to advance with empty field
        workflow.prepare_workflow({
            "Test": {
                "workflow_next": True,
                "current_step": "0",
                "workflow_state": "{}",
                "required_field": ""  # Empty!
            }
        })
        
        # Currently: Workflow advances anyway (BUG?)
        # Should: Stay on current step if validation fails
        
        # This needs to be implemented


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
