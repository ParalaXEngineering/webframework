"""
Logging Viewer Page - Flask blueprint for real-time log monitoring.

This module provides real-time monitoring of framework log files with a modern
tabbed interface showing log content with automatic updates using DataTables.
"""

# Standard library
import os
import re
from typing import Dict, Any, List

# Third-party
from flask import Blueprint, render_template, request, jsonify

# Local modules
from ..modules import displayer
from ..modules.auth import require_admin
from ..modules.app_context import app_context
from ..modules.i18n.messages import (
    ERROR_INVALID_LOG_FILE,
    ERROR_LOG_FILE_NOT_FOUND,
    TEXT_LOG_VIEWER,
    TEXT_LOGS,
    TEXT_LOG_FILES,
    TEXT_TOTAL_SIZE,
    TEXT_SIZE_KB,
    TEXT_DIRECTORY,
    TEXT_NO_LOGS_DIR,
    TEXT_ERROR_READING_LOGS,
    TEXT_NO_LOG_FILES,
)

# Constants - Blueprint and URL routing
BLUEPRINT_NAME = "logging"
BLUEPRINT_PREFIX = "/logging"
ROUTE_LOGS = "/logs"
ROUTE_CONFIG = "/config"
ROUTE_API = "/api/<log_file>"

# Constants - Log levels and styling
LOG_LEVELS = {
    'DEBUG': 'secondary',
    'INFO': 'info',
    'WARNING': 'warning',
    'ERROR': 'danger',
    'CRITICAL': 'dark'
}
LEVEL_NAMES = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
BADGE_TEMPLATE = '<span class="badge bg-{color}">{level}</span>'

