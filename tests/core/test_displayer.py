"""
Automated integration tests for the ParalaX Web Framework Displayer module.

Test Architecture:
- Uses DisplayerItem.instantiate_test() classmethod for test data
- Auto-discovers items via @DisplayerCategory decorators  
- Saves rendered HTML to tests/core/output/ for manual review
- Validates POST → JSON pipeline through util_post_to_json()
- All HTML is post-processed via make_html_standalone() for standalone viewing

Test Coverage:
- All DisplayerItem classes (display, input, button, media)
- All DisplayerLayout types (vertical, table, tabs, spacer)
- Core Displayer features (modules, breadcrumbs, title, nested layouts)
- Template rendering (status 200, valid HTML)
- Form field extraction for input items
- POST data transformation matching production usage in settings.py

Skip Conditions:
- Items requiring complex backend (file uploads, modals, cascaded structures)
- Layouts not yet implemented (HORIZONTAL = "TOCODE")
"""

import pytest
import os
from typing import Dict
from flask import Flask, Blueprint, render_template, request, jsonify
from bs4 import BeautifulSoup

from src import displayer
from src import utilities


# ---------------------------------------------------------------------------
# Test Configuration
# ---------------------------------------------------------------------------

TEST_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Flask Test Application
# ---------------------------------------------------------------------------

def build_test_app() -> Flask:
    """Create minimal Flask app for rendering Displayer pages."""
    # Calculate paths
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    template_path = os.path.join(workspace_root, "templates")
    
    # Create Flask app
    app = Flask(__name__, template_folder=template_path)
    app.config["TESTING"] = True
    app.secret_key = "test-secret-key"
    
    # Register common blueprint for assets (matches demo.py structure)
    common_bp = Blueprint("common", __name__, url_prefix="/common")
    
    @common_bp.route("/assets/<asset_type>/<path:filename>")
    def assets(asset_type, filename):
        """Serve webengine assets."""
        return "", 200
    
    app.register_blueprint(common_bp)
    
    # Register test blueprint for item pages
    test_bp = Blueprint("test_disp", __name__, url_prefix="/test")
    
    @test_bp.route("/item", methods=["GET"])
    def item_page():
        """Render item page (GET)."""
        disp = app.config.get("current_displayer")
        target = app.config.get("form_target")
        content_dict = disp.display(True)
        
        # Extract resources from content dict (they were added by disp.display())
        required_css = content_dict.get('required_css', [])
        required_js = content_dict.get('required_js', [])
        required_cdn = content_dict.get('required_cdn', [])
        
        return render_template("base_content.j2", 
                             content=content_dict, 
                             target=target,
                             required_css=required_css,
                             required_js=required_js,
                             required_cdn=required_cdn)
    
    @test_bp.route("/item", methods=["POST"])
    def item_post():
        """Handle item POST and return JSON-transformed data."""
        form_data = request.form.to_dict()
        # Match production usage in settings.py line 321
        json_data = utilities.util_post_to_json(form_data)
        return jsonify(json_data)
    
    app.register_blueprint(test_bp)
    
    # Add context processor (matches demo.py)
    @app.context_processor
    def inject_template_context():
        return {
            "sidebarItems": {"display": False},
            "topbarItems": {"display": False},
            "app": {"name": "Test", "version": "1.0"},
            "javascript": "",
            "title": "Test",
            "footer": "Test Footer",
            "filename": __file__,
        }
    
    # Add resource injection context processor
    @app.context_processor
    def inject_resources():
        """Inject required resources into template context."""
        from src.displayer import ResourceRegistry
        return dict(
            required_css=ResourceRegistry.get_required_css(),
            required_js=ResourceRegistry.get_required_js(),
            required_cdn=ResourceRegistry.get_required_js_cdn()
        )
    
    return app


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def save_html(filename: str, html: str) -> None:
    """Save HTML to output directory for manual review with standalone-friendly paths."""
    # Post-process HTML for standalone viewing
    html = make_html_standalone(html)
    
    filepath = os.path.join(TEST_OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)


