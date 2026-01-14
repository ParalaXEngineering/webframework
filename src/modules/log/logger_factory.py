"""Logging helpers.

Provides a factory function to create loggers with both rotating file and
console handlers using a unified format. Directory and file handlers are
created lazily when `get_logger` is first called to avoid import-time
side-effects.

IMPORTANT: Automatically detects application root to write logs to the correct location.
- When framework is a submodule: logs go to parent project's logs/ directory
- When framework is standalone: logs go to framework's logs/ directory
"""

import html
import json
import logging
import os
import sys
import threading
import traceback
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def _detect_app_root() -> Path:
    """Detect the application root directory intelligently.
    
    Returns:
        Path to the application root (where logs should be written)
    """
    # Priority 1: Check if LOG_DIR env var is already set (explicit override)
    if 'LOG_DIR' in os.environ:
        return Path(os.environ['LOG_DIR']).parent
    
    # Priority 2: Detect if framework is a submodule
    # Framework is at: project_root/submodules/framework/src/modules/log/
    # So go up to get: log(0) -> modules(1) -> src(2) -> framework(3) -> submodules(4) -> ROOT(5)
    framework_file = Path(__file__)
    
    # Check if we're in a submodule structure (submodules/framework exists)
    if (framework_file.parents[3].name == 'framework' and 
        framework_file.parents[4].name == 'submodules'):
        # We're a submodule - use parent project root
        return framework_file.parents[5]
    
    # Priority 3: We're standalone framework - use framework root
    # Framework root is at: framework/src/modules/log/ -> go up 3 levels to framework root
    return framework_file.parents[3]


# Detect application root and set LOG_DIR
_APP_ROOT = _detect_app_root()
LOG_DIR = os.environ.get('LOG_DIR', str(_APP_ROOT / 'logs'))

# Ensure LOG_DIR is set in environment for consistency
if 'LOG_DIR' not in os.environ:
    os.environ['LOG_DIR'] = LOG_DIR

# Lock to guard logger creation/configuration across threads
_logger_lock = threading.Lock()
# Cached configuration from config.json
_log_config: Optional[Dict] = None
_config_file_path: Optional[Path] = None


def set_config_file(config_path: Path) -> None:
    """Set the path to the config.json file for loading logging configuration.
    
    Args:
        config_path: Path to config.json containing logging configuration
    """
    global _config_file_path, _log_config
    _config_file_path = config_path
    _log_config = None  # Invalidate cache


