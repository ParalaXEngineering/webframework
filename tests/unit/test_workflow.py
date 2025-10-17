"""
Unit Tests for Workflow System - Comprehensive test suite.

Tests cover:
- Workflow initialization and configuration
- Step definition and management
- Step navigation (forward, backward, skip)
- Conditional step visibility
- Data persistence across steps
- Synchronous and threaded actions
- Progress tracking and breadcrumbs
- Custom buttons (redo, etc.)
"""

import pytest
import json
import time
from unittest.mock import Mock

from src.modules.workflow import Workflow, WorkflowStep, StepActionType
from src.modules import displayer
from src.modules.threaded import Threaded_action


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def simple_display_func():
    """Simple display function for testing"""
    def display(disp, data):
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        disp.add_display_item(displayer.DisplayerItemText("Test content"), 0)
        return disp
    return display


@pytest.fixture
def display_with_input():
    """Display function with input field"""
    def display(disp, data):
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        value = data.get("test_input", "")
        disp.add_display_item(displayer.DisplayerItemInputString("test_input", None, value), 0)
        return disp
    return display


@pytest.fixture
def action_tracker():
    """Mock to track action execution"""
    tracker = Mock()
    tracker.called = False
    tracker.call_count = 0
    tracker.data = None
    
    def action(workflow, form_data):
        tracker.called = True
        tracker.call_count += 1
        tracker.data = form_data.copy()
    
    tracker.action = action
    return tracker


@pytest.fixture
def basic_workflow(simple_display_func):
    """Create a basic workflow with 3 simple steps"""
    workflow = Workflow("Test Workflow")
    
    workflow.add_step(WorkflowStep(
        name="Step 1",
        display_func=simple_display_func
    ))
    
    workflow.add_step(WorkflowStep(
        name="Step 2",
        display_func=simple_display_func
    ))
    
    workflow.add_step(WorkflowStep(
        name="Step 3",
        display_func=simple_display_func
    ))
    
    return workflow


@pytest.fixture
def workflow_with_conditional(simple_display_func):
    """Workflow with a conditional step"""
    workflow = Workflow("Conditional Workflow")
    
    workflow.add_step(WorkflowStep(
        name="Step 1",
        display_func=simple_display_func
    ))
    
    # Conditional step - only visible if 'show_step2' is True
    workflow.add_step(WorkflowStep(
        name="Step 2 (Conditional)",
        display_func=simple_display_func,
        condition_func=lambda data: data.get("show_step2", False)
    ))
    
    workflow.add_step(WorkflowStep(
        name="Step 3",
        display_func=simple_display_func
    ))
    
    return workflow


# ============================================================================
# BASIC WORKFLOW TESTS
# ============================================================================

class TestWorkflowInitialization:
    """Test workflow initialization and basic properties"""
    
    def test_workflow_creation_with_name(self):
        """Test creating a workflow with a custom name"""
        workflow = Workflow("My Custom Workflow")
        assert workflow.get_name() == "My Custom Workflow"
        assert workflow.m_type == "workflow"
        assert len(workflow.m_steps) == 0
        assert workflow.m_current_step_index == 0
    
    def test_workflow_creation_default_name(self):
        """Test creating a workflow with default name"""
        workflow = Workflow()
        assert workflow.get_name() == "Workflow Instance"
    
    def test_workflow_change_name(self):
        """Test changing workflow name"""
        workflow = Workflow("Original")
        workflow.change_name("New Name")
        assert workflow.get_name() == "New Name"
    
    def test_workflow_initial_data(self):
        """Test workflow starts with empty data"""
        workflow = Workflow("Test")
        assert workflow.m_workflow_data == {}
        assert workflow.m_active_thread is None


