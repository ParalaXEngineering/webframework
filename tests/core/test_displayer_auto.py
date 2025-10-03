"""
Auto-discovery tests for Displayer items using the @DisplayerCategory decorator system.
Automatically tests all DisplayerItem classes based on their category.
"""

import pytest
from src import displayer


class TestDisplayerCategorySystem:
    """Test the DisplayerCategory decorator system itself."""
    
    def test_category_registry_exists(self):
        """Test that DisplayerCategory has a registry."""
        assert hasattr(displayer.DisplayerCategory, '_registry')
        assert isinstance(displayer.DisplayerCategory._registry, dict)
    
    def test_all_categories_exist(self):
        """Test that all expected categories exist."""
        expected_categories = ['input', 'display', 'button', 'media', 'advanced']
        registry = displayer.DisplayerCategory._registry
        
        for category in expected_categories:
            assert category in registry, f"Category '{category}' not in registry"
    
    def test_categories_have_items(self):
        """Test that categories have registered items."""
        registry = displayer.DisplayerCategory.get_all()
        
        # At least INPUT and DISPLAY should have items
        assert len(registry.get('input', [])) > 0, "No INPUT items registered"
        assert len(registry.get('display', [])) > 0, "No DISPLAY items registered"
    
    def test_get_all_works(self):
        """Test that get_all() method works."""
        all_items = displayer.DisplayerCategory.get_all()
        assert isinstance(all_items, dict)
        
        # Test filtered get
        input_items = displayer.DisplayerCategory.get_all('input')
        assert isinstance(input_items, list)


class TestDisplayItems:
    """Auto-discovery tests for DISPLAY category items."""
    
    @pytest.fixture
    def display_items(self):
        """Get all registered DISPLAY items."""
        return displayer.DisplayerCategory.get_all('display')
    
    def test_display_items_exist(self, display_items):
        """Test that DISPLAY items are registered."""
        assert len(display_items) > 0, "No DISPLAY items found"
        print(f"\nFound {len(display_items)} DISPLAY items:")
        for item_class in display_items:
            print(f"  - {item_class.__name__}")
    
    @pytest.mark.parametrize("item_class", displayer.DisplayerCategory.get_all('display'))
    def test_display_item_instantiation(self, item_class):
        """Test that each DISPLAY item can be instantiated."""
        # DisplayerItemText example: just needs text
        if item_class.__name__ == 'DisplayerItemText':
            item = item_class("Test text")
            assert item.m_type == displayer.DisplayerItems.TEXT
            assert item.m_text == "Test text"
        
        elif item_class.__name__ == 'DisplayerItemAlert':
            item = item_class("Alert message", displayer.BSstyle.INFO)
            assert item.m_type == displayer.DisplayerItems.ALERT
            assert item.m_text == "Alert message"
        
        elif item_class.__name__ == 'DisplayerItemBadge':
            item = item_class("Badge text", displayer.BSstyle.PRIMARY)
            assert item.m_type == displayer.DisplayerItems.BADGE
        
        elif item_class.__name__ == 'DisplayerItemPlaceholder':
            item = item_class("placeholder", "Content")
            assert item.m_type == displayer.DisplayerItems.PLACEHOLDER
        
        else:
            pytest.skip(f"No test defined for {item_class.__name__}")
    
    @pytest.mark.parametrize("item_class", displayer.DisplayerCategory.get_all('display'))
    def test_display_item_has_type(self, item_class):
        """Test that each DISPLAY item class is a DisplayerItem."""
        assert issubclass(item_class, displayer.DisplayerItem)


class TestInputItems:
    """Auto-discovery tests for INPUT category items."""
    
    @pytest.fixture
    def input_items(self):
        """Get all registered INPUT items."""
        return displayer.DisplayerCategory.get_all('input')
    
    def test_input_items_exist(self, input_items):
        """Test that INPUT items are registered."""
        assert len(input_items) > 0, "No INPUT items found"
        print(f"\nFound {len(input_items)} INPUT items:")
        for item_class in input_items:
            print(f"  - {item_class.__name__}")
    
    @pytest.mark.parametrize("item_class", displayer.DisplayerCategory.get_all('input'))
    def test_input_item_has_type(self, item_class):
        """Test that each INPUT item class is a DisplayerItem."""
        assert issubclass(item_class, displayer.DisplayerItem)
    
    @pytest.mark.parametrize("item_class", displayer.DisplayerCategory.get_all('input'))
    def test_input_item_has_id_parameter(self, item_class):
        """Test that each INPUT item's __init__ has an 'id' parameter."""
        import inspect
        sig = inspect.signature(item_class.__init__)
        params = list(sig.parameters.keys())
        
        # Skip 'self' parameter
        params = [p for p in params if p != 'self']
        
        # First parameter should be 'id' or 'ids' for most input items
        if len(params) > 0:
            first_param = params[0]
            assert first_param in ['id', 'ids'], \
                f"{item_class.__name__}.__init__ first param is '{first_param}', expected 'id' or 'ids'"


