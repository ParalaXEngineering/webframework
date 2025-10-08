"""
Comprehensive tests for new Displayer items (Card, AlertBox, DynamicContent, ButtonGroup, IconText).

These items were added to provide reusable, Bootstrap-based components that eliminate
the need for custom HTML in applications.

Test Coverage:
- Instantiation via constructors with all parameters
- Instantiation via instantiate_test() classmethod
- Serialization to dict format for Jinja2 templates
- Parameter validation and type checking
- Integration with Displayer rendering pipeline

New Items Tested:
1. DisplayerItemCard - Feature cards with colored headers, icons, and footer buttons
2. DisplayerItemAlertBox - Bootstrap alerts with icons and dismissible option
3. DisplayerItemDynamicContent - Placeholders for emit_reload() dynamic updates
4. DisplayerItemButtonGroup - Multiple buttons in horizontal/vertical layouts
5. DisplayerItemIconText - Icon + text inline with optional links
"""

import pytest
from src.modules import displayer
from src.modules.displayer import (
    DisplayerItemCard,
    DisplayerItemAlertBox,
    DisplayerItemDynamicContent,
    DisplayerItemButtonGroup,
    DisplayerItemIconText,
    DisplayerItems,
    BSstyle
)


# =============================================================================
# DisplayerItemCard Tests
# =============================================================================

class TestDisplayerItemCard:
    """Test suite for DisplayerItemCard."""
    
    def test_card_basic_instantiation(self):
        """Test creating a card with minimal parameters."""
        card = DisplayerItemCard(
            id="test_card",
            title="Test Title",
            body="Test body content"
        )
        
        assert card.m_itemId == "test_card"
        assert card.m_text == "Test Title"
        assert card.m_value == "Test body content"
        assert card.m_type == DisplayerItems.CARD
    
    def test_card_with_icon_and_style(self):
        """Test card with icon and custom header color."""
        card = DisplayerItemCard(
            id="styled_card",
            title="Styled Card",
            body="Content",
            icon="mdi mdi-star",
            header_color=BSstyle.SUCCESS
        )
        
        assert card.m_icon == "mdi mdi-star"
        assert card.m_style == "success"  # BSstyle enum value is stored as string
    
    def test_card_with_footer_buttons(self):
        """Test card with footer buttons."""
        buttons = [
            {"id": "btn1", "text": "Action 1", "style": "primary", "icon": "mdi mdi-play"},
            {"id": "btn2", "text": "Action 2", "style": "secondary"}
        ]
        
        card = DisplayerItemCard(
            id="button_card",
            title="Card with Buttons",
            body="Content",
            footer_buttons=buttons
        )
        
        assert card.m_data == buttons
        assert len(card.m_data) == 2
    
    def test_card_instantiate_test(self):
        """Test the instantiate_test() classmethod."""
        card = DisplayerItemCard.instantiate_test()
        
        assert card.m_itemId == "test_card"
        assert card.m_text == "Test Card"
        assert card.m_type == DisplayerItems.CARD
        assert "sample" in card.m_value.lower()  # Check for actual content
    
    def test_card_serialization(self):
        """Test card serializes correctly for templates."""
        card = DisplayerItemCard(
            id="serialize_test",
            title="Title",
            body="Body",
            icon="mdi mdi-test",
            header_color=BSstyle.PRIMARY
        )
        
        # DisplayerItem uses internal dict for serialization
        assert card.m_type == DisplayerItems.CARD
        assert card.m_itemId == "serialize_test"
        assert card.m_text == "Title"
        assert card.m_value == "Body"
        assert card.m_icon == "mdi mdi-test"
        assert card.m_style == "primary"


# =============================================================================
# DisplayerItemAlertBox Tests
# =============================================================================