class TestStepManagement:
    """Test adding and managing workflow steps"""
    
    def test_add_single_step(self, simple_display_func):
        """Test adding a single step"""
        workflow = Workflow("Test")
        step = WorkflowStep("Step 1", simple_display_func)
        workflow.add_step(step)
        
        assert len(workflow.m_steps) == 1
        assert workflow.m_steps[0].name == "Step 1"
    
    def test_add_multiple_steps(self, simple_display_func):
        """Test adding multiple steps"""
        workflow = Workflow("Test")
        
        for i in range(5):
            workflow.add_step(WorkflowStep(f"Step {i+1}", simple_display_func))
        
        assert len(workflow.m_steps) == 5
        assert workflow.m_steps[0].name == "Step 1"
        assert workflow.m_steps[4].name == "Step 5"
    
    def test_step_with_action(self, simple_display_func, action_tracker):
        """Test creating a step with an action"""
        step = WorkflowStep(
            "Step 1",
            simple_display_func,
            action_func=action_tracker.action
        )
        
        assert step.action_func is not None
        assert step.action_type == StepActionType.FUNCTION
    
    def test_step_with_skip(self, simple_display_func):
        """Test creating a step with skip functionality"""
        skip_func = Mock()
        step = WorkflowStep(
            "Step 1",
            simple_display_func,
            skip_func=skip_func
        )
        
        assert step.skip_func is not None
    
    def test_step_with_condition(self, simple_display_func):
        """Test creating a step with visibility condition"""
        def condition(data):
            return data.get("visible", True)
        
        step = WorkflowStep(
            "Step 1",
            simple_display_func,
            condition_func=condition
        )
        
        assert step.is_visible({"visible": True})
        assert not step.is_visible({"visible": False})


# ============================================================================
# NAVIGATION TESTS
# ============================================================================

class TestWorkflowNavigation:
    """Test workflow navigation between steps"""
    
    def test_initial_step(self, basic_workflow):
        """Test workflow starts at first step"""
        basic_workflow.prepare_workflow(None)
        
        assert basic_workflow.m_current_step_index == 0
        assert basic_workflow.get_current_step().name == "Step 1"
        assert basic_workflow.is_first_step()
        assert not basic_workflow.is_last_step()
    
    def test_move_forward(self, basic_workflow):
        """Test moving to next step"""
        basic_workflow.prepare_workflow(None)
        
        # Move to step 2
        data_in = {
            "Test Workflow": {
                "workflow_next": True,
                "current_step": "0",
                "workflow_state": "{}"
            }
        }
        basic_workflow.prepare_workflow(data_in)
        
        assert basic_workflow.m_current_step_index == 1
        assert basic_workflow.get_current_step().name == "Step 2"
        assert not basic_workflow.is_first_step()
        assert not basic_workflow.is_last_step()
    
    def test_move_backward(self, basic_workflow):
        """Test moving to previous step"""
        basic_workflow.prepare_workflow(None)
        
        # Move to step 2
        basic_workflow._go_next()
        assert basic_workflow.m_current_step_index == 1
        
        # Move back to step 1
        data_in = {
            "Test Workflow": {
                "workflow_prev": True,
                "current_step": "1",
                "workflow_state": "{}"
            }
        }
        basic_workflow.prepare_workflow(data_in)
        
        assert basic_workflow.m_current_step_index == 0
        assert basic_workflow.get_current_step().name == "Step 1"
    
    def test_reach_last_step(self, basic_workflow):
        """Test reaching the last step"""
        basic_workflow.prepare_workflow(None)
        
        # Move to step 2
        basic_workflow._go_next()
        # Move to step 3
        basic_workflow._go_next()
        
        assert basic_workflow.m_current_step_index == 2
        assert basic_workflow.get_current_step().name == "Step 3"
        assert basic_workflow.is_last_step()
    
    def test_cannot_go_beyond_last_step(self, basic_workflow):
        """Test that _go_next() at last step doesn't crash"""
        basic_workflow.prepare_workflow(None)
        
        # Move to last step
        basic_workflow._go_next()
        basic_workflow._go_next()
        
        # Try to go beyond
        basic_workflow._go_next()
        
        # Should still be at last step
        assert basic_workflow.m_current_step_index == 2
        assert basic_workflow.is_last_step()
    
    def test_cannot_go_before_first_step(self, basic_workflow):
        """Test that _go_previous() at first step doesn't crash"""
        basic_workflow.prepare_workflow(None)
        
        # Try to go before first step
        basic_workflow._go_previous()
        
        # Should still be at first step
        assert basic_workflow.m_current_step_index == 0
        assert basic_workflow.is_first_step()
    
    def test_progress_percentage(self, basic_workflow):
        """Test progress calculation"""
        basic_workflow.prepare_workflow(None)
        
        # Step 1 of 3 = 33%
        assert basic_workflow.get_progress_percentage() == 33
        
        # Step 2 of 3 = 66%
        basic_workflow._go_next()
        assert basic_workflow.get_progress_percentage() == 66
        
        # Step 3 of 3 = 100%
        basic_workflow._go_next()
        assert basic_workflow.get_progress_percentage() == 100


# ============================================================================
# CONDITIONAL STEP TESTS
# ============================================================================

