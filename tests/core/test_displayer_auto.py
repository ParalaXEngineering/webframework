"""
Automated integration tests for the ParalaX Web Framework Displayer module.

Test Architecture:
- Uses DisplayerItem.instantiate_test() classmethod for test data
- Auto-discovers items via @DisplayerCategory decorators  
- Saves rendered HTML to tests/core/output/ for manual review
- Validates POST → JSON pipeline through util_post_to_json()
- Minimal test count: test_displayer_items + test_displayer_layouts

Test Coverage:
- Template rendering (status 200, valid HTML)
- Form field extraction for input items
- POST data transformation matching production usage in settings.py
- Layout-specific HTML structure validation

Skip Conditions:
- Items requiring complex backend (file uploads, modals, cascaded structures)
- Layouts not yet implemented (HORIZONTAL = "TOCODE")
"""

import pytest
import os
from typing import Dict, Any
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
        return render_template("base_content.j2", content=disp.display(True), target=target)
    
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
        (r'href="/static/vendors/([^"]+)"', r'href="../../webengine/assets/vendors/\1"'),
        (r'src="/static/vendors/([^"]+)"', r'src="../../webengine/assets/vendors/\1"'),
        
        # Static CSS
        (r'href="/static/css/([^"]+)"', r'href="../../webengine/assets/css/\1"'),
        
        # Common assets (favicon, images)
        (r'href="/common/assets/([^"]+)"', r'href="../../webengine/assets/\1"'),
        (r'src="/common/assets/([^"]+)"', r'src="../../webengine/assets/\1"'),
        
        # Static fonts
        (r'href="/static/fonts/([^"]+)"', r'href="../../webengine/assets/fonts/\1"'),
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
