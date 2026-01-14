"""
Unified Logging Configuration for Manual_Webapp

Configures console-only logging using framework's logger factory.
Simple setup for Manual_Webapp without file rotation.
"""

import logging
import os
from pathlib import Path


def setup_simple_logging(framework_root: Path, manual_webapp_root: Path):
    """
    Configure console-only logging for Manual_Webapp using framework's logger factory.
    
    Manual_Webapp uses a simplified logging setup:
    - Console output only (no file handlers)
    - Framework logger factory handles configuration
    - Logs to Manual_Webapp/logs directory if file logging needed
    
    Args:
        framework_root: Path to the framework root directory
        manual_webapp_root: Path to the Manual_Webapp root directory
    """
    # Import framework's logger factory
    sys_path = str(framework_root)
    if sys_path not in __import__('sys').path:
        __import__('sys').path.insert(0, sys_path)
    
    from src.modules.log import logger_factory
    
    # Set LOG_DIR to Manual_Webapp's logs folder
    log_dir = manual_webapp_root / 'logs'
    logger_factory.LOG_DIR = str(log_dir)
    os.environ['LOG_DIR'] = str(log_dir)
    
    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # No config file for Manual_Webapp - uses defaults
    # Pre-configure standard loggers to ensure they use defaults
    standard_loggers = ['werkzeug', 'socketio', 'engineio']
    for logger_name in standard_loggers:
        logger = logger_factory.get_logger(logger_name)
        # Set to WARNING for less verbose console output
        logger.setLevel(logging.WARNING)
        for handler in logger.handlers:
            handler.setLevel(logging.WARNING)
    
    print(f"Logging configured for Manual_Webapp")
    print(f"Logs directory: {log_dir}")