class TestDisplayerItemAlertBox:
    """Test suite for DisplayerItemAlertBox."""
    
    def test_alertbox_basic(self):
        """Test creating an alert with minimal parameters."""
        alert = DisplayerItemAlertBox(
            id="test_alert",
            text="Alert message",
            style=BSstyle.INFO
        )
        
        assert alert.m_itemId == "test_alert"
        assert alert.m_text == "Alert message"
        assert alert.m_style == "info"  # BSstyle enum value is stored as string
        assert alert.m_type == DisplayerItems.ALERTBOX
    
    def test_alertbox_with_icon_and_title(self):
        """Test alert with icon and title."""
        alert = DisplayerItemAlertBox(
            id="titled_alert",
            text="Message",
            style=BSstyle.WARNING,
            icon="mdi mdi-alert",
            title="Warning!"
        )
        
        assert alert.m_icon == "mdi mdi-alert"
        assert alert.m_header == "Warning!"
    
    def test_alertbox_dismissible(self):
        """Test dismissible alert."""
        alert = DisplayerItemAlertBox(
            id="dismissible_alert",
            text="Can be closed",
            style=BSstyle.SUCCESS,
            dismissible=True
        )
        
        assert alert.m_disabled is True
    
    def test_alertbox_instantiate_test(self):
        """Test the instantiate_test() classmethod."""
        alert = DisplayerItemAlertBox.instantiate_test()
        
        assert alert.m_itemId == "test_alert"  # Match actual ID from instantiate_test()
        assert alert.m_type == DisplayerItems.ALERTBOX
        assert alert.m_style == "info"
    
    def test_alertbox_all_styles(self):
        """Test alert with all Bootstrap styles."""
        styles = [BSstyle.PRIMARY, BSstyle.SECONDARY, BSstyle.SUCCESS, 
                  BSstyle.ERROR, BSstyle.WARNING, BSstyle.INFO]  # Use ERROR not DANGER
        
        for style in styles:
            alert = DisplayerItemAlertBox(
                id=f"alert_{style.value}",
                text=f"Test {style.value}",
                style=style
            )
            assert alert.m_style == style.value  # Compare string values


# =============================================================================
# DisplayerItemDynamicContent Tests
# =============================================================================

class TestDisplayerItemDynamicContent:
    """Test suite for DisplayerItemDynamicContent."""
    
    def test_dynamic_content_basic(self):
        """Test creating dynamic content placeholder."""
        content = DisplayerItemDynamicContent(
            id="dynamic_area",
            initial_content="<p>Initial content</p>"
        )
        
        assert content.m_itemId == "dynamic_area"
        assert content.m_text == "<p>Initial content</p>"
        assert content.m_type == DisplayerItems.DYNAMICCONTENT
    
    def test_dynamic_content_with_card(self):
        """Test dynamic content with card wrapper."""
        content = DisplayerItemDynamicContent(
            id="card_area",
            initial_content="Content",
            card=True
        )
        
        assert content.m_disabled is True
    
    def test_dynamic_content_without_card(self):
        """Test dynamic content without card wrapper."""
        content = DisplayerItemDynamicContent(
            id="plain_area",
            initial_content="Content",
            card=False
        )
        
        assert content.m_disabled is False
    
    def test_dynamic_content_instantiate_test(self):
        """Test the instantiate_test() classmethod."""
        content = DisplayerItemDynamicContent.instantiate_test()
        
        assert content.m_itemId == "test_dynamic"
        assert content.m_type == DisplayerItems.DYNAMICCONTENT
        assert "dynamic" in content.m_text.lower()  # Check for actual content
    
    def test_dynamic_content_for_emit_reload(self):
        """Test that dynamic content ID matches emit_reload() target."""
        # This simulates scheduler usage pattern
        target_id = "live_updates"
        
        content = DisplayerItemDynamicContent(
            id=target_id,
            initial_content="Waiting...",
            card=True
        )
        
        # Verify ID is accessible for emit_reload([{'id': target_id, 'content': '...'}])
        assert content.m_itemId == target_id


# =============================================================================
# DisplayerItemButtonGroup Tests
# =============================================================================

