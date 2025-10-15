# Workflow System Documentation

## Overview

The Workflow system provides a modern, declarative way to create multi-step processes (wizards) in your web application. It features:

- **Declarative step definition** - Define each step as a self-contained unit
- **Automatic form state persistence** - All form data is preserved across steps
- **Conditional step visibility** - Show/hide steps based on previous inputs
- **Sync and threaded actions** - Support both immediate and background processing
- **Progress tracking** - Automatic breadcrumbs and progress indicators
- **Bidirectional navigation** - Users can go back to previous steps

## Quick Start

### Basic Workflow

```python
from src.modules.workflow import Workflow, WorkflowStep
from src.modules import displayer

# Create workflow
workflow = Workflow("My Wizard")

# Define display function
def show_step1(disp, workflow_data):
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
    disp.add_display_item(displayer.DisplayerItemText("Enter your name:"), 0)
    
    # Restore previous value if going back
    name = workflow_data.get("name", "")
    disp.add_display_item(displayer.DisplayerItemInputString("name", None, name), 0)
    return disp

# Define action function
def process_step1(workflow, form_data):
    print(f"Name entered: {form_data.get('name')}")

# Add step
workflow.add_step(WorkflowStep(
    name="Personal Info",
    display_func=show_step1,
    action_func=process_step1
))

# In your Flask route
@app.route('/wizard', methods=['GET', 'POST'])
def wizard():
    disp = displayer.Displayer()
    
    if request.method == 'POST':
        data_in = utilities.util_post_to_json(request.form.to_dict())
        workflow.prepare_workflow(data_in)
    else:
        workflow.prepare_workflow(None)
    
    workflow.add_display(disp)
    return render_template("base_content.j2", content=disp.display())
```

## Core Concepts

### WorkflowStep

A `WorkflowStep` encapsulates everything about a single step:

```python
step = WorkflowStep(
    name="Step Name",           # Display name (shown in breadcrumbs)
    display_func=my_display,    # Function to render the step
    action_func=my_action,      # Function to execute on "Next"
    skip_func=my_skip,          # Function to execute on "Skip" (optional)
    condition_func=my_condition,# Function to determine visibility (optional)
    action_type=StepActionType.FUNCTION,  # FUNCTION, THREADED, or NONE
    description="Description",  # Optional description
    icon="bi-check"             # Optional icon class
)
```

#### Display Function

Signature: `(displayer, workflow_data) -> displayer`

- **displayer**: The Displayer instance to populate
- **workflow_data**: Dictionary containing all data from previous steps

```python
def my_display(disp, workflow_data):
    # Always restore previous values for going back
    email = workflow_data.get("email", "")
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [6, 6]))
    disp.add_display_item(displayer.DisplayerItemText("Email:"), 0)
    disp.add_display_item(displayer.DisplayerItemInputString("email", None, email), 1)
    
    return disp
```

#### Action Function

Signature: `(workflow, form_data) -> None` or `(workflow, form_data) -> Threaded_action`

- **workflow**: The Workflow instance (access `workflow.m_workflow_data`)
- **form_data**: Dictionary of form data from current step only

```python
# Synchronous action
def my_action(workflow, form_data):
    email = form_data.get("email")
    # Process immediately
    print(f"Processing {email}")

# Threaded action
def my_threaded_action(workflow, form_data):
    thread = MyThreadedAction(form_data.get("email"))
    return thread  # Workflow will start it
```

#### Skip Function

Signature: `(workflow, form_data) -> None`

Called when user clicks "Skip" button. Use to set default values:

```python
def my_skip(workflow, form_data):
    # Set defaults
    workflow.m_workflow_data["use_defaults"] = True
    workflow.m_workflow_data["theme"] = "light"
```

#### Condition Function

Signature: `(workflow_data) -> bool`

Determines if step should be visible:

```python
# Only show this step if user selected "advanced"
condition_func=lambda data: data.get("mode") == "advanced"

# Show if email is provided
condition_func=lambda data: "email" in data and data["email"]
```

### Action Types

```python
from src.modules.workflow import StepActionType

# No action
action_type=StepActionType.NONE

# Synchronous function (default)
action_type=StepActionType.FUNCTION

# Threaded action
action_type=StepActionType.THREADED
```

## Advanced Features

### Conditional Steps

Steps can be shown/hidden based on previous inputs:

```python
workflow.add_step(WorkflowStep(
    name="Python Config",
    display_func=show_python_config,
    condition_func=lambda data: data.get("language") == "python"
))

workflow.add_step(WorkflowStep(
    name="JavaScript Config",
    display_func=show_js_config,
    condition_func=lambda data: data.get("language") == "javascript"
))
```

The workflow automatically:
- Computes visible steps on each navigation
- Skips hidden steps when moving forward/backward
- Updates progress percentage based on visible steps only

### Form State Persistence

All form data is automatically:
- Saved when moving to next step
- Preserved in a hidden field as JSON
- Restored when going back
- Available in `workflow_data` parameter

```python
def my_display(disp, workflow_data):
    # All previous data is available
    name = workflow_data.get("name", "")
    email = workflow_data.get("email", "")
    language = workflow_data.get("language", "")
    
    # Show confirmation of previous steps
    disp.add_display_item(
        displayer.DisplayerItemAlert(
            f"Creating account for {name} ({email})",
            displayer.BSstyle.INFO
        ),
        0
    )
```

### Threaded Actions

For long-running operations, use threaded actions:

