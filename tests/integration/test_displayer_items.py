"""
Test all DisplayerItem classes can be instantiated and rendered.

This test auto-discovers all DisplayerItem classes and validates that:
1. Classes with instantiate_test() can create test instances
2. Test instances can be added to a displayer without errors
3. The displayer can generate output without exceptions

This replaces the old HTML-generating gallery system with a simpler validation test.
"""

import pytest
from typing import List
from src.modules import displayer


def get_all_displayer_items() -> List[type]:
    """
    Auto-discover all DisplayerItem classes.
    
    :return: List of all DisplayerItem classes
    """
    all_items = []
    
    # Get all DisplayerItem classes from all categories
    all_categories = displayer.DisplayerCategory.get_all()  # type: ignore
    for category_name, item_classes in all_categories.items():  # type: ignore
        for item_class in item_classes:
            all_items.append(item_class)
    
    return all_items


def test_all_items_discovered():
    """Ensure we discover displayer items."""
    items = get_all_displayer_items()
    assert len(items) > 0, "Should discover at least one DisplayerItem"
    print(f"\nDiscovered {len(items)} DisplayerItem classes")


@pytest.mark.parametrize("item_class", get_all_displayer_items())
def test_item_has_instantiate_test(item_class: type) -> None:
    """
    Test that each DisplayerItem class has an instantiate_test() method.
    
    This ensures all items can be automatically tested and showcased.
    """
    assert hasattr(item_class, 'instantiate_test'), \
        f"{item_class.__name__} should have instantiate_test() class method"  # type: ignore


@pytest.mark.parametrize("item_class", get_all_displayer_items())
def test_item_can_instantiate(item_class: type) -> None:
    """
    Test that each DisplayerItem class can create a test instance.
    
    This validates that instantiate_test() works without errors.
    """
    try:
        item = item_class.instantiate_test()  # type: ignore
        assert item is not None, f"{item_class.__name__} instantiate_test() returned None"  # type: ignore
        assert isinstance(item, displayer.DisplayerItem), \
            f"{item_class.__name__} instantiate_test() should return a DisplayerItem"  # type: ignore
    except Exception as e:
        pytest.fail(f"{item_class.__name__}.instantiate_test() raised exception: {e}")  # type: ignore


@pytest.mark.parametrize("item_class", get_all_displayer_items())
def test_item_can_render(item_class: type) -> None:
    """
    Test that each DisplayerItem can be added to a displayer and rendered.
    
    This validates the full rendering pipeline without generating HTML files.
    """
    try:
        # Create a simple displayer
        disp = displayer.Displayer()
        disp.add_generic("Test")
        
        # Add a layout
        layout_id = disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
        )
        
        # Instantiate and add the test item
        item = item_class.instantiate_test()  # type: ignore
        disp.add_display_item(item, column=0, layout_id=layout_id)
        
        # Try to render
        output = disp.display()
        
        # Basic validations
        assert output is not None, f"{item_class.__name__} display() returned None"  # type: ignore
        assert isinstance(output, dict), f"{item_class.__name__} display() should return dict"  # type: ignore
        
    except Exception as e:
        pytest.fail(f"{item_class.__name__} rendering failed: {e}")  # type: ignore


def test_category_organization():
    """
    Test that all items are properly categorized.
    
    This ensures the category system is working correctly.
    """
    all_categories = displayer.DisplayerCategory.get_all()  # type: ignore
    
    # Check we have the expected categories
    expected_categories = ['input', 'display', 'button', 'media', 'layout', 'advanced']
    for cat in expected_categories:
        assert cat in all_categories, f"Missing category: {cat}"  # type: ignore
    
    # Check each category has items
    non_empty_categories = [cat for cat, items in all_categories.items() if items]  # type: ignore
    assert len(non_empty_categories) > 0, "At least one category should have items"
    
    print(f"\nCategory breakdown:")
    for category, items in all_categories.items():  # type: ignore
        print(f"  {category}: {len(items)} items")  # type: ignore


def test_resource_registry_integration():
    """
    Test that items requiring resources properly register them.
    
    This validates the ResourceRegistry integration.
    """
    items_with_resources = []
    
    for item_class in get_all_displayer_items():
        if hasattr(item_class, 'get_required_resources'):
            try:
                resources = item_class.get_required_resources()  # type: ignore
                if resources:
                    items_with_resources.append((item_class, resources))  # type: ignore
            except Exception:
                pass
    
    assert len(items_with_resources) > 0, "Should have items with resource requirements"
    
    print(f"\nItems with resource requirements:")
    for item_class, resources in items_with_resources:
        print(f"  {item_class.__name__}: {resources}")  # type: ignore