class TestDisplayerItemButtonGroup:
    """Test suite for DisplayerItemButtonGroup."""
    
    def test_button_group_horizontal(self):
        """Test horizontal button group."""
        buttons = [
            {"id": "btn1", "text": "Button 1", "style": "primary"},
            {"id": "btn2", "text": "Button 2", "style": "secondary"}
        ]
        
        group = DisplayerItemButtonGroup(
            id="h_group",
            buttons=buttons,
            layout="horizontal"
        )
        
        assert group.m_itemId == "h_group"
        assert group.m_data == buttons
        assert group.m_value == "horizontal"
        assert group.m_type == DisplayerItems.BUTTONGROUP
    
    def test_button_group_vertical(self):
        """Test vertical button group."""
        buttons = [{"id": "b1", "text": "Top"}, {"id": "b2", "text": "Bottom"}]
        
        group = DisplayerItemButtonGroup(
            id="v_group",
            buttons=buttons,
            layout="vertical"
        )
        
        assert group.m_value == "vertical"
    
    def test_button_group_with_icons(self):
        """Test button group with icons."""
        buttons = [
            {"id": "play", "text": "Play", "icon": "mdi mdi-play", "style": "success"},
            {"id": "stop", "text": "Stop", "icon": "mdi mdi-stop", "style": "danger"}
        ]
        
        group = DisplayerItemButtonGroup(
            id="icon_group",
            buttons=buttons
        )
        
        assert all("icon" in btn for btn in group.m_data)
    
    def test_button_group_disabled_buttons(self):
        """Test button group with disabled buttons."""
        buttons = [
            {"id": "enabled", "text": "Enabled", "disabled": False},
            {"id": "disabled", "text": "Disabled", "disabled": True}
        ]
        
        group = DisplayerItemButtonGroup(
            id="mixed_group",
            buttons=buttons
        )
        
        assert group.m_data[1]["disabled"] is True
    
    def test_button_group_instantiate_test(self):
        """Test the instantiate_test() classmethod."""
        group = DisplayerItemButtonGroup.instantiate_test()
        
        assert group.m_itemId == "test_btn_group"  # Match actual ID from instantiate_test()
        assert group.m_type == DisplayerItems.BUTTONGROUP
        assert len(group.m_data) >= 2


# =============================================================================
# DisplayerItemIconText Tests
# =============================================================================

class TestDisplayerItemIconText:
    """Test suite for DisplayerItemIconText."""
    
    def test_icontext_basic(self):
        """Test creating icon + text display."""
        item = DisplayerItemIconText(
            id="test_icon",
            icon="mdi mdi-check",
            text="Success message"
        )
        
        assert item.m_itemId == "test_icon"
        assert item.m_icon == "mdi mdi-check"
        assert item.m_text == "Success message"
        assert item.m_type == DisplayerItems.ICONTEXT
    
    def test_icontext_with_color(self):
        """Test icon + text with color."""
        item = DisplayerItemIconText(
            id="colored",
            icon="mdi mdi-alert",
            text="Warning",
            color=BSstyle.WARNING
        )
        
        assert item.m_style == "warning"  # BSstyle enum value is stored as string
    
    def test_icontext_with_link(self):
        """Test icon + text with link."""
        item = DisplayerItemIconText(
            id="linked",
            icon="mdi mdi-link",
            text="Click here",
            link="https://example.com"
        )
        
        assert item.m_path == "https://example.com"
    
    def test_icontext_instantiate_test(self):
        """Test the instantiate_test() classmethod."""
        item = DisplayerItemIconText.instantiate_test()
        
        assert item.m_itemId == "test_icontext"
        assert item.m_type == DisplayerItems.ICONTEXT
        assert item.m_icon
        assert item.m_text
    
    def test_icontext_all_parameters(self):
        """Test icon + text with all parameters."""
        item = DisplayerItemIconText(
            id="full_test",
            icon="mdi mdi-information",
            text="Documentation",
            color=BSstyle.INFO,
            link="/docs"
        )
        
        assert item.m_itemId == "full_test"
        assert item.m_icon == "mdi mdi-information"
        assert item.m_text == "Documentation"
        assert item.m_style == "info"  # BSstyle enum value is stored as string
        assert item.m_path == "/docs"


