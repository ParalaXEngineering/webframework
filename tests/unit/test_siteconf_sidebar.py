"""
Unit tests for Site_conf sidebar generation based on enabled features.

Tests that sidebar items are correctly added when features are enabled.
"""
import pytest
import sys
from pathlib import Path

# Setup path - must be done before imports
test_dir = Path(__file__).parent.parent
framework_dir = test_dir.parent
src_dir = framework_dir / 'src'
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from src.modules.site_conf import Site_conf


class TestSidebarGeneration:
    """Test that sidebar is correctly populated based on enabled features."""
    
    def test_empty_sidebar_by_default(self):
        """Test that sidebar is empty when no features are enabled."""
        conf = Site_conf()
        assert len(conf.m_sidebar) == 0
    
    def test_authentication_adds_user_sections(self):
        """Test that enabling authentication adds User Management and Admin sections."""
        conf = Site_conf()
        conf.enable_authentication(add_to_sidebar=True)
        
        # Check sidebar has items
        assert len(conf.m_sidebar) > 0
        
        # Find User Management section
        has_user_mgmt_title = False
        has_account_section = False
        has_admin_section = False
        
        for item in conf.m_sidebar:
            if item.get("name") == "User Management" and item.get("isTitle"):
                has_user_mgmt_title = True
            if item.get("endpoint") == "user":
                has_account_section = True
                # Check submenu items
                assert "submenu" in item
                submenu_names = [s["name"] for s in item["submenu"]]
                assert "My Profile" in submenu_names
                assert "My Preferences" in submenu_names
            if item.get("endpoint") == "admin":
                has_admin_section = True
                # Check submenu items
                assert "submenu" in item
                submenu_names = [s["name"] for s in item["submenu"]]
                assert "Users" in submenu_names
                assert "Permissions" in submenu_names
                assert "Groups" in submenu_names
        
        assert has_user_mgmt_title, "Should have 'User Management' title"
        assert has_account_section, "Should have 'Account' section with user endpoint"
        assert has_admin_section, "Should have 'Admin' section"
    
    def test_threads_adds_system_section(self):
        """Test that enabling threads creates System section with Monitoring."""
        conf = Site_conf()
        conf.enable_threads(add_to_sidebar=True)
        
        # Should have System title and Monitoring section
        has_system_title = False
        has_monitoring_section = False
        has_threads_submenu = False
        
        for item in conf.m_sidebar:
            if item.get("name") == "System" and item.get("isTitle"):
                has_system_title = True
            if item.get("endpoint") == "monitoring":
                has_monitoring_section = True
                # Check for threads submenu
                if "submenu" in item:
                    for submenu in item["submenu"]:
                        if submenu.get("name") == "Thread Monitor":
                            has_threads_submenu = True
        
        assert has_system_title, "Should have 'System' title"
        assert has_monitoring_section, "Should have 'Monitoring' section"
        assert has_threads_submenu, "Should have 'Thread Monitor' submenu"
    
    def test_multiple_features_organize_into_sections(self):
        """Test that multiple framework features organize into logical sections."""
        conf = Site_conf()
        conf.enable_threads(add_to_sidebar=True)
        conf.enable_log_viewer(add_to_sidebar=True)
        conf.enable_settings(add_to_sidebar=True)
        conf.enable_updater(add_to_sidebar=True)
        
        # Count System titles - should only be 1
        system_title_count = sum(
            1 for item in conf.m_sidebar 
            if item.get("name") == "System" and item.get("isTitle")
        )
        assert system_title_count == 1, "Should only have one 'System' title"
        
        # Check Monitoring section has monitoring tools
        monitoring_section = next(
            (item for item in conf.m_sidebar if item.get("endpoint") == "monitoring"), 
            None
        )
        assert monitoring_section is not None, "Should have Monitoring section"
        monitoring_submenus = [s["name"] for s in monitoring_section.get("submenu", [])]
        assert "Thread Monitor" in monitoring_submenus
        assert "Log Viewer" in monitoring_submenus
        
        # Check Tools section has tools
        tools_section = next(
            (item for item in conf.m_sidebar if item.get("endpoint") == "tools"), 
            None
        )
        assert tools_section is not None, "Should have Tools section"
        tools_submenus = [s["name"] for s in tools_section.get("submenu", [])]
        assert "Settings" in tools_submenus
        
        # Check Deployment section has deployment tools
        deployment_section = next(
            (item for item in conf.m_sidebar if item.get("endpoint") == "deployment"), 
            None
        )
        assert deployment_section is not None, "Should have Deployment section"
        deployment_submenus = [s["name"] for s in deployment_section.get("submenu", [])]
        assert "Updater" in deployment_submenus
    
    def test_enable_all_features(self):
        """Test that enable_all_features adds all appropriate sidebar items."""
        conf = Site_conf()
        conf.enable_all_features(add_to_sidebar=True)
        
        # Check for User Management
        has_user_section = any(
            item.get("endpoint") == "user" for item in conf.m_sidebar
        )
        
        # Check for System sections
        has_monitoring = any(
            item.get("endpoint") == "monitoring" for item in conf.m_sidebar
        )
        has_tools = any(
            item.get("endpoint") == "tools" for item in conf.m_sidebar
        )
        has_deployment = any(
            item.get("endpoint") == "deployment" for item in conf.m_sidebar
        )
        
        # Get all submenu items from all sections
        all_submenus = []
        for item in conf.m_sidebar:
            if "submenu" in item:
                all_submenus.extend([s["name"] for s in item["submenu"]])
        
        assert has_user_section, "Should have user management section"
        assert has_monitoring, "Should have monitoring section"
        assert has_tools, "Should have tools section"
        assert has_deployment, "Should have deployment section"
        assert "Thread Monitor" in all_submenus
        assert "Log Viewer" in all_submenus
        assert "Settings" in all_submenus
        assert "Bug Tracker" in all_submenus
        assert "Updater" in all_submenus
        assert "Packager" in all_submenus
    
    def test_authentication_disabled_no_user_section(self):
        """Test that user sections are not added when authentication is disabled."""
        conf = Site_conf()
        conf.enable_threads(add_to_sidebar=True)
        conf.enable_settings(add_to_sidebar=True)
        
        # Should NOT have user or admin sections
        has_user_section = any(
            item.get("endpoint") == "user" for item in conf.m_sidebar
        )
        has_admin_section = any(
            item.get("endpoint") == "admin" for item in conf.m_sidebar
        )
        
        assert not has_user_section, "Should NOT have user section when auth disabled"
        assert not has_admin_section, "Should NOT have admin section when auth disabled"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