# Constants - Log file parsing
LOG_PATTERN_FULL = r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d{3})\s*-\s*(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*-\s*([^\-]+?)\s*-\s*([^\-]+?\.py):(\d+)\s*-\s*(.*)$'
LOG_PATTERN_FALLBACK = r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d{3})\s*-\s*(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*-\s*(.*)$'
LOG_FILE_EXTENSION = '.log'
TEXT_NA = 'N/A'



# Constants - Table configuration
TABLE_COLUMNS_LOG = ["#", "Timestamp", "Level", "File", "Line", "Message"]
TABLE_ID_LOG = "log_table_{}"
TABLE_PAGE_LENGTH = 25
TABLE_SORT_COLUMN = 0
TABLE_SORT_ORDER = "desc"

# Constants - API response keys
API_PARAM_DRAW = 'draw'
API_PARAM_START = 'start'
API_PARAM_LENGTH = 'length'
API_PARAM_SEARCH = 'search[value]'
API_PARAM_ORDER_COL = 'order[0][column]'
API_PARAM_ORDER_DIR = 'order[0][dir]'
API_RESPONSE_DRAW = "draw"
API_RESPONSE_TOTAL = "recordsTotal"
API_RESPONSE_FILTERED = "recordsFiltered"
API_RESPONSE_DATA = "data"
API_RESPONSE_ERROR = "error"
API_RESPONSE_PANES = "searchPanes"
API_RESPONSE_OPTIONS = "options"

# Constants - SearchPanes configuration
SEARCHPANES_LIMIT = 50
SEARCHPANES_COL_MAPPING = {
    '2': 'level',
    '3': 'file',
    '4': 'line',
    'level_html': 'level',
    'file': 'file',
    'line': 'line',
    'Level': 'level',
    'File': 'file',
    'Line': 'line'
}



# Constants - Security and validation
INVALID_PATH_CHARS = ['..', '/']

bp = Blueprint(BLUEPRINT_NAME, __name__, url_prefix=BLUEPRINT_PREFIX)


def _parse_log_line(line: str) -> Dict[str, Any]:
    """
    Parse a log line into components (same logic as log_emitter).
    
    Expected formats:
    1. "2025-10-09 15:45:54,146 - INFO - log.emitter - log_emitter.py:53 - Log emitter started"
       timestamp - LEVEL - module - file:line - message
    2. "2024-01-15 10:30:45,123 - LEVEL - message" (fallback)
    
    Args:
        line: Raw log line
        
    Returns:
        Dict with timestamp, file, line, level, message
    """
    # Pattern 1: timestamp - LEVEL - module - file:line - message
    match1 = re.match(LOG_PATTERN_FULL, line.strip())
    
    if match1:
        return {
            'timestamp': match1.group(1),
            'file': match1.group(4),  # file.py
            'line': match1.group(5),  # 215
            'level': match1.group(2),
            'message': match1.group(6)
        }
    
    # Pattern 2: timestamp - LEVEL - message (fallback)
    match2 = re.match(LOG_PATTERN_FALLBACK, line.strip())
    
    if match2:
        return {
            'timestamp': match2.group(1),
            'file': '',
            'line': '',
            'level': match2.group(2),
            'message': match2.group(3)
        }
    
    # If no pattern matches, treat entire line as message
    return {
        'timestamp': '',
        'file': '',
        'line': '',
        'level': LEVEL_NAMES[1],  # INFO
        'message': line.strip()
    }


def _get_level_badge(level: str) -> str:
    """Get Bootstrap badge HTML for log level."""
    color = LOG_LEVELS.get(level, LOG_LEVELS[LEVEL_NAMES[1]])  # Default to INFO color
    return BADGE_TEMPLATE.format(color=color, level=level)


@bp.route(ROUTE_LOGS, methods=["GET"])
@require_admin()
def logs():
    """Display log files in tabs with SERVER_SIDE DataTables for efficient viewing."""
    from ..modules.log.logger_factory import get_all_loggers
    
    disp = displayer.Displayer()
    disp.add_generic(TEXT_LOG_VIEWER)
    disp.set_title(TEXT_LOG_VIEWER)
    
    disp.add_breadcrumb(TEXT_LOGS, f"{BLUEPRINT_NAME}.logs", [])
    
    # Get logs directory from app_context (uses project's logs, not framework's)
    app_path = app_context.app_path or os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    logs_dir = os.path.join(app_path, 'logs')
    
    # Check if logs directory exists
    if not os.path.exists(logs_dir):
        disp.add_display_item(displayer.DisplayerItemText(
            f"<div class='alert alert-danger'>{TEXT_NO_LOGS_DIR}: {logs_dir}</div>"
        ))
        return render_template("base_content.j2", content=disp.display())
    
    # Get all log files
    log_files = []
    try:
        for filename in sorted(os.listdir(logs_dir)):
            if filename.endswith(LOG_FILE_EXTENSION):
                filepath = os.path.join(logs_dir, filename)
                log_files.append({
                    'name': filename,
                    'path': filepath,
                    'size': os.path.getsize(filepath)
                })
    except Exception as e:
        disp.add_display_item(displayer.DisplayerItemText(
            f"<div class='alert alert-danger'>{TEXT_ERROR_READING_LOGS}: {str(e)}</div>"
        ))
        return render_template("base_content.j2", content=disp.display())
    
    if not log_files:
        disp.add_display_item(displayer.DisplayerItemText(
            f"<div class='alert alert-warning'>{TEXT_NO_LOG_FILES}: {logs_dir}</div>"
        ))
        return render_template("base_content.j2", content=disp.display())
    
    # Statistics section
    total_size = sum(f['size'] for f in log_files)
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [3, 3, 3, 3]
    ))
    
    disp.add_display_item(displayer.DisplayerItemText(
        f"<div class='text-center'><h3>{len(log_files)}</h3><small>{TEXT_LOG_FILES}</small></div>"
    ), 0)
    disp.add_display_item(displayer.DisplayerItemText(
        f"<div class='text-center'><h3>{total_size / 1024:.2f} {TEXT_SIZE_KB}</h3><small>{TEXT_TOTAL_SIZE}</small></div>"
    ), 1)
    disp.add_display_item(displayer.DisplayerItemText(
        f"<div class='text-center'><h3>{os.path.basename(logs_dir)}</h3><small>{TEXT_DIRECTORY}</small></div>"
    ), 2)
    
    disp.duplicate_master_layout()
    disp.add_display_item(displayer.DisplayerItemSeparator(), 0)
    
    # Info message about SERVER_SIDE DataTables (always live)
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    
    # Create TABS layout - one tab per log file
    tab_titles = [f['name'] for f in log_files]
    master_layout_id = disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.TABS,
        tab_titles
    ))
    
    # For each log file, add a TABLE with SERVER_SIDE DataTable
    for tab_index, log_file in enumerate(log_files):
        # Add TABLE layout with SERVER_SIDE DataTable config
        disp.add_slave_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.TABLE,
                columns=TABLE_COLUMNS_LOG,
                datatable_config={
                    "table_id": TABLE_ID_LOG.format(log_file['name'].replace('.', '_')),
                    "mode": displayer.TableMode.SERVER_SIDE,
                    "api_endpoint": f"{BLUEPRINT_NAME}.get_logs",  # Blueprint.function
                    "api_params": {"log_file": log_file['name']},  # URL parameters
                    "columns": [
                        {"data": "line_num"},
                        {"data": "timestamp"},
                        {"data": "level_html"},  # Server-side HTML badges
                        {"data": "file"},
                        {"data": "line"},
                        {"data": "message"}
                    ],
                    "searchable_columns": [2, 3, 4],  # SearchPanes on Level (col 2), File (col 3), Line (col 4)
                    "order": [[TABLE_SORT_COLUMN, TABLE_SORT_ORDER]],  # Most recent first (line number descending)
                    "pageLength": TABLE_PAGE_LENGTH,
                    "serverSide": True,  # Enable server-side processing
                    "processing": True   # Show processing indicator
                }
            ),
            column=tab_index,
            layout_id=master_layout_id
        )
    
    # Render page
    content = disp.display()
    
    return render_template("base_content.j2", 
                         content=content, 
                         target=f"{BLUEPRINT_NAME}.logs")




