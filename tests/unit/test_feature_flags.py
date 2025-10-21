"""
Unit tests for feature flag configuration and conditional blueprint registration.

Tests that verify:
1. Common blueprint is always registered (provides assets)
2. Scheduler can be disabled without crashes
3. Other blueprints are conditionally registered
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


class TestFeatureFlags:
    """Test feature flag configuration."""
    
    def test_default_features_disabled(self):
        """Test that all features are disabled by default."""
        conf = Site_conf()
        assert conf.m_enable_authentication is False
        assert conf.m_enable_scheduler is False
        assert conf.m_enable_threads is False
        assert conf.m_enable_log_viewer is False
        assert conf.m_enable_bug_tracker is False
        assert conf.m_enable_settings is False
    
    def test_enable_authentication(self):
        """Test enabling authentication feature."""
        conf = Site_conf()
        conf.enable_authentication(add_to_sidebar=False)
        assert conf.m_enable_authentication is True
        assert conf.m_topbar["login"] is True
    
    def test_enable_scheduler(self):
        """Test enabling scheduler feature."""
        conf = Site_conf()
        conf.enable_scheduler()
        assert conf.m_enable_scheduler is True
    
    def test_enable_threads(self):
        """Test enabling threads feature."""
        conf = Site_conf()
        conf.enable_threads(add_to_sidebar=False)
        assert conf.m_enable_threads is True
    
    def test_enable_all_features(self):
        """Test enabling all features at once."""
        conf = Site_conf()
        conf.enable_all_features(add_to_sidebar=False)
        assert conf.m_enable_authentication is True
        assert conf.m_enable_scheduler is True
        assert conf.m_enable_threads is True
        assert conf.m_enable_log_viewer is True
        assert conf.m_enable_bug_tracker is True
        assert conf.m_enable_settings is True


def test_common_blueprint_always_available():
    """Test that common blueprint is not in PAGE_FEATURE_REQUIREMENTS.
    
    This ensures the 'common' blueprint is always registered, even when
    authentication is disabled, because it provides essential assets serving.
    """
    # We can't easily import main.py without Flask, so we'll read it
    main_py = (framework_dir / "src" / "main.py").read_text()
    
    # Verify 'common' is NOT in PAGE_FEATURE_REQUIREMENTS
    assert "'common':" not in main_py or "# 'common':" in main_py, \
        "Common blueprint should always be registered (not in PAGE_FEATURE_REQUIREMENTS)"
    
    # Verify the comment exists
    assert "Always registered" in main_py or "always registered" in main_py, \
        "Should have comment explaining common is always registered"


def test_scheduler_null_check():
    """Test that scheduler.scheduler_obj is checked for None before access.
    
    This ensures the app doesn't crash when scheduler is disabled.
    """
    main_py = (framework_dir / "src" / "main.py").read_text()
    
    # Find the before_request function
    assert "def before_request():" in main_py
    
    # Verify that scheduler access is guarded by a None check
    # Look for pattern: if scheduler.scheduler_obj is not None:
    assert "if scheduler.scheduler_obj is not None:" in main_py, \
        "Scheduler access in before_request should check for None"
    
    # Verify the m_user_connected assignment is after the check
    lines = main_py.split('\n')
    scheduler_check_line = None
    user_connected_line = None
    
    for i, line in enumerate(lines):
        if 'if scheduler.scheduler_obj is not None:' in line:
            scheduler_check_line = i
        if 'scheduler.scheduler_obj.m_user_connected = False' in line and scheduler_check_line:
            # Check if this line comes after the None check
            if i > scheduler_check_line:
                user_connected_line = i
                break
    
    assert scheduler_check_line is not None, "Should have None check for scheduler"
    assert user_connected_line is not None, "m_user_connected should be set after None check"
    assert user_connected_line > scheduler_check_line, "m_user_connected must be inside the None check block"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