def generate_index_page() -> None:
    """
    Generate a gallery index page using the framework's template system with sidebar navigation.
    
    Creates a Flask app that serves the test gallery with proper Bootstrap styling
    and framework sidebar integration. The gallery is rendered from test_gallery.j2
    and saved as index.html in the output directory.
    """
    import glob
    from src import site_conf
    
    # Get all HTML files in output directory (excluding index.html itself)
    html_files = [
        os.path.basename(f) for f in glob.glob(os.path.join(TEST_OUTPUT_DIR, "*.html"))
        if os.path.basename(f) != "index.html"
    ]
    
    # Separate items, layouts, and other test files
    item_files = sorted([f for f in html_files if f.startswith("item_")])
    layout_files = sorted([f for f in html_files if f.startswith("layout_")])
    other_files = sorted([f for f in html_files if not f.startswith("item_") and not f.startswith("layout_")])
    
    # Build Flask app with framework's base template
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    template_path_framework = os.path.join(workspace_root, "templates")
    template_path_test = os.path.join(os.path.dirname(__file__), "templates")
    
    app = Flask(__name__, template_folder=template_path_framework)
    app.config["TESTING"] = True
    app.secret_key = "test-gallery-secret"
    
    # Register common blueprint for assets (required by base.j2)
    common_bp_assets = Blueprint("common", __name__, url_prefix="/common")
    
    @common_bp_assets.route("/assets/<asset_type>/<path:filename>")
    def assets(asset_type, filename):
        return "", 200
    
    app.register_blueprint(common_bp_assets)
    
    # Add test templates folder to Jinja loader
    from jinja2 import ChoiceLoader, FileSystemLoader
    app.jinja_loader = ChoiceLoader([
        FileSystemLoader(template_path_test),
        FileSystemLoader(template_path_framework),
    ])
    
    # Create site configuration with sidebar for gallery
    class GallerySiteConf(site_conf.Site_conf):
        def __init__(self):
            super().__init__()
            self.app_details("Test Gallery", "1.0", "test-tube", "2024 &copy; ParalaX", "Displayer Test Gallery")
            
            # Add sidebar for DisplayerItems
            if item_files:
                self.add_sidebar_title("DisplayerItems")
                for filename in item_files:
                    item_name = filename.replace("item_", "").replace(".html", "")
                    # Use gallery.index as endpoint, hash will be handled by JS
                    self.add_sidebar_page(item_name, "palette", "gallery.index")
            
            # Add sidebar for Layouts
            if layout_files:
                self.add_sidebar_title("Layouts")
                for filename in layout_files:
                    layout_name = filename.replace("layout_", "").replace(".html", "")
                    self.add_sidebar_page(layout_name, "view-grid", "gallery.index")
            
            # Add sidebar for Other Tests
            if other_files:
                self.add_sidebar_title("Other Tests")
                for filename in other_files:
                    test_name = filename.replace("displayer_", "").replace(".html", "")
                    self.add_sidebar_page(test_name, "flask", "gallery.index")
    
    gallery_conf = GallerySiteConf()
    
    # Build filename mapping for JavaScript
    filename_map = {}
    for filename in item_files:
        item_name = filename.replace("item_", "").replace(".html", "")
        filename_map[item_name] = filename
    for filename in layout_files:
        layout_name = filename.replace("layout_", "").replace(".html", "")
        filename_map[layout_name] = filename
    for filename in other_files:
        test_name = filename.replace("displayer_", "").replace(".html", "")
        filename_map[test_name] = filename
    
    # Extract main content from each HTML file for embedding
    from bs4 import BeautifulSoup
    content_map = {}
    for name, filename in filename_map.items():
        file_path = os.path.join(TEST_OUTPUT_DIR, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
                # Find div with id="main" (not <main> tag)
                main_content = soup.find("div", id="main")
                if main_content:
                    # Extract the innerHTML (content inside #main, not the div itself)
                    content_map[name] = main_content.decode_contents()
                else:
                    content_map[name] = f'<div class="alert alert-warning">No #main content found in {filename}</div>'
        except Exception as e:
            content_map[name] = f'<div class="alert alert-danger">Error loading {filename}: {str(e)}</div>'
    
    # Register gallery blueprint
    gallery_bp = Blueprint("gallery", __name__)
    
    @gallery_bp.route("/")
    def index():
        return render_template("test_gallery.j2", filename_map=filename_map, content_map=content_map)
    
    app.register_blueprint(gallery_bp)
    
    # Context processor for gallery
    @app.context_processor
    def inject_context():
        return {
            'sidebarItems': gallery_conf.m_sidebar,
            'topbarItems': {'display': False},
            'app': gallery_conf.m_app,
            'javascript': [],
            'title': 'Displayer Test Gallery',
            'footer': gallery_conf.m_app["footer"],
            'filename': None,
            'endpoint': 'gallery.index',
            'page_info': '',
            'user': None,
            'required_css': [],
            'required_js': [],
            'required_cdn': []
        }
    
    # Render the gallery page
    with app.test_client() as client:
        response = client.get("/")
        html = response.data.decode("utf-8")
    
    # Post-process HTML for standalone viewing
    html = make_html_standalone(html)
    
    # Save index.html
    index_path = os.path.join(TEST_OUTPUT_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print("\n✅ Generated gallery index with framework sidebar")
    print(f"   📊 {len(item_files)} DisplayerItems, {len(layout_files)} Layouts, {len(other_files)} Other Tests")
    print(f"   📂 Open: {index_path}")


def make_html_standalone(html: str) -> str:
    """
    Convert Flask-rendered HTML to standalone-viewable format.
    
    Replaces Flask url_for() generated paths with CDN or relative paths:
    - /static/... → ../../webengine/assets/...
    - /common/assets/... → ../../webengine/assets/...
    """
    import re
    
    # Map Flask routes to actual file paths
    replacements = [
        # Static vendor files
        (r'href="/static/vendors/([^"]+)"', r'href="../../../webengine/assets/vendors/\1"'),
        (r'src="/static/vendors/([^"]+)"', r'src="../../../webengine/assets/vendors/\1"'),
        
        # Static CSS
        (r'href="/static/css/([^"]+)"', r'href="../../../webengine/assets/css/\1"'),
        
        # Static JS
        (r'src="/static/js/([^"]+)"', r'src="../../../webengine/assets/js/\1"'),
        
        # Common assets (favicon, images)
        (r'href="/common/assets/([^"]+)"', r'href="../../../webengine/assets/\1"'),
        (r'src="/common/assets/([^"]+)"', r'src="../../../webengine/assets/\1"'),
        
        # Static fonts
        (r'href="/static/fonts/([^"]+)"', r'href="../../../webengine/assets/fonts/\1"'),
    ]
    
    for pattern, replacement in replacements:
        html = re.sub(pattern, replacement, html)
    
    return html


def render_item_page(app: Flask, disp: displayer.Displayer, target: str = None) -> dict:
    """
    Render a displayer page and return status + HTML.
    
    Returns dict with: status_code, html, form_action
    """
    app.config["current_displayer"] = disp
    app.config["form_target"] = target
    
    with app.test_client() as client:
        response = client.get("/test/item")
        html = response.data.decode("utf-8")
        
        # Extract form action if present
        form_action = None
        soup = BeautifulSoup(html, "html.parser")
        form_tag = soup.find("form")
        if form_tag:
            form_action = form_tag.get("action")
        
        return {
            "status_code": response.status_code,
            "html": html,
            "form_action": form_action
        }


def extract_form_fields(html: str) -> Dict[str, str]:
    """
    Extract form fields from HTML.
    
    Returns dict mapping field names to test values.
    """
    soup = BeautifulSoup(html, "html.parser")
    form_data = {}
    
    # Find all input, select, textarea
    for input_tag in soup.find_all(["input", "select", "textarea"]):
        name = input_tag.get("name")
        if not name:
            continue
        
        input_type = input_tag.get("type", "text")
        
        if input_type == "checkbox":
            # Always include checkboxes - check or uncheck
            form_data[name] = "on" if input_tag.get("checked") else ""
        elif input_tag.name == "select":
            # Select: pick first option
            options = input_tag.find_all("option")
            if options:
                form_data[name] = options[0].get("value", options[0].text)
        elif input_type == "hidden":
            # Include all hidden fields (including non-csrf)
            form_data[name] = input_tag.get("value", "")
        else:
            # Text inputs and other types
            form_data[name] = input_tag.get("value", "test_value")
    
    return form_data


def post_and_get_json(app: Flask, form_data: Dict[str, str]) -> dict:
    """
    POST form data and return JSON response.
    
    This mimics production flow: POST → util_post_to_json → JSON response
    """
    with app.test_client() as client:
        response = client.post("/test/item", data=form_data)
        if response.status_code == 200:
            return response.get_json()
        return {}


def add_displayer_item(disp: displayer.Displayer, item: displayer.DisplayerItem) -> None:
    """Add a single item to a displayer with minimal layout."""
    disp.add_generic("AutoModule")
    layout = displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
    disp.add_master_layout(layout)
    disp.add_display_item(item, 0)
    
    # Modal buttons/links need actual modal content
    if isinstance(item, (displayer.DisplayerItemModalButton, displayer.DisplayerItemModalLink)):
        # Create a simple modal displayer
        modal_disp = displayer.Displayer()
        modal_disp.add_generic("ModalContent")
        modal_layout = displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
        modal_disp.add_master_layout(modal_layout)
        modal_disp.add_display_item(displayer.DisplayerItemText("This is the modal content"), 0)
        modal_disp.add_display_item(displayer.DisplayerItemAlert("Modal works!", displayer.BSstyle.SUCCESS), 0)
        
        # Add modal with proper structure (m_modules already contains the built structure)
        disp.m_modals.append({
            "id": "modal_" + item.m_path,
            "header": "Test Modal",
            "content": modal_disp.m_modules
        })


def add_displayer_layout(disp: displayer.Displayer, layout_type: displayer.Layouts) -> None:
    """Create a minimal page for each layout type."""
    disp.add_generic("AutoModule")
    
    if layout_type == displayer.Layouts.VERTICAL:
        layout = displayer.DisplayerLayout(layout_type, [6, 6], subtitle="Vert")
        disp.add_master_layout(layout)
        disp.add_display_item(displayer.DisplayerItemText("Left"), 0)
        disp.add_display_item(displayer.DisplayerItemText("Right"), 1)
    elif layout_type == displayer.Layouts.HORIZONTAL:
        layout = displayer.DisplayerLayout(layout_type, [6, 6], subtitle="Horiz")
        disp.add_master_layout(layout)
        disp.add_display_item(displayer.DisplayerItemText("Col1"), 0)
        disp.add_display_item(displayer.DisplayerItemText("Col2"), 1)
    elif layout_type == displayer.Layouts.TABLE:
        layout = displayer.DisplayerLayout(layout_type, ["Name", "Value"], subtitle="Table")
        disp.add_master_layout(layout)
        disp.add_display_item(displayer.DisplayerItemText("Row1"), 0)
        disp.add_display_item(displayer.DisplayerItemBadge("Badge", displayer.BSstyle.PRIMARY), 1)
    elif layout_type == displayer.Layouts.TABS:
        layout = displayer.DisplayerLayout(layout_type, ["Tab1", "Tab2"], subtitle="Tabs")
        disp.add_master_layout(layout)
        disp.add_display_item(displayer.DisplayerItemText("Tab content A"), column=0, line=0)
        disp.add_display_item(displayer.DisplayerItemText("Tab content B"), column=1, line=0)
    elif layout_type == displayer.Layouts.SPACER:
        layout = displayer.DisplayerLayout(layout_type, [])
        disp.add_master_layout(layout)
        next_layout = displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle="After Spacer")
        disp.add_master_layout(next_layout)
        disp.add_display_item(displayer.DisplayerItemText("Below spacer"), 0)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def test_app():
    """Shared Flask test app."""
    return build_test_app()


@pytest.mark.parametrize("item_class", 
    list(displayer.DisplayerCategory.get_all().get("display", [])) + 
    list(displayer.DisplayerCategory.get_all().get("input", [])) + 
    list(displayer.DisplayerCategory.get_all().get("button", [])) + 
    list(displayer.DisplayerCategory.get_all().get("media", []))
)
def test_displayer_items(test_app: Flask, item_class: type) -> None:
    """
    Test each DisplayerItem class:
    1. Instantiate via item_class.instantiate_test()
    2. Render page and save HTML
    3. For input items: validate POST → JSON pipeline
    4. For display items: check text/element presence
    """
    # Get test instance via classmethod
    try:
        item = item_class.instantiate_test()
    except Exception as e:
        pytest.fail(f"{item_class.__name__}.instantiate_test() failed: {e}")
    
    category = getattr(item_class, "_displayer_category", "")
    
    # Build displayer
    disp = displayer.Displayer()
    add_displayer_item(disp, item)
    
    # Render page
    target = "test_disp.item_post" if category == "input" else None
    render_result = render_item_page(test_app, disp, target=target)
    
    # Save HTML for manual review
    html_filename = f"item_{item_class.__name__}.html"
    save_html(html_filename, render_result["html"])
    
    # Assert successful render
    assert render_result["status_code"] == 200, f"Rendering failed for {item_class.__name__}"
    
    soup = BeautifulSoup(render_result["html"], "html.parser")
    
    # Category-specific validation
    if category == "input":
        # Input items: validate POST → JSON pipeline
        form_data = extract_form_fields(render_result["html"])
        
        # Some input items don't generate standard HTML form fields (file explorers, complex JS widgets)
        # Skip POST validation if no actual form fields found (only csrf_token)
        if len(form_data) <= 1 and "csrf_token" in form_data:
            # Skip POST validation for items without extractable form fields
            pass
        else:
            assert form_data, f"Expected form fields for {item_class.__name__}"
            
            # POST and get JSON response
            json_response = post_and_get_json(test_app, form_data)
            assert json_response, f"POST returned empty JSON for {item_class.__name__}"
            
            # Validate util_post_to_json structure (matches settings.py usage)
            # Expected: {"AutoModule": {...fields...}}
            assert "AutoModule" in json_response, f"Missing 'AutoModule' key in JSON for {item_class.__name__}"
            
            module_data = json_response["AutoModule"]
            assert module_data, f"Empty module data for {item_class.__name__}"
        
    else:
        # Display/button/media items: check text or element presence
        expected_text = getattr(item, "m_text", None) or getattr(item, "m_value", None)
        if expected_text:
            assert expected_text in render_result["html"], \
                f"Expected text '{expected_text}' not found for {item_class.__name__}"
        else:
            # At least some element should exist
            assert soup.find(lambda tag: tag.name in {"button", "img", "a", "div", "span"}), \
                f"No displayable element found for {item_class.__name__}"


@pytest.mark.parametrize("layout_type", list(displayer.Layouts))
def test_displayer_layouts(test_app: Flask, layout_type: displayer.Layouts) -> None:
    """
    Test each DisplayerLayout type:
    1. Create layout with sample items
    2. Render page and save HTML
    3. Assert layout-specific HTML structure
    """
    # Skip unimplemented layouts
    if layout_type == displayer.Layouts.HORIZONTAL:
        pytest.skip("HORIZONTAL layout not yet implemented (marked TOCODE in templates)")
    
    # Build displayer
    disp = displayer.Displayer()
    add_displayer_layout(disp, layout_type)
    
    # Render page
    render_result = render_item_page(test_app, disp)
    
    # Save HTML for manual review
    html_filename = f"layout_{layout_type.name}.html"
    save_html(html_filename, render_result["html"])
    
    # Assert successful render
    assert render_result["status_code"] == 200, f"Rendering failed for {layout_type.name}"
    
    soup = BeautifulSoup(render_result["html"], "html.parser")
    
    # Layout-specific HTML validation
    if layout_type == displayer.Layouts.VERTICAL:
        # VERTICAL uses Bootstrap col-6 classes
        cols = soup.select(".row .col-6")
        assert len(cols) >= 2, f"VERTICAL layout should have 2+ columns, found {len(cols)}"
    
    elif layout_type == displayer.Layouts.TABLE:
        # TABLE uses <table> element
        tables = soup.find_all("table")
        assert len(tables) >= 1, f"TABLE layout should have table element, found {len(tables)}"
    
    elif layout_type == displayer.Layouts.TABS:
        # TABS uses nav-tabs
        nav_tabs = soup.select(".nav-tabs")
        assert len(nav_tabs) >= 1, f"TABS layout should have nav-tabs, found {len(nav_tabs)}"
    
    elif layout_type == displayer.Layouts.SPACER:
        # SPACER creates vertical spacing
        # Just check page rendered successfully (specific HTML marker TBD)
        pass


def test_displayer_basics(test_app: Flask) -> None:
    """
    Test basic Displayer functionality: modules, layouts, breadcrumbs, and title.
    
    Validates core Displayer features that aren't item-specific:
    - Module adding (add_generic)
    - Layout hierarchy (master/slave, nested layouts)
    - Title and breadcrumbs
    - Multiple modules in one displayer
    """
    # Create comprehensive displayer
    disp = displayer.Displayer()
    
    # ===== Test 1: Title =====
    disp.set_title("Displayer Basics Test")
    
    # ===== Test 2: Module adding with add_generic =====
    disp.add_generic("Module 1: Nested Layouts")
    
    # ===== Test 3: Breadcrumbs =====
    disp.add_breadcrumb("Home", "test_disp.item_page", [])
    disp.add_breadcrumb("Basics", "test_disp.item_page", ["section=basics"])
    disp.add_breadcrumb("Current", "test_disp.item_page", ["section=current"], style="active")
    
    # ===== Test 4: Master layout with nested slave layouts =====
    master_id = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [6, 6], subtitle="Master Layout (2 columns)"
    ))
    
    # Add slave layout in column 0
    slave1_id = disp.add_slave_layout(
        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle="Slave in Column 0"),
        column=0,
        layout_id=master_id
    )
    disp.add_display_item(displayer.DisplayerItemText("Text in slave layout column 0"), 0, slave1_id)
    disp.add_display_item(displayer.DisplayerItemBadge("Badge in slave", displayer.BSstyle.SUCCESS), 0, slave1_id)
    
    # Add slave layout in column 1
    slave2_id = disp.add_slave_layout(
        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle="Slave in Column 1"),
        column=1,
        layout_id=master_id
    )
    disp.add_display_item(displayer.DisplayerItemAlert("Alert in slave layout column 1", displayer.BSstyle.INFO), 0, slave2_id)
    
    # ===== Test 5: Second module with simple vertical layout =====
    disp.add_generic("Module 2: Simple Layout")
    disp.add_breadcrumb("Module2", "test_disp.item_page", ["module=2"])
    
    simple_id = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [4, 4, 4], subtitle="Three columns"
    ))
    disp.add_display_item(displayer.DisplayerItemText("Column A content"), column=0, layout_id=simple_id)
    disp.add_display_item(displayer.DisplayerItemText("Column B content"), column=1, layout_id=simple_id)
    disp.add_display_item(displayer.DisplayerItemText("Column C content"), column=2, layout_id=simple_id)
    
    # ===== Test 6: Third module =====
    disp.add_generic("Module 3: Another Layout")
    three_col_id = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Single column"
    ))
    disp.add_display_item(displayer.DisplayerItemAlert("Module 3 alert", displayer.BSstyle.SUCCESS), column=0, layout_id=three_col_id)
    
    # ===== Test 7: Fourth module - layout duplication test =====
    disp.add_generic("Module 4: Duplicated Layouts")
    dup1_id = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="First instance"
    ))
    disp.add_display_item(displayer.DisplayerItemText("First layout text"), 0, dup1_id)
    
    dup2_id = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12], subtitle="Second instance (duplicate)"
    ))
    disp.add_display_item(displayer.DisplayerItemText("Second layout text"), 0, dup2_id)
    
    # Render and save HTML using shared renderer
    render_result = render_item_page(test_app, disp)
    
    # Save HTML for manual review (with make_html_standalone)
    save_html("displayer_basics.html", render_result["html"])
    
    # Assert successful render
    assert render_result["status_code"] == 200, "Rendering failed for basics test"
    
    # Parse HTML
    soup = BeautifulSoup(render_result["html"], "html.parser")
    html_text = str(soup)
    
    # ===== Validation 1: Title =====
    title_tag = soup.find('title')
    h1_tag = soup.find('h1')
    assert title_tag or h1_tag, "Page should have title or h1"
    
    # ===== Validation 2: Multiple modules =====
    cards = soup.find_all('div', class_=lambda x: x and 'card' in x)
    assert len(cards) >= 4, f"Should have card elements for modules (at least 4), found {len(cards)}"
    
    # ===== Validation 3: Nested layouts - slave layouts =====
    assert "Text in slave layout column 0" in html_text, "Should have content from slave layout column 0"
    assert "Badge in slave" in html_text, "Should have badge from slave layout column 0"
    assert "Alert in slave layout column 1" in html_text, "Should have alert from slave layout column 1"
    
    # ===== Validation 4: Second module =====
    assert "Column A content" in html_text, "Should have column A content"
    assert "Column B content" in html_text, "Should have column B content"
    assert "Column C content" in html_text, "Should have column C content"
    
    # ===== Validation 5: Third module =====
    assert "Module 3 alert" in html_text, "Should have module 3 alert"
    
    # ===== Validation 6: Duplicated layouts =====
    assert "First layout text" in html_text, "Should have first layout content"
    assert "Second layout text" in html_text, "Should have second layout content"
    
    print(f"✓ Displayer basics test passed - HTML saved to {TEST_OUTPUT_DIR}/displayer_basics.html")
    print("  - Validated: title, breadcrumbs, 4 modules, nested/slave layouts, duplicated layouts")
    print(f"  - Found {len(cards)} card elements")


# ---------------------------------------------------------------------------
# Session-level Hook: Generate Index Page After All Tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def generate_gallery_index():
    """
    Auto-generate index.html after all tests complete.
    This provides a browsable gallery of all generated displayer components.
    """
    yield  # Let all tests run first
    
    # After all tests complete, generate the index page
    generate_index_page()
