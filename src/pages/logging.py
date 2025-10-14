"""
Logging Viewer Page - Flask blueprint for real-time log monitoring.

This module provides real-time monitoring of framework log files with a modern
tabbed interface showing log content with automatic updates using DataTables.
"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from ..modules import displayer
from .common import require_admin
import os
import re

bp = Blueprint("logging", __name__, url_prefix="/logging")


def _parse_log_line(line: str) -> dict:
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
    pattern1 = r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d{3})\s*-\s*(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*-\s*([^\-]+?)\s*-\s*([^\-]+?\.py):(\d+)\s*-\s*(.*)$'
    match1 = re.match(pattern1, line.strip())
    
    if match1:
        return {
            'timestamp': match1.group(1),
            'file': match1.group(4),  # file.py
            'line': match1.group(5),  # 215
            'level': match1.group(2),
            'message': match1.group(6)
        }
    
    # Pattern 2: timestamp - LEVEL - message (fallback)
    pattern2 = r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d{3})\s*-\s*(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*-\s*(.*)$'
    match2 = re.match(pattern2, line.strip())
    
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
        'level': 'INFO',
        'message': line.strip()
    }


def _get_level_badge(level: str) -> str:
    """Get Bootstrap badge HTML for log level."""
    badges = {
        'DEBUG': '<span class="badge bg-secondary">DEBUG</span>',
        'INFO': '<span class="badge bg-info">INFO</span>',
        'WARNING': '<span class="badge bg-warning">WARNING</span>',
        'ERROR': '<span class="badge bg-danger">ERROR</span>',
        'CRITICAL': '<span class="badge bg-dark">CRITICAL</span>'
    }
    return badges.get(level, f'<span class="badge bg-secondary">{level}</span>')


@bp.route("/logs", methods=["GET"])
@require_admin
def logs():
    """Display log files in tabs with SERVER_SIDE DataTables for efficient viewing."""
    disp = displayer.Displayer()
    disp.add_generic("Log Viewer")
    disp.set_title("Log Viewer")
    
    disp.add_breadcrumb("Home", "demo.index", [])
    disp.add_breadcrumb("Logs", "logging.logs", [])
    
    # Get logs directory
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    
    # Check if logs directory exists
    if not os.path.exists(logs_dir):
        disp.add_display_item(displayer.DisplayerItemText(
            f"<div class='alert alert-danger'>Logs directory not found: {logs_dir}</div>"
        ))
        return render_template("base_content.j2", content=disp.display())
    
    # Get all log files
    log_files = []
    try:
        for filename in sorted(os.listdir(logs_dir)):
            if filename.endswith('.log'):
                filepath = os.path.join(logs_dir, filename)
                log_files.append({
                    'name': filename,
                    'path': filepath,
                    'size': os.path.getsize(filepath)
                })
    except Exception as e:
        disp.add_display_item(displayer.DisplayerItemText(
            f"<div class='alert alert-danger'>Error reading logs directory: {str(e)}</div>"
        ))
        return render_template("base_content.j2", content=disp.display())
    
    if not log_files:
        disp.add_display_item(displayer.DisplayerItemText(
            f"<div class='alert alert-warning'>No log files found in: {logs_dir}</div>"
        ))
        return render_template("base_content.j2", content=disp.display())
    
    # Statistics section
    total_size = sum(f['size'] for f in log_files)
    disp.add_master_layout(displayer.DisplayerLayout(
        displayer.Layouts.VERTICAL, [4, 4, 4]
    ))
    
    disp.add_display_item(displayer.DisplayerItemText(
        f"<div class='text-center'><h3>{len(log_files)}</h3><small>Log Files</small></div>"
    ), 0)
    disp.add_display_item(displayer.DisplayerItemText(
        f"<div class='text-center'><h3>{total_size / 1024:.2f} KB</h3><small>Total Size</small></div>"
    ), 1)
    disp.add_display_item(displayer.DisplayerItemText(
        f"<div class='text-center'><h3>{os.path.basename(logs_dir)}</h3><small>Directory</small></div>"
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
        slave_layout_id = disp.add_slave_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.TABLE,
                columns=["#", "Timestamp", "Level", "File", "Line", "Message"],
                datatable_config={
                    "table_id": f"log_table_{log_file['name'].replace('.', '_')}",
                    "mode": displayer.TableMode.SERVER_SIDE,
                    "api_endpoint": "logging.api_log_data",  # Blueprint.function
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
                    "order": [[0, "desc"]],  # Most recent first (line number descending)
                    "pageLength": 25,
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
                         target="logging.logs")




@bp.route("/api/<log_file>")
@require_admin
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
    if '..' in log_file or '/' in log_file:
        return jsonify({"error": "Invalid log file name"}), 400
    
    # Get DataTables parameters
    draw = request.args.get('draw', type=int, default=1)
    start = request.args.get('start', type=int, default=0)
    length = request.args.get('length', type=int, default=25)
    search_value = request.args.get('search[value]', default='')
    order_column = request.args.get('order[0][column]', type=int, default=0)
    order_dir = request.args.get('order[0][dir]', default='desc')
    
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    log_path = os.path.join(logs_dir, log_file)
    
    if not os.path.exists(log_path):
        return jsonify({
            "draw": draw,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": "Log file not found"
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
                    'file': entry['file'] if entry['file'] else 'N/A',
                    'line': entry['line'] if entry['line'] else 'N/A',
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
            # Map all possible identifiers (column index, data field name, display name) to internal data keys
            identifier_to_datakey = {
                # Column indexes (as strings)
                '2': 'level',
                '3': 'file',
                '4': 'line',
                # Data field names
                'level_html': 'level',
                'file': 'file',
                'line': 'line',
                # Display column names (for fallback)
                'Level': 'level',
                'File': 'file',
                'Line': 'line'
            }
            
            for col_identifier, selected_values in searchpanes_filters.items():
                data_key = identifier_to_datakey.get(col_identifier)
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
        reverse = (order_dir == 'desc')
        
        try:
            # Handle numeric vs string sorting
            if sort_key == 'line_num' or sort_key == 'line':
                # Numeric sorting for line numbers
                def sort_func(x):
                    val = x[sort_key]
                    if val == 'N/A' or val == '':
                        return -1 if reverse else float('inf')
                    try:
                        return int(val)
                    except:
                        return -1 if reverse else float('inf')
                filtered_data.sort(key=sort_func, reverse=reverse)
            else:
                filtered_data.sort(key=lambda x: str(x[sort_key]).lower(), reverse=reverse)
        except:
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
            if file != 'N/A':
                file_counts[file] = file_counts.get(file, 0) + 1
        
        file_options = [
            {
                'label': file,
                'value': file,
                'total': count,
                'count': sum(1 for r in filtered_data if r['file'] == file)
            }
            for file, count in sorted(file_counts.items())[:50]  # Limit to 50 most common
        ]
        searchpanes_options['3'] = file_options
        searchpanes_options['file'] = file_options
        
        # Column 4 / "line": Line
        line_counts = {}
        for row in all_data:
            line_num = row['line']
            if line_num != 'N/A':
                line_counts[line_num] = line_counts.get(line_num, 0) + 1
        
        line_options = [
            {
                'label': line_num,
                'value': line_num,
                'total': count,
                'count': sum(1 for r in filtered_data if r['line'] == line_num)
            }
            for line_num, count in sorted(line_counts.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0)[:50]  # Top 50 by numeric order
        ]
        searchpanes_options['4'] = line_options
        searchpanes_options['line'] = line_options
        
        return jsonify({
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": output_data,
            "searchPanes": {
                "options": searchpanes_options
            }
        })
    
    except Exception as e:
        return jsonify({
            "draw": draw,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": str(e)
        }), 500