@bp.route(ROUTE_CONFIG, methods=["GET", "POST"])
@require_admin()
def config():
    """Display logger configuration page with grouped loggers."""
    from ..modules.log.logger_factory import get_all_loggers, set_log_level as set_level_func, get_logger
    from collections import defaultdict
    from flask import flash, redirect, url_for
    from ..modules import utilities
    
    logger = get_logger(__name__)
    
    # Handle POST request (form submission)
    if request.method == 'POST':
        try:
            # Use util_post_to_json to strip page title prefix from field names
            data = utilities.util_post_to_json(request.form.to_dict())
            
            # Extract the nested form data (under 'Logger Configuration' key)
            form_data = data.get('Logger Configuration', {})
            logger_name = form_data.get('logger_name', 'root')
            log_level = form_data.get('log_level', 'INFO')
            
            # Check if it's a group pattern (ends with .*)
            if logger_name.endswith('.*'):
                # Get prefix without .*
                prefix = logger_name[:-2]
                
                # Get all loggers matching the prefix
                all_loggers = get_all_loggers()
                matching_loggers = [name for name, _, _ in all_loggers if name.startswith(prefix)]
                
                if not matching_loggers:
                    flash(f"✗ No loggers found matching {logger_name}", "warning")
                else:
                    # Set level for all matching loggers
                    count = 0
                    for match_name in matching_loggers:
                        success, _ = set_level_func(match_name, log_level)
                        if success:
                            count += 1
                    
                    flash(f"✓ Set {count} loggers in {logger_name} to {log_level}", "success")
            else:
                # Single logger
                success, message = set_level_func(logger_name, log_level)
                
                if success:
                    flash(f"✓ {message}", "success")
                else:
                    flash(f"✗ {message}", "danger")
                
        except Exception as e:
            flash(f"✗ Error setting log level: {str(e)}", "danger")
        
        return redirect(url_for(f"{BLUEPRINT_NAME}.config"))
    
    disp = displayer.Displayer()
    disp.add_generic("Logger Configuration")
    disp.set_title("Logger Configuration")
    
    disp.add_breadcrumb(TEXT_LOGS, f"{BLUEPRINT_NAME}.logs", [])
    disp.add_breadcrumb("Configuration", f"{BLUEPRINT_NAME}.config", [])
    
    # Get all active loggers
    loggers_info = get_all_loggers()
    
    # Group loggers by prefix (e.g., "src.*", "website.pages.*")
    grouped = defaultdict(list)
    level_priority = {'DEBUG': 0, 'INFO': 10, 'WARNING': 20, 'ERROR': 30, 'CRITICAL': 40, 'NOTSET': 50}
    
    for logger_name, level_name, handler_count in loggers_info:
        # Determine group prefix
        if logger_name == "root":
            group = "root"
        elif '.' in logger_name:
            # Group by first component (e.g., "framework.tooltip" -> "framework.*")
            parts = logger_name.split('.')
            group = f"{parts[0]}.*"
        else:
            # Single-name loggers: werkzeug, socketio, engineio, trackerdb
            group = f"{logger_name}.*"
        
        grouped[group].append((logger_name, level_name, handler_count))
    
    # Calculate group-level info (most permissive level, total handlers)
    # Only show configurable (persistent) logger groups
    configurable_groups = {'root', 'framework.*', 'tracker.*', 'trackerdb.*', 'website.*', 'werkzeug.*', 'socketio.*', 'engineio.*'}
    
    group_info = []
    for group, loggers in grouped.items():
        # Skip non-configurable logger groups (third-party libraries)
        if group not in configurable_groups:
            continue
            
        # Find most permissive level (lowest priority number = DEBUG is most permissive)
        min_level = min((level_priority.get(lvl, 50) for _, lvl, _ in loggers))
        group_level = next(lvl for lvl, pri in level_priority.items() if pri == min_level)
        total_handlers = sum(h for _, _, h in loggers)
        group_info.append((group, group_level, len(loggers), total_handlers))
    
    # Level change form
    disp.add_display_item(displayer.DisplayerItemText("<h5>Change Logger Level</h5>"), 0)
    
    form_layout = disp.add_slave_layout(
        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [4, 4, 4]),
        column=0,
        layout_id=0
    )
    
    # Logger group selector
    group_names = sorted([g for g, _, _, _ in group_info])
    if not group_names:
        group_names = ["root"]
    
    disp.add_display_item(
        displayer.DisplayerItemInputSelect(
            "logger_name",
            "Logger Group",
            value=group_names[0],
            choices=group_names
        ),
        0, form_layout
    )
    
    # Level selector
    disp.add_display_item(
        displayer.DisplayerItemInputSelect(
            "log_level",
            "New Level",
            value="INFO",
            choices=LEVEL_NAMES
        ),
        1, form_layout
    )
    
    # Submit button
    disp.add_display_item(
        displayer.DisplayerItemButton(
            "submit_level",
            "Set Level",
            icon="save",
            color=displayer.BSstyle.PRIMARY
        ),
        2, form_layout
    )

    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [12]
    ))
    
    # Display grouped loggers
    disp.add_display_item(displayer.DisplayerItemText(f"<h5>Logger Groups ({len(group_info)})</h5>"), 0)
    
    # Convert level name to BSstyle for badge
    level_style_map = {
        'DEBUG': displayer.BSstyle.SECONDARY,
        'INFO': displayer.BSstyle.INFO,
        'WARNING': displayer.BSstyle.WARNING,
        'ERROR': displayer.BSstyle.ERROR,
        'CRITICAL': displayer.BSstyle.DARK,
        'NOTSET': displayer.BSstyle.LIGHT
    }
    
    # Table for grouped loggers
    table_layout = disp.add_master_layout(
        displayer.DisplayerLayout(
            displayer.Layouts.TABLE,
            columns=["Logger Group", "Level", "Loggers", "Handlers"]
        )
    )
    
    for group, level_name, logger_count, handler_count in sorted(group_info):
        disp.add_display_item(displayer.DisplayerItemText(group), 0, table_layout)
        
        level_style = level_style_map.get(level_name, displayer.BSstyle.INFO)
        disp.add_display_item(displayer.DisplayerItemBadge(level_name, level_style), 1, table_layout)
        
        disp.add_display_item(displayer.DisplayerItemText(str(logger_count)), 2, table_layout)
        disp.add_display_item(displayer.DisplayerItemText(str(handler_count)), 3, table_layout)
    
    # Render page
    content = disp.display()
    
    return render_template("base_content.j2", 
                         content=content, 
                         target=f"{BLUEPRINT_NAME}.config")