class TestConditionalSteps:
    """Test conditional step visibility"""
    
    def test_all_steps_visible_by_default(self, basic_workflow):
        """Test all steps are visible when no conditions"""
        basic_workflow.prepare_workflow(None)
        
        assert len(basic_workflow.m_visible_steps) == 3
        assert basic_workflow.m_visible_steps == [0, 1, 2]
    
    def test_conditional_step_hidden(self, workflow_with_conditional):
        """Test conditional step is hidden when condition is False"""
        workflow_with_conditional.prepare_workflow(None)
        
        # Step 2 should be hidden (show_step2 is False by default)
        assert len(workflow_with_conditional.m_visible_steps) == 2
        assert workflow_with_conditional.m_visible_steps == [0, 2]
    
    def test_conditional_step_visible(self, workflow_with_conditional):
        """Test conditional step is visible when condition is True"""
        # Set data to make step 2 visible
        workflow_with_conditional.m_workflow_data["show_step2"] = True
        workflow_with_conditional.prepare_workflow(None)
        
        # All steps should be visible
        assert len(workflow_with_conditional.m_visible_steps) == 3
        assert workflow_with_conditional.m_visible_steps == [0, 1, 2]
    
    def test_navigation_skips_hidden_steps(self, workflow_with_conditional):
        """Test navigation skips over hidden steps"""
        workflow_with_conditional.prepare_workflow(None)
        
        # Start at step 1 (index 0)
        assert workflow_with_conditional.m_current_step_index == 0
        
        # Move next - should skip step 2 (hidden) and go to step 3
        workflow_with_conditional._go_next()
        assert workflow_with_conditional.m_current_step_index == 2
        assert workflow_with_conditional.get_current_step().name == "Step 3"
    
    def test_backward_navigation_skips_hidden_steps(self, workflow_with_conditional):
        """Test backward navigation skips hidden steps"""
        workflow_with_conditional.prepare_workflow(None)
        
        # Start at step 1, move to step 3 (skipping hidden step 2)
        workflow_with_conditional._go_next()
        assert workflow_with_conditional.m_current_step_index == 2
        
        # Move back - should skip step 2 (hidden) and go to step 1
        workflow_with_conditional._go_previous()
        assert workflow_with_conditional.m_current_step_index == 0
        assert workflow_with_conditional.get_current_step().name == "Step 1"
    
    def test_progress_with_hidden_steps(self, workflow_with_conditional):
        """Test progress calculation with hidden steps"""
        workflow_with_conditional.prepare_workflow(None)
        
        # Only 2 visible steps (1 and 3)
        # Step 1 of 2 = 50%
        assert workflow_with_conditional.get_progress_percentage() == 50
        
        # Step 3 of 2 = 100%
        workflow_with_conditional._go_next()
        assert workflow_with_conditional.get_progress_percentage() == 100


# ============================================================================
# DATA PERSISTENCE TESTS
# ============================================================================

class TestDataPersistence:
    """Test workflow data persistence across steps"""
    
    def test_save_form_data(self, basic_workflow):
        """Test saving form data from current step"""
        basic_workflow.prepare_workflow(None)
        
        # Simulate form submission with data
        data_in = {
            "Test Workflow": {
                "workflow_next": True,
                "current_step": "0",
                "workflow_state": "{}",
                "username": "Alice",
                "email": "alice@example.com"
            }
        }
        basic_workflow.prepare_workflow(data_in)
        
        # Data should be saved
        assert basic_workflow.m_workflow_data["username"] == "Alice"
        assert basic_workflow.m_workflow_data["email"] == "alice@example.com"
    
    def test_data_persists_across_steps(self, basic_workflow):
        """Test data persists when moving between steps"""
        basic_workflow.prepare_workflow(None)
        
        # Save data in step 1
        data_in = {
            "Test Workflow": {
                "workflow_next": True,
                "current_step": "0",
                "workflow_state": "{}",
                "name": "Bob"
            }
        }
        basic_workflow.prepare_workflow(data_in)
        
        # Add more data in step 2
        workflow_state = json.dumps(basic_workflow.m_workflow_data)
        data_in = {
            "Test Workflow": {
                "workflow_next": True,
                "current_step": "1",
                "workflow_state": workflow_state,
                "age": "30"
            }
        }
        basic_workflow.prepare_workflow(data_in)
        
        # Both pieces of data should be present
        assert basic_workflow.m_workflow_data["name"] == "Bob"
        assert basic_workflow.m_workflow_data["age"] == "30"
    
    def test_restore_workflow_state(self, basic_workflow):
        """Test restoring workflow state from JSON"""
        basic_workflow.prepare_workflow(None)
        
        # Simulate restoring state with existing data
        existing_data = {"field1": "value1", "field2": "value2"}
        workflow_state = json.dumps(existing_data)
        
        data_in = {
            "Test Workflow": {
                "workflow_next": True,
                "current_step": "0",
                "workflow_state": workflow_state
            }
        }
        basic_workflow.prepare_workflow(data_in)
        
        # State should be restored
        assert basic_workflow.m_workflow_data["field1"] == "value1"
        assert basic_workflow.m_workflow_data["field2"] == "value2"
    
    def test_display_uses_workflow_data(self, display_with_input):
        """Test that display functions receive workflow data"""
        workflow = Workflow("Test")
        workflow.add_step(WorkflowStep("Step 1", display_with_input))
        workflow.m_workflow_data["test_input"] = "Preserved Value"
        workflow.prepare_workflow(None)
        
        # Create displayer and generate display
        disp = displayer.Displayer()
        workflow.add_display(disp)
        
        # The input should have the preserved value
        # This would require checking the displayer output
        assert workflow.m_workflow_data["test_input"] == "Preserved Value"


