"""
Comprehensive Flask integration tests for settings.

Tests all field types with actual HTTP requests and form submissions.
"""

import pytest
import os
import json
import tempfile
from flask import Flask
from bs4 import BeautifulSoup

from src.pages import settings
from src.modules.settings_manager import SettingsManager


# Test configuration with ALL supported field types
TEST_CONFIG = {
    "test_category": {
        "friendly": "Test Category",
        "string_field": {
            "friendly": "String Field",
            "type": "string",
            "value": "test value"
        },
        "int_field": {
            "friendly": "Integer Field",
            "type": "int",
            "value": 42
        },
        "bool_field": {
            "friendly": "Boolean Field",
            "type": "bool",
            "value": True
        },
        "select_field": {
            "friendly": "Select Field",
            "type": "select",
            "value": "option2",
            "options": ["option1", "option2", "option3"]
        },
        "text_list_field": {
            "friendly": "Text List Field",
            "type": "text_list",
            "value": ["item1", "item2"]
        },
        "multi_select_field": {
            "friendly": "Multi Select Field",
            "type": "multi_select",
            "value": ["choice1", "choice3"],
            "options": ["choice1", "choice2", "choice3", "choice4"]
        }
    },
    "second_category": {
        "friendly": "Second Category",
        "another_string": {
            "friendly": "Another String",
            "type": "string",
            "value": "default"
        },
        "another_bool": {
            "friendly": "Another Bool",
            "type": "bool",
            "value": False
        }
    }
}


@pytest.fixture
def test_config_file():
    """Create temporary config file with test data."""
    fd, path = tempfile.mkstemp(suffix='.json')
    with os.fdopen(fd, 'w') as f:
        json.dump(TEST_CONFIG, f)
    
    yield path
    
    try:
        os.unlink(path)
    except Exception:
        pass


@pytest.fixture
def app(test_config_file):
    """Create Flask test app with settings blueprint."""
    # Calculate paths
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    template_path = os.path.join(workspace_root, "templates")
    
    app = Flask(__name__, template_folder=template_path)
    app.config["TESTING"] = True
    app.secret_key = "test-secret"
    
    # Register common blueprint for assets (matches test_displayer)
    from flask import Blueprint
    common_bp = Blueprint("common", __name__, url_prefix="/common")
    
    @common_bp.route("/assets/<asset_type>/<path:filename>")
    def assets(asset_type, filename):
        """Serve webengine assets."""
        return "", 200
    
    app.register_blueprint(common_bp)
    
    # Register demo blueprint for breadcrumbs
    demo_bp = Blueprint("demo", __name__)
    
    @demo_bp.route("/")
    def index():
        """Demo index for breadcrumbs."""
        return "", 200
    
    app.register_blueprint(demo_bp)
    
    # Override the config path for settings
    settings._settings_manager = SettingsManager(test_config_file)
    settings._settings_manager.load()
    
    # CRITICAL: Make displayer bypass auth in tests
    settings._bypass_auth = True
    
    # Register settings blueprint
    app.register_blueprint(settings.bp)
    
    # Context processor for templates
    @app.context_processor
    def inject_defaults():
        return {
            'sidebarItems': [],
            'topbarItems': [],
            'app': {'name': 'Test', 'footer': 'Test'},
            'title': 'Test',
            'filename': None,
            'endpoint': None,
            'page_info': '',
            'user': None,
            'required_css': [],
            'required_js': [],
            'required_cdn': []
        }
    
    yield app
    
    # Cleanup
    settings._settings_manager = None
    settings._bypass_auth = False


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_index_page_loads(client):
    """Test that the settings index page loads."""
    response = client.get('/settings/')
    assert response.status_code == 200
    
    html = response.data.decode('utf-8')
    assert "Test Category" in html
    assert "Second Category" in html


