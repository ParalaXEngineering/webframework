# Workflow System Architecture

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Flask Route                              │
│  @app.route('/wizard', methods=['GET', 'POST'])             │
└────────────┬────────────────────────────────────────────────┘
             │
             ↓
┌────────────────────────────────────────────────────────────┐
│  GET Request → workflow.prepare_workflow(None)              │
│  POST Request → workflow.prepare_workflow(data_in)          │
└────────────┬───────────────────────────────────────────────┘
             │
             ↓
┌────────────────────────────────────────────────────────────┐
│               Workflow Processing                           │
│  1. Restore state from hidden field (JSON)                  │
│  2. Compute visible steps based on conditions              │
│  3. Handle navigation (next/prev/skip)                      │
│  4. Execute action/skip functions                           │
│  5. Update current_step_index                               │
└────────────┬───────────────────────────────────────────────┘
             │
             ↓
┌────────────────────────────────────────────────────────────┐
│          workflow.add_display(displayer)                    │
│  1. Add module to displayer                                 │
│  2. Generate breadcrumbs                                    │
│  3. Show progress indicator                                 │
│  4. Call current step's display_func                        │
│  5. Add navigation buttons                                  │
│  6. Add hidden state fields                                 │
└────────────┬───────────────────────────────────────────────┘
             │
             ↓
┌────────────────────────────────────────────────────────────┐
│                Render Template                              │
│  render_template("base_content.j2", ...)                   │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

```
┌─────────────────┐
│  Browser Form   │
│  ┌───────────┐ │
│  │ Field: A  │ │
│  │ Field: B  │ │
│  │ [Next]    │ │
│  └───────────┘ │
└────────┬────────┘
         │ POST
         ↓
┌─────────────────────────────────────────────────────────┐
│  util_post_to_json(form_data)                           │
│  {                                                       │
│    "workflow_name": {                                   │
│      "workflow_state": '{"previous": "data"}',         │
│      "current_step": "1",                               │
│      "workflow_next": true,                             │
│      "field_a": "value_a",                              │
│      "field_b": "value_b"                               │
│    }                                                     │
│  }                                                       │
└────────┬────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────┐
│  workflow.prepare_workflow(data_in)                     │
│                                                          │
│  1. Parse workflow_state JSON                           │
│     m_workflow_data = {"previous": "data"}             │
│                                                          │
│  2. Save new form data                                  │
│     m_workflow_data["field_a"] = "value_a"             │
│     m_workflow_data["field_b"] = "value_b"             │
│                                                          │
│  3. Execute action                                      │
│     current_step.execute_action(workflow, form_data)   │
│                                                          │
│  4. Move to next step                                   │
│     m_current_step_index = 2                            │
└────────┬────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────┐
│  Step 2 Display Function                                │
│                                                          │
│  def display_step2(disp, workflow_data):                │
│    # Access ALL previous data                           │
│    prev_val = workflow_data.get("field_a")             │
│                                                          │
│    # Restore value if going back                        │
│    current = workflow_data.get("field_c", "")          │
│                                                          │
│    disp.add_display_item(                               │
│      DisplayerItemInputString("field_c", None, current)│
│    )                                                     │
└────────┬────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────┐
│  Hidden Fields in Generated HTML                        │
│  <input type="hidden" name="current_step" value="2">   │
│  <input type="hidden" name="workflow_state"            │
│         value='{"field_a":"value_a","field_b":"..."}'>│
└─────────────────────────────────────────────────────────┘
```

## WorkflowStep Lifecycle

```
┌──────────────────────────────────────────────────────────┐
│                 WorkflowStep Creation                     │
│  step = WorkflowStep(                                    │
│    name="Step Name",                                     │
│    display_func=my_display,                             │
│    action_func=my_action,                               │
│    skip_func=my_skip,        # optional                 │
│    condition_func=my_cond    # optional                 │
│  )                                                       │
└────────┬─────────────────────────────────────────────────┘
         │
         ↓
┌──────────────────────────────────────────────────────────┐
│              Step Visibility Check                        │
│  step.is_visible(workflow_data)                          │
│    → calls condition_func(workflow_data) → bool         │
│                                                          │
│  If True → Step is in visible_steps list                │
│  If False → Step is skipped automatically               │
└────────┬─────────────────────────────────────────────────┘
         │
         ↓ (if visible)
┌──────────────────────────────────────────────────────────┐
│               Display Phase                               │
│  step.display_func(displayer, workflow_data)            │
│    → Generate form fields                                │
│    → Restore previous values                             │
│    → Return updated displayer                            │
└────────┬─────────────────────────────────────────────────┘
         │
         ↓ (on Next button)
┌──────────────────────────────────────────────────────────┐
│               Action Phase                                │
│  step.execute_action(workflow, form_data)               │
│                                                          │
│  If action_type == FUNCTION:                            │
│    action_func(workflow, form_data)                     │
│                                                          │
│  If action_type == THREADED:                            │
│    thread = action_func(workflow, form_data)           │
│    thread.start()                                       │
│    workflow.m_active_thread = thread                    │
└────────┬─────────────────────────────────────────────────┘
         │
         ↓ (or on Skip button)
┌──────────────────────────────────────────────────────────┐
│               Skip Phase                                  │
│  step.execute_skip(workflow, form_data)                 │
│    → Set default values                                  │
│    → Skip to next step                                   │
└──────────────────────────────────────────────────────────┘
```

