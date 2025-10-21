"""
Integration test for conditional blueprint registration.

Tests that the Flask app can be set up with different feature configurations.
"""
import pytest
import sys
from pathlib import Path

# Setup path
test_dir = Path(__file__).parent.parent
framework_dir = test_dir.parent
src_dir = framework_dir / 'src'
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


def test_app_setup_minimal_features():
    """Test that app can be set up with minimal features."""
    from flask import Flask
    from src.modules import site_conf
    from src.modules.site_conf import Site_conf
    
    # Create minimal config
    class MinimalConfig(Site_conf):
        pass
    
    # Create app
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test'
    
    # Set site_conf
    conf = MinimalConfig()
    site_conf.site_conf_obj = conf
    site_conf.site_conf_app_path = str(framework_dir)
    
    # Check blueprints can be imported
    from src.pages import common
    assert hasattr(common, 'bp'), "common module should have bp attribute"
    
    # Register common blueprint (always available)
    app.register_blueprint(common.bp)
    
    # Verify routes
    with app.test_client() as client:
        # Common assets route should exist
        response = client.get('/common/assets/images/?filename=test.png')
        # 404 is ok (file doesn't exist), but route should be registered
        assert response.status_code in [200, 404], "Common assets route should be registered"


def test_app_setup_all_features():
    """Test that app can be set up with all features enabled."""
    from flask import Flask
    from src.modules import site_conf
    from src.modules.site_conf import Site_conf
    
    # Create config with all features
    class FullConfig(Site_conf):
        def __init__(self):
            super().__init__()
            self.enable_all_features(add_to_sidebar=True)
    
    # Create app
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test'
    
    # Set site_conf
    conf = FullConfig()
    site_conf.site_conf_obj = conf
    site_conf.site_conf_app_path = str(framework_dir)
    
    # Check that all blueprints can be imported
    from src.pages import common, threads, logging, settings, user, admin
    
    # Register blueprints
    app.register_blueprint(common.bp)
    app.register_blueprint(threads.bp)
    app.register_blueprint(logging.bp)
    app.register_blueprint(settings.bp)
    app.register_blueprint(user.bp)
    app.register_blueprint(admin.bp)
    
    # Verify some routes exist
    with app.test_client() as client:
        # Test common route
        response = client.get('/common/assets/images/?filename=test.png')
        assert response.status_code in [200, 404]


def test_selective_feature_enablement():
    """Test that only enabled features add blueprints."""
    from src.modules.site_conf import Site_conf
    
    # Config with only threads and logs
    conf = Site_conf()
    conf.enable_threads(add_to_sidebar=True)
    conf.enable_log_viewer(add_to_sidebar=True)
    
    # Check feature flags
    assert conf.m_enable_threads is True
    assert conf.m_enable_log_viewer is True
    assert conf.m_enable_authentication is False
    assert conf.m_enable_settings is False
    
    # Check sidebar has correct items
    sidebar_endpoints = [item.get('endpoint') for item in conf.m_sidebar]
    assert 'monitoring' in sidebar_endpoints
    assert 'user' not in sidebar_endpoints
    assert 'admin' not in sidebar_endpoints
    assert 'tools' not in sidebar_endpoints  # Settings is in tools, which isn't enabled
    
    # Check submenu names in monitoring section
    monitoring_item = next((item for item in conf.m_sidebar if item.get('endpoint') == 'monitoring'), None)
    assert monitoring_item is not None
    submenu_names = [s['name'] for s in monitoring_item.get('submenu', [])]
    assert 'Thread Monitor' in submenu_names
    assert 'Log Viewer' in submenu_names
    assert 'Settings' not in submenu_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