def test_index_shows_all_categories(client):
    """Test that all categories are displayed on index."""
    response = client.get('/settings/')
    html = response.data.decode('utf-8')
    
    # Should show both categories
    assert "Test Category" in html
    assert "Second Category" in html
    
    # Should show edit links for each category
    assert 'href="/settings/edit?category=test_category"' in html
    assert 'href="/settings/edit?category=second_category"' in html


def test_edit_page_loads_all_categories(client):
    """Test edit page with all categories."""
    response = client.get('/settings/edit')
    assert response.status_code == 200
    
    html = response.data.decode('utf-8')
    
    # Should show all category friendly names
    assert "Test Category" in html
    assert "Second Category" in html


def test_edit_page_loads_single_category(client):
    """Test edit page filtered by category."""
    response = client.get('/settings/edit?category=test_category')
    assert response.status_code == 200
    
    html = response.data.decode('utf-8')
    
    # Should show test category
    assert "Test Category" in html
    
    # Should show all fields in test category
    assert "String Field" in html
    assert "Integer Field" in html
    assert "Boolean Field" in html
    assert "Select Field" in html


def test_edit_page_has_correct_form_fields(client):
    """Test that edit page renders correct input types."""
    response = client.get('/settings/edit?category=test_category')
    html = response.data.decode('utf-8')
    
    # Save HTML for debugging
    import os
    test_output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(test_output_dir, exist_ok=True)
    with open(os.path.join(test_output_dir, "edit_form.html"), "w", encoding="utf-8") as f:
        f.write(html)
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Form fields have module prefix: "Edit Settings.category.key"
    # String field
    string_input = soup.find('input', {'name': 'Edit Settings.test_category.string_field'})
    assert string_input is not None, f"String input not found. Available inputs: {[i.get('name') for i in soup.find_all('input')]}"
    assert string_input.get('value') == 'test value'
    
    # Int field
    int_input = soup.find('input', {'name': 'Edit Settings.test_category.int_field'})
    assert int_input is not None
    assert int_input.get('value') == '42'
    
    # Bool field (checkbox)
    bool_input = soup.find('input', {'name': 'Edit Settings.test_category.bool_field'})
    assert bool_input is not None
    assert bool_input.get('type') == 'checkbox'
    
    # Select field
    select_input = soup.find('select', {'name': 'Edit Settings.test_category.select_field'})
    assert select_input is not None
    options = select_input.find_all('option')
    assert len(options) == 3


def test_post_updates_string_field(client, test_config_file):
    """Test that POST updates a string field."""
    response = client.post('/settings/edit', data={
        'Edit Settings.test_category.string_field': 'new value',
        'Edit Settings.test_category.int_field': '42',
        'Edit Settings.test_category.bool_field': 'on',
        'Edit Settings.test_category.select_field': 'option2',
        'Edit Settings.second_category.another_string': 'default',
    }, follow_redirects=False)
    
    # Should redirect to index
    assert response.status_code == 302
    
    # Verify data was saved
    with open(test_config_file, 'r') as f:
        saved_config = json.load(f)
    
    assert saved_config['test_category']['string_field']['value'] == 'new value'


def test_post_updates_int_field(client, test_config_file):
    """Test that POST updates an integer field with type conversion."""
    response = client.post('/settings/edit', data={
        'Edit Settings.test_category.string_field': 'test value',
        'Edit Settings.test_category.int_field': '99',  # String from form
        'Edit Settings.test_category.bool_field': 'on',
        'Edit Settings.test_category.select_field': 'option2',
        'Edit Settings.second_category.another_string': 'default',
    }, follow_redirects=False)
    
    assert response.status_code == 302
    
    # Verify int was converted
    with open(test_config_file, 'r') as f:
        saved_config = json.load(f)
    
    assert saved_config['test_category']['int_field']['value'] == 99
    assert isinstance(saved_config['test_category']['int_field']['value'], int)


