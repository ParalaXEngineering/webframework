# Displayer Testing Guide

This document explains the testing setup for the ParalaX Web Framework displayer system.

## Overview

The testing system includes:
1. **demo.py** - Interactive Flask application for visual testing
2. **Unit tests** - Data structure validation tests
3. **Form tests** - POST data validation tests  
4. **VS Code integration** - Debug configurations

## Running the Demo Application

### Option 1: Using VS Code (Recommended)

1. Open the project in VS Code
2. Press **F5** or go to **Run > Start Debugging**
3. Select **"Python: Demo Application"**
4. Open your browser to http://localhost:5001

### Option 2: Using Terminal

```bash
# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows

# Run the demo
python demo.py
```

### Demo Pages

The demo application includes several pages:

- **Home** (`/`) - Main navigation page
- **Layout Demos** (`/layouts`) - All layout types (vertical, horizontal, table, spacer)
- **Text & Display** (`/text-display`) - Text, alerts, badges, buttons, links
- **Input Items** (`/inputs`) - All input types with working form submission
- **Complete Showcase** (`/complete-showcase`) - Comprehensive demo of all features

## Running Tests

### All Tests

```bash
pytest tests/
```

### Specific Test Files

```bash
# Unit tests (data structures)
pytest tests/test_displayer_unit.py -v

# Form POST validation tests
pytest tests/test_displayer_forms.py -v
```

### Using VS Code

1. Press **F5** and select **"Python: Run Tests"**
2. Or right-click on a test file and select **"Run Python File in Terminal"**

## Test Structure

### Unit Tests (`test_displayer_unit.py`)

Tests the data structure of displayer components:
- DisplayerLayout with all layout types
- All 40+ DisplayerItem types
- Proper attribute assignment
- Default values
- Style enumerations

**What it validates:**
- Objects are created correctly
- Attributes have expected values
- Internal data structures match specification

**What it doesn't validate:**
- HTML rendering (human visual check required)
- Template output (requires demo.py)

### Form Tests (`test_displayer_forms.py`)

Tests POST data handling from forms:
- Single-level fields (`field: value`)
- Nested fields (`level0.level1.level2: value`)
- List fields (`listNN` pattern)
- Mapping fields (`mapleft`/`mapright`)
- Multi-select fields (`item_choice: on`)

**Example POST data transformations:**

```python
# Input POST data
{
    "user.name": "John",
    "user.age": "30",
    "list00": "item1",
    "list01": "item2"
}

# Output JSON (via util_post_to_json)
{
    "user": {
        "name": "John",
        "age": 30
    },
    "list": ["item1", "item2"]
}
```

## Visual Testing with Demo

While automated tests validate data structures, visual testing is required for:

1. **Layout appearance** - Does the column arrangement look correct?
2. **Style application** - Are colors, spacing, and styles rendered properly?
3. **Responsiveness** - Does the layout adapt to different screen sizes?
4. **Input interactions** - Do form fields work correctly?
5. **Jinja2 template rendering** - Is the HTML output correct?

### Visual Testing Workflow

1. Run `demo.py` (Flask server)
2. Navigate through all demo pages
3. Check layout, styling, and interactions
4. Submit forms and verify results
5. Test on different screen sizes (responsive)
6. Check browser console for JavaScript errors

## Adding New Tests

### Adding a New DisplayerItem Test

```python
def test_new_item():
    """Test the new DisplayerItem type."""
    item = displayer.DisplayerItemNewType("param1", "param2")
    
    assert item.m_attribute1 == "expected_value"
    assert item.m_attribute2 == expected_value
```

### Adding a New Form Test

```python
def test_new_form_structure():
    """Test POST data transformation for new pattern."""
    post_data = {
        "field.subfield": "value"
    }
    
    result = utilities.util_post_to_json(post_data)
    
    assert result == {
        "field": {
            "subfield": "value"
        }
    }
```

### Adding to Demo

```python
@app.route('/new-demo')
def new_demo():
    """Demonstrate new feature."""
    disp = displayer.Displayer()
    disp.add_generic("New Feature Demo")
    disp.set_title("New Feature")
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemNewType(...), 0)
    
    return render_template("base_content.j2", content=disp.display())
```

## Debugging

### VS Code Debugger

Use the launch configurations in `.vscode/launch.json`:

1. **Python: Demo Application** - Debug the Flask demo server
2. **Python: Run Tests** - Debug all tests
3. **Python: Run Specific Test** - Debug the currently open test file

Set breakpoints by clicking in the gutter next to line numbers.

### Common Issues

**Issue: Port 5000 already in use**
- Solution: Demo uses port 5001 by default
- Or change the port in `demo.py` line 457

**Issue: Module not found**
- Solution: Ensure virtual environment is activated
- Check that you're running from the project root directory

**Issue: Template not found**
- Solution: Verify `templates/` and `webengine/` directories exist
- Check Flask template_folder and static_folder configuration

**Issue: Type errors from Pylance**
- Note: Some type warnings are overly strict
- The code will run correctly despite warnings
- Focus on runtime errors during testing

## Testing Checklist

Before considering displayer testing complete:

- [ ] All unit tests pass (`pytest tests/test_displayer_unit.py`)
- [ ] All form tests pass (`pytest tests/test_displayer_forms.py`)
- [ ] Demo server runs without errors
- [ ] All demo pages load correctly
- [ ] Layouts render properly (visual check)
- [ ] All input types work (visual check)
- [ ] Form submission works (visual check)
- [ ] No JavaScript console errors (visual check)
- [ ] Responsive layouts work (visual check)
- [ ] All 40+ DisplayerItem types tested

## Additional Resources

- **Framework Documentation**: `docs/build/html/index.html`
- **Source Code**: `src/displayer.py` (1723 lines)
- **Utilities**: `src/utilities.py` (POST data handling)
- **Templates**: `templates/` directory
- **Real Usage Examples**: `src/settings.py`, `src/main.py`

## Contact

For questions or issues with the testing system, refer to the main project documentation or source code comments.
