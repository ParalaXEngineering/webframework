"""
OTP (One-Time Password) Manager for OnTarget 2FA authentication.

This module handles generation, storage, and validation of single-use
authentication codes. OTP codes are valid for 30 seconds and auto-regenerate.

The OTP secret is stored in: /var/lib/dfnet/{target}/oufnis/otp_secret
where {target} is 'ppu' or 'hmi' based on the device IP.
"""
import os
import secrets
import string
import logging
import time
from pathlib import Path
from typing import Tuple, Optional

from submodules.framework.src import utilities

logger = logging.getLogger("website")

# OTP Configuration
OTP_LENGTH = 6  # 6-digit code
OTP_VALIDITY_SECONDS = 30  # Code valid for 30 seconds
OTP_BASE_PATH = "/var/lib/dfnet"
OTP_SUBDIR = "oufnis"
OTP_FILENAME = "otp_secret"
OTP_TIMESTAMP_FILENAME = "otp_timestamp"

# Singleton instance
_otp_manager_instance = None


def get_otp_manager() -> 'OTPManager':
    """Get or create the singleton OTP manager instance."""
    global _otp_manager_instance
    if _otp_manager_instance is None:
        _otp_manager_instance = OTPManager()
    return _otp_manager_instance


class OTPManager:
    """
    Manages One-Time Password generation, storage, and validation.
    
    The OTP is stored on disk with a 30-second validity period.
    After expiration, a new code is automatically generated.
    """
    
    def __init__(self):
        self._current_otp: Optional[str] = None
        self._otp_created_at: float = 0.0
        self._otp_file_path: Optional[Path] = None
        self._initialized = False
        
    def _get_target_type(self) -> str:
        """
        Determine the target type from configuration.
        
        Returns:
            str: 'ppu' or 'hmi' based on config, defaults to 'unknown'
        """
        return "hmi"
    
    def _get_otp_file_path(self) -> Path:
        """
        Get the path to the OTP secret file.
        
        Returns:
            Path: Full path to the OTP secret file
        """
        if self._otp_file_path is None:
            target_type = self._get_target_type()
            self._otp_file_path = Path(OTP_BASE_PATH) / target_type / OTP_SUBDIR / OTP_FILENAME
        return self._otp_file_path
    
    def _get_timestamp_file_path(self) -> Path:
        """Get the path to the OTP timestamp file."""
        target_type = self._get_target_type()
        return Path(OTP_BASE_PATH) / target_type / OTP_SUBDIR / OTP_TIMESTAMP_FILENAME
    
    def _write_timestamp(self, timestamp: float) -> bool:
        """Write the OTP creation timestamp to file."""
        try:
            ts_path = self._get_timestamp_file_path()
            ts_path.parent.mkdir(parents=True, exist_ok=True)
            ts_path.write_text(str(timestamp))
            return True
        except Exception as e:
            logger.error(f"Failed to write timestamp: {e}")
            return False
    
    def _read_timestamp(self) -> float:
        """Read the OTP creation timestamp from file."""
        try:
            ts_path = self._get_timestamp_file_path()
            if ts_path.exists():
                return float(ts_path.read_text().strip())
        except Exception as e:
            logger.error(f"Failed to read timestamp: {e}")
        return 0.0
    
    def _is_expired(self) -> bool:
        """Check if the current OTP has expired (older than 30 seconds)."""
        if self._otp_created_at == 0:
            return True
        elapsed = time.time() - self._otp_created_at
        return elapsed >= OTP_VALIDITY_SECONDS
    
    def get_time_remaining(self) -> int:
        """
        Get the remaining validity time for the current OTP in seconds.
        
        Returns:
            int: Seconds remaining (0 if expired)
        """
        if self._otp_created_at == 0:
            return 0
        elapsed = time.time() - self._otp_created_at
        remaining = OTP_VALIDITY_SECONDS - elapsed
        return max(0, int(remaining))
    
    def _generate_otp(self) -> str:
        """
        Generate a new random OTP code.
        
        Returns:
            str: A random 6-digit numeric code
        """
        # Use only digits for user-friendly entry
        return ''.join(secrets.choice(string.digits) for _ in range(OTP_LENGTH))
    
    def _ensure_directory(self, file_path: Path) -> bool:
        """
        Ensure the directory for the OTP file exists.
        
        Args:
            file_path: Path to the OTP file
            
        Returns:
            bool: True if directory exists or was created
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            return True
        except PermissionError:
            logger.error(f"Permission denied creating directory: {file_path.parent}")
            return False
        except Exception as e:
            logger.error(f"Failed to create directory {file_path.parent}: {e}")
            return False
    
    def _write_otp_to_file(self, otp: str) -> bool:
        """
        Write the OTP to the secret file.
        
        Args:
            otp: The OTP code to write
            
        Returns:
            bool: True if successfully written
        """
        file_path = self._get_otp_file_path()
        
        if not self._ensure_directory(file_path):
            return False
        
        try:
            # Write atomically using temp file
            temp_path = file_path.with_suffix('.tmp')
            temp_path.write_text(otp)
            temp_path.replace(file_path)
            
            # Set permissions to be readable (for overlay display service)
            os.chmod(file_path, 0o644)
            
            # Also write the timestamp
            now = time.time()
            self._write_timestamp(now)
            self._otp_created_at = now
            
            logger.info(f"OTP written to {file_path}")
            return True
        except PermissionError:
            logger.error(f"Permission denied writing OTP to {file_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to write OTP to {file_path}: {e}")
            return False
    
    def _read_otp_from_file(self) -> Optional[str]:
        """
        Read the current OTP from the secret file.
        
        Returns:
            str or None: The stored OTP, or None if not found
        """
        file_path = self._get_otp_file_path()
        
        try:
            if file_path.exists():
                otp = file_path.read_text().strip()
                if otp and len(otp) == OTP_LENGTH and otp.isdigit():
                    return otp
                else:
                    logger.warning(f"Invalid OTP format in {file_path}, will regenerate")
                    return None
            return None
        except Exception as e:
            logger.error(f"Failed to read OTP from {file_path}: {e}")
            return None
    
    def initialize(self) -> Tuple[bool, str]:
        """
        Initialize the OTP manager, generating a new OTP if needed.
        
        Should be called at application startup when running on target.
        
        Returns:
            Tuple[bool, str]: (success, current_otp or error_message)
        """
        if self._initialized:
            return True, self._current_otp or ""
        
        # Try to read existing OTP and timestamp
        self._current_otp = self._read_otp_from_file()
        self._otp_created_at = self._read_timestamp()
        
        if self._current_otp is None or self._is_expired():
            # Generate new OTP (expired or missing)
            self._current_otp = self._generate_otp()
            if not self._write_otp_to_file(self._current_otp):
                return False, "Failed to write OTP to file"
            logger.info("Generated new OTP at startup")
        else:
            logger.info(f"Loaded existing OTP from file ({self.get_time_remaining()}s remaining)")
        
        self._initialized = True
        return True, self._current_otp
    
    def validate(self, user_input: str) -> Tuple[bool, str]:
        """
        Validate a user-provided OTP code.
        
        Args:
            user_input: The OTP code entered by the user
            
        Returns:
            Tuple[bool, str]: (valid, message)
        """
        if not self._initialized:
            success, msg = self.initialize()
            if not success:
                return False, f"OTP system not initialized: {msg}"
        
        # Check if OTP has expired
        if self._is_expired():
            logger.warning("OTP expired during validation")
            return False, "Code expired"
        
        # Normalize input
        user_input = user_input.strip()
        
        # Validate format
        if not user_input or len(user_input) != OTP_LENGTH or not user_input.isdigit():
            logger.warning(f"Invalid OTP format received (length={len(user_input) if user_input else 0})")
            return False, "Invalid OTP format"
        
        # Check against stored OTP
        if user_input != self._current_otp:
            logger.warning("Invalid OTP attempt")
            return False, "Invalid OTP code"
        
        # OTP is valid - do NOT regenerate here since it auto-expires after 30s
        logger.info("OTP validated successfully")
        return True, "OTP validated"
    
    def get_current_otp(self) -> Optional[str]:
        """
        Get the current OTP code, regenerating if expired.
        
        Auto-regenerates the OTP if it's older than 30 seconds.
        
        Returns:
            str or None: The current OTP code
        """
        if not self._initialized:
            self.initialize()
        
        # Check expiration and regenerate if needed
        if self._is_expired():
            logger.info("OTP expired, auto-regenerating")
            self._current_otp = self._generate_otp()
            self._write_otp_to_file(self._current_otp)
        
        return self._current_otp
    
    def get_otp_file_path_str(self) -> str:
        """
        Get the full path to the OTP file as a string.
        
        Useful for configuring external display services.
        
        Returns:
            str: Full path to the OTP secret file
        """
        return str(self._get_otp_file_path())
    
    def regenerate(self) -> Tuple[bool, str]:
        """
        Force regeneration of a new OTP code.
        
        Useful for security invalidation or admin reset.
        
        Returns:
            Tuple[bool, str]: (success, new_otp or error_message)
        """
        new_otp = self._generate_otp()
        
        if self._write_otp_to_file(new_otp):
            self._current_otp = new_otp
            logger.info("OTP forcefully regenerated")
            return True, new_otp
        else:
            return False, "Failed to write new OTP"
    
    def is_enabled(self) -> bool:
        """
        Check if OTP/2FA is enabled (only on target Linux systems).
        
        Returns:
            bool: True if running on target and OTP should be used
        """
        import socket
        hostname = socket.gethostname()
        return "al70x" in hostname


# Convenience functions for direct usage
def init_otp() -> Tuple[bool, str]:
    """Initialize OTP at application startup."""
    return get_otp_manager().initialize()


def validate_otp(code: str) -> Tuple[bool, str]:
    """Validate an OTP code."""
    return get_otp_manager().validate(code)


def is_otp_enabled() -> bool:
    """Check if OTP is enabled for this environment."""
    return get_otp_manager().is_enabled()


def get_current_otp() -> Optional[str]:
    """Get the current OTP code for display."""
    return get_otp_manager().get_current_otp()
