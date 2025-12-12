"""
IP-Based Rate Limiter Module

Provides IP-based rate limiting for login attempts to prevent brute-force attacks
from distributed sources. Works alongside username-based lockout for defense-in-depth.

Key differences from FailedLoginManager:
- Tracks by IP address (not username) to prevent distributed attacks
- In-memory only (no persistence needed, resets on restart)
- Shorter lockout window (prevents hammering the login page)
- Complements username-based lockout (both can trigger independently)
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# =============================================================================
# Rate Limiting Constants
# =============================================================================
DEFAULT_MAX_ATTEMPTS = 10  # Higher than username lockout (allows legitimate retries)
DEFAULT_WINDOW_SECONDS = 300  # 5 minutes - track attempts within this window
DEFAULT_LOCKOUT_SECONDS = 900  # 15 minutes - lockout duration after max attempts


@dataclass
class RateLimiter:
    """
    Simple in-memory IP-based rate limiter for login attempts.
    
    Tracks login attempts by IP address to prevent brute-force attacks from
    distributed sources that might try different usernames from the same IP.
    
    Features:
    - Tracks attempts per IP address
    - Sliding window (old attempts auto-expire)
    - In-memory only (acceptable for rate limiting)
    - No external dependencies
    
    Note:
        This is complementary to username-based lockout. Both can trigger:
        - Username lockout: 5 failures on one account
        - IP rate limit: 10 failures from one IP (any usernames)
    
    Usage:
        limiter = RateLimiter()
        
        # Check before login attempt
        allowed, message = limiter.check(request.remote_addr)
        if not allowed:
            return message, 429
        
        # Record outcome
        limiter.record_attempt(request.remote_addr, success=password_correct)
    """
    
    max_attempts: int = DEFAULT_MAX_ATTEMPTS
    """Maximum failed attempts allowed within the window."""
    
    window_seconds: int = DEFAULT_WINDOW_SECONDS
    """Time window for counting attempts (5 minutes)."""
    
    lockout_seconds: int = DEFAULT_LOCKOUT_SECONDS
    """Lockout duration after exceeding max attempts (15 minutes)."""
    
    # {ip_address: [(timestamp, success), ...]}
    _attempts: Dict[str, List[Tuple[float, bool]]] = field(
        default_factory=lambda: defaultdict(list)
    )
    
    def check(self, identifier: str) -> Tuple[bool, str]:
        """
        Check if identifier (IP address) is rate limited.
        
        Args:
            identifier: IP address to check
            
        Returns:
            Tuple of (allowed: bool, message: str)
            - (True, "") if allowed to proceed
            - (False, "error message") if rate limited
        """
        now = time.time()
        attempts = self._attempts[identifier]
        
        # Clean old attempts outside lockout window
        attempts[:] = [
            (ts, success) 
            for ts, success in attempts 
            if now - ts < self.lockout_seconds
        ]
        
        # Count recent failed attempts
        failed_attempts = [
            ts for ts, success in attempts 
            if not success and now - ts < self.window_seconds
        ]
        
        # Check if locked out
        if len(failed_attempts) >= self.max_attempts:
            # Find oldest failure to calculate remaining lockout time
            oldest_fail = min(failed_attempts)
            elapsed = now - oldest_fail
            remaining = self.lockout_seconds - elapsed
            
            if remaining > 0:
                minutes = int(remaining // 60)
                seconds = int(remaining % 60)
                message = (
                    f"Too many login attempts from your IP address. "
                    f"Please try again in {minutes}m {seconds}s."
                )
                return False, message
        
        return True, ""
    
    def record_attempt(self, identifier: str, success: bool) -> None:
        """
        Record a login attempt outcome.
        
        Args:
            identifier: IP address making the attempt
            success: True if login succeeded, False if failed
        """
        self._attempts[identifier].append((time.time(), success))
        
        # Clear history on successful login (user authenticated)
        if success:
            self._attempts[identifier] = []
    
    def get_attempt_count(self, identifier: str) -> int:
        """
        Get the number of recent failed attempts for an IP.
        
        Args:
            identifier: IP address to check
            
        Returns:
            Number of failed attempts within the window
        """
        now = time.time()
        attempts = self._attempts.get(identifier, [])
        return sum(
            1 for ts, success in attempts 
            if not success and now - ts < self.window_seconds
        )


# Global instance for use across the application
login_rate_limiter = RateLimiter()
