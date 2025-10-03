"""
HTTP Form Testing
Tests for form data processing and JSON transformation.
Tests utilities.util_post_to_json which transforms POST form data to nested JSON.
"""

import pytest
from src import utilities


class TestFormDataTransformation:
    """Test form data transformation to JSON using . separator."""
    
    def test_simple_field_transformation(self):
        """Test simple fields remain flat."""
        form_data = {
            'name': 'John',
            'age': '30'
        }
        result = utilities.util_post_to_json(form_data)
        assert result == {
            'name': 'John',
            'age': '30'  # No type conversion for simple strings
        }
    
    def test_nested_field_transformation(self):
        """Test nested field transformation with . separator."""
        form_data = {
            'user.name': 'Alice',
            'user.email': 'alice@example.com'
        }
        result = utilities.util_post_to_json(form_data)
        assert result == {
            'user': {
                'name': 'Alice',
                'email': 'alice@example.com'
            }
        }
    
    def test_deep_nesting_transformation(self):
        """Test deeply nested field transformation."""
        form_data = {
            'company.address.street': 'Main St',
            'company.address.city': 'NYC'
        }
        result = utilities.util_post_to_json(form_data)
        assert result == {
            'company': {
                'address': {
                    'street': 'Main St',
                    'city': 'NYC'
                }
            }
        }
    
    def test_empty_fields(self):
        """Test empty fields are handled."""
        form_data = {
            'name': '',
            'age': ''
        }
        result = utilities.util_post_to_json(form_data)
        assert result == {'name': '', 'age': ''}
    
    def test_special_characters(self):
        """Test special characters in values."""
        form_data = {
            'message': 'Hello & goodbye',
            'email': 'test@example.com'
        }
        result = utilities.util_post_to_json(form_data)
        assert result['message'] == 'Hello & goodbye'
        assert result['email'] == 'test@example.com'
    
    def test_mixed_nested_and_flat(self):
        """Test mix of nested and flat fields."""
        form_data = {
            'name': 'Bob',
            'contact.phone': '555-1234',
            'contact.email': 'bob@example.com',
            'age': '25'
        }
        result = utilities.util_post_to_json(form_data)
        assert result['name'] == 'Bob'
        assert result['age'] == '25'
        assert result['contact']['phone'] == '555-1234'
        assert result['contact']['email'] == 'bob@example.com'
    
    def test_multichoice_fields(self):
        """Test multichoice checkbox pattern (item_choice: 'on')."""
        form_data = {
            'colors_red': 'on',
            'colors_blue': 'on',
            'colors_green': 'on'
        }
        result = utilities.util_post_to_json(form_data)
        # Should create array: colors = ['red', 'blue', 'green']
        assert 'colors' in result
        assert isinstance(result['colors'], list)
        assert 'red' in result['colors']
        assert 'blue' in result['colors']
        assert 'green' in result['colors']
    
    def test_prefix_with_hash(self):
        """Test fields with # prefix get stripped."""
        form_data = {
            '#hidden': 'value',
            'normal': 'data'
        }
        result = utilities.util_post_to_json(form_data)
        # # prefix gets removed
        assert 'hidden' in result
        assert result['hidden'] == 'value'
        assert result['normal'] == 'data'