@bp.route(ROUTE_API, methods=["GET"])
@require_admin()
def get_logs(log_file: str):
    """
    SERVER_SIDE DataTables AJAX endpoint.
    Returns log entries in DataTables server-side processing format.
    
    DataTables sends parameters:
    - draw: Draw counter for sequencing
    - start: Starting record index
    - length: Number of records to return (-1 for all)
    - search[value]: Global search string
    - order[0][column]: Column index to sort by
    - order[0][dir]: Sort direction (asc/desc)
    
    Returns JSON with:
    - draw: Echo of draw parameter
    - recordsTotal: Total records before filtering
    - recordsFiltered: Total records after filtering
    - data: Array of row objects
    """
    # Security: validate log_file name (no path traversal)
    if any(char in log_file for char in INVALID_PATH_CHARS):
        return jsonify({API_RESPONSE_ERROR: ERROR_INVALID_LOG_FILE}), 400
    
    # Get DataTables parameters
    draw = request.args.get(API_PARAM_DRAW, type=int, default=1)
    start = request.args.get(API_PARAM_START, type=int, default=0)
    length = request.args.get(API_PARAM_LENGTH, type=int, default=TABLE_PAGE_LENGTH)
    search_value = request.args.get(API_PARAM_SEARCH, default='')
    order_column = request.args.get(API_PARAM_ORDER_COL, type=int, default=0)
    order_dir = request.args.get(API_PARAM_ORDER_DIR, default=TABLE_SORT_ORDER)
    
    # Get logs directory from app_context (uses project's logs, not framework's)
    app_path = app_context.app_path or os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    logs_dir = os.path.join(app_path, 'logs')
    log_path = os.path.join(logs_dir, log_file)
    
    if not os.path.exists(log_path):
        return jsonify({
            API_RESPONSE_DRAW: draw,
            API_RESPONSE_TOTAL: 0,
            API_RESPONSE_FILTERED: 0,
            API_RESPONSE_DATA: [],
            API_RESPONSE_ERROR: ERROR_LOG_FILE_NOT_FOUND
        }), 404
    
    try:
        # Read entire log file
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Parse all entries
        all_data = []
        for idx, line in enumerate(lines, start=1):
            if line.strip():
                entry = _parse_log_line(line)
                all_data.append({
                    'line_num': idx,
                    'timestamp': entry['timestamp'],
                    'level': entry['level'],  # Plain text for searching/sorting
                    'level_html': _get_level_badge(entry['level']),  # HTML for display
                    'file': entry['file'] if entry['file'] else TEXT_NA,
                    'line': entry['line'] if entry['line'] else TEXT_NA,
                    'message': entry['message']
                })
        
        records_total = len(all_data)
        
        # Apply SearchPanes filters
        # DataTables sends filter params in various formats depending on version/config
        # Could be: searchPanes[2][0], searchPanes[level_html][0], columns[2][search][value], etc.
        filtered_data = all_data
        searchpanes_filters = {}
        
        # Parse SearchPanes filters from query params
        for key in request.args:
            if key.startswith('searchPanes['):
                # Extract identifier: searchPanes[2][0] -> "2" or searchPanes[level_html][0] -> "level_html"
                match = re.match(r'searchPanes\[([^\]]+)\]', key)
                if match:
                    col_identifier = match.group(1)
                    if col_identifier not in searchpanes_filters:
                        searchpanes_filters[col_identifier] = []
                    # Get all values for this identifier
                    values = request.args.getlist(key)
                    searchpanes_filters[col_identifier].extend(values)
        
        # Apply filters by mapping column identifier to data key
        if searchpanes_filters:
            for col_identifier, selected_values in searchpanes_filters.items():
                data_key = SEARCHPANES_COL_MAPPING.get(col_identifier)
                if data_key and selected_values:
                    filtered_data = [
                        row for row in filtered_data 
                        if str(row[data_key]) in selected_values
                    ]
        
        # Apply search filter (global search across all columns)
        if search_value:
            search_filtered = []
            search_lower = search_value.lower()
            for row in filtered_data:
                if (search_lower in str(row['line_num']).lower() or
                    search_lower in row['timestamp'].lower() or
                    search_lower in row['level'].lower() or
                    search_lower in row['file'].lower() or
                    search_lower in row['line'].lower() or
                    search_lower in row['message'].lower()):
                    search_filtered.append(row)
            filtered_data = search_filtered
        
        records_filtered = len(filtered_data)
        
        # Apply sorting
        sort_keys = {
            0: 'line_num',
            1: 'timestamp',
            2: 'level',
            3: 'file',
            4: 'line',
            5: 'message'
        }
        sort_key = sort_keys.get(order_column, 'line_num')
        reverse = (order_dir == TABLE_SORT_ORDER)
        
        try:
            # Handle numeric vs string sorting
            if sort_key == 'line_num' or sort_key == 'line':
                # Numeric sorting for line numbers
                def sort_func(x):
                    val = x[sort_key]
                    if val == TEXT_NA or val == '':
                        return -1 if reverse else float('inf')
                    try:
                        return int(val)
                    except (ValueError, TypeError):
                        return -1 if reverse else float('inf')
                filtered_data.sort(key=sort_func, reverse=reverse)
            else:
                filtered_data.sort(key=lambda x: str(x[sort_key]).lower(), reverse=reverse)
        except Exception:
            pass  # If sorting fails, keep original order
        
        # Apply pagination (handle -1 for "all")
        if length == -1:
            paginated_data = filtered_data[start:]
        else:
            paginated_data = filtered_data[start:start + length]
        
        # Format output (use HTML badges for level display)
        output_data = []
        for row in paginated_data:
            output_data.append({
                'line_num': row['line_num'],
                'timestamp': row['timestamp'],
                'level_html': row['level_html'],  # HTML badges rendered server-side
                'file': row['file'],
                'line': row['line'],
                'message': row['message']
            })
        
        # Build SearchPanes options (distinct values for searchable columns)
        # For server-side mode, DataTables may expect column indexes OR column data names
        # We'll provide BOTH to ensure compatibility
        # Columns: 0=line_num, 1=timestamp, 2=level_html, 3=file, 4=line, 5=message
        searchpanes_options = {}
        
        # Column 2 / "level_html": Level 
        level_counts = {}
        for row in all_data:
            level = row['level']
            level_counts[level] = level_counts.get(level, 0) + 1
        
        level_options = [
            {
                'label': _get_level_badge(level),  # HTML badge for SearchPane display
                'value': level,  # Plain text for filtering
                'total': count,
                'count': sum(1 for r in filtered_data if r['level'] == level)
            }
            for level, count in sorted(level_counts.items())
        ]
        searchpanes_options['2'] = level_options
        searchpanes_options['level_html'] = level_options
        
        # Column 3 / "file": File
        file_counts = {}
        for row in all_data:
            file = row['file']
            if file != TEXT_NA:
                file_counts[file] = file_counts.get(file, 0) + 1
        
        file_options = [
            {
                'label': file,
                'value': file,
                'total': count,
                'count': sum(1 for r in filtered_data if r['file'] == file)
            }
            for file, count in sorted(file_counts.items())[:SEARCHPANES_LIMIT]  # Limit to most common
        ]
        searchpanes_options['3'] = file_options
        searchpanes_options['file'] = file_options
        
        # Column 4 / "line": Line
        line_counts = {}
        for row in all_data:
            line_num = row['line']
            if line_num != TEXT_NA:
                line_counts[line_num] = line_counts.get(line_num, 0) + 1
        
        line_options = [
            {
                'label': line_num,
                'value': line_num,
                'total': count,
                'count': sum(1 for r in filtered_data if r['line'] == line_num)
            }
            for line_num, count in sorted(line_counts.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0)[:SEARCHPANES_LIMIT]  # Top limit by numeric order
        ]
        searchpanes_options['4'] = line_options
        searchpanes_options['line'] = line_options
        
        return jsonify({
            API_RESPONSE_DRAW: draw,
            API_RESPONSE_TOTAL: records_total,
            API_RESPONSE_FILTERED: records_filtered,
            API_RESPONSE_DATA: output_data,
            API_RESPONSE_PANES: {
                API_RESPONSE_OPTIONS: searchpanes_options
            }
        })
    
    except Exception as e:
        return jsonify({
            API_RESPONSE_DRAW: draw,
            API_RESPONSE_TOTAL: 0,
            API_RESPONSE_FILTERED: 0,
            API_RESPONSE_DATA: [],
            API_RESPONSE_ERROR: str(e)
        }), 500


# set_log_level route removed - now handled directly in config() POST handler