class TestButtonItems:
    """Auto-discovery tests for BUTTON category items."""
    
    @pytest.fixture
    def button_items(self):
        """Get all registered BUTTON items."""
        return displayer.DisplayerCategory.get_all('button')
    
    def test_button_items_exist(self, button_items):
        """Test that BUTTON items are registered."""
        assert len(button_items) > 0, "No BUTTON items found"
        print(f"\nFound {len(button_items)} BUTTON items:")
        for item_class in button_items:
            print(f"  - {item_class.__name__}")
    
    @pytest.mark.parametrize("item_class", displayer.DisplayerCategory.get_all('button'))
    def test_button_item_has_type(self, item_class):
        """Test that each BUTTON item class is a DisplayerItem."""
        assert issubclass(item_class, displayer.DisplayerItem)


class TestMediaItems:
    """Auto-discovery tests for MEDIA category items."""
    
    @pytest.fixture
    def media_items(self):
        """Get all registered MEDIA items."""
        return displayer.DisplayerCategory.get_all('media')
    
    def test_media_items_exist(self, media_items):
        """Test that MEDIA items are registered."""
        assert len(media_items) > 0, "No MEDIA items found"
        print(f"\nFound {len(media_items)} MEDIA items:")
        for item_class in media_items:
            print(f"  - {item_class.__name__}")
    
    @pytest.mark.parametrize("item_class", displayer.DisplayerCategory.get_all('media'))
    def test_media_item_has_type(self, item_class):
        """Test that each MEDIA item class is a DisplayerItem."""
        assert issubclass(item_class, displayer.DisplayerItem)


class TestDisplayerLayouts:
    """Tests for DisplayerLayout functionality."""
    
    def test_vertical_layout(self):
        """Test VERTICAL layout creation."""
        layout = displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [6, 6])
        assert layout.m_type == displayer.Layouts.VERTICAL.value
        assert layout.m_column == [6, 6]
    
    def test_horizontal_layout(self):
        """Test HORIZONTAL layout creation."""
        layout = displayer.DisplayerLayout(displayer.Layouts.HORIZONTAL, [4, 4, 4])
        assert layout.m_type == displayer.Layouts.HORIZONTAL.value
        assert layout.m_column == [4, 4, 4]
    
    def test_table_layout(self):
        """Test TABLE layout creation."""
        layout = displayer.DisplayerLayout(
            displayer.Layouts.TABLE,
            columns=[6, 6]
        )
        assert layout.m_type == displayer.Layouts.TABLE.value
    
    def test_spacer_layout(self):
        """Test SPACER layout creation."""
        layout = displayer.DisplayerLayout(displayer.Layouts.SPACER)
        assert layout.m_type == displayer.Layouts.SPACER.value


class TestDisplayerCore:
    """Tests for core Displayer functionality."""
    
    def test_displayer_creation(self):
        """Test creating a Displayer instance."""
        disp = displayer.Displayer()
        assert disp is not None
        assert hasattr(disp, 'm_modules')
    
    def test_add_generic_module(self):
        """Test adding a generic module."""
        disp = displayer.Displayer()
        disp.add_generic("TestModule")
        assert "TestModule" in disp.m_modules
    
    def test_add_master_layout(self):
        """Test adding a master layout."""
        disp = displayer.Displayer()
        disp.add_generic("TestModule")
        layout = displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12])
        disp.add_master_layout(layout)
        assert "layouts" in disp.m_modules["TestModule"]
    
    def test_add_display_item(self):
        """Test adding a display item."""
        disp = displayer.Displayer()
        disp.add_generic("TestModule")
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12]))
        
        item = displayer.DisplayerItemText("Test content")
        result = disp.add_display_item(item, 0)
        assert result is True


if __name__ == "__main__":
    # Print registry for debugging
    print("\n" + "="*60)
    print("DisplayerCategory Registry:")
    print("="*60)
    for category, items in displayer.DisplayerCategory.get_all().items():
        print(f"\n{category.upper()} ({len(items)} items):")
        for item_class in items:
            print(f"  - {item_class.__name__}")
    
    print("\n" + "="*60)
    print("Running tests...")
    print("="*60 + "\n")
    
    pytest.main([__file__, "-v", "-s"])
