"""
Tests for IP-based rate limiting on login attempts.

Tests the RateLimiter class that prevents brute-force attacks
from the same IP address.
"""

import pytest
import time
from src.modules.auth.rate_limiter import RateLimiter


def test_rate_limiter_allows_normal_usage():
    """Test that normal login attempts are allowed."""
    limiter = RateLimiter(max_attempts=5)
    
    # First 4 attempts should be allowed
    for i in range(4):
        allowed, message = limiter.check("192.168.1.1")
        assert allowed is True
        assert message == ""
        limiter.record_attempt("192.168.1.1", success=False)


def test_rate_limiter_blocks_after_max_attempts():
    """Test that IP is blocked after exceeding max attempts."""
    limiter = RateLimiter(max_attempts=5, window_seconds=60, lockout_seconds=120)
    
    # Make 5 failed attempts
    for i in range(5):
        limiter.record_attempt("10.0.0.1", success=False)
    
    # 6th attempt should be blocked
    allowed, message = limiter.check("10.0.0.1")
    assert allowed is False
    assert "too many" in message.lower() or "try again" in message.lower()


def test_rate_limiter_clears_on_successful_login():
    """Test that successful login clears the failure history."""
    limiter = RateLimiter(max_attempts=5)
    
    # Make some failed attempts
    for i in range(3):
        limiter.record_attempt("172.16.0.1", success=False)
    
    # Successful login
    limiter.record_attempt("172.16.0.1", success=True)
    
    # Counter should be reset
    count = limiter.get_attempt_count("172.16.0.1")
    assert count == 0


def test_rate_limiter_different_ips_independent():
    """Test that different IPs are tracked independently."""
    limiter = RateLimiter(max_attempts=3)
    
    # IP1 makes failed attempts
    for i in range(3):
        limiter.record_attempt("1.1.1.1", success=False)
    
    # IP1 should be blocked
    allowed1, _ = limiter.check("1.1.1.1")
    assert allowed1 is False
    
    # IP2 should still be allowed
    allowed2, _ = limiter.check("2.2.2.2")
    assert allowed2 is True


def test_rate_limiter_attempt_count():
    """Test that attempt count is tracked correctly."""
    limiter = RateLimiter()
    
    # No attempts initially
    count = limiter.get_attempt_count("192.168.1.100")
    assert count == 0
    
    # Record some failures
    limiter.record_attempt("192.168.1.100", success=False)
    limiter.record_attempt("192.168.1.100", success=False)
    
    count = limiter.get_attempt_count("192.168.1.100")
    assert count == 2


def test_rate_limiter_lockout_message_format():
    """Test that lockout message includes time remaining."""
    limiter = RateLimiter(max_attempts=2, lockout_seconds=300)
    
    # Trigger lockout
    limiter.record_attempt("10.10.10.10", success=False)
    limiter.record_attempt("10.10.10.10", success=False)
    
    allowed, message = limiter.check("10.10.10.10")
    
    assert allowed is False
    assert "m" in message or "minutes" in message.lower()
    # Should mention either minutes or seconds
    assert any(unit in message.lower() for unit in ["minute", "second", "m", "s"])