## Conditional Step Example

```
Workflow Steps:
  0. Choose Language
  1. Python Config      (condition: language == "python")
  2. JavaScript Config  (condition: language == "javascript")
  3. Summary

User selects "python":
  ┌─────────────────────────────────────────┐
  │ visible_steps = [0, 1, 3]               │
  │                                         │
  │ Step 0 → Step 1 → Step 3                │
  │ (Language) → (Python) → (Summary)       │
  │                                         │
  │ Progress: Step 1 = 33%, 2 = 66%, 3 = 100%│
  └─────────────────────────────────────────┘

User selects "javascript":
  ┌─────────────────────────────────────────┐
  │ visible_steps = [0, 2, 3]               │
  │                                         │
  │ Step 0 → Step 2 → Step 3                │
  │ (Language) → (JavaScript) → (Summary)   │
  │                                         │
  │ Progress: Step 1 = 33%, 2 = 66%, 3 = 100%│
  └─────────────────────────────────────────┘

Key point: Steps 1 and 2 never appear together!
```

## State Management

```
┌─────────────────────────────────────────────────────────┐
│                 m_workflow_data                         │
│  {                                                      │
│    "name": "Alice",          # From step 1             │
│    "email": "alice@ex.com",  # From step 1             │
│    "language": "python",     # From step 2             │
│    "python_version": "3.11", # From step 3             │
│    "use_venv": true,         # From step 3             │
│    ...                                                  │
│  }                                                      │
│                                                         │
│  ↓ Serialized to JSON                                  │
│                                                         │
│  <input type="hidden" name="workflow_state"            │
│         value='{"name":"Alice","email":"..."}'>       │
│                                                         │
│  ↓ On next POST                                        │
│                                                         │
│  Restored: m_workflow_data = json.loads(...)          │
└─────────────────────────────────────────────────────────┘

Benefits:
  ✓ No server-side session storage needed
  ✓ Stateless workflow handling
  ✓ Can go back/forward freely
  ✓ All data preserved automatically
```

## Navigation Logic

```
User clicks "Next":
  1. Save current step data to m_workflow_data
  2. Execute current step's action
  3. Recompute visible_steps (conditions may have changed!)
  4. Find next visible step
  5. Update m_current_step_index
  6. Display new step

User clicks "Previous":
  1. Skip action execution
  2. Find previous visible step
  3. Update m_current_step_index
  4. Display previous step (data is restored from m_workflow_data)

User clicks "Skip":
  1. Execute current step's skip function
  2. Set default values
  3. Move to next visible step
```

## Progress Calculation

```
visible_steps = [0, 2, 4, 5]  # Some steps hidden by conditions
total_visible = 4
current_step_index = 4

# Find position in visible list
visible_position = visible_steps.index(4) = 2  # 3rd visible step (0-indexed)

# Calculate progress
progress = (visible_position + 1) / total_visible * 100
         = (2 + 1) / 4 * 100
         = 75%

Breadcrumbs show: "Step 3 of 4 (75% complete)"
```

## Integration Points

```
┌────────────────────────────────────────────────────────┐
│                   Workflow System                       │
└────────┬──────────────────────┬────────────────────────┘
         │                      │
         ↓                      ↓
┌─────────────────┐    ┌────────────────────┐
│   Displayer     │    │  Threaded Actions  │
│   • Layouts     │    │  • Background      │
│   • Items       │    │    processing      │
│   • Forms       │    │  • Status updates  │
└─────────────────┘    └────────────────────┘
         │                      │
         ↓                      ↓
┌──────────────────────────────────────────┐
│            Flask Route                    │
│  • GET: Initialize workflow               │
│  • POST: Process step & navigate         │
└──────────────────────────────────────────┘
         │
         ↓
┌──────────────────────────────────────────┐
│          Jinja2 Template                  │
│  • Render form                            │
│  • Show progress                          │
│  • Display breadcrumbs                    │
└──────────────────────────────────────────┘
```

## Example: Going Back

```
State at Step 3:
  m_workflow_data = {
    "name": "Alice",
    "email": "alice@example.com",
    "language": "python"
  }

User clicks "Previous" →

display_step2(disp, workflow_data):
  # All data from step 3 is preserved!
  email = workflow_data.get("email")  # "alice@example.com"
  
  # Restore in form
  disp.add_display_item(
    DisplayerItemInputString("email", None, email)
  )
  
  # Form shows: "alice@example.com" already filled in!

User modifies email → Clicks "Next" →

  # New email value overwrites old one
  m_workflow_data["email"] = "alice.new@example.com"
  
  # All other data preserved
  # Continue from step 3 with updated email
```

This architecture ensures:
- ✅ Seamless back/forward navigation
- ✅ Data persistence without database
- ✅ Conditional step visibility
- ✅ Clean separation of concerns
- ✅ Easy to test and maintain