def _load_log_config() -> Dict:
    """Load logging configuration from config.json.
    
    Returns:
        Dict containing logging configuration, or defaults if not found
    """
    global _log_config, _config_file_path
    
    if _log_config is not None:
        return _log_config
    
    # Default configuration if file doesn't exist
    defaults = {
        "log_dir": {"value": "logs"},
        "rotation": {"value": "time"},
        "rotation_when": {"value": "W0"},
        "rotation_interval": {"value": 1},
        "max_bytes": {"value": 10_000_000},
        "backup_count": {"value": 5},
        "format": {"value": "%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - %(message)s"},
        "loggers": {
            "root": {"value": "DEBUG"},
            "framework": {"value": "INFO"},
            "tracker": {"value": "INFO"},
            "website": {"value": "DEBUG"},
            "werkzeug": {"value": "ERROR"},
            "socketio": {"value": "WARNING"},
            "engineio": {"value": "WARNING"}
        }
    }
    
    if _config_file_path is None or not _config_file_path.exists():
        _log_config = defaults
        return _log_config
    
    try:
        with open(_config_file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            _log_config = config.get("logging", defaults)
            return _log_config
    except Exception:
        _log_config = defaults
        return _log_config


def _get_logger_level(name: str) -> int:
    """Determine appropriate log level for a logger based on its name.
    
    Args:
        name: Logger name (e.g., 'framework.tooltip', 'trackerdb', 'website.pages')
    
    Returns:
        Logging level constant (DEBUG, INFO, etc.)
    """
    config = _load_log_config()
    loggers = config.get("loggers", {})
    
    # Check for exact matches first (e.g., werkzeug, socketio, engineio)
    if name in loggers:
        level_str = loggers[name].get("value", "INFO")
        return getattr(logging, level_str, logging.INFO)
    
    # Check for prefix matches (framework.*, tracker.*, website.*)
    for prefix in ["framework", "tracker", "trackerdb", "website"]:
        if name.startswith(prefix):
            logger_key = "tracker" if prefix == "trackerdb" else prefix
            if logger_key in loggers:
                level_str = loggers[logger_key].get("value", "INFO")
                return getattr(logging, level_str, logging.INFO)
    
    # Fall back to root logger level
    level_str = loggers.get("root", {}).get("value", "DEBUG")
    return getattr(logging, level_str, logging.DEBUG)

def get_logger(
    name: str,
    level: Optional[int] = None,
    max_bytes: Optional[int] = None,
    backup_count: Optional[int] = None
) -> logging.Logger:
    """Create and configure a logger.

    The logger is configured with a rotating file handler (time or size-based)
    and a console handler. If the logger already has handlers attached, it is
    returned unchanged to avoid duplicate logs.

    Args:
        name (str): Logger name; also used as the log file base name.
        level (int, optional): Logging level. If None, determined from config.
        max_bytes (int, optional): Maximum size in bytes before a log file is
            rotated (size-based rotation). If None, uses config value.
        backup_count (int, optional): Number of rotated log files to keep.
            If None, uses config value.

    Returns:
        logging.Logger: Configured (or previously existing) logger instance.
    """
    logger = logging.getLogger(name)

    # If this logger already has handlers attached specifically, return it.
    # We check `logger.handlers` (not `hasHandlers`) to avoid early exit when
    # only ancestor loggers define handlers.
    if logger.handlers:
        return logger

    # Guard configuration so multiple threads don't add duplicate handlers
    with _logger_lock:
        # Re-check inside the lock in case another thread configured it.
        if logger.handlers:
            return logger

        # Load configuration
        config = _load_log_config()
        
        # Determine level from config if not explicitly provided
        if level is None:
            level = _get_logger_level(name)
        
        logger.setLevel(level)

        # Get log directory from config
        global LOG_DIR
        log_dir = config.get("log_dir", {}).get("value", LOG_DIR)
        
        # Ensure log directory exists (lazy creation)
        Path(log_dir).mkdir(parents=True, exist_ok=True)

        # Determine rotation strategy
        rotation = config.get("rotation", {}).get("value", "time")
        backup_cnt = backup_count if backup_count is not None else config.get("backup_count", {}).get("value", 5)
        
        # File handler (rotating) - delay file creation until first emit
        log_path = str(Path(log_dir) / f"{name}.log")
        
        if rotation == "time":
            when = config.get("rotation_when", {}).get("value", "W0")
            interval = config.get("rotation_interval", {}).get("value", 1)
            file_handler = TimedRotatingFileHandler(
                log_path,
                when=when,
                interval=interval,
                backupCount=backup_cnt,
                encoding="utf-8",
                delay=True,
            )
        else:  # size-based
            max_b = max_bytes if max_bytes is not None else config.get("max_bytes", {}).get("value", 1_000_000)
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=max_b,
                backupCount=backup_cnt,
                encoding="utf-8",
                delay=True,
            )
        
        file_handler.setLevel(level)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        # Get formatter from config
        format_str = config.get("format", {}).get("value", 
            '%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - %(message)s')
        formatter = logging.Formatter(format_str)
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        # Prevent messages from being propagated to ancestor loggers (avoids duplicates)
        logger.propagate = False

    return logger


def format_exception_html(exc: Exception, include_traceback: bool = True) -> str:
    """Format an exception as a single-line HTML string for log viewers.
    
    This function formats exceptions and their tracebacks into an HTML string
    that appears as a single log entry. Newlines are replaced with <br> tags,
    and the text is properly escaped.
    
    Args:
        exc: The exception to format
        include_traceback: Whether to include the full traceback (default: True)
    
    Returns:
        str: HTML-formatted exception string on a single line
    
    Example:
        >>> try:
        ...     raise ValueError("Test error")
        ... except Exception as e:
        ...     logger.error(format_exception_html(e))
    """
    if include_traceback:
        tb = traceback.format_exc()
        # Escape HTML special characters and replace newlines with <br>
        escaped = html.escape(tb).replace('\n', '<br>')
        return escaped
    else:
        # Just the exception message
        return html.escape(str(exc))


def initialize_logging(app_root: Path, config_file: Optional[Path] = None) -> None:
    """Initialize the logging system for an application.
    
    This function should be called once at application startup to configure
    logging. It sets up the logger factory to read from the application's
    config file and configures standard loggers.
    
    Args:
        app_root: Path to the application root directory
        config_file: Path to config.json file (default: app_root/website/config.json)
    """
    global LOG_DIR
    
    # Set config file path
    if config_file is None:
        config_file = app_root / 'website' / 'config.json'
    
    set_config_file(config_file)
    
    # Set LOG_DIR to app's logs folder (not framework's)
    log_dir = app_root / 'logs'
    LOG_DIR = str(log_dir)
    os.environ['LOG_DIR'] = str(log_dir)
    
    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Pre-configure standard loggers to ensure they use our config
    standard_loggers = ['werkzeug', 'socketio', 'engineio']
    for logger_name in standard_loggers:
        get_logger(logger_name)
    
    print(f"Logging configured from: {config_file}")
    print(f"Logs directory: {log_dir}")


