# Logging Page - SERVER_SIDE DataTables Implementation

## Overview
The logging page now uses DataTables SERVER_SIDE mode with AJAX for efficient, always-live log viewing.

## Architecture

### 1. Main Route (`/logging/logs`)
- Discovers log files in `logs/` directory
- Creates TABS layout (one tab per log file)
- Each tab has a TABLE with SERVER_SIDE DataTable configuration

### 2. AJAX API Endpoint (`/logging/api/<log_file>`)
Returns DataTables server-side processing format:
```json
{
    "draw": 1,
    "recordsTotal": 1523,
    "recordsFiltered": 42,
    "data": [
        {
            "line_num": 1,
            "timestamp": "2025-10-10 13:27:11",
            "level": "<span class='badge bg-info'>INFO</span>",
            "file_line": "main.py:73",
            "message": "Application starting up"
        },
        ...
    ]
}
```

**Supports:**
- ✅ Search: Global search across all columns
- ✅ Sorting: By any column (asc/desc)
- ✅ Pagination: Configurable page size
- ✅ Security: Validates log file names (no path traversal)

### 3. Frontend (DataTables)
- `serverSide: true` - Enable server-side processing
- `processing: true` - Show loading indicator
- `ajax.url` - Points to `/logging/api/<log_file>`
- `ajax.dataSrc: 'data'` - Extract data from response

### 4. Tab Handling
JavaScript automatically redraws DataTables when tabs become visible:
```javascript
tabTrigger.addEventListener('shown.bs.tab', function(event) {
    const tables = targetPane.querySelectorAll('table.dataTable');
    tables.forEach(function(table) {
        DataTable.getInstance(table).columns.adjust().draw();
    });
});
```

## Benefits

1. **Always Live**: DataTables queries the endpoint on every interaction
2. **Efficient**: Only requested rows are parsed and sent
3. **Scalable**: Can handle large log files (reads entire file but only sends paginated results)
4. **Search/Sort**: Built-in by DataTables with server-side support
5. **No Polling**: DataTables handles refresh on user interaction

## Configuration

In `logging.py` route:
```python
datatable_config={
    "table_id": f"log_table_{log_file['name'].replace('.', '_')}",
    "mode": displayer.TableMode.SERVER_SIDE,
    "api_endpoint": "logging.api_log_data",
    "api_params": {"log_file": log_file['name']},
    "columns": [
        {"data": "line_num"},
        {"data": "timestamp"},
        {"data": "level"},
        {"data": "file_line"},
        {"data": "message"}
    ],
    "order": [[0, "desc"]],  # Most recent first
    "pageLength": 25,
    "serverSide": True,
    "processing": True
}
```

## Testing

1. Start the test webapp: `.venv/bin/python tests/manual_test_webapp.py`
2. Navigate to: http://localhost:5001/logging/logs
3. Verify:
   - Tabs appear for each log file
   - Tables display log entries
   - Search works across columns
   - Sorting works on each column
   - Pagination works
   - Tab switching redraws tables correctly

## Future Enhancements

- Add auto-refresh timer (optional, every N seconds)
- Column-specific search (DataTables SearchPanes)
- Export functionality (CSV, PDF)
- Log level filtering buttons
- Tail mode (auto-scroll to newest entries)
