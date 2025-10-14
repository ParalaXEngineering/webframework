"""
Unit tests for security_utils module (FailedLoginManager).

Tests cover:
- Failed attempt tracking
- Account lockout after threshold
- Automatic unlock after timeout
- Persistent storage across restarts
- Edge cases and concurrency
"""

import pytest
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

from src.modules.auth.security_utils import FailedLoginManager


class TestFailedLoginManager:
    """Test suite for FailedLoginManager class."""
    
    @pytest.fixture
    def temp_lockout_file(self, tmp_path):
        """Provide a temporary lockout file path."""
        return str(tmp_path / "test_failed_logins.json")
    
    @pytest.fixture
    def manager(self, temp_lockout_file):
        """Create a FailedLoginManager instance with temp file."""
        return FailedLoginManager(
            lockout_file=temp_lockout_file,
            max_attempts=5,
            lockout_minutes=5
        )
    
    def test_initialization(self, temp_lockout_file):
        """Test FailedLoginManager initialization."""
        manager = FailedLoginManager(
            lockout_file=temp_lockout_file,
            max_attempts=3,
            lockout_minutes=10
        )
        
        assert manager.max_attempts == 3
        assert manager.lockout_minutes == 10
        assert manager.lockout_file == Path(temp_lockout_file)
        assert isinstance(manager.attempts, dict)
    
    def test_get_user_status_new_user(self, manager):
        """Test getting status for a new user."""
        status = manager.get_user_status("newuser")
        
        assert status['count'] == 0
        assert status['locked_until'] is None
    
    def test_increment_attempts(self, manager):
        """Test incrementing failed attempts."""
        username = "testuser"
        
        count1 = manager.increment_attempts(username)
        assert count1 == 1
        
        count2 = manager.increment_attempts(username)
        assert count2 == 2
        
        count3 = manager.increment_attempts(username)
        assert count3 == 3
    
    def test_get_remaining_attempts(self, manager):
        """Test getting remaining attempts before lockout."""
        username = "testuser"
        
        assert manager.get_remaining_attempts(username) == 5
        
        manager.increment_attempts(username)
        assert manager.get_remaining_attempts(username) == 4
        
        manager.increment_attempts(username)
        assert manager.get_remaining_attempts(username) == 3
    
    def test_reset_attempts(self, manager):
        """Test resetting failed attempts."""
        username = "testuser"
        
        manager.increment_attempts(username)
        manager.increment_attempts(username)
        manager.increment_attempts(username)
        
        assert manager.get_user_status(username)['count'] == 3
        
        manager.reset_attempts(username)
        
        assert manager.get_user_status(username)['count'] == 0
        assert manager.get_user_status(username)['locked_until'] is None
    
    def test_lockout_after_max_attempts(self, manager):
        """Test account locks after reaching max attempts."""
        username = "testuser"
        
        # Make 4 failed attempts (not locked yet)
        for i in range(4):
            manager.increment_attempts(username)
            is_locked, _ = manager.is_locked(username)
            assert not is_locked
        
        # 5th attempt should lock the account
        count = manager.increment_attempts(username)
        assert count == 5
        
        is_locked, locked_until = manager.is_locked(username)
        assert is_locked
        assert locked_until is not None
        assert locked_until > datetime.now()
    
    def test_lockout_duration(self, manager):
        """Test lockout lasts for specified duration."""
        username = "testuser"
        
        # Lock the account
        for _ in range(5):
            manager.increment_attempts(username)
        
        is_locked, locked_until = manager.is_locked(username)
        assert is_locked
        
        # Check locked_until is approximately 5 minutes in future
        expected_unlock = datetime.now() + timedelta(minutes=5)
        time_diff = abs((locked_until - expected_unlock).total_seconds())
        assert time_diff < 2  # Within 2 seconds tolerance
    
    def test_get_lockout_time_remaining(self, manager):
        """Test getting remaining lockout time."""
        username = "testuser"
        
        # Initially no lockout
        assert manager.get_lockout_time_remaining(username) == 0.0
        
        # Lock the account
        for _ in range(5):
            manager.increment_attempts(username)
        
        remaining = manager.get_lockout_time_remaining(username)
        assert remaining > 0
        assert remaining <= 300  # 5 minutes = 300 seconds
    
    def test_persistence_save_and_load(self, temp_lockout_file):
        """Test failed attempts persist across manager instances."""
        username = "testuser"
        
        # Create first manager and make some attempts
        manager1 = FailedLoginManager(lockout_file=temp_lockout_file)
        manager1.increment_attempts(username)
        manager1.increment_attempts(username)
        manager1.increment_attempts(username)
        
        # Create second manager (simulates restart)
        manager2 = FailedLoginManager(lockout_file=temp_lockout_file)
        
        # Attempts should be loaded
        status = manager2.get_user_status(username)
        assert status['count'] == 3
    
    def test_persistence_locked_state(self, temp_lockout_file):
        """Test locked state persists across restarts."""
        username = "testuser"
        
        # Lock the account
        manager1 = FailedLoginManager(lockout_file=temp_lockout_file)
        for _ in range(5):
            manager1.increment_attempts(username)
        
        is_locked1, locked_until1 = manager1.is_locked(username)
        assert is_locked1
        
        # Restart manager
        manager2 = FailedLoginManager(lockout_file=temp_lockout_file)
        is_locked2, locked_until2 = manager2.is_locked(username)
        
        assert is_locked2
        assert locked_until2 is not None
        assert locked_until1 is not None
        # Times should be very close (within 1 second)
        time_diff = abs((locked_until1 - locked_until2).total_seconds())
        assert time_diff < 1
    
    def test_auto_unlock_after_timeout(self, temp_lockout_file):
        """Test account auto-unlocks after timeout expires."""
        username = "testuser"
        
        # Create manager with short lockout (for testing)
        manager = FailedLoginManager(
            lockout_file=temp_lockout_file,
            max_attempts=5,
            lockout_minutes=1  # 1 minute
        )
        
        # Lock the account
        for _ in range(5):
            manager.increment_attempts(username)
        
        is_locked, _ = manager.is_locked(username)
        assert is_locked
        
        # Wait for lockout to expire
        time.sleep(1)
        
        # Should be auto-unlocked
        is_locked, _ = manager.is_locked(username)
        assert not is_locked
        
        # Attempts should be reset
        status = manager.get_user_status(username)
        assert status['count'] == 0
    
    def test_get_all_locked_users(self, manager):
        """Test getting list of all locked users."""
        # Lock multiple accounts
        for _ in range(5):
            manager.increment_attempts("user1")
            manager.increment_attempts("user2")
        
        # user3 has attempts but not locked
        manager.increment_attempts("user3")
        manager.increment_attempts("user3")
        
        locked_users = manager.get_all_locked_users()
        
        assert len(locked_users) == 2
        usernames = [username for username, _ in locked_users]
        assert "user1" in usernames
        assert "user2" in usernames
        assert "user3" not in usernames
    
    def test_clear_all_attempts(self, manager):
        """Test clearing all failed attempts (admin function)."""
        # Make attempts for multiple users
        manager.increment_attempts("user1")
        manager.increment_attempts("user1")
        manager.increment_attempts("user2")
        
        # Lock one user
        for _ in range(5):
            manager.increment_attempts("user3")
        
        assert manager.get_user_status("user1")['count'] == 2
        assert manager.get_user_status("user2")['count'] == 1
        is_locked, _ = manager.is_locked("user3")
        assert is_locked
        
        # Clear all
        manager.clear_all_attempts()
        
        # All should be reset
        assert manager.get_user_status("user1")['count'] == 0
        assert manager.get_user_status("user2")['count'] == 0
        is_locked, _ = manager.is_locked("user3")
        assert not is_locked
    
    def test_multiple_users_independent(self, manager):
        """Test failed attempts are tracked independently per user."""
        manager.increment_attempts("alice")
        manager.increment_attempts("alice")
        manager.increment_attempts("alice")
        
        manager.increment_attempts("bob")
        
        assert manager.get_user_status("alice")['count'] == 3
        assert manager.get_user_status("bob")['count'] == 1
        assert manager.get_remaining_attempts("alice") == 2
        assert manager.get_remaining_attempts("bob") == 4
    
    def test_custom_max_attempts(self, temp_lockout_file):
        """Test custom max_attempts configuration."""
        manager = FailedLoginManager(
            lockout_file=temp_lockout_file,
            max_attempts=3,  # Lower threshold
            lockout_minutes=5
        )
        
        username = "testuser"
        
        # Make 2 attempts (not locked)
        manager.increment_attempts(username)
        manager.increment_attempts(username)
        is_locked, _ = manager.is_locked(username)
        assert not is_locked
        
        # 3rd attempt should lock
        manager.increment_attempts(username)
        is_locked, _ = manager.is_locked(username)
        assert is_locked
    
    def test_json_file_format(self, temp_lockout_file):
        """Test the JSON file is correctly formatted."""
        manager = FailedLoginManager(lockout_file=temp_lockout_file)
        
        # Make some attempts
        manager.increment_attempts("user1")
        manager.increment_attempts("user1")
        
        # Lock a user
        for _ in range(5):
            manager.increment_attempts("user2")
        
        # Read the JSON file directly
        with open(temp_lockout_file, 'r') as f:
            data = json.load(f)
        
        assert "user1" in data
        assert "user2" in data
        assert data["user1"]["count"] == 2
        assert data["user1"]["locked_until"] is None
        assert data["user2"]["count"] == 5
        assert data["user2"]["locked_until"] is not None
        
        # locked_until should be valid ISO format
        datetime.fromisoformat(data["user2"]["locked_until"])
    
    def test_concurrent_increments(self, manager):
        """Test multiple rapid increments work correctly."""
        username = "testuser"
        
        # Rapidly increment (simulating concurrent attempts)
        for _ in range(10):
            manager.increment_attempts(username)
        
        # Should be locked after 5 attempts
        status = manager.get_user_status(username)
        assert status['count'] == 10  # All increments recorded
        
        is_locked, _ = manager.is_locked(username)
        assert is_locked
    
    def test_reset_while_locked(self, manager):
        """Test resetting attempts while account is locked."""
        username = "testuser"
        
        # Lock the account
        for _ in range(5):
            manager.increment_attempts(username)
        
        is_locked, _ = manager.is_locked(username)
        assert is_locked
        
        # Reset attempts (admin override or successful auth)
        manager.reset_attempts(username)
        
        # Should be unlocked
        is_locked, _ = manager.is_locked(username)
        assert not is_locked
        
        status = manager.get_user_status(username)
        assert status['count'] == 0
        assert status['locked_until'] is None
