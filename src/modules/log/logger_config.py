"""
Unified logger configuration wrapper.

Ensures all loggers (both from logger_factory and logging.getLogger) 
are configured consistently via log_config.ini.
"""

import logging
import logging.config
from pathlib import Path


def setup_logging_from_ini(ini_path: str, disable_existing: bool = False) -> None:
    """
    Load logging configuration from INI file.
    
    This should be called ONCE at application startup, before any other logging occurs.
    
    Args:
        ini_path: Path to log_config.ini file
        disable_existing: If False (recommended), existing loggers are preserved
    """
    if not Path(ini_path).exists():
        raise FileNotFoundError(f"Logging config not found: {ini_path}")
    
    logging.config.fileConfig(
        ini_path,
        disable_existing_loggers=disable_existing
    )
    
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    root_logger = logging.getLogger()
    root_logger.info("Logging configured from: %s", ini_path)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger that respects log_config.ini configuration.
    
    If the logger name is not explicitly configured in the INI,
    it will inherit from root logger and use its handlers.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
