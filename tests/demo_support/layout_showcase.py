"""
Layout Showcase - Auto-generated layout type demonstrations

This module showcases all DisplayerLayout types with examples.
"""

from flask import Blueprint, render_template, redirect, url_for, session, request
from functools import wraps
from src.modules import displayer

# Create blueprint for layout showcase
layout_bp = Blueprint('layouts', __name__, url_prefix='/layouts')


def require_login(f):
    """Decorator to require login for layout showcase pages."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('common.login'))
        return f(*args, **kwargs)
    return decorated_function


def get_all_layouts():
    """
    Get all available layout types.
    
    Returns:
        list: List of tuples (layout_name, layout_enum, description)
    """
    layouts = [
        ("Vertical", displayer.Layouts.VERTICAL, "Items flow naturally in columns (small items left-to-right, large items stack)"),
        ("Horizontal", displayer.Layouts.HORIZONTAL, "Items always stack vertically (forced block display, one per row)"),
        ("Table", displayer.Layouts.TABLE, "Tabular layout with rows and columns"),
        ("Tabs", displayer.Layouts.TABS, "Tabbed interface for organizing content"),
        ("Spacer", displayer.Layouts.SPACER, "Empty space for visual separation"),
        ("User-Defined", displayer.Layouts.USER_DEFINED, "Custom grid layout with visual drag-and-drop editor"),
    ]
    return layouts


@layout_bp.route('/')
@require_login
def index():
    """Layout showcase index - shows all layout types."""
    disp = displayer.Displayer()
    disp.add_generic("Layout Showcase")
    disp.set_title("DisplayerLayout Showcase")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Layouts", "layouts.index", [])
    
    # Info alert
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "<strong>Layout Type Showcase</strong> - "
        "Explore all available layout types with live examples and code snippets. "
        "Layouts control how DisplayerItems are arranged on the page.",
        displayer.BSstyle.INFO
    ), 0)
    
    # Get all layouts
    layouts = get_all_layouts()
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle=f"{len(layouts)} Layout Types"
    ))
    
    layout_id = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE,
        columns=["Layout Type", "Description", "Action"]
    ))
    
    for line, (layout_name, layout_enum, description) in enumerate(layouts):
        # Layout name
        disp.add_display_item(
            displayer.DisplayerItemText(f"<strong>{layout_name}</strong>"),
            column=0, layout_id=layout_id, line=line
        )
        
        # Description
        disp.add_display_item(
            displayer.DisplayerItemText(description),
            column=1, layout_id=layout_id, line=line
        )
        
        # Button - Special handling for User-Defined layout
        if layout_name.lower() == "user-defined":
            link = url_for('user_defined_layout.index')
        else:
            link = url_for('layouts.layout_detail', layout=layout_name.lower())
        
        disp.add_display_item(
            displayer.DisplayerItemButtonLink(
                id=f"btn_{layout_name.lower().replace('-', '_')}",
                text="View Examples",
                icon="arrow-right",
                link=link,
                color=displayer.BSstyle.PRIMARY
            ),
            column=2, layout_id=layout_id, line=line
        )
    
    return render_template("base_content.j2", content=disp.display())


@layout_bp.route('/layout/<layout>')
@layout_bp.route('/layout')  # Also accept query parameter for sidebar compatibility
@require_login
def layout_detail(layout: str = ""):
    """Display examples and documentation for a specific layout type."""
    # Handle both path parameter and query parameter
    if not layout:
        layout = request.args.get('layout', '')
    
    if not layout:
        return redirect(url_for('layouts.index'))
    
    layout = layout.lower()
    
    # Map layout name to function
    layout_functions = {
        'vertical': show_vertical_layout,
        'horizontal': show_horizontal_layout,
        'table': show_table_layout,
        'tabs': show_tabs_layout,
        'spacer': show_spacer_layout,
    }
    
    # Redirect USER_DEFINED to its own blueprint
    if layout == 'user-defined':
        return redirect(url_for('user_defined_layout.index'))
    
    if layout not in layout_functions:
        return redirect(url_for('layouts.index'))
    
    return layout_functions[layout]()


def show_vertical_layout():
    """Show vertical layout examples."""
    disp = displayer.Displayer()
    disp.add_generic("Vertical Layout")
    disp.set_title("Vertical Layout - Column-Based Grid")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Layouts", "layouts.index", [])
    disp.add_breadcrumb("Vertical", "layouts.layout_detail", ["layout=vertical"])
    
    # Description
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "<strong>Vertical Layout (Bootstrap Grid)</strong><br>"
        "Creates columns that flow horizontally. Uses Bootstrap's 12-column grid system. "
        "Each column width is specified as a number from 1-12. Total should equal 12 for full width.",
        displayer.BSstyle.INFO
    ), 0)
    
    # Example 1: Equal columns
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [4, 4, 4],
        subtitle="Example 1: Three Equal Columns [4, 4, 4]"
    ))
    disp.add_display_item(displayer.DisplayerItemText("Column 1 (width=4)"), 0)
    disp.add_display_item(displayer.DisplayerItemText("Column 2 (width=4)"), 1)
    disp.add_display_item(displayer.DisplayerItemText("Column 3 (width=4)"), 2)
    
    # Code snippet
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    code_example = '''layout_id = disp.add_master_layout(displayer.DisplayerLayout(
    displayer.Layouts.VERTICAL, [4, 4, 4],
    subtitle="Three Equal Columns"
))
disp.add_display_item(displayer.DisplayerItemText("Column 1"), 0, layout_id=layout_id)
disp.add_display_item(displayer.DisplayerItemText("Column 2"), 1, layout_id=layout_id)
disp.add_display_item(displayer.DisplayerItemText("Column 3"), 2, layout_id=layout_id)'''
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_vertical_1",
        code=code_example,
        language="python",
        show_line_numbers=True
    ), 0)
    
    # Example 2: Variable columns
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 6, 3],
        subtitle="Example 2: Variable Width Columns [3, 6, 3]"
    ))
    disp.add_display_item(displayer.DisplayerItemText("Small (3)"), 0)
    disp.add_display_item(displayer.DisplayerItemText("Large (6)"), 1)
    disp.add_display_item(displayer.DisplayerItemText("Small (3)"), 2)
    
    # Code snippet
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    code_example = '''disp.add_master_layout(displayer.DisplayerLayout(
    displayer.Layouts.VERTICAL, [3, 6, 3],
    subtitle="Variable Width Columns"
))
disp.add_display_item(displayer.DisplayerItemText("Small"), 0)
disp.add_display_item(displayer.DisplayerItemText("Large"), 1)
disp.add_display_item(displayer.DisplayerItemText("Small"), 2)'''
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_vertical_2",
        code=code_example,
        language="python",
        show_line_numbers=True
    ), 0)
    
    # Example 3: Full width
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Example 3: Full Width Single Column [12]"
    ))
    disp.add_display_item(displayer.DisplayerItemText("This content spans the full width (12 columns)"), 0)
    
    # Code snippet
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    code_example = '''disp.add_master_layout(displayer.DisplayerLayout(
    displayer.Layouts.VERTICAL, [12],
    subtitle="Full Width"
))
disp.add_display_item(displayer.DisplayerItemText("Full width content"), 0)'''
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_vertical_3",
        code=code_example,
        language="python",
        show_line_numbers=False
    ), 0)
    
    return render_template("base_content.j2", content=disp.display())


def show_horizontal_layout():
    """Show horizontal layout examples."""
    disp = displayer.Displayer()
    disp.add_generic("Horizontal Layout")
    disp.set_title("Horizontal Layout - Force Vertical Stacking")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Layouts", "layouts.index", [])
    disp.add_breadcrumb("Horizontal", "layouts.layout_detail", ["layout=horizontal"])
    
    # Description
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        id="desc",
        title="HORIZONTAL Layout - Forced Vertical Stacking",
        fancy_header=True,
        text="Forces each item to take full column width and stack vertically, one per row. "
        "Unlike VERTICAL layout where small items flow left-to-right if they fit, "
        "HORIZONTAL wraps each item in a block-level div (mb-2) ensuring they always stack. "
        "Use [12] for full width, [8] for centered column, etc.",
        highlightType=displayer.BSstyle.INFO,
        icon="information"
    ), 0)
    
    # Example 1: Full width stacked items
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Example 1: Full Width Stacked Items [12]"
    ))
    
    h_layout = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.HORIZONTAL,
        columns=[12]
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        id="alert1",
        text="First item - Full width alert box",
        highlightType=displayer.BSstyle.PRIMARY,
        icon="information"
    ), column=0, layout_id=h_layout)
    disp.add_display_item(displayer.DisplayerItemText(
        "<p>Second item - Regular text content that flows naturally.</p>"
    ), column=0, layout_id=h_layout)
    disp.add_display_item(displayer.DisplayerItemAlert(
        id="alert2",
        text="Third item - Another alert box stacked below",
        highlightType=displayer.BSstyle.SUCCESS,
        icon="check-circle"
    ), column=0, layout_id=h_layout)
    
    # Code snippet
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    code_example = '''h_layout = disp.add_master_layout(displayer.DisplayerLayout(
    displayer.Layouts.HORIZONTAL,
    columns=[12]  # Full width
))
disp.add_display_item(displayer.DisplayerItemAlert(id="a1", text="...", highlightType=BSstyle.PRIMARY), column=0, layout_id=h_layout)
disp.add_display_item(displayer.DisplayerItemText(...), column=0, layout_id=h_layout)
disp.add_display_item(displayer.DisplayerItemAlert(id="a2", text="...", highlightType=BSstyle.SUCCESS), column=0, layout_id=h_layout)'''
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_horizontal_1",
        code=code_example,
        language="python",
        show_line_numbers=True
    ), 0)
    
    # Example 2: Centered narrower column
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Example 2: Centered Column [8] with Alignment"
    ))
    
    h_layout2 = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.HORIZONTAL,
        columns=[8],
        alignment=[displayer.BSalign.C]
    ))
    disp.add_display_item(displayer.DisplayerItemText(
        "<h5>Centered Content</h5>"
    ), column=0, layout_id=h_layout2)
    disp.add_display_item(displayer.DisplayerItemText(
        "<p>This column is only 8/12 width, creating margins on both sides. "
        "Items are center-aligned within the column.</p>"
    ), column=0, layout_id=h_layout2)
    disp.add_display_item(displayer.DisplayerItemBadge(
        "Centered Badge",
        displayer.BSstyle.INFO
    ), column=0, layout_id=h_layout2)
    
    # Code snippet
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    code_example2 = '''h_layout = disp.add_master_layout(displayer.DisplayerLayout(
    displayer.Layouts.HORIZONTAL,
    columns=[8],  # Narrower, centered column
    alignment=[displayer.BSalign.C]  # C = center
))
disp.add_display_item(displayer.DisplayerItemText("<h5>Centered</h5>"), column=0, layout_id=h_layout)
disp.add_display_item(displayer.DisplayerItemText("<p>Content</p>"), column=0, layout_id=h_layout)
disp.add_display_item(displayer.DisplayerItemBadge("Badge", BSstyle.INFO), column=0, layout_id=h_layout)'''
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_horizontal_2",
        code=code_example2,
        language="python",
        show_line_numbers=True
    ), 0)
    
    # Example 3: Comparison with VERTICAL - Key Difference
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Example 3: Key Difference - HORIZONTAL vs VERTICAL"
    ))
    
    # Show VERTICAL behavior with badges
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="VERTICAL [12] - Small items flow left-to-right"
    ))
    v_layout = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL,
        columns=[12]
    ))
    disp.add_display_item(displayer.DisplayerItemBadge("Badge 1", displayer.BSstyle.PRIMARY), column=0, layout_id=v_layout)
    disp.add_display_item(displayer.DisplayerItemBadge("Badge 2", displayer.BSstyle.SUCCESS), column=0, layout_id=v_layout)
    disp.add_display_item(displayer.DisplayerItemBadge("Badge 3", displayer.BSstyle.WARNING), column=0, layout_id=v_layout)
    disp.add_display_item(displayer.DisplayerItemText("<p class='mt-2'>↑ Notice badges appear left-to-right (natural flow)</p>"), column=0, layout_id=v_layout)
    
    # Show HORIZONTAL behavior with same badges
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="HORIZONTAL [12] - All items forced vertically"
    ))
    h_layout3 = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.HORIZONTAL,
        columns=[12]
    ))
    disp.add_display_item(displayer.DisplayerItemBadge("Badge 1", displayer.BSstyle.PRIMARY), column=0, layout_id=h_layout3)
    disp.add_display_item(displayer.DisplayerItemBadge("Badge 2", displayer.BSstyle.SUCCESS), column=0, layout_id=h_layout3)
    disp.add_display_item(displayer.DisplayerItemBadge("Badge 3", displayer.BSstyle.WARNING), column=0, layout_id=h_layout3)
    disp.add_display_item(displayer.DisplayerItemText("<p>↑ Notice badges stack vertically (forced block display)</p>"), column=0, layout_id=h_layout3)
    
    # Explanation
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        id="alert_key_difference",
        fancy_header=True,
        title="Key Difference",
        icon="lightbulb",
        text=
        "<ul>"
        "<li><strong>VERTICAL layout:</strong> Items flow naturally. Small items (badges, buttons) "
        "appear <strong>left-to-right</strong> if they fit in the column width. "
        "This is standard Bootstrap behavior.</li>"
        "<li><strong>HORIZONTAL layout:</strong> Each item is wrapped in a block-level div with mb-2 spacing. "
        "Items <strong>always stack vertically</strong>, one per row, regardless of their size.</li>"
        "</ul>"
        "<p><strong>Use HORIZONTAL when:</strong> You want guaranteed vertical stacking (forms, card lists, sequential content).<br>"
        "<strong>Use VERTICAL when:</strong> You want natural flow or need multiple columns.</p>",
        highlightType=displayer.BSstyle.PRIMARY,
    ), 0)
    
    return render_template("base_content.j2", content=disp.display())


def show_table_layout():
    """Show table layout examples with all table modes."""
    disp = displayer.Displayer()
    disp.add_generic("Table Layout")
    disp.set_title("Table Layout - All Table Modes")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Layouts", "layouts.index", [])
    disp.add_breadcrumb("Table", "layouts.layout_detail", ["layout=table"])
    
    # Description
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "<strong>Table Layout - All Modes</strong><br>"
        "Tables support multiple rendering modes for different use cases: "
        "<strong>SIMPLE</strong> (plain HTML), <strong>INTERACTIVE</strong> (DataTables with manual population), "
        "<strong>BULK_DATA</strong> (JSON pre-loaded for large datasets), and <strong>SERVER_SIDE</strong> (AJAX endpoint).",
        displayer.BSstyle.INFO
    ), 0)
    
    # ===== Mode 1: SIMPLE - Plain HTML Table =====
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="1. TableMode.SIMPLE - Plain HTML Table"
    ))
    disp.add_display_item(displayer.DisplayerItemText(
        "<p>Basic HTML table without DataTables JavaScript. Best for small datasets (< 20 rows). "
        "No search, sorting, or pagination features.</p>"
    ), 0)
    
    table_id = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE,
        columns=["Name", "Email", "Role"]
        # No datatable_config = plain HTML
    ))
    
    disp.add_display_item(displayer.DisplayerItemText("Alice Smith"), column=0, line=0, layout_id=table_id)
    disp.add_display_item(displayer.DisplayerItemText("alice@example.com"), column=1, line=0, layout_id=table_id)
    disp.add_display_item(displayer.DisplayerItemBadge("Admin", displayer.BSstyle.PRIMARY), column=2, line=0, layout_id=table_id)
    
    disp.add_display_item(displayer.DisplayerItemText("Bob Johnson"), column=0, line=1, layout_id=table_id)
    disp.add_display_item(displayer.DisplayerItemText("bob@example.com"), column=1, line=1, layout_id=table_id)
    disp.add_display_item(displayer.DisplayerItemBadge("User", displayer.BSstyle.SUCCESS), column=2, line=1, layout_id=table_id)
    
    # Code snippet for SIMPLE mode
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    code_simple = '''# SIMPLE Mode - Plain HTML table (no DataTables)
table_id = disp.add_master_layout(displayer.DisplayerLayout(
    displayer.Layouts.TABLE,
    columns=["Name", "Email", "Role"]
    # No datatable_config = plain HTML table
))

# Add rows using DisplayerItems
disp.add_display_item(displayer.DisplayerItemText("Alice"), column=0, line=0, layout_id=table_id)
disp.add_display_item(displayer.DisplayerItemText("alice@example.com"), column=1, line=0, layout_id=table_id)
disp.add_display_item(displayer.DisplayerItemBadge("Admin", BSstyle.PRIMARY), column=2, line=0, layout_id=table_id)'''
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_table_simple",
        code=code_simple,
        language="python",
        show_line_numbers=True
    ), 0)
    
    # ===== Mode 2: INTERACTIVE - Manual Row Population =====
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="2. TableMode.INTERACTIVE - DataTables with Manual Population"
    ))
    disp.add_display_item(displayer.DisplayerItemText(
        "<p>Uses DataTables for rendering with DisplayerItems for content. Best for medium datasets (20-100 rows). "
        "Includes search, sorting, and optional search panes on specific columns.</p>"
    ), 0)
    
    table_id = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE,
        columns=["Product", "Price", "Stock", "Actions"],
        datatable_config={
            "table_id": "interactive_demo",
            "mode": displayer.TableMode.INTERACTIVE,
            "searchable_columns": [0, 2]  # Search panes on Product and Stock columns
        }
    ))
    
    products = [
        ("Laptop", "$1,299", "In Stock", "primary"),
        ("Mouse", "$29", "Low Stock", "warning"),
        ("Keyboard", "$89", "In Stock", "success"),
        ("Monitor", "$349", "Out of Stock", "error"),
    ]
    
    for line, (product, price, stock, badge_style) in enumerate(products):
        disp.add_display_item(displayer.DisplayerItemText(product), column=0, line=line, layout_id=table_id)
        disp.add_display_item(displayer.DisplayerItemText(price), column=1, line=line, layout_id=table_id)
        disp.add_display_item(
            displayer.DisplayerItemBadge(stock, getattr(displayer.BSstyle, badge_style.upper())), 
            column=2, line=line, layout_id=table_id
        )
        disp.add_display_item(displayer.DisplayerItemButton(f"buy_{line}", "Buy Now"), column=3, line=line, layout_id=table_id)
    
    # Code snippet for INTERACTIVE mode
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    code_interactive = '''# INTERACTIVE Mode - DataTables with manual row population
table_id = disp.add_master_layout(displayer.DisplayerLayout(
    displayer.Layouts.TABLE,
    columns=["Product", "Price", "Stock", "Actions"],
    datatable_config={
        "table_id": "interactive_demo",
        "mode": displayer.TableMode.INTERACTIVE,
        "searchable_columns": [0, 2]  # Search panes on Product & Stock columns
    }
))

# Add rows with DisplayerItems
products = [("Laptop", "$1,299", "In Stock"), ("Mouse", "$29", "Low Stock")]
for line, (product, price, stock) in enumerate(products):
    disp.add_display_item(DisplayerItemText(product), column=0, line=line, layout_id=table_id)
    disp.add_display_item(DisplayerItemText(price), column=1, line=line, layout_id=table_id)
    disp.add_display_item(DisplayerItemBadge(stock, BSstyle.SUCCESS), column=2, line=line, layout_id=table_id)'''
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_table_interactive",
        code=code_interactive,
        language="python",
        show_line_numbers=True
    ), 0)
    
    # ===== Mode 3: BULK_DATA - Pre-loaded JSON =====
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="3. TableMode.BULK_DATA - Pre-loaded JSON Data"
    ))
    disp.add_display_item(displayer.DisplayerItemText(
        "<p>Most efficient for large datasets (100s-1000s of rows). Data is loaded as JSON array. "
        "Full DataTables features with search panes, sorting, and pagination.</p>"
    ), 0)
    
    bulk_data = [
        {"User": "Alice Cooper", "Department": "Engineering", "Status": "Active", "Projects": 5},
        {"User": "Bob Dylan", "Department": "Marketing", "Status": "Active", "Projects": 3},
        {"User": "Charlie Brown", "Department": "Engineering", "Status": "On Leave", "Projects": 2},
        {"User": "Diana Ross", "Department": "Sales", "Status": "Active", "Projects": 8},
        {"User": "Eddie Vedder", "Department": "Engineering", "Status": "Active", "Projects": 4},
        {"User": "Frank Sinatra", "Department": "Sales", "Status": "Active", "Projects": 6},
        {"User": "Grace Jones", "Department": "Marketing", "Status": "Active", "Projects": 7},
        {"User": "Henry Rollins", "Department": "Engineering", "Status": "On Leave", "Projects": 1},
    ]
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE,
        columns=["User", "Department", "Status", "Projects"],
        datatable_config={
            "table_id": "bulk_demo",
            "mode": displayer.TableMode.BULK_DATA,
            "data": bulk_data,
            "columns": [
                {"data": "User"},
                {"data": "Department"},
                {"data": "Status"},
                {"data": "Projects"}
            ],
            "searchable_columns": [1, 2]  # Search panes on Department & Status
        }
    ))
    
    # Code snippet for BULK_DATA mode
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    code_bulk = '''# BULK_DATA Mode - Pre-loaded JSON (best for large datasets)
bulk_data = [
    {"User": "Alice", "Department": "Engineering", "Status": "Active", "Projects": 5},
    {"User": "Bob", "Department": "Marketing", "Status": "Active", "Projects": 3},
    # ... hundreds or thousands of rows
]

disp.add_master_layout(displayer.DisplayerLayout(
    displayer.Layouts.TABLE,
    columns=["User", "Department", "Status", "Projects"],
    datatable_config={
        "table_id": "bulk_demo",
        "mode": displayer.TableMode.BULK_DATA,
        "data": bulk_data,  # Direct JSON data
        "columns": [
            {"data": "User"},
            {"data": "Department"},
            {"data": "Status"},
            {"data": "Projects"}
        ],
        "searchable_columns": [1, 2]  # Search panes on Department & Status
    }
))'''
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_table_bulk",
        code=code_bulk,
        language="python",
        show_line_numbers=True
    ), 0)
    
    # ===== Mode 4: SERVER_SIDE - AJAX Endpoint =====
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="4. TableMode.SERVER_SIDE - AJAX Data Source"
    ))
    disp.add_display_item(displayer.DisplayerItemText(
        "<p>For dynamic or real-time data. Fetches data from an API endpoint using AJAX. "
        "Supports auto-refresh, server-side pagination, and real-time updates.</p>"
    ), 0)
    
    disp.add_display_item(displayer.DisplayerItemAlert(
        "<strong>Note:</strong> SERVER_SIDE mode requires a Flask API endpoint. "
        "See code example below for implementation details.",
        displayer.BSstyle.WARNING
    ), 0)
    
    # Code snippet for SERVER_SIDE mode
    code_server = '''# SERVER_SIDE Mode - AJAX endpoint (for dynamic/real-time data)
disp.add_master_layout(displayer.DisplayerLayout(
    displayer.Layouts.TABLE,
    columns=["Name", "Status", "Last Update"],
    datatable_config={
        "table_id": "ajax_demo",
        "mode": displayer.TableMode.SERVER_SIDE,
        "api_endpoint": "api.get_users",  # Flask route name
        "columns": [
            {"data": "Name"},
            {"data": "Status"},
            {"data": "LastUpdate"}
        ],
        "refresh_interval": 3000  # Auto-refresh every 3 seconds
    }
))

# API endpoint implementation (Flask route):
@api_bp.route('/get-users')
def get_users():
    """API endpoint for SERVER_SIDE table mode."""
    # Return JSON in DataTables format
    return jsonify({
        "data": [
            {"Name": "Alice", "Status": "Online", "LastUpdate": "2 min ago"},
            {"Name": "Bob", "Status": "Away", "LastUpdate": "15 min ago"}
        ]
    })'''
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_table_server",
        code=code_server,
        language="python",
        show_line_numbers=True
    ), 0)
    
    # Summary table
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Quick Comparison"
    ))
    
    summary_id = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE,
        columns=["Mode", "Best For", "Features", "Performance"]
    ))
    
    comparisons = [
        ("SIMPLE", "< 20 rows", "Basic HTML table", "Fast"),
        ("INTERACTIVE", "20-100 rows", "Search, sort, pagination", "Medium"),
        ("BULK_DATA", "100s-1000s rows", "All DataTables features", "Fast"),
        ("SERVER_SIDE", "Real-time data", "AJAX, auto-refresh", "Depends on API"),
    ]
    
    for line, (mode, best_for, features, performance) in enumerate(comparisons):
        disp.add_display_item(displayer.DisplayerItemBadge(mode, displayer.BSstyle.PRIMARY), 
                             column=0, line=line, layout_id=summary_id)
        disp.add_display_item(displayer.DisplayerItemText(best_for), 
                             column=1, line=line, layout_id=summary_id)
        disp.add_display_item(displayer.DisplayerItemText(features), 
                             column=2, line=line, layout_id=summary_id)
        disp.add_display_item(displayer.DisplayerItemText(performance), 
                             column=3, line=line, layout_id=summary_id)
    
    return render_template("base_content.j2", content=disp.display())


def show_tabs_layout():
    """Show tabs layout examples."""
    disp = displayer.Displayer()
    disp.add_generic("Tabs Layout")
    disp.set_title("Tabs Layout - Tabbed Interface")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Layouts", "layouts.index", [])
    disp.add_breadcrumb("Tabs", "layouts.layout_detail", ["layout=tabs"])
    
    # Description
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "<strong>Tabs Layout</strong><br>"
        "Creates a tabbed interface where content is organized into separate tabs. "
        "Users can click tabs to switch between different content sections. "
        "Useful for organizing related content without overwhelming the page.",
        displayer.BSstyle.INFO
    ), 0)
    
    # Example: Tabs with different content
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Example: Multi-Tab Interface"
    ))
    
    tabs_id = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABS,
        ["Overview", "Details", "Settings"]
    ))
    
    # Tab 0: Overview
    disp.add_display_item(displayer.DisplayerItemText(
        "<h5>Overview Tab</h5><p>This is the overview content. "
        "Tabs are great for organizing different sections of information.</p>"
    ), column=0, layout_id=tabs_id)
    
    # Tab 1: Details
    disp.add_display_item(displayer.DisplayerItemText(
        "<h5>Details Tab</h5><p>This tab contains detailed information. "
        "Each tab can contain any DisplayerItems including nested layouts.</p>"
    ), column=1, layout_id=tabs_id)
    
    # Tab 2: Settings
    disp.add_display_item(displayer.DisplayerItemText(
        "<h5>Settings Tab</h5><p>This tab could contain form inputs or settings. "
        "Tabs help keep the interface clean and organized.</p>"
    ), column=2, layout_id=tabs_id)
    
    # Code snippet
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    code_example = '''tabs_id = disp.add_master_layout(displayer.DisplayerLayout(
    displayer.Layouts.TABS,
    ["Overview", "Details", "Settings"]
))

# Add content to each tab by specifying column (tab index)
disp.add_display_item(displayer.DisplayerItemText("Overview content"), column=0, layout_id=tabs_id)
disp.add_display_item(displayer.DisplayerItemText("Details content"), column=1, layout_id=tabs_id)
disp.add_display_item(displayer.DisplayerItemText("Settings content"), column=2, layout_id=tabs_id)'''
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_tabs_1",
        code=code_example,
        language="python",
        show_line_numbers=True
    ), 0)
    
    return render_template("base_content.j2", content=disp.display())


def show_spacer_layout():
    """Show spacer layout examples."""
    disp = displayer.Displayer()
    disp.add_generic("Spacer Layout")
    disp.set_title("Spacer Layout - Visual Separation")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Layouts", "layouts.index", [])
    disp.add_breadcrumb("Spacer", "layouts.layout_detail", ["layout=spacer"])
    
    # Description
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "<strong>Spacer Layout</strong><br>"
        "Creates empty vertical space for visual separation between sections. "
        "Helps improve readability by adding breathing room between dense content areas.",
        displayer.BSstyle.INFO
    ), 0)
    
    # Example: Spacer usage
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Example: Content with Spacers"
    ))
    
    disp.add_display_item(displayer.DisplayerItemText(
        "<p><strong>Section 1:</strong> This is the first section of content.</p>"
    ), 0)
    
    # Add spacer
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.SPACER, [12]
    ))
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemText(
        "<p><strong>Section 2:</strong> Notice the empty space above? That's a spacer layout providing visual separation.</p>"
    ), 0)
    
    # Add another spacer
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.SPACER, [12]
    ))
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemText(
        "<p><strong>Section 3:</strong> Spacers are especially useful between major sections to improve page flow.</p>"
    ), 0)
    
    # Code snippet
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    code_example = '''# Content before spacer
disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
disp.add_display_item(displayer.DisplayerItemText("Section 1"), 0)

# Add spacer
disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.SPACER, [12]))

# Content after spacer
disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
disp.add_display_item(displayer.DisplayerItemText("Section 2"), 0)'''
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_spacer_1",
        code=code_example,
        language="python",
        show_line_numbers=True
    ), 0)
    
    return render_template("base_content.j2", content=disp.display())


def get_all_layouts_for_sidebar():
    """
    Get all layouts for sidebar generation.
    
    Returns:
        list: List of tuples (layout_name, layout_key)
    """
    layouts = get_all_layouts()
    return [(name, name.lower()) for name, _, _ in layouts]