```python
from src.modules.threaded import Threaded_action

class MyProcessingAction(Threaded_action):
    m_default_name = "Processing"
    
    def __init__(self, data):
        super().__init__()
        self.data = data
    
    def run_main(self):
        self.emit_status("progress", "Processing...", 103, "Starting")
        # Do work...
        time.sleep(2)
        self.emit_status("progress", "Done!", 101, "Complete")

def my_threaded_action(workflow, form_data):
    thread = MyProcessingAction(form_data)
    return thread  # Workflow starts it automatically

workflow.add_step(WorkflowStep(
    name="Processing",
    display_func=show_processing,
    action_func=my_threaded_action,
    action_type=StepActionType.THREADED
))
```

### Skippable Steps

Add skip functionality to optional steps:

```python
def my_skip(workflow, form_data):
    # Set reasonable defaults
    workflow.m_workflow_data["advanced_mode"] = False
    workflow.m_workflow_data["theme"] = "default"

workflow.add_step(WorkflowStep(
    name="Advanced Settings",
    display_func=show_advanced,
    action_func=save_advanced,
    skip_func=my_skip  # Enables "Skip" button
))
```

### Progress Tracking

Progress is automatically displayed:
- **Breadcrumbs**: Show all visible steps with current highlighted
- **Progress bar**: Visual percentage complete (based on visible steps)
- **Step counter**: "Step 3 of 7"

Access progress programmatically:

```python
progress = workflow.get_progress_percentage()  # 0-100
is_first = workflow.is_first_step()
is_last = workflow.is_last_step()
visible_steps = workflow.m_visible_steps  # List of visible step indices
```

## Complete Example

See `tests/demo_support/demo_workflow.py` for a comprehensive example showing:
- Multi-step form
- Conditional Python/JavaScript configuration
- Skippable advanced options
- Threaded processing step
- Summary with all collected data

Run the demo:
```
http://localhost:5000/workflow-demo
```

## API Reference

### Workflow Class

```python
class Workflow:
    def __init__(self, name: Optional[str] = None)
    
    def add_step(self, step: WorkflowStep) -> None
    def prepare_workflow(self, data_in: Optional[Dict]) -> bool
    def add_display(self, disp: Displayer) -> Displayer
    
    def get_current_step(self) -> Optional[WorkflowStep]
    def is_first_step(self) -> bool
    def is_last_step(self) -> bool
    def get_progress_percentage(self) -> int
    
    # Properties
    m_name: str
    m_steps: List[WorkflowStep]
    m_current_step_index: int
    m_workflow_data: Dict[str, Any]
    m_visible_steps: List[int]
    m_active_thread: Optional[Threaded_action]
```

### WorkflowStep Class

```python
class WorkflowStep:
    def __init__(
        self,
        name: str,
        display_func: Callable,
        action_func: Optional[Callable] = None,
        skip_func: Optional[Callable] = None,
        condition_func: Optional[Callable[[Dict], bool]] = None,
        action_type: StepActionType = StepActionType.FUNCTION,
        description: Optional[str] = None,
        icon: Optional[str] = None
    )
    
    def is_visible(self, workflow_data: Dict) -> bool
    def execute_action(self, workflow: Workflow, form_data: Dict) -> None
    def execute_skip(self, workflow: Workflow, form_data: Dict) -> None
```

### StepActionType Enum

```python
class StepActionType(Enum):
    NONE = "none"
    FUNCTION = "function"
    THREADED = "threaded"
```

## Migration from Old System

Old system (list-based):
```python
self.m_steps["display"].append(self.display_step1)
self.m_steps["workers"].append(self.worker_step1)
self.m_steps["skippers"].append(self.skipper_step1)
self.m_steps["submenus"].append("Step 1")
```

New system (declarative):
```python
self.add_step(WorkflowStep(
    name="Step 1",
    display_func=self.display_step1,
    action_func=self.worker_step1,
    skip_func=self.skipper_step1
))
```

Key differences:
- **All-in-one**: Each step is one object, not spread across 4 lists
- **Automatic state**: No manual state management needed
- **Conditional**: Built-in support for conditional steps
- **Type safety**: Better IDE support and type checking

## Best Practices

1. **Always restore values in display functions**:
   ```python
   value = workflow_data.get("field_name", "default")
   ```

2. **Use descriptive step names** - they appear in breadcrumbs

3. **Keep actions lightweight** - use threaded actions for heavy work

4. **Validate in action functions**:
   ```python
   def my_action(workflow, form_data):
       if not form_data.get("email"):
           scheduler.scheduler_obj.emit_popup(
               scheduler.logLevel.warning,
               "Email is required"
           )
   ```

5. **Provide skip defaults** - make optional steps truly optional

6. **Test conditional logic** - verify steps show/hide correctly

7. **Use workflow_data for cross-step references**:
   ```python
   def display_summary(disp, workflow_data):
       # Reference all previous steps
       name = workflow_data.get("name")
       email = workflow_data.get("email")
   ```

## Troubleshooting

**Step not appearing:**
- Check `condition_func` - it might be returning False
- Verify step was added: `print(len(workflow.m_steps))`
- Check visible steps: `print(workflow.m_visible_steps)`

**Data not persisting:**
- Ensure display function restores from `workflow_data`
- Check that form fields have correct IDs
- Verify POST data is being processed

**Threaded action not starting:**
- Ensure `action_type=StepActionType.THREADED`
- Action function must return a `Threaded_action` instance
- Check thread manager: `/threads/`

**Progress bar incorrect:**
- Progress is based on visible steps only
- Recomputed on each navigation
- Hidden steps don't count toward progress