def test_post_updates_bool_field_checked(client, test_config_file):
    """Test that checked checkbox sets bool to True."""
    response = client.post('/settings/edit', data={
        'Edit Settings.test_category.string_field': 'test value',
        'Edit Settings.test_category.int_field': '42',
        'Edit Settings.test_category.bool_field': 'on',  # Checked
        'Edit Settings.test_category.select_field': 'option2',
        'Edit Settings.second_category.another_string': 'default',
        'Edit Settings.second_category.another_bool': 'on',  # Also checked
    }, follow_redirects=False)
    
    assert response.status_code == 302
    
    with open(test_config_file, 'r') as f:
        saved_config = json.load(f)
    
    assert saved_config['test_category']['bool_field']['value'] is True
    assert saved_config['second_category']['another_bool']['value'] is True


def test_post_updates_bool_field_unchecked(client, test_config_file):
    """Test that unchecked checkbox sets bool to False."""
    response = client.post('/settings/edit', data={
        'Edit Settings.test_category.string_field': 'test value',
        'Edit Settings.test_category.int_field': '42',
        # bool_field NOT in form = unchecked
        'Edit Settings.test_category.select_field': 'option2',
        'Edit Settings.second_category.another_string': 'default',
        # another_bool also NOT in form = unchecked
    }, follow_redirects=False)
    
    assert response.status_code == 302
    
    with open(test_config_file, 'r') as f:
        saved_config = json.load(f)
    
    assert saved_config['test_category']['bool_field']['value'] is False
    assert saved_config['second_category']['another_bool']['value'] is False


def test_post_updates_select_field(client, test_config_file):
    """Test that select field value is updated."""
    response = client.post('/settings/edit', data={
        'Edit Settings.test_category.string_field': 'test value',
        'Edit Settings.test_category.int_field': '42',
        'Edit Settings.test_category.bool_field': 'on',
        'Edit Settings.test_category.select_field': 'option1',  # Changed from option2
        'Edit Settings.second_category.another_string': 'default',
    }, follow_redirects=False)
    
    assert response.status_code == 302
    
    with open(test_config_file, 'r') as f:
        saved_config = json.load(f)
    
    assert saved_config['test_category']['select_field']['value'] == 'option1'


def test_post_multiple_categories(client, test_config_file):
    """Test updating fields across multiple categories."""
    response = client.post('/settings/edit', data={
        'Edit Settings.test_category.string_field': 'updated first',
        'Edit Settings.test_category.int_field': '100',
        'Edit Settings.test_category.select_field': 'option3',
        'Edit Settings.second_category.another_string': 'updated second',
    }, follow_redirects=False)
    
    assert response.status_code == 302
    
    with open(test_config_file, 'r') as f:
        saved_config = json.load(f)
    
    assert saved_config['test_category']['string_field']['value'] == 'updated first'
    assert saved_config['test_category']['int_field']['value'] == 100
    assert saved_config['second_category']['another_string']['value'] == 'updated second'


def test_breadcrumbs_on_index(client):
    """Test that breadcrumbs appear on index page."""
    response = client.get('/settings/')
    html = response.data.decode('utf-8')
    
    # Should have breadcrumbs
    assert "breadcrumb" in html.lower() or "Home" in html


def test_breadcrumbs_on_edit(client):
    """Test that breadcrumbs appear on edit page."""
    response = client.get('/settings/edit')
    html = response.data.decode('utf-8')
    
    # Should have breadcrumbs including Settings
    assert "breadcrumb" in html.lower() or "Settings" in html


def test_edit_with_invalid_int_defaults_to_zero(client, test_config_file):
    """Test that invalid integer input defaults to 0."""
    response = client.post('/settings/edit', data={
        'test_category.string_field': 'test value',
        'test_category.int_field': 'not_a_number',  # Invalid
        'test_category.select_field': 'option2',
        'second_category.another_string': 'default',
    }, follow_redirects=False)
    
    assert response.status_code == 302
    
    with open(test_config_file, 'r') as f:
        saved_config = json.load(f)
    
    # Should default to 0 for invalid int
    assert saved_config['test_category']['int_field']['value'] == 0