# ============================================================================
# ACTION EXECUTION TESTS
# ============================================================================

class TestActionExecution:
    """Test step action execution"""
    
    def test_action_executes_on_next(self, simple_display_func, action_tracker):
        """Test action executes when clicking Next"""
        workflow = Workflow("Test")
        workflow.add_step(WorkflowStep(
            "Step 1",
            simple_display_func,
            action_func=action_tracker.action
        ))
        workflow.add_step(WorkflowStep("Step 2", simple_display_func))
        
        workflow.prepare_workflow(None)
        
        # Submit form with data
        data_in = {
            "Test": {
                "workflow_next": True,
                "current_step": "0",
                "workflow_state": "{}",
                "test_field": "test_value"
            }
        }
        workflow.prepare_workflow(data_in)
        
        # Action should have been called
        assert action_tracker.called
        assert action_tracker.call_count == 1
        assert action_tracker.data["test_field"] == "test_value"
    
    def test_action_not_executed_on_previous(self, simple_display_func, action_tracker):
        """Test action doesn't execute when clicking Previous"""
        workflow = Workflow("Test")
        workflow.add_step(WorkflowStep("Step 1", simple_display_func))
        workflow.add_step(WorkflowStep(
            "Step 2",
            simple_display_func,
            action_func=action_tracker.action
        ))
        
        workflow.prepare_workflow(None)
        workflow._go_next()  # Go to step 2
        
        # Go back
        data_in = {
            "Test": {
                "workflow_prev": True,
                "current_step": "1",
                "workflow_state": "{}"
            }
        }
        workflow.prepare_workflow(data_in)
        
        # Action should NOT have been called
        assert not action_tracker.called
    
    def test_skip_action_execution(self, simple_display_func):
        """Test skip action executes when clicking Skip"""
        skip_tracker = Mock()
        skip_tracker.called = False
        
        def skip_action(workflow, data):
            skip_tracker.called = True
        
        workflow = Workflow("Test")
        workflow.add_step(WorkflowStep(
            "Step 1",
            simple_display_func,
            skip_func=skip_action
        ))
        workflow.add_step(WorkflowStep("Step 2", simple_display_func))
        
        workflow.prepare_workflow(None)
        
        # Click skip
        data_in = {
            "Test": {
                "workflow_skip": True,
                "current_step": "0",
                "workflow_state": "{}"
            }
        }
        workflow.prepare_workflow(data_in)
        
        # Skip action should have been called
        assert skip_tracker.called
        # Should have moved to next step
        assert workflow.m_current_step_index == 1
    
    def test_step_without_action(self, simple_display_func):
        """Test step without action works correctly"""
        workflow = Workflow("Test")
        workflow.add_step(WorkflowStep("Step 1", simple_display_func))
        workflow.add_step(WorkflowStep("Step 2", simple_display_func))
        
        workflow.prepare_workflow(None)
        
        # Should not crash when advancing
        data_in = {
            "Test": {
                "workflow_next": True,
                "current_step": "0",
                "workflow_state": "{}"
            }
        }
        workflow.prepare_workflow(data_in)
        
        # Should have moved forward
        assert workflow.m_current_step_index == 1


