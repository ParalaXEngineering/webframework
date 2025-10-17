"""
Component Showcase - Auto-generated displayer item routes

This module automatically discovers all DisplayerItem classes and creates
routes for them organized by category. When a new displayer item is added,
it will automatically appear in the sidebar.
"""

from flask import Blueprint, render_template, redirect, url_for, session
from functools import wraps
from src.modules import displayer

# Create blueprint for component showcase
showcase_bp = Blueprint('showcase', __name__, url_prefix='/components')


def require_login(f):
    """Decorator to require login for showcase pages."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('common.login'))
        return f(*args, **kwargs)
    return decorated_function


def get_category_icon(category: str) -> str:
    """Get icon for a category."""
    icons = {
        'input': 'mdi-form-textbox',
        'display': 'mdi-text-box',
        'button': 'mdi-gesture-tap',
        'media': 'mdi-image-multiple',
        'layout': 'mdi-view-dashboard',
        'advanced': 'mdi-star'
    }
    return icons.get(category, 'mdi-palette')


def get_category_friendly_name(category: str) -> str:
    """Get friendly name for a category."""
    names = {
        'input': 'Input Components',
        'display': 'Display Components',
        'button': 'Buttons & Links',
        'media': 'Media Components',
        'layout': 'Layout Components',
        'advanced': 'Advanced Components'
    }
    return names.get(category, category.title())


@showcase_bp.route('/')
@require_login
def index():
    """Component showcase index - shows all categories."""
    disp = displayer.Displayer()
    disp.add_generic("Component Showcase")
    disp.set_title("DisplayerItem Component Showcase")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Components", "showcase.index", [])
    
    # Info alert
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    disp.add_display_item(displayer.DisplayerItemAlert(
        "<strong>Auto-Generated Component Showcase</strong> - "
        "All displayer items are automatically discovered and organized by category. "
        "When you add a new DisplayerItem class, it will appear here automatically.",
        displayer.BSstyle.INFO
    ), 0)
    
    # Get all categories
    all_categories_dict = displayer.DisplayerCategory.get_all()  # type: ignore
    
    # Display categories in a table for easy navigation
    categories = [cat for cat in all_categories_dict.keys() if all_categories_dict[cat]]  # type: ignore
    
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle=f"{len(categories)} Component Categories"
    ))
    
    layout_id = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE,
        columns=["Category", "Icon", "Components", "Action"]
    ))
    
    for line, category in enumerate(sorted(categories)):
        items = all_categories_dict[category]  # type: ignore
        
        # Category name
        disp.add_display_item(
            displayer.DisplayerItemText(f"<strong>{get_category_friendly_name(category)}</strong>"),
            column=0, layout_id=layout_id, line=line
        )
        
        # Icon
        disp.add_display_item(
            displayer.DisplayerItemText(f'<i class="mdi {get_category_icon(category)}"></i>'),
            column=1, layout_id=layout_id, line=line
        )
        
        # Count
        disp.add_display_item(
            displayer.DisplayerItemBadge(f"{len(items)}", displayer.BSstyle.INFO),
            column=2, layout_id=layout_id, line=line
        )
        
        # Button
        disp.add_display_item(
            displayer.DisplayerItemButtonLink(
                id=f"btn_{category}",
                text="Browse",
                icon="arrow-right",
                link=url_for('showcase.category', category=category),
                color=displayer.BSstyle.PRIMARY
            ),
            column=3, layout_id=layout_id, line=line
        )
    
    return render_template("base_content.j2", content=disp.display())


@showcase_bp.route('/category/<category>')
@showcase_bp.route('/category')  # Also accept query parameter for sidebar compatibility
@require_login
def category(category: str = ""):
    """Show all components in a category."""
    # Handle both path parameter and query parameter
    if not category:
        from flask import request
        category = request.args.get('category', '')
    
    disp = displayer.Displayer()
    category_name = get_category_friendly_name(category)
    disp.add_generic(category_name)
    disp.set_title(category_name)
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Components", "showcase.index", [])
    disp.add_breadcrumb(category_name, "showcase.category", [f"category={category}"])
    
    # Get items in this category
    items = displayer.DisplayerCategory.get_all(category)  # type: ignore
    
    if not items:
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [12]
        ))
        disp.add_display_item(displayer.DisplayerItemAlert(
            f"No components found in category: {category}",
            displayer.BSstyle.WARNING
        ), 0)
        return render_template("base_content.j2", content=disp.display())
    
    # Display items in a table
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle=f"{len(items)} components in this category"
    ))
    
    layout_id = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABLE,
        columns=["Component", "Description", "Action"]
    ))
    
    for line, item_class in enumerate(sorted(items, key=lambda x: x.__name__)):  # type: ignore
        # Component name
        item_name = getattr(item_class, '__name__', str(item_class))
        disp.add_display_item(
            displayer.DisplayerItemText(f"<code>{item_name}</code>"),
            column=0, layout_id=layout_id, line=line
        )
        
        # Description from docstring
        doc = getattr(item_class, '__doc__', None) or "No description available"
        doc = doc.strip().split('\n')[0]  # First line only
        disp.add_display_item(
            displayer.DisplayerItemText(doc),
            column=1, layout_id=layout_id, line=line
        )
        
        # View button
        disp.add_display_item(
            displayer.DisplayerItemButtonLink(
                id=f"view_{item_name}",
                text="View Demo",
                icon="eye",
                link=url_for('showcase.component', 
                           category=category,
                           component=item_name),
                color=displayer.BSstyle.PRIMARY
            ),
            column=2, layout_id=layout_id, line=line
        )
    
    return render_template("base_content.j2", content=disp.display())


@showcase_bp.route('/category/<category>/<component>')
@showcase_bp.route('/component')  # Also accept query parameters for sidebar compatibility
@require_login
def component(category: str = "", component: str = ""):
    """Display a single component demo."""
    import inspect
    from flask import request
    
    # Handle both path parameters and query parameters
    if not category:
        category = request.args.get('category', '')
    if not component:
        component = request.args.get('component', '')
    
    disp = displayer.Displayer()
    disp.add_generic(component)
    disp.set_title(f"{component} Demo")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Components", "showcase.index", [])
    disp.add_breadcrumb(get_category_friendly_name(category), 
                       "showcase.category", [f"category={category}"])
    disp.add_breadcrumb(component, "showcase.component", 
                       [f"category={category}", f"component={component}"])
    
    # Get the component class
    items = displayer.DisplayerCategory.get_all(category)  # type: ignore
    item_class = None
    for item in items:
        if item.__name__ == component:  # type: ignore
            item_class = item
            break
    
    if not item_class:
        disp.add_master_layout(displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [12]
        ))
        disp.add_display_item(displayer.DisplayerItemAlert(
            f"Component not found: {component}",
            displayer.BSstyle.ERROR
        ), 0)
        return render_template("base_content.j2", content=disp.display())
    
    # Component info - format docstring nicely
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    
    doc = item_class.__doc__ or "No documentation available"
    doc = doc.strip()
    
    # Clean up the docstring for display:
    # 1. Remove excessive indentation
    # 2. Preserve line breaks
    # 3. Format as HTML with proper breaks
    lines = doc.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            cleaned_lines.append(stripped)
        elif cleaned_lines:  # Empty line becomes a paragraph break
            cleaned_lines.append('<br>')
    
    formatted_doc = '<br>'.join(cleaned_lines)
    
    disp.add_display_item(displayer.DisplayerItemAlert(
        f"<strong>{component}</strong><br><br>{formatted_doc}",
        displayer.BSstyle.INFO
    ), 0)
    
    # Try to instantiate and display the component
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Live Demo"
    ))
    
    test_item = None
    error_msg = None
    
    try:
        # Check if item has instantiate_test method
        if hasattr(item_class, 'instantiate_test'):
            test_item = item_class.instantiate_test()  # type: ignore
            disp.add_display_item(test_item, 0)
        else:
            disp.add_display_item(displayer.DisplayerItemAlert(
                f"This component does not have an instantiate_test() method. "
                f"Add one to enable automatic testing.",
                displayer.BSstyle.WARNING
            ), 0)
    except Exception as e:
        error_msg = str(e)
        disp.add_display_item(displayer.DisplayerItemAlert(
            f"<strong>Error instantiating component:</strong><br><code>{error_msg}</code>",
            displayer.BSstyle.ERROR
        ), 0)
    
    # Extract and show usage examples from docstring
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Usage Example"
    ))
    
    try:
        # Get the class docstring and __init__ docstring
        class_doc = item_class.__doc__ or ""
        init_doc = item_class.__init__.__doc__ if hasattr(item_class.__init__, '__doc__') else ""  # type: ignore
        
        # Look for Example: section in docstrings
        example_code = None
        for doc in [init_doc, class_doc]:
            if not doc:
                continue
            
            lines = doc.split('\n')
            in_example = False
            example_lines = []
            
            for line in lines:
                # Start of example section
                if 'Example:' in line or 'Examples:' in line:
                    in_example = True
                    continue
                
                # End of example section (new section or unindented line)
                if in_example and line and not line.startswith(' '):
                    break
                
                # Collect example lines
                if in_example and line.strip():
                    # Remove the ">>>" prompt if present
                    cleaned = line.strip()
                    if cleaned.startswith('>>>'):
                        cleaned = cleaned[3:].strip()
                    elif cleaned.startswith('...'):
                        cleaned = cleaned[3:].strip()
                    
                    # Skip doctest output (lines without code)
                    if cleaned and not cleaned.startswith('#'):
                        example_lines.append(cleaned)
            
            if example_lines:
                example_code = '\n'.join(example_lines)
                break
        
        if example_code:
            # Display using DisplayerItemCode for proper syntax highlighting
            disp.add_display_item(displayer.DisplayerItemCode(
                id=f"code_{component}",
                code=example_code,
                language="python",
                show_line_numbers=True,
                title=f"{component} Usage Example"
            ), 0)
        else:
            # Fallback: show a generic instantiation example based on signature
            sig = inspect.signature(item_class.__init__)  # type: ignore
            params = []
            for param_name, param in sig.parameters.items():
                if param_name in ('self', 'itemType'):
                    continue
                # Use parameter name as example value
                if param.annotation == str or 'str' in str(param.annotation):
                    params.append(f'{param_name}="example_{param_name}"')
                elif param.annotation == int or 'int' in str(param.annotation):
                    params.append(f'{param_name}=0')
                elif param.annotation == bool or 'bool' in str(param.annotation):
                    params.append(f'{param_name}=True')
                elif 'BSstyle' in str(param.annotation):
                    params.append(f'{param_name}=BSstyle.PRIMARY')
                else:
                    params.append(f'{param_name}=...')
            
            example = f"item = {item_class.__name__}(\n    {',\n    '.join(params)}\n)"  # type: ignore
            disp.add_display_item(displayer.DisplayerItemCode(
                id=f"code_{component}_fallback",
                code=example,
                language="python",
                show_line_numbers=False,
                title="Auto-generated Example"
            ), 0)
            disp.add_display_item(displayer.DisplayerItemAlert(
                "No usage example found in docstring. Add an Example: section to the class or __init__ docstring.",
                displayer.BSstyle.WARNING
            ), 0)
            
    except Exception as e:
        disp.add_display_item(displayer.DisplayerItemAlert(
            f"<strong>Error extracting example:</strong><br><code>{str(e)}</code>",
            displayer.BSstyle.ERROR
        ), 0)
    
    # Show implementation details
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12],
        subtitle="Implementation Details"
    ))
    
    # Get __init__ signature
    try:
        sig = inspect.signature(item_class.__init__)  # type: ignore
        params = []
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            param_str = param_name
            if param.annotation != inspect.Parameter.empty:
                param_str += f": {param.annotation.__name__ if hasattr(param.annotation, '__name__') else str(param.annotation)}"
            if param.default != inspect.Parameter.empty:
                param_str += f" = {repr(param.default)}"
            params.append(param_str)
        
        constructor_sig = f"{item_class.__name__}({', '.join(params)})"  # type: ignore
    except:
        constructor_sig = f"{item_class.__name__}(...)"  # type: ignore
    
    disp.add_display_item(displayer.DisplayerItemText(
        f"<p><strong>Category:</strong> <code>{get_category_friendly_name(category)}</code></p>"
        f"<p><strong>Module:</strong> <code>{item_class.__module__}</code></p>"  # type: ignore
        f"<p><strong>Constructor:</strong> <code>{constructor_sig}</code></p>"
    ), 0)
    
    return render_template("base_content.j2", content=disp.display())


def get_all_components_for_sidebar():
    """
    Get all components organized by category for sidebar generation.
    
    Returns:
        list: List of tuples (category_name, category_key, component_count)
    """
    all_categories_dict = displayer.DisplayerCategory.get_all()  # type: ignore
    result = []
    
    for category, items in all_categories_dict.items():  # type: ignore
        if items:  # Only include non-empty categories
            result.append((
                get_category_friendly_name(category),
                category,
                len(items)
            ))
    
    return sorted(result)