def get_all_loggers() -> List[Tuple[str, str, int]]:
    """Get all currently configured loggers with their levels.
    
    Returns:
        List of tuples: (logger_name, level_name, handler_count)
    """
    loggers = []
    
    # Get all existing loggers from logging manager
    logger_dict = logging.Logger.manager.loggerDict
    
    # Add root logger
    root = logging.getLogger()
    loggers.append(("root", logging.getLevelName(root.level), len(root.handlers)))
    
    # Add all other loggers
    for name in sorted(logger_dict.keys()):
        logger_obj = logger_dict[name]
        # PlaceHolder objects don't have levels
        if isinstance(logger_obj, logging.Logger):
            loggers.append((
                name,
                logging.getLevelName(logger_obj.level),
                len(logger_obj.handlers)
            ))
    
    return loggers


def set_log_level(logger_name: str, level: str) -> Tuple[bool, str]:
    """Set the log level for a specific logger at runtime.
    
    Args:
        logger_name: Name of the logger (e.g., 'root', 'framework', 'tracker.models')
        level: Level name as string ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        level_int = getattr(logging, level.upper(), None)
        if level_int is None:
            return False, f"Invalid log level: {level}"
        
        with _logger_lock:
            # Update the config cache
            global _log_config
            if _log_config is None:
                _load_log_config()
            
            # Determine which config key to update
            config_key = None
            if logger_name == "root":
                config_key = "root"
            elif logger_name in ["werkzeug", "socketio", "engineio"]:
                config_key = logger_name
            elif logger_name.startswith("framework"):
                config_key = "framework"
            elif logger_name.startswith("tracker") or logger_name.startswith("trackerdb"):
                config_key = "tracker"
            elif logger_name.startswith("website"):
                config_key = "website"
            else:
                # For specific loggers, update the logger directly but not config
                logger = logging.getLogger(logger_name)
                logger.setLevel(level_int)
                for handler in logger.handlers:
                    handler.setLevel(level_int)
                return True, f"Set {logger_name} to {level} (runtime only, not persisted)"
            
            # Update config cache
            if config_key and _log_config and "loggers" in _log_config:
                if config_key not in _log_config["loggers"]:
                    _log_config["loggers"][config_key] = {}
                _log_config["loggers"][config_key]["value"] = level.upper()
            
            # Update actual logger
            if logger_name == "root":
                logger = logging.getLogger()
            else:
                logger = logging.getLogger(logger_name)
            
            logger.setLevel(level_int)
            for handler in logger.handlers:
                handler.setLevel(level_int)
            
            # Update all child loggers with matching prefix
            if config_key and config_key in ["framework", "tracker", "website"]:
                logger_dict = logging.Logger.manager.loggerDict
                for name in logger_dict.keys():
                    if name.startswith(config_key) or (config_key == "tracker" and name.startswith("trackerdb")):
                        child_logger = logging.getLogger(name)
                        if isinstance(child_logger, logging.Logger):
                            child_logger.setLevel(level_int)
                            for handler in child_logger.handlers:
                                handler.setLevel(level_int)
            
            # Persist to config file if available
            if _config_file_path and _config_file_path.exists():
                try:
                    with open(_config_file_path, 'r', encoding='utf-8') as f:
                        full_config = json.load(f)
                    
                    if "logging" not in full_config:
                        full_config["logging"] = {}
                    if "loggers" not in full_config["logging"]:
                        full_config["logging"]["loggers"] = {}
                    
                    if config_key not in full_config["logging"]["loggers"]:
                        full_config["logging"]["loggers"][config_key] = {}
                    
                    full_config["logging"]["loggers"][config_key]["value"] = level.upper()
                    
                    with open(_config_file_path, 'w', encoding='utf-8') as f:
                        json.dump(full_config, f, indent=2)
                    
                    return True, f"Set {logger_name} to {level} (persisted to config)"
                except Exception as e:
                    return True, f"Set {logger_name} to {level} (runtime only, failed to persist: {e})"
            
            return True, f"Set {logger_name} to {level}"
            
    except Exception as e:
        return False, f"Error setting log level: {e}"