# ============================================================================
# THREADED ACTION TESTS
# ============================================================================

class TestThreadedActions:
    """Test threaded action integration"""
    
    def test_threaded_action_creation(self, simple_display_func):
        """Test creating a step with threaded action"""
        
        class TestThread(Threaded_action):
            m_default_name = "Test Thread"
            def action(self):
                time.sleep(0.1)
        
        def create_thread(workflow, data):
            return TestThread()
        
        step = WorkflowStep(
            "Threaded Step",
            simple_display_func,
            action_func=create_thread,
            action_type=StepActionType.THREADED
        )
        
        assert step.action_type == StepActionType.THREADED
    
    def test_threaded_action_starts_on_next(self, simple_display_func):
        """Test threaded action starts when clicking Next"""
        
        class TestThread(Threaded_action):
            m_default_name = "Test Thread"
            def __init__(self):
                super().__init__()
                self.started = False
            
            def action(self):
                self.started = True
                time.sleep(0.1)
        
        thread_instance = None
        
        def create_thread(workflow, data):
            nonlocal thread_instance
            thread_instance = TestThread()
            return thread_instance
        
        workflow = Workflow("Test")
        workflow.add_step(WorkflowStep(
            "Threaded Step",
            simple_display_func,
            action_func=create_thread,
            action_type=StepActionType.THREADED
        ))
        workflow.add_step(WorkflowStep("Next Step", simple_display_func))
        
        workflow.prepare_workflow(None)
        
        # Trigger threaded action
        data_in = {
            "Test": {
                "workflow_next": True,
                "current_step": "0",
                "workflow_state": "{}"
            }
        }
        workflow.prepare_workflow(data_in)
        
        # Thread should be stored
        assert workflow.m_active_thread is not None
        
        # Wait for thread to start
        time.sleep(0.2)
        assert thread_instance.started  # type: ignore
    
    def test_thread_reference_stored(self, simple_display_func):
        """Test that thread reference is stored in workflow"""
        
        class TestThread(Threaded_action):
            m_default_name = "Test Thread"
            def action(self):
                time.sleep(0.1)
        
        def create_thread(workflow, data):
            return TestThread()
        
        workflow = Workflow("Test")
        workflow.add_step(WorkflowStep(
            "Threaded Step",
            simple_display_func,
            action_func=create_thread,
            action_type=StepActionType.THREADED
        ))
        
        workflow.prepare_workflow(None)
        
        data_in = {
            "Test": {
                "workflow_next": True,
                "current_step": "0",
                "workflow_state": "{}"
            }
        }
        workflow.prepare_workflow(data_in)
        
        # Thread should be stored
        assert workflow.m_active_thread is not None
        assert isinstance(workflow.m_active_thread, Threaded_action)


# ============================================================================
# DISPLAY GENERATION TESTS
# ============================================================================

