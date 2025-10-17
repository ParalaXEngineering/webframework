"""
User-Defined Layout Demo

Demonstrates the USER_DEFINED layout type which allows users to create
custom grid layouts using a visual drag-and-drop editor.
"""

import json
from flask import Blueprint, render_template, redirect, url_for, session, request
from functools import wraps
from src.modules import displayer
from src.modules.displayer import ResourceRegistry

# Create blueprint for user-defined layout demo
user_defined_bp = Blueprint('user_defined_layout', __name__, url_prefix='/layouts/user-defined')


def require_login(f):
    """Decorator to require login for demo pages."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('common.login'))
        return f(*args, **kwargs)
    return decorated_function


@user_defined_bp.route('/')
@require_login
def index():
    """Main page for USER_DEFINED layout demonstration."""
    disp = displayer.Displayer()
    disp.add_generic("User-Defined Layout")
    disp.set_title("USER_DEFINED Layout - Custom Grid Builder")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Layouts", "layouts.index", [])
    disp.add_breadcrumb("User-Defined", "user_defined_layout.index", [])
    
    # Description
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "<strong>USER_DEFINED Layout</strong><br>"
        "Create custom grid layouts using a visual drag-and-drop editor. "
        "This layout type uses GridStack.js to provide an interactive editor "
        "where you can arrange fields in a Bootstrap 12-column grid. "
        "The layout configuration is saved as JSON and can be reused.",
        displayer.BSstyle.INFO
    ), 0)
    
    # Navigation buttons
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [6, 6]
    ))
    
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        id="btn_editor",
        text="Open Layout Editor",
        icon="grid-3x3-gap",
        link=url_for('user_defined_layout.editor'),
        color=displayer.BSstyle.PRIMARY
    ), 0)
    
    # Check if we have a saved layout
    has_layout = 'user_defined_layout' in session
    
    if has_layout:
        disp.add_display_item(displayer.DisplayerItemButtonLink(
            id="btn_preview",
            text="Preview Saved Layout",
            icon="eye",
            link=url_for('user_defined_layout.preview'),
            color=displayer.BSstyle.SUCCESS
        ), 1)
    else:
        disp.add_display_item(displayer.DisplayerItemAlert(
            "No saved layout yet. Use the editor to create one!",
            displayer.BSstyle.WARNING
        ), 1)
    
    # Features section
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Features"
    ))
    
    features_html = """
    <ul class="list-group">
        <li class="list-group-item">
            <i class="bi bi-arrows-move text-primary"></i>
            <strong>Drag & Drop:</strong> Visually arrange fields in the grid
        </li>
        <li class="list-group-item">
            <i class="bi bi-arrows-angle-expand text-success"></i>
            <strong>Resize:</strong> Adjust field widths from 1-12 columns
        </li>
        <li class="list-group-item">
            <i class="bi bi-list-ol text-info"></i>
            <strong>8 Example Fields:</strong> example1 through example8 available
        </li>
        <li class="list-group-item">
            <i class="bi bi-file-earmark-code text-warning"></i>
            <strong>JSON Export:</strong> Save and reuse layout configurations
        </li>
        <li class="list-group-item">
            <i class="bi bi-bootstrap text-danger"></i>
            <strong>Bootstrap Compatible:</strong> 12-column grid system
        </li>
    </ul>
    """
    
    disp.add_display_item(displayer.DisplayerItemText(features_html), 0)
    
    # How it works
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="How It Works"
    ))
    
    disp.add_display_item(displayer.DisplayerItemText(
        "<ol>"
        "<li><strong>Design:</strong> Use the visual editor to create your layout</li>"
        "<li><strong>Save:</strong> The layout is saved as JSON configuration</li>"
        "<li><strong>Use:</strong> Reference field IDs when adding items to the layout</li>"
        "<li><strong>Render:</strong> The framework automatically positions items based on your design</li>"
        "</ol>"
    ), 0)
    
    display_content = disp.display()
    return render_template("base_content.j2", content=display_content, **display_content)


@user_defined_bp.route('/editor', methods=['GET', 'POST'])
@require_login
def editor():
    """Visual layout editor page."""
    if request.method == 'POST':
        # Save the layout configuration
        layout_json = request.form.get('layout_json', '{}')
        try:
            layout_config = json.loads(layout_json)
            session['user_defined_layout'] = layout_config
            session.modified = True
            
            # Redirect to preview
            return redirect(url_for('user_defined_layout.preview'))
        except json.JSONDecodeError:
            # Handle invalid JSON
            pass
    
    # Load existing layout if present
    existing_layout = session.get('user_defined_layout', {})
    
    # IMPORTANT: Create displayer first (this resets ResourceRegistry)
    disp = displayer.Displayer()
    
    # THEN require gridstack resources for the editor (must be after Displayer init!)
    ResourceRegistry.require('gridstack')
    
    # Debug: Check what resources are registered
    print("DEBUG: Required CSS:", ResourceRegistry.get_required_css())
    print("DEBUG: Required CSS CDN:", ResourceRegistry.get_required_css_cdn())
    print("DEBUG: Required JS:", ResourceRegistry.get_required_js())
    print("DEBUG: Required JS CDN:", ResourceRegistry.get_required_js_cdn())
    
    disp.add_generic("Layout Editor")
    disp.set_title("USER_DEFINED Layout Editor")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Layouts", "layouts.index", [])
    disp.add_breadcrumb("User-Defined", "user_defined_layout.index", [])
    disp.add_breadcrumb("Editor", "user_defined_layout.editor", [])
    
    # Instructions
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "<strong>Layout Editor</strong><br>"
        "Drag items to rearrange, resize from edges/corners. Each field can be assigned to one of 8 example fields. "
        "Click 'Add New Item' to add more fields to your layout. Maximum 12 columns per row.",
        displayer.BSstyle.INFO
    ), 0)
    
    # Editor content - custom HTML with GridStack
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    
    editor_html = f"""
    <form method="POST" action="{url_for('user_defined_layout.editor')}">
        <div class="layout-editor-toolbar">
            <button type="button" class="btn btn-primary" onclick="addNewItem()">
                <i class="bi bi-plus-circle"></i> Add New Item
            </button>
            <button type="button" class="btn btn-warning" onclick="clearLayout()">
                <i class="bi bi-trash"></i> Clear All
            </button>
            <button type="button" class="btn btn-outline-secondary" onclick="copyJSON()">
                <i class="bi bi-clipboard"></i> Copy JSON
            </button>
            <button type="submit" class="btn btn-success">
                <i class="bi bi-save"></i> Save & Preview
            </button>
        </div>
        
        <div class="card mb-3">
            <div class="card-body">
                <div class="grid-stack show-grid"></div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0">JSON Configuration</h5>
            </div>
            <div class="card-body">
                <div class="json-preview" id="json-preview">{json.dumps(existing_layout, indent=2) if existing_layout else '{}'}</div>
                <input type="hidden" id="layout-json" name="layout_json" value='{json.dumps(existing_layout) if existing_layout else "{}"}'>
            </div>
        </div>
    </form>
    """
    
    # Use DisplayerItemAlert with style NONE to render raw HTML
    disp.add_display_item(displayer.DisplayerItemAlert(editor_html, displayer.BSstyle.NONE), 0)
    
    # Unpack the display dict to make resources available to base.j2
    display_content = disp.display()
    return render_template("base_content.j2", content=display_content, **display_content)


@user_defined_bp.route('/preview')
@require_login
def preview():
    """Preview the saved user-defined layout with example data."""
    # Get saved layout
    layout_config = session.get('user_defined_layout')
    
    if not layout_config or 'items' not in layout_config:
        # No layout saved, redirect to editor
        return redirect(url_for('user_defined_layout.editor'))
    
    disp = displayer.Displayer()
    disp.add_generic("Layout Preview")
    disp.set_title("USER_DEFINED Layout Preview")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Layouts", "layouts.index", [])
    disp.add_breadcrumb("User-Defined", "user_defined_layout.index", [])
    disp.add_breadcrumb("Preview", "user_defined_layout.preview", [])
    
    # Info alert
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        f"<strong>Preview Mode</strong><br>"
        f"This is how your custom layout looks with actual displayer items. "
        f"Layout has {len(layout_config.get('items', []))} fields configured.",
        displayer.BSstyle.SUCCESS
    ), 0)
    
    # Action buttons
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [6, 6]
    ))
    
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        id="btn_back_editor",
        text="Edit Layout",
        icon="pencil",
        link=url_for('user_defined_layout.editor'),
        color=displayer.BSstyle.PRIMARY
    ), 0)
    
    disp.add_display_item(displayer.DisplayerItemButtonLink(
        id="btn_view_code",
        text="View Code Example",
        icon="code-slash",
        link=url_for('user_defined_layout.code_example'),
        color=displayer.BSstyle.INFO
    ), 1)
    
    # Show JSON config
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Layout Configuration"
    ))
    
    json_code = json.dumps(layout_config, indent=2)
    disp.add_display_item(displayer.DisplayerItemCode(
        id="config_json",
        code=json_code,
        language="json",
        show_line_numbers=True
    ), 0)
    
    # Create the USER_DEFINED layout with the saved configuration
    try:
        layout_id = disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.USER_DEFINED,
            user_defined_config=layout_config,
            subtitle="Your Custom Layout"
        ))
        
        # Add example items to each field
        example_items = {
            'example1': displayer.DisplayerItemAlert("Example 1: Alert Component", displayer.BSstyle.PRIMARY),
            'example2': displayer.DisplayerItemText("<strong>Example 2:</strong> Text item with HTML"),
            'example3': displayer.DisplayerItemBadge("Example 3: Badge", displayer.BSstyle.SUCCESS),
            'example4': displayer.DisplayerItemInputString("example4_input", "Example 4: Input", value=""),
            'example5': displayer.DisplayerItemInputNumeric("example5_num", "Example 5: Number", value=42),
            'example6': displayer.DisplayerItemInputSelect("example6_select", "Example 6: Select", value="Option A", choices=["Option A", "Option B", "Option C"]),
            'example7': displayer.DisplayerItemButtonLink(
                id="example7_btn",
                text="Example 7: Button",
                icon="star",
                link="#",
                color=displayer.BSstyle.WARNING
            ),
            'example8': displayer.DisplayerItemAlert("Example 8: Another Alert", displayer.BSstyle.INFO),
        }
        
        # Add items based on the layout configuration
        for item_config in layout_config.get('items', []):
            field_id = item_config.get('field_id')
            if field_id in example_items:
                disp.add_display_item(example_items[field_id], column=field_id, layout_id=layout_id)
        
    except Exception as e:
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [12]
        ))
        disp.add_display_item(displayer.DisplayerItemAlert(
            f"<strong>Error:</strong> Failed to render layout: {str(e)}",
            displayer.BSstyle.ERROR
        ), 0)
    
    display_content = disp.display()
    return render_template("base_content.j2", content=display_content, **display_content)


@user_defined_bp.route('/code-example')
@require_login
def code_example():
    """Show code example for using USER_DEFINED layout."""
    layout_config = session.get('user_defined_layout', {})
    
    disp = displayer.Displayer()
    disp.add_generic("Code Example")
    disp.set_title("USER_DEFINED Layout - Code Example")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Layouts", "layouts.index", [])
    disp.add_breadcrumb("User-Defined", "user_defined_layout.index", [])
    disp.add_breadcrumb("Code Example", "user_defined_layout.code_example", [])
    
    # Description
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "<strong>Implementation Example</strong><br>"
        "Here's how to use the USER_DEFINED layout in your code with the current configuration.",
        displayer.BSstyle.INFO
    ), 0)
    
    # Python code example
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Python Implementation"
    ))
    
    json_config_str = json.dumps(layout_config, indent=4) if layout_config else "{}"
    
    code_example = f'''# Step 1: Define your layout configuration (from the editor)
layout_config = {json_config_str}

# Step 2: Create the USER_DEFINED layout
layout_id = disp.add_master_layout(displayer.DisplayerLayout(
    displayer.Layouts.USER_DEFINED,
    user_defined_config=layout_config,
    subtitle="My Custom Layout"
))

# Step 3: Add items to each field using the field_id as the column parameter
# Note: Use the field_id string (e.g., 'example1') as the column parameter

disp.add_display_item(
    displayer.DisplayerItemText("Content for example1"),
    column="example1",  # Use field_id as column
    layout_id=layout_id
)

disp.add_display_item(
    displayer.DisplayerItemInputString("input2", "Label", "Default"),
    column="example2",
    layout_id=layout_id
)

# Continue for all fields in your layout...
'''
    
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_usage",
        code=code_example,
        language="python",
        show_line_numbers=True
    ), 0)
    
    # JSON structure explanation
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="JSON Structure"
    ))
    
    json_structure = '''{
    "version": "1.0",
    "columns": 12,  // Bootstrap 12-column grid
    "items": [
        {
            "field_id": "example1",  // Unique field identifier
            "x": 0,                  // Column position (0-11)
            "y": 0,                  // Row position
            "w": 6,                  // Width in columns (1-12)
            "h": 1                   // Height in rows
        },
        {
            "field_id": "example2",
            "x": 6,
            "y": 0,
            "w": 6,
            "h": 1
        }
    ]
}'''
    
    disp.add_display_item(displayer.DisplayerItemCode(
        id="json_structure",
        code=json_structure,
        language="json",
        show_line_numbers=True
    ), 0)
    
    # Best practices
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Best Practices"
    ))
    
    best_practices = """
    <ul class="list-group">
        <li class="list-group-item">
            <strong>Validation:</strong> The layout configuration is validated automatically. 
            Ensure x + w ≤ 12 for each item.
        </li>
        <li class="list-group-item">
            <strong>Field IDs:</strong> Use descriptive field IDs that match your data model 
            (not just example1, example2...).
        </li>
        <li class="list-group-item">
            <strong>Persistence:</strong> Store layout configurations in your database or config files 
            for reuse across sessions.
        </li>
        <li class="list-group-item">
            <strong>Responsive:</strong> GridStack handles mobile responsiveness automatically, 
            stacking items vertically on small screens.
        </li>
        <li class="list-group-item">
            <strong>Testing:</strong> Always preview your layout with actual data before deploying 
            to production.
        </li>
    </ul>
    """
    
    disp.add_display_item(displayer.DisplayerItemText(best_practices), 0)
    
    display_content = disp.display()
    return render_template("base_content.j2", content=display_content, **display_content)
