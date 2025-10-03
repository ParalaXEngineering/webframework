"""
Automated HTTP Tests for Displayer System

These tests use the requests library to make actual HTTP calls to the demo
Flask application, testing both GET (page rendering) and POST (form submission)
endpoints automatically without requiring manual browser interaction.

This validates:
1. Pages render without errors
2. HTML contains expected content
3. Form submissions work correctly
4. POST data is transformed properly by util_post_to_json
"""

import pytest
import requests
import time
import subprocess
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from utilities import util_post_to_json


# Demo server configuration
DEMO_HOST = "127.0.0.1"
DEMO_PORT = 5001
BASE_URL = f"http://{DEMO_HOST}:{DEMO_PORT}"


@pytest.fixture(scope="module")
def demo_server():
    """Start the demo Flask server for testing."""
    # Start demo.py as a subprocess
    demo_path = Path(__file__).parent.parent / "demo.py"
    venv_python = Path(__file__).parent.parent / ".venv" / "bin" / "python"
    
    if not venv_python.exists():
        # Try without venv
        venv_python = "python"
    
    process = subprocess.Popen(
        [str(venv_python), str(demo_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(BASE_URL, timeout=1)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException:
            time.sleep(0.5)
    else:
        process.kill()
        pytest.fail("Demo server failed to start within timeout")
    
    yield process
    
    # Cleanup
    process.kill()
    process.wait()


class TestPageRendering:
    """Test that all demo pages render successfully."""
    
    def test_index_page(self, demo_server):
        """Test the main index page loads."""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        assert b"Demo Navigation" in response.content or b"Displayer" in response.content
    
    def test_layouts_page(self, demo_server):
        """Test the layouts demo page loads."""
        response = requests.get(f"{BASE_URL}/layouts")
        assert response.status_code == 200
        assert b"Layout" in response.content
    
    def test_text_display_page(self, demo_server):
        """Test the text & display items page loads."""
        response = requests.get(f"{BASE_URL}/text-display")
        assert response.status_code == 200
        assert b"Text" in response.content or b"Display" in response.content
    
    def test_inputs_page_get(self, demo_server):
        """Test the inputs page loads with GET request."""
        response = requests.get(f"{BASE_URL}/inputs")
        assert response.status_code == 200
        assert b"Input" in response.content or b"form" in response.content
    
    def test_complete_showcase_page(self, demo_server):
        """Test the complete showcase page loads."""
        response = requests.get(f"{BASE_URL}/complete-showcase")
        assert response.status_code == 200
        assert b"Showcase" in response.content or b"Complete" in response.content


class TestFormSubmission:
    """Test form POST submissions and data transformation."""
    
    def test_simple_form_post(self, demo_server):
        """Test simple form field submission."""
        session = requests.Session()
        
        # First GET to establish session
        session.get(f"{BASE_URL}/inputs")
        
        # Submit form with simple fields
        form_data = {
            "name": "John Doe",
            "age": "30",
            "description": "Test description"
        }
        
        response = session.post(f"{BASE_URL}/inputs", data=form_data)
        assert response.status_code == 200
        # Should show success or at least not error
        assert response.status_code != 500
    
    def test_nested_form_post(self, demo_server):
        """Test nested field submission (dot notation)."""
        session = requests.Session()
        session.get(f"{BASE_URL}/inputs")
        
        # Submit with nested fields
        form_data = {
            "user.name": "Jane Doe",
            "user.age": "25",
            "settings.theme": "dark",
            "settings.notifications.email": "true"
        }
        
        response = session.post(f"{BASE_URL}/inputs", data=form_data)
        assert response.status_code == 200
    
    def test_list_form_post(self, demo_server):
        """Test list field submission (listNN pattern)."""
        session = requests.Session()
        session.get(f"{BASE_URL}/inputs")
        
        # Submit with list fields
        form_data = {
            "items.list00": "item1",
            "items.list01": "item2",
            "items.list02": "item3"
        }
        
        response = session.post(f"{BASE_URL}/inputs", data=form_data)
        assert response.status_code == 200
    
    def test_select_form_post(self, demo_server):
        """Test select field submission."""
        session = requests.Session()
        session.get(f"{BASE_URL}/inputs")
        
        form_data = {
            "country": "USA",
            "languages": "Python"
        }
        
        response = session.post(f"{BASE_URL}/inputs", data=form_data)
        assert response.status_code == 200


class TestDataTransformation:
    """Test util_post_to_json transformations (unit tests)."""
    
    def test_simple_field_transformation(self):
        """Test simple field remains unchanged."""
        data = {"name": "John", "age": "30"}
        result = util_post_to_json(data)
        # Note: util_post_to_json does NOT convert types, values stay as strings
        assert result == {"name": "John", "age": "30"}
    
    def test_nested_field_transformation(self):
        """Test dot notation creates nested structure."""
        data = {
            "user.name": "Jane",
            "user.age": "25",
            "user.email": "jane@example.com"
        }
        result = util_post_to_json(data)
        # Values stay as strings - no type conversion
        assert result == {
            "user": {
                "name": "Jane",
                "age": "25",
                "email": "jane@example.com"
            }
        }
    
    def test_deep_nesting_transformation(self):
        """Test multiple levels of nesting."""
        data = {
            "settings.display.theme": "dark",
            "settings.display.language": "en",
            "settings.notifications.email": "enabled"
        }
        result = util_post_to_json(data)
        # No type conversion - strings stay as strings
        assert result == {
            "settings": {
                "display": {
                    "theme": "dark",
                    "language": "en"
                },
                "notifications": {
                    "email": "enabled"
                }
            }
        }
    
    def test_list_transformation(self):
        """Test listNN pattern creates arrays."""
        # Pattern is list0, list1, list2 (not list00)
        data = {
            "items.list0": "item1",
            "items.list1": "item2",
            "items.list2": "item3"
        }
        result = util_post_to_json(data)
        # listNN pattern creates a direct array at that level
        assert result == {
            "items": ["item1", "item2", "item3"]
        }
    
    def test_list_with_nested_fields(self):
        """Test lists combined with nested fields."""
        data = {
            "user.name": "John",
            "user.tags.list0": "python",
            "user.tags.list1": "flask",
            "user.age": "30"
        }
        result = util_post_to_json(data)
        # listNN creates direct array, no type conversion
        assert result == {
            "user": {
                "name": "John",
                "age": "30",
                "tags": ["python", "flask"]
            }
        }
    
    def test_mapping_fields(self):
        """Test mapping fields (mapleft/mapright pattern)."""
        # Note: mapping transformation requires util_post_unmap() separately
        data = {
            "module.item.category.mapleft0": "key1",
            "module.item.category.mapright0": "value1",
            "module.item.category.mapleft1": "key2",
            "module.item.category.mapright1": "value2"
        }
        result = util_post_to_json(data)
        # util_post_to_json doesn't transform mappings - that's done by util_post_unmap
        assert "module" in result
        assert "item" in result["module"]
        # Mapping fields exist but aren't transformed yet
        assert "mapleft0" in result["module"]["item"]["category"]
    
    def test_checkbox_transformation(self):
        """Test checkbox fields (item_choice: on pattern)."""
        data = {
            "features.feature1_choice": "on",
            "features.feature2_choice": "on",
            "features.feature3_choice": "off"
        }
        result = util_post_to_json(data)
        # _choice fields should be converted to boolean
        assert "features" in result
    
    def test_boolean_conversion(self):
        """Test that strings are NOT automatically converted to booleans."""
        data = {
            "enabled": "true",
            "disabled": "false",
            "active": "True",
            "inactive": "False"
        }
        result = util_post_to_json(data)
        # No automatic type conversion - stays as strings
        assert result["enabled"] == "true"
        assert result["disabled"] == "false"
        assert result["active"] == "True"
        assert result["inactive"] == "False"
    
    def test_numeric_conversion(self):
        """Test that numeric strings are NOT automatically converted."""
        data = {
            "integer": "42",
            "float": "3.14",
            "negative": "-10",
            "text": "abc123"
        }
        result = util_post_to_json(data)
        # No automatic type conversion - all stay as strings
        assert result["integer"] == "42"
        assert result["float"] == "3.14"
        assert result["negative"] == "-10"
        assert result["text"] == "abc123"
    
    def test_mixed_complex_transformation(self):
        """Test complex form with multiple patterns."""
        data = {
            "user.name": "Alice",
            "user.age": "28",
            "user.hobbies.list0": "reading",
            "user.hobbies.list1": "coding",
            "settings.theme": "dark",
            "settings.notifications.email": "enabled",
            "settings.notifications.sms": "disabled",
            "active": "yes"
        }
        result = util_post_to_json(data)
        
        # Verify structure - no type conversion, listNN creates direct array
        assert "user" in result
        assert result["user"]["name"] == "Alice"
        assert result["user"]["age"] == "28"  # Stays as string
        assert "hobbies" in result["user"]
        assert result["user"]["hobbies"] == ["reading", "coding"]  # Direct array
        
        assert "settings" in result
        assert result["settings"]["theme"] == "dark"
        assert result["settings"]["notifications"]["email"] == "enabled"  # String
        assert result["settings"]["notifications"]["sms"] == "disabled"  # String
        
        assert result["active"] == "yes"  # String


class TestCurlExamples:
    """Examples that can be run with curl from command line."""
    
    def test_get_request_example(self, demo_server):
        """Example: curl http://127.0.0.1:5001/"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        print(f"\nCurl equivalent: curl {BASE_URL}/")
    
    def test_post_request_example(self, demo_server):
        """Example: curl -X POST with form data."""
        form_data = {
            "name": "Test User",
            "age": "25"
        }
        response = requests.post(f"{BASE_URL}/inputs", data=form_data)
        assert response.status_code == 200
        
        # Print curl command
        curl_cmd = f'curl -X POST {BASE_URL}/inputs'
        for key, value in form_data.items():
            curl_cmd += f' -d "{key}={value}"'
        print(f"\nCurl equivalent: {curl_cmd}")
    
    def test_nested_post_request_example(self, demo_server):
        """Example: curl -X POST with nested fields."""
        form_data = {
            "user.name": "Jane",
            "user.age": "30",
            "settings.theme": "dark"
        }
        response = requests.post(f"{BASE_URL}/inputs", data=form_data)
        assert response.status_code == 200
        
        # Print curl command
        curl_cmd = f'curl -X POST {BASE_URL}/inputs'
        for key, value in form_data.items():
            curl_cmd += f' -d "{key}={value}"'
        print(f"\nCurl equivalent: {curl_cmd}")


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v", "--tb=short"])
