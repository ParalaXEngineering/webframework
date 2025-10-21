"""Logging helpers.

Provides a factory function to create loggers with both rotating file and
console handlers using a unified format. Directory and file handlers are
created lazily when `get_logger` is first called to avoid import-time
side-effects.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import threading
import traceback
import html

LOG_DIR = "logs"
# Lock to guard logger creation/configuration across threads
_logger_lock = threading.Lock()

def get_logger(
    name: str,
    level: int = logging.DEBUG,
    max_bytes: int = 1_000_000,
    backup_count: int = 5
) -> logging.Logger:
    """Create and configure a logger.

    The logger is configured with a rotating file handler (size-based) and a
    console handler. If the logger already has handlers attached, it is
    returned unchanged to avoid duplicate logs.

    Args:
        name (str): Logger name; also used as the log file base name.
        level (int, optional): Logging level. Defaults to ``logging.DEBUG``.
        max_bytes (int, optional): Maximum size in bytes before a log file is
            rotated. Defaults to ``1_000_000``.
        backup_count (int, optional): Number of rotated log files to keep.
            Defaults to ``5``.

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

        logger.setLevel(level)

        # Ensure log directory exists (lazy creation)
        Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

        # File handler (rotating) - delay file creation until first emit
        log_path = str(Path(LOG_DIR) / f"{name}.log")
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
            delay=True,
        )
        file_handler.setLevel(level)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        # Common formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - %(message)s'
        )
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