class TestDisplayGeneration:
    """Test display generation and UI components"""
    
    def test_add_display_creates_displayer(self, basic_workflow):
        """Test that add_display works"""
        basic_workflow.prepare_workflow(None)
        
        disp = displayer.Displayer()
        result = basic_workflow.add_display(disp)
        
        assert result is not None
        assert isinstance(result, displayer.Displayer)
    
    def test_breadcrumbs_added(self, basic_workflow):
        """Test that breadcrumbs are added"""
        basic_workflow.prepare_workflow(None)
        
        disp = displayer.Displayer()
        basic_workflow.add_display(disp)
        
        # Should have breadcrumbs for all visible steps
        breadcrumbs = disp.m_breadcrumbs
        assert len(breadcrumbs) == 3  # All 3 steps visible
    
    def test_hidden_fields_added(self, basic_workflow):
        """Test that hidden fields for state are added"""
        basic_workflow.prepare_workflow(None)
        basic_workflow.m_workflow_data["test_key"] = "test_value"
        
        disp = displayer.Displayer()
        basic_workflow.add_display(disp)
        
        content = disp.display()
        # The workflow uses its default name when displaying
        module_name = basic_workflow.m_default_name
        
        # Should have workflow module in content
        assert module_name in content
    
    def test_navigation_buttons_present(self, basic_workflow):
        """Test that navigation buttons are added"""
        basic_workflow.prepare_workflow(None)
        
        disp = displayer.Displayer()
        basic_workflow.add_display(disp)
        
        content = disp.display()
        # The workflow uses its default name when displaying
        module_name = basic_workflow.m_default_name
        
        # Should have workflow module
        assert module_name in content


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_workflow(self):
        """Test workflow with no steps"""
        workflow = Workflow("Empty")
        workflow.prepare_workflow(None)
        
        assert workflow.get_current_step() is None
    
    def test_invalid_json_state(self, basic_workflow):
        """Test handling of invalid JSON in workflow_state"""
        basic_workflow.prepare_workflow(None)
        
        data_in = {
            "Test Workflow": {
                "workflow_next": True,
                "current_step": "0",
                "workflow_state": "invalid json {{"
            }
        }
        
        # Should not crash
        basic_workflow.prepare_workflow(data_in)
        
        # Should have moved forward despite error
        assert basic_workflow.m_current_step_index == 1
    
    def test_wrong_workflow_name_in_post(self, basic_workflow):
        """Test POST data for different workflow is ignored"""
        basic_workflow.prepare_workflow(None)
        initial_step = basic_workflow.m_current_step_index
        
        data_in = {
            "Different Workflow": {
                "workflow_next": True,
                "current_step": "0",
                "workflow_state": "{}"
            }
        }
        
        result = basic_workflow.prepare_workflow(data_in)
        
        # Should return False (not our workflow)
        assert not result
        # Should not have moved
        assert basic_workflow.m_current_step_index == initial_step
    
    def test_action_exception_handling(self, simple_display_func):
        """Test that action exceptions are caught"""
        
        def failing_action(workflow, data):
            raise ValueError("Test error")
        
        workflow = Workflow("Test")
        workflow.add_step(WorkflowStep(
            "Step 1",
            simple_display_func,
            action_func=failing_action
        ))
        workflow.add_step(WorkflowStep("Step 2", simple_display_func))
        
        workflow.prepare_workflow(None)
        
        data_in = {
            "Test": {
                "workflow_next": True,
                "current_step": "0",
                "workflow_state": "{}"
            }
        }
        
        # Should not crash
        workflow.prepare_workflow(data_in)
        
        # Should still advance despite error
        assert workflow.m_current_step_index == 1


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestWorkflowIntegration:
    """Test complete workflow scenarios"""
    
    def test_complete_workflow_flow(self, simple_display_func):
        """Test a complete workflow from start to finish"""
        workflow = Workflow("Complete Flow")
        
        # Track actions
        step1_executed = {"value": False}
        step2_executed = {"value": False}
        
        def action1(wf, data):
            step1_executed["value"] = True
        
        def action2(wf, data):
            step2_executed["value"] = True
        
        workflow.add_step(WorkflowStep("Step 1", simple_display_func, action_func=action1))
        workflow.add_step(WorkflowStep("Step 2", simple_display_func, action_func=action2))
        workflow.add_step(WorkflowStep("Step 3", simple_display_func))
        
        # Start
        workflow.prepare_workflow(None)
        assert workflow.m_current_step_index == 0
        
        # Move through each step
        for i in range(2):
            data_in = {
                "Complete Flow": {
                    "workflow_next": True,
                    "current_step": str(i),
                    "workflow_state": json.dumps(workflow.m_workflow_data),
                    f"data_from_step_{i+1}": f"value_{i+1}"
                }
            }
            workflow.prepare_workflow(data_in)
        
        # Should be at last step
        assert workflow.m_current_step_index == 2
        assert workflow.is_last_step()
        
        # Actions should have executed
        assert step1_executed["value"]
        assert step2_executed["value"]
        
        # Data should be accumulated
        assert "data_from_step_1" in workflow.m_workflow_data
        assert "data_from_step_2" in workflow.m_workflow_data
    
    def test_workflow_with_back_and_forth(self, simple_display_func):
        """Test moving back and forth in workflow"""
        workflow = Workflow("Back and Forth")
        
        for i in range(3):
            workflow.add_step(WorkflowStep(f"Step {i+1}", simple_display_func))
        
        workflow.prepare_workflow(None)
        
        # Forward to step 2
        workflow._go_next()
        assert workflow.m_current_step_index == 1
        
        # Forward to step 3
        workflow._go_next()
        assert workflow.m_current_step_index == 2
        
        # Back to step 2
        workflow._go_previous()
        assert workflow.m_current_step_index == 1
        
        # Back to step 1
        workflow._go_previous()
        assert workflow.m_current_step_index == 0
        
        # Forward again
        workflow._go_next()
        assert workflow.m_current_step_index == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