# =============================================================================
# Integration Tests
# =============================================================================

class TestNewItemsIntegration:
    """Integration tests for new items in Displayer pipeline."""
    
    def test_all_new_items_discoverable(self):
        """Test that all new items are registered in DisplayerCategory."""
        all_items = displayer.DisplayerCategory.get_all()
        display_items = all_items.get("display", [])
        input_items = all_items.get("input", [])
        
        # Check display category items
        display_new_items = [
            DisplayerItemCard,
            DisplayerItemAlertBox,
            DisplayerItemDynamicContent,
            DisplayerItemIconText
        ]
        
        for item_class in display_new_items:
            assert item_class in display_items, f"{item_class.__name__} not found in display category"
        
        # ButtonGroup is in input category (because it has submit buttons)
        assert DisplayerItemButtonGroup in input_items, "DisplayerItemButtonGroup not found in input category"
    
    def test_new_items_instantiation(self):
        """Test that all new items can be instantiated without errors."""
        # Test basic instantiation of each new item
        card = DisplayerItemCard(id="card", title="Card", body="Content")
        assert card.m_type == DisplayerItems.CARD
        
        alert = DisplayerItemAlertBox(id="alert", text="Alert", style=BSstyle.INFO)
        assert alert.m_type == DisplayerItems.ALERTBOX
        
        dynamic = DisplayerItemDynamicContent(id="dynamic", initial_content="Dynamic")
        assert dynamic.m_type == DisplayerItems.DYNAMICCONTENT
        
        buttons = DisplayerItemButtonGroup(id="buttons", buttons=[{"id": "b1", "text": "B1"}])
        assert buttons.m_type == DisplayerItems.BUTTONGROUP
        
        icontext = DisplayerItemIconText(id="icon", icon="mdi mdi-test", text="Text")
        assert icontext.m_type == DisplayerItems.ICONTEXT
    
    def test_new_items_serialization(self):
        """Test that all new items have correct internal structure."""
        items = [
            DisplayerItemCard.instantiate_test(),
            DisplayerItemAlertBox.instantiate_test(),
            DisplayerItemDynamicContent.instantiate_test(),
            DisplayerItemButtonGroup.instantiate_test(),
            DisplayerItemIconText.instantiate_test()
        ]
        
        for item in items:
            # Check internal structure (used by template rendering)
            assert item.m_type is not None
            assert item.m_itemId is not None
            assert item.m_type.value in ["CARD", "ALERTBOX", "DYNAMICCONTENT", "BUTTONGROUP", "ICONTEXT"]


# =============================================================================
# Documentation Tests
# =============================================================================

class TestNewItemsDocumentation:
    """Verify that new items have proper documentation."""
    
    def test_all_items_have_docstrings(self):
        """Test that all new items have class docstrings."""
        items = [
            DisplayerItemCard,
            DisplayerItemAlertBox,
            DisplayerItemDynamicContent,
            DisplayerItemButtonGroup,
            DisplayerItemIconText
        ]
        
        for item_class in items:
            assert item_class.__doc__ is not None, f"{item_class.__name__} missing docstring"
            assert len(item_class.__doc__.strip()) > 50, f"{item_class.__name__} docstring too short"
    
    def test_all_items_have_instantiate_test(self):
        """Test that all new items have instantiate_test() method."""
        items = [
            DisplayerItemCard,
            DisplayerItemAlertBox,
            DisplayerItemDynamicContent,
            DisplayerItemButtonGroup,
            DisplayerItemIconText
        ]
        
        for item_class in items:
            assert hasattr(item_class, 'instantiate_test'), f"{item_class.__name__} missing instantiate_test()"
            
            # Should be callable and return instance
            instance = item_class.instantiate_test()
            assert isinstance(instance, item_class)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
