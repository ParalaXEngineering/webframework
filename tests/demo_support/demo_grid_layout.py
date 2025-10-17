"""
Grid Layout Demo

Demonstrates the GRID layout type with DisplayerItemGridEditor for creating
custom grid layouts using a visual drag-and-drop editor.
"""

import json
from flask import Blueprint, render_template, redirect, url_for, session, request
from functools import wraps
from src.modules import displayer
from src.modules.displayer import ResourceRegistry
from src.modules.utilities import util_post_to_json

# Create blueprint for grid layout demo
grid_layout_bp = Blueprint('grid_layout', __name__, url_prefix='/layouts/grid')


def require_login(f):
    """Decorator to require login for demo pages."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('common.login'))
        return f(*args, **kwargs)
    return decorated_function


@grid_layout_bp.route('/', methods=['GET', 'POST'])
@require_login
def index():
    """Single-page demo: Grid editor + live preview + code example."""
    disp = displayer.Displayer()
    disp.add_generic("Grid Layout Editor")
    disp.set_title("GRID Layout - Interactive Editor")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Layouts", "layouts.index", [])
    disp.add_breadcrumb("Grid", "grid_layout.index", [])
    
    # ========================================================================
    # SECTION 1: Grid Editor (Top)
    # ========================================================================
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    
    disp.add_display_item(displayer.DisplayerItemAlert(
        "<strong>GRID Layout Editor</strong><br>"
        "Design custom grid layouts with drag-and-drop. "
        "Select fields from the dropdown, add them to the grid, then drag and resize to create your layout. "
        "Click 'Save & Preview' to see the result below.",
        displayer.BSstyle.INFO,
        title="Interactive Grid Builder"
    ), 0)
    
    # Define available fields for the editor
    available_fields = {
        "header": "Page Header",
        "stats": "Statistics Widget",
        "chart": "Analytics Chart",
        "table": "Data Table",
        "sidebar": "Sidebar Info",
        "footer": "Footer Content",
        "alerts": "Alert Messages",
        "activity": "Recent Activity"
    }
    
    # Get saved layout from form submission or use None
    saved_layout_json = None
    if request.method == 'POST':
        print(f"[DEBUG] POST received. Form data keys: {list(request.form.keys())}")
        
        # Use util_post_to_json to parse the hierarchical form data
        form_data = util_post_to_json(dict(request.form))
        print(f"[DEBUG] Parsed form data: {form_data}")
        
        # The layout_config will be nested under the module name
        # Navigate the structure to find it
        if 'Grid Layout Editor' in form_data and 'layout_config' in form_data['Grid Layout Editor']:
            saved_layout_json = form_data['Grid Layout Editor']['layout_config']
            print(f"[DEBUG] Layout config extracted: {saved_layout_json[:100] if saved_layout_json else 'None'}...")
            # Store in session for persistence across refreshes
            session['grid_layout_demo'] = saved_layout_json
        else:
            print("[DEBUG] No layout_config found in parsed form data")
    elif 'grid_layout_demo' in session:
        # Load from session
        saved_layout_json = session['grid_layout_demo']
        print(f"[DEBUG] Loaded from session: {saved_layout_json[:100] if saved_layout_json else 'None'}...")
    
    # Add the grid editor
    disp.add_display_item(displayer.DisplayerItemGridEditor(
        id="layout_config",
        fields=available_fields,
        value=saved_layout_json,
        columns=12
    ), 0)
    
    # Save button
    disp.add_display_item(displayer.DisplayerItemButton(
        id="save_preview",
        text="Save and Preview",
        icon="content-save"
    ), 0)
    
    # ========================================================================
    # SECTION 2: Live Preview (Middle)
    # ========================================================================
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    
    disp.add_display_item(displayer.DisplayerItemAlert(
        "The grid layout you design above will be rendered here. Each field is shown as a card placeholder.",
        displayer.BSstyle.PRIMARY,
        title="Live Preview"
    ), 0)
    
    # If we have a saved layout, render it
    if saved_layout_json:
        print(f"[DEBUG] Rendering layout with JSON: {saved_layout_json[:200]}...")
        try:
            layout_config = json.loads(saved_layout_json)
            print(f"[DEBUG] Parsed config: {layout_config}")
            
            # Create GRID layout with the saved configuration
            preview_layout = displayer.DisplayerLayout(
                displayer.Layouts.GRID,
                grid_config=layout_config
            )
            disp.add_master_layout(preview_layout)
            print(f"[DEBUG] Added GRID layout with {len(layout_config.get('items', []))} items")
            
            # Add placeholder cards for each field in the layout
            for item_config in layout_config.get('items', []):
                field_id = item_config['field_id']
                field_name = available_fields.get(field_id, field_id)
                
                # Create a card placeholder showing the field info
                disp.add_display_item(
                    displayer.DisplayerItemCard(
                        id=f"preview_{field_id}",
                        title=field_id,
                        body=f"<strong>{field_name}</strong><br>"
                             f"<small class='text-muted'>Position: ({item_config['x']}, {item_config['y']}) | "
                             f"Size: {item_config['w']}×{item_config['h']}</small>",
                        icon="widgets",
                        header_color=displayer.BSstyle.PRIMARY,
                        footer_buttons=[]
                    ),
                    field_id  # Use field_id as the column parameter for GRID layout
                )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            disp.add_master_layout(displayer.DisplayerLayout(
                displayer.Layouts.VERTICAL, [12]
            ))
            disp.add_display_item(displayer.DisplayerItemAlert(
                f"Error rendering layout: {str(e)}",
                displayer.BSstyle.ERROR
            ), 0)
    else:
        # No layout yet
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [12]
        ))
        disp.add_display_item(displayer.DisplayerItemAlert(
            "No layout configured yet. Add fields to the grid editor above and click 'Save & Preview'.",
            displayer.BSstyle.WARNING
        ), 0)
    
    # ========================================================================
    # SECTION 3: Code Examples (Bottom)
    # ========================================================================
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))

    
    # Example 1: Adding the Grid Editor
    example_add_editor = '''# Step 1: Add the Grid Editor to your page
from src.modules import displayer

# Define available fields that users can add to the grid
available_fields = {
    "header": "Page Header",
    "stats": "Statistics Widget",
    "chart": "Analytics Chart",
    "table": "Data Table",
    "sidebar": "Sidebar Info"
}

# Add the grid editor (it includes a hidden field for the JSON)
disp.add_display_item(displayer.DisplayerItemGridEditor(
    id="layout_config",       # Form field name
    fields=available_fields,  # Available fields dict
    value=saved_json,         # Optional: preload existing layout
    columns=12                # Number of grid columns
), 0)

# Add a save button
disp.add_display_item(displayer.DisplayerItemButton(
    id="save_layout",
    text="Save Layout",
    icon="content-save"
), 0)
'''
    
    # Example 2: Recovering the data from POST
    example_recover_data = '''# Step 2: Recover the Grid Layout from POST request
from src.modules.utilities import util_post_to_json
import json

@app.route('/your-page', methods=['GET', 'POST'])
def your_page():
    if request.method == 'POST':
        # Parse the hierarchical form data
        form_data = util_post_to_json(dict(request.form))
        
        # Extract the layout config (nested under module name)
        # form_data = {'Your Module Name': {'layout_config': '...'}}
        module_name = 'Your Module Name'  # Use your module name
        if module_name in form_data and 'layout_config' in form_data[module_name]:
            layout_json = form_data[module_name]['layout_config']
            layout_config = json.loads(layout_json)
            
            # Save to database, session, etc.
            session['saved_layout'] = layout_json
            # or: db.save_layout(user_id, layout_config)
'''
    
    # Example 3: Displaying the Grid Layout
    example_display_grid = '''# Step 3: Display content using the saved GRID layout
from src.modules import displayer
import json

# Load the saved layout
layout_json = session.get('saved_layout')  # or from database
layout_config = json.loads(layout_json)

# Create a GRID layout with the configuration
grid_layout = displayer.DisplayerLayout(
    displayer.Layouts.GRID,
    grid_config=layout_config  # Pass the parsed JSON config
)
disp.add_master_layout(grid_layout)

# Add DisplayerItems for each field in the layout
for item in layout_config['items']:
    field_id = item['field_id']
    
    # Add your displayer items - they'll be positioned by the grid
    disp.add_display_item(
        displayer.DisplayerItemCard(
            id=f"card_{field_id}",
            title="My Content",
            body="Your content here...",
            icon="widgets"
        ),
        field_id  # IMPORTANT: Use field_id as the column parameter
    )
'''
    
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_add_editor",
        code=example_add_editor,
        language="python",
        title="1. Adding the Grid Editor",
        max_height="500px",
        show_line_numbers=True
    ), 0)
    
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_recover_data",
        code=example_recover_data,
        language="python",
        title="2. Recovering Data from POST",
        max_height="400px",
        show_line_numbers=True
    ), 0)
    
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_display_grid",
        code=example_display_grid,
        language="python",
        title="3. Displaying the Grid Layout",
        max_height="500px",
        show_line_numbers=True
    ), 0)
    
    # Current layout JSON display
    if saved_layout_json:
        disp.add_display_item(displayer.DisplayerItemCode(
            id="current_json",
            code=json.dumps(json.loads(saved_layout_json), indent=2),
            language="json",
            title="Current Layout Configuration",
            max_height="300px",
            show_line_numbers=False
        ), 0)
    
    # Render
    display_content = disp.display()
    return render_template("base_content.j2", content=display_content, **display_content, target="grid_layout.index")
