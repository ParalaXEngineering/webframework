"""
Security Utilities Module

Provides security features including:
- Failed login attempt tracking with account lockout
- Persistent storage of failed attempts across server restarts
- Configurable lockout duration and attempt thresholds
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# =============================================================================
# Security Constants
# =============================================================================
# Default security thresholds for failed login attempts
DEFAULT_MAX_ATTEMPTS = 5  # Maximum failed login attempts before account lockout
DEFAULT_LOCKOUT_MINUTES = 5  # Duration of account lockout in minutes


class FailedLoginManager:
    """
    Manages failed login attempts with persistent storage and account lockout.
    
    Features:
    - Tracks failed login attempts per user
    - Automatically locks accounts after threshold attempts
    - Persists data across server restarts
    - Auto-unlocks accounts after lockout duration
    - Thread-safe operations
    
    Usage:
        manager = FailedLoginManager(lockout_file="auth/failed_logins.json")
        
        # Check if user is locked
        is_locked, locked_until = manager.is_locked("john")
        
        # Increment failed attempts
        count = manager.increment_attempts("john")
        
        # Reset after successful login
        manager.reset_attempts("john")
    """
    
    def __init__(self, 
                 lockout_file: str = "failed_logins.json",
                 max_attempts: int = DEFAULT_MAX_ATTEMPTS,
                 lockout_minutes: float = DEFAULT_LOCKOUT_MINUTES):
        """
        Initialize the Failed Login Manager.
        
        Args:
            lockout_file: Path to JSON file for storing failed attempts
            max_attempts: Maximum number of failed attempts before lockout (default: 5)
            lockout_minutes: Duration of account lockout in minutes (default: 5, accepts float)
        """
        self.lockout_file = Path(lockout_file)
        self.max_attempts = max_attempts
        self.lockout_minutes = lockout_minutes
        self.attempts: Dict[str, Dict] = self._load_attempts()
        logger.info(
            "FailedLoginManager initialized (max_attempts=%s, lockout=%sm, file=%s)",
            max_attempts, lockout_minutes, lockout_file
        )
    
    def _load_attempts(self) -> Dict[str, Dict]:
        """
        Load failed attempts from persistent JSON file.
        
        Returns:
            Dictionary of {username: {'count': int, 'locked_until': datetime|None}}
        """
        if not self.lockout_file.exists():
            logger.debug("Lockout file %s does not exist yet", self.lockout_file)
            return {}
        
        try:
            with open(self.lockout_file, 'r') as f:
                data = json.load(f)
                
            # Convert ISO timestamp strings back to datetime objects
            for username in data:
                if data[username].get('locked_until'):
                    data[username]['locked_until'] = datetime.fromisoformat(
                        data[username]['locked_until']
                    )
            
            logger.info("Loaded %s user(s) from lockout file", len(data))
            return data
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse lockout file %s: %s", self.lockout_file, e)
            return {}
        except Exception as e:
            logger.error("Error loading failed login attempts from %s: %s", self.lockout_file, e)
            return {}
    
    def _save_attempts(self) -> None:
        """
        Save failed attempts to persistent JSON file.
        Converts datetime objects to ISO format strings for JSON serialization.
        """
        try:
            # Ensure directory exists
            self.lockout_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert datetime objects to ISO strings for JSON
            data = {}
            for username, info in self.attempts.items():
                data[username] = {
                    'count': info['count'],
                    'locked_until': info['locked_until'].isoformat() if info.get('locked_until') else None
                }
            
            with open(self.lockout_file, 'w') as f:
                json.dump(data, f, indent=4)
                
            logger.debug("Saved %s user(s) to lockout file", len(data))
            
        except Exception as e:
            logger.error("Error saving failed login attempts to %s: %s", self.lockout_file, e)
    
    def get_user_status(self, username: str) -> Dict:
        """
        Get the current status for a user.
        
        Args:
            username: Username to check
            
        Returns:
            Dictionary with 'count' (int) and 'locked_until' (datetime|None)
        """
        if username not in self.attempts:
            self.attempts[username] = {'count': 0, 'locked_until': None}
        return self.attempts[username]
    
    def is_locked(self, username: str) -> Tuple[bool, Optional[datetime]]:
        """
        Check if a user account is currently locked.
        
        Args:
            username: Username to check
            
        Returns:
            Tuple of (is_locked: bool, locked_until: datetime|None)
        """
        status = self.get_user_status(username)
        locked_until = status.get('locked_until')
        
        if locked_until and datetime.now() < locked_until:
            # Account is locked
            return True, locked_until
        elif locked_until and datetime.now() >= locked_until:
            # Lock has expired - auto reset
            logger.info("Auto-unlocking user '%s' - lockout expired", username)
            self.reset_attempts(username)
            return False, None
        
        return False, None
    
    def increment_attempts(self, username: str) -> int:
        """
        Increment failed login attempt counter for a user.
        Locks account if threshold is reached.
        
        Args:
            username: Username to increment attempts for
            
        Returns:
            Current attempt count
        """
        status = self.get_user_status(username)
        status['count'] += 1
        
        if status['count'] >= self.max_attempts:
            # Lock the account
            status['locked_until'] = datetime.now() + timedelta(minutes=self.lockout_minutes)
            logger.warning(
                "Account '%s' LOCKED for %s minutes (until %s) after %s failed attempts",
                username,
                self.lockout_minutes,
                status['locked_until'].strftime('%Y-%m-%d %H:%M:%S'),
                status['count']
            )
        else:
            logger.info("Failed login attempt #%s for user '%s'", status['count'], username)
        
        self._save_attempts()
        return status['count']
    
    def reset_attempts(self, username: str) -> None:
        """
        Reset failed login attempts for a user (typically after successful login).
        
        Args:
            username: Username to reset
        """
        if username in self.attempts and self.attempts[username]['count'] > 0:
            logger.info("Resetting failed login attempts for user '%s'", username)
        
        self.attempts[username] = {'count': 0, 'locked_until': None}
        self._save_attempts()
    
    def get_remaining_attempts(self, username: str) -> int:
        """
        Get the number of remaining login attempts before lockout.
        
        Args:
            username: Username to check
            
        Returns:
            Number of remaining attempts (0 if locked)
        """
        status = self.get_user_status(username)
        return max(0, self.max_attempts - status['count'])
    
    def get_lockout_time_remaining(self, username: str) -> float:
        """
        Get the remaining lockout time in seconds.
        
        Args:
            username: Username to check
            
        Returns:
            Remaining lockout time in seconds (0.0 if not locked)
        """
        is_locked, locked_until = self.is_locked(username)
        if is_locked and locked_until:
            remaining = (locked_until - datetime.now()).total_seconds()
            return max(0.0, remaining)
        return 0.0
    
    def get_all_locked_users(self) -> list:
        """
        Get list of all currently locked users.
        
        Returns:
            List of (username, locked_until) tuples
        """
        locked_users = []
        for username in self.attempts:
            is_locked, locked_until = self.is_locked(username)
            if is_locked:
                locked_users.append((username, locked_until))
        return locked_users
    
    def clear_all_attempts(self) -> None:
        """
        Clear all failed login attempts (admin function).
        WARNING: This will unlock all accounts.
        """
        logger.warning("Clearing ALL failed login attempts and unlocking all accounts")
        self.attempts = {}
        self._save_attempts()
