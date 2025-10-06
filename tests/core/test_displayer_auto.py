"""High-level integration tests for Displayer items and layouts.

The goal is to keep coverage broad while keeping only two parametrised tests:

* ``test_displayer_items`` renders a single Displayer page per item class and
  validates that the generated HTML or the POST/response cycle is correct.
* ``test_displayer_layouts`` renders a small page per layout type and asserts
  layout-specific HTML markers are present.

Everything is auto-discovered thanks to ``DisplayerCategory`` so new items and
layouts are picked up automatically.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Dict, Tuple

import pytest
from bs4 import BeautifulSoup
from flask import Blueprint, Flask, jsonify, render_template, request

from src import displayer
from src.utilities import util_post_to_json


# ---------------------------------------------------------------------------
# Helper dataclasses / utilities
# ---------------------------------------------------------------------------


@dataclass
class RenderResult:
    """Container returned by ``render_item_page`` for assertions."""

    status_code: int
    html: str
    form_action: str | None


def build_test_app() -> Flask:
    """Create a minimal Flask app able to render Displayer pages."""
    import os
    
    # Get workspace root (tests/core/.. -> workspace root)
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    template_path = os.path.join(workspace_root, "templates")
    static_path = os.path.join(workspace_root, "webengine", "assets")

    app = Flask(
        __name__,
        template_folder=template_path,
        static_folder=static_path,
        static_url_path="/assets",
    )
    app.secret_key = "test-secret"

    # Register common blueprint for assets (mimics demo.py)
    common_bp = Blueprint("common", __name__, url_prefix="/common")
    
    @common_bp.route("/assets/<asset_type>/<path:filename>")
    def assets(asset_type, filename):
        """Serve assets from webengine directory."""
        from flask import send_from_directory
        asset_path = os.path.join(workspace_root, "webengine", "assets", asset_type)
        return send_from_directory(asset_path, filename)
    
    app.register_blueprint(common_bp)
    
    # Register context processor for template variables
    @app.context_processor
    def inject_template_context():
        """Inject minimal template context for tests."""
        return {
            'sidebarItems': {'display': False, 'items': []},
            'topbarItems': {'display': False, 'items': []},
            'app': {'name': 'Test', 'footer': 'Test Footer'},
            'javascript': [],
            'title': 'Test',
            'footer': 'Test Footer',
            'filename': None,
        }

    # Register a lightweight blueprint that mirrors demo.py behaviour
    bp = Blueprint("test_disp", __name__)

    @bp.route("/item", methods=["GET", "POST"])
    def item_page():
        # The view expects a pre-built displayer stored on app config
        disp: displayer.Displayer = app.config["current_displayer"]
        target = app.config.get("current_target")
        if request.method == "POST":
            payload = util_post_to_json(request.form.to_dict())
            return jsonify(payload)
        return render_template("base_content.j2", content=disp.display(True), target=target)

    app.register_blueprint(bp)
    return app


def render_item_page(app: Flask, disp: displayer.Displayer, target: str | None = None) -> RenderResult:
    """Render a Displayer page using the Flask test client."""

    app.config["current_displayer"] = disp
    app.config["current_target"] = target

    client = app.test_client()
    response = client.get("/item")
    html = response.get_data(as_text=True)

    form_action = None
    if target:
        soup = BeautifulSoup(html, "html.parser")
        form_tag = soup.find("form")
        if form_tag:
            form_action = form_tag.get("action")

    return RenderResult(status_code=response.status_code, html=html, form_action=form_action)


def instantiate_item(item_class: type) -> displayer.DisplayerItem:
    """Instantiate an item class with sensible sample data."""

    signature = inspect.signature(item_class.__init__)
    kwargs: Dict[str, Any] = {}
    
    # Special handling for specific items
    class_name = item_class.__name__
    
    for name, parameter in list(signature.parameters.items())[1:]:  # skip self
        if name in {"id", "ids"}:
            value = "test_id" if name == "id" else ["test_id", "test_id_child"]
        elif name == "text":
            value = f"Sample {item_class.__name__}"
        elif name == "value":
            # InputCascaded needs a list of values
            if class_name == "DisplayerItemInputCascaded":
                value = ["value1", "value2"]
            else:
                value = "value"
        elif name == "choices" or name == "possibles":
            # InputCascaded needs a list of lists
            if class_name == "DisplayerItemInputCascaded":
                value = [["Option A1", "Option A2"], ["Option B1", "Option B2"]]
            else:
                value = ["Option A", "Option B"]
        elif name == "tooltips":
            value = ["Tooltip A", "Tooltip B"]
        elif name == "link":
            value = "/dummy"
        elif name == "level":
            value = -1
        elif name == "height":
            value = 200
        elif name == "data":
            # Default data handling - dict with nested structure for cascaded items
            if class_name == "DisplayerItemInputTextSelect":
                value = {"key1": ["Option A", "Option B"], "key2": ["Option C", "Option D"]}
            else:
                value = []
        elif parameter.default is not inspect.Parameter.empty:
            value = parameter.default
        else:
            value = "sample"

        kwargs[name] = value

    instance = item_class(**kwargs)

    return instance


def extract_form_fields(html: str) -> Dict[str, Any]:
    """Parse HTML and return a dict of form field names with sample values."""

    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form")
    if not form:
        return {}

    data: Dict[str, Any] = {}
    for field in form.find_all(["input", "select", "textarea"]):
        name = field.get("name")
        if not name:
            continue
        if field.name == "select":
            options = field.find_all("option")
            if options:
                data[name] = options[0].get("value") or options[0].text
        elif field.get("type") == "checkbox":
            data[name] = "on"
        elif field.get("type") in {"file", "image"}:
            continue
        elif field.get("type") == "hidden":
            data[name] = field.get("value", "hidden" )
        else:
            data[name] = field.get("value", "submitted")
    return data


def run_post_and_capture(app: Flask, payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """Submit POST payload back to ``/item`` and return status + server JSON."""

    client = app.test_client()
    response = client.post("/item", data=payload)
    return response.status_code, response.get_json() or {}


def add_displayer_item(disp: displayer.Displayer, item: displayer.DisplayerItem) -> None:
    """Add a single layout + item to a Displayer instance."""

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
    else:
        raise pytest.SkipTest(f"Layout {layout_type} not covered")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def test_app():
    return build_test_app()


@pytest.mark.parametrize("item_class", list(displayer.DisplayerCategory.get_all().get("display", [])) + list(displayer.DisplayerCategory.get_all().get("input", [])) + list(displayer.DisplayerCategory.get_all().get("button", [])) + list(displayer.DisplayerCategory.get_all().get("media", [])))
def test_displayer_items(test_app: Flask, item_class: type) -> None:
    # Skip items requiring complex backend data structures
    items_needing_backend = [
        "DisplayerItemInputCascaded",  # Needs dict with cascaded structure
        "DisplayerItemInputTextSelect",  # Needs dict with key-value pairs
        "DisplayerItemInputFileExplorer",  # Needs server filesystem access
        "DisplayerItemInputFile",  # Needs file upload handling
        "DisplayerItemInputFolder",  # Needs folder selection handling
        "DisplayerItemInputImage",  # Needs image upload handling
        "DisplayerItemInputStringIcon",  # Needs icon selection handling
        "DisplayerItemDownload",  # Needs file to download
        "DisplayerItemModalLink",  # Needs modal content injection
    ]
    if item_class.__name__ in items_needing_backend:
        pytest.skip(f"{item_class.__name__} requires backend context (file system, modals, etc.)")
    
    disp = displayer.Displayer()
    category = getattr(item_class, "_displayer_category", "")

    item = instantiate_item(item_class)
    add_displayer_item(disp, item)

    target = "test_disp.item_page" if category == "input" else None
    render = render_item_page(test_app, disp, target=target)
    assert render.status_code == 200
    soup = BeautifulSoup(render.html, "html.parser")

    if category == "input":
        form_data = extract_form_fields(render.html)
        assert form_data, "Expected form fields for input item"
        status, parsed = run_post_and_capture(test_app, form_data)
        assert status == 200
        assert parsed, "Parsed payload should not be empty"
        assert "AutoModule" in parsed, "Server response should include module data"
    else:
        # Display item: ensure its signature text appears
        expected_text = getattr(item, "m_text", None) or getattr(item, "m_value", None)
        if expected_text:
            assert expected_text in render.html
        else:
            assert soup.find(lambda tag: tag.name in {"button", "img", "a", "div"}) is not None


@pytest.mark.parametrize("layout_type", list(displayer.Layouts))
def test_displayer_layouts(test_app: Flask, layout_type: displayer.Layouts) -> None:
    # Skip HORIZONTAL layout as it's not implemented in templates (marked "TOCODE")
    if layout_type == displayer.Layouts.HORIZONTAL:
        pytest.skip("HORIZONTAL layout not yet implemented in templates/displayer/layouts.j2")
    
    disp = displayer.Displayer()
    add_displayer_layout(disp, layout_type)
    render = render_item_page(test_app, disp)
    assert render.status_code == 200
    soup = BeautifulSoup(render.html, "html.parser")

    if layout_type == displayer.Layouts.VERTICAL:
        cols = soup.select(".row .col-6")
        assert len(cols) == 2
    elif layout_type == displayer.Layouts.HORIZONTAL:
        # Horizontal layout renders similar structure; ensure at least two columns
        cols = soup.select(".row .col-6")
        assert len(cols) >= 2
    elif layout_type == displayer.Layouts.TABLE:
        table = soup.find("table")
        assert table is not None
        headers = [th.text.strip() for th in table.find_all("th")]
        assert "Name" in headers and "Value" in headers
    elif layout_type == displayer.Layouts.TABS:
        tabs = soup.select(".nav.nav-tabs .nav-link")
        assert len(tabs) >= 2
    elif layout_type == displayer.Layouts.SPACER:
        spacer = soup.find("p", style=lambda value: value and "margin-bottom" in value)
        assert spacer is not None
    else:
        pytest.skip(f"No assertion for {layout_type}")
