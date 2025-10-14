"""
Log Parser Module

Handles reading and parsing of log files.
Extracted from settings.py to separate business logic from presentation layer.
"""

from typing import List, Dict, Any


def read_log_file(log_file_path: str, max_lines: int = 100) -> List[str]:
    """
    Read the last N lines from a log file.
    
    Args:
        log_file_path: Path to the log file
        max_lines: Maximum number of lines to read from the end (default: 100)
        
    Returns:
        List of log lines (most recent last)
        
    Example:
        >>> lines = read_log_file("app.log", max_lines=50)
        >>> for line in lines:
        ...     print(line)
    """
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return lines[-max_lines:] if len(lines) > max_lines else lines
    except FileNotFoundError:
        return [f"Log file not found: {log_file_path}"]
    except Exception as e:
        return [f"Error reading log file: {str(e)}"]


def parse_log_lines(lines: List[str]) -> List[Dict[str, Any]]:
    """
    Parse log lines into structured format.
    
    Args:
        lines: List of raw log lines
        
    Returns:
        List of dictionaries with parsed log entries
        Each entry contains: timestamp, level, message
        
    Example:
        >>> lines = ["2024-01-15 10:30:00 INFO Starting application"]
        >>> parsed = parse_log_lines(lines)
        >>> print(parsed[0]['level'])  # 'INFO'
    """
    parsed_logs = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Try to parse common log format: TIMESTAMP LEVEL MESSAGE
        parts = line.split(maxsplit=2)
        
        if len(parts) >= 3:
            entry = {
                'timestamp': f"{parts[0]} {parts[1] if ':' in parts[1] else ''}",
                'level': _extract_log_level(line),
                'message': parts[2] if len(parts) > 2 else '',
                'raw': line
            }
        else:
            entry = {
                'timestamp': '',
                'level': 'UNKNOWN',
                'message': line,
                'raw': line
            }
        
        parsed_logs.append(entry)
    
    return parsed_logs


def _extract_log_level(line: str) -> str:
    """
    Extract log level from a log line.
    
    Args:
        line: Raw log line
        
    Returns:
        Log level (INFO, WARNING, ERROR, DEBUG) or UNKNOWN
    """
    line_upper = line.upper()
    
    levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'WARN', 'FATAL']
    
    for level in levels:
        if level in line_upper:
            return level
    
    return 'UNKNOWN'


def filter_logs_by_level(parsed_logs: List[Dict[str, Any]], level: str) -> List[Dict[str, Any]]:
    """
    Filter parsed logs by log level.
    
    Args:
        parsed_logs: List of parsed log entries
        level: Log level to filter (INFO, WARNING, ERROR, etc.)
        
    Returns:
        Filtered list of log entries
        
    Example:
        >>> errors = filter_logs_by_level(parsed_logs, 'ERROR')
    """
    level_upper = level.upper()
    return [log for log in parsed_logs if log['level'] == level_upper]
