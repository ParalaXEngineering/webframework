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
        ("Vertical", displayer.Layouts.VERTICAL, "Columns arranged horizontally with customizable widths (Bootstrap grid)"),
        ("Horizontal", displayer.Layouts.HORIZONTAL, "Items arranged horizontally in a single row"),
        ("Table", displayer.Layouts.TABLE, "Tabular layout with rows and columns"),
        ("Tabs", displayer.Layouts.TABS, "Tabbed interface for organizing content"),
        ("Spacer", displayer.Layouts.SPACER, "Empty space for visual separation"),
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
        
        # Button
        disp.add_display_item(
            displayer.DisplayerItemButtonLink(
                id=f"btn_{layout_name.lower()}",
                text="View Examples",
                icon="arrow-right",
                link=url_for('layouts.layout_detail', layout=layout_name.lower()),
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
    disp.set_title("Horizontal Layout - Inline Items")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Layouts", "layouts.index", [])
    disp.add_breadcrumb("Horizontal", "layouts.layout_detail", ["layout=horizontal"])
    
    # Description
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "<strong>Horizontal Layout</strong><br>"
        "Arranges items in a single horizontal row. Items are displayed inline with minimal spacing. "
        "Useful for toolbars, button groups, and inline elements.",
        displayer.BSstyle.INFO
    ), 0)
    
    # Example 1: Button group
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Example 1: Button Group"
    ))
    
    h_layout = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.HORIZONTAL
    ))
    disp.add_display_item(displayer.DisplayerItemButton("btn1", "Save"), layout_id=h_layout)
    disp.add_display_item(displayer.DisplayerItemButton("btn2", "Cancel"), layout_id=h_layout)
    disp.add_display_item(displayer.DisplayerItemButton("btn3", "Reset"), layout_id=h_layout)
    
    # Code snippet
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    code_example = '''h_layout = disp.add_master_layout(displayer.DisplayerLayout(
    displayer.Layouts.HORIZONTAL
))
disp.add_display_item(displayer.DisplayerItemButton("btn1", "Save"), layout_id=h_layout)
disp.add_display_item(displayer.DisplayerItemButton("btn2", "Cancel"), layout_id=h_layout)
disp.add_display_item(displayer.DisplayerItemButton("btn3", "Reset"), layout_id=h_layout)'''
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_horizontal_1",
        code=code_example,
        language="python",
        show_line_numbers=True
    ), 0)
    
    return render_template("base_content.j2", content=disp.display())


def show_table_layout():
    """Show table layout examples."""
    disp = displayer.Displayer()
    disp.add_generic("Table Layout")
    disp.set_title("Table Layout - Tabular Data")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Layouts", "layouts.index", [])
    disp.add_breadcrumb("Table", "layouts.layout_detail", ["layout=table"])
    
    # Description
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "<strong>Table Layout</strong><br>"
        "Creates a structured table with headers and rows. Supports DataTables integration for "
        "advanced features like sorting, searching, and pagination. See the Table Modes demo for advanced examples.",
        displayer.BSstyle.INFO
    ), 0)
    
    # Example 1: Simple table
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Example 1: Simple Table"
    ))
    
    table_id = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE,
        columns=["Name", "Role", "Status"]
    ))
    
    disp.add_display_item(displayer.DisplayerItemText("Alice Smith"), column=0, line=0, layout_id=table_id)
    disp.add_display_item(displayer.DisplayerItemText("Developer"), column=1, line=0, layout_id=table_id)
    disp.add_display_item(displayer.DisplayerItemBadge("Active", displayer.BSstyle.SUCCESS), column=2, line=0, layout_id=table_id)
    
    disp.add_display_item(displayer.DisplayerItemText("Bob Johnson"), column=0, line=1, layout_id=table_id)
    disp.add_display_item(displayer.DisplayerItemText("Designer"), column=1, line=1, layout_id=table_id)
    disp.add_display_item(displayer.DisplayerItemBadge("Away", displayer.BSstyle.WARNING), column=2, line=1, layout_id=table_id)
    
    # Code snippet
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    code_example = '''table_id = disp.add_master_layout(displayer.DisplayerLayout(
    displayer.Layouts.TABLE,
    columns=["Name", "Role", "Status"]
))

# Add rows
disp.add_display_item(displayer.DisplayerItemText("Alice"), column=0, line=0, layout_id=table_id)
disp.add_display_item(displayer.DisplayerItemText("Developer"), column=1, line=0, layout_id=table_id)
disp.add_display_item(displayer.DisplayerItemBadge("Active", BSstyle.SUCCESS), column=2, line=0, layout_id=table_id)'''
    disp.add_display_item(displayer.DisplayerItemCode(
        id="code_table_1",
        code=code_example,
        language="python",
        show_line_numbers=True
    ), 0)
    
    # Link to advanced table demo
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        '<strong>Advanced Table Features</strong><br>'
        'For DataTables integration, search panes, server-side processing, and more, '
        'see the <a href="/demo/table-modes" class="alert-link">Table Modes Demo</a>.',
        displayer.BSstyle.INFO
    ), 0)
    
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
