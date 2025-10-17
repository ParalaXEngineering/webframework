# GridStack.js Installation

GridStack is used for the USER_DEFINED layout editor.

## Local Files (For Offline Use)

The required files have been downloaded and are ready to use:
- `gridstack.min.css` - GridStack styles
- `gridstack-all.min.js` - GridStack library (UMD bundle for browser use)

**Note:** The file `gridstack.min.js` is an ES6 module and **cannot** be used in browsers directly. 
Always use `gridstack-all.min.js` which is the bundled UMD version.

## Re-download Instructions

If you need to update GridStack, run:
```bash
./download_gridstack.sh
```

Or manually download from:
1. Go to: https://cdn.jsdelivr.net/npm/gridstack@10.3.1/dist/
2. Download:
   - `gridstack.min.css` → `gridstack.min.css`
   - `gridstack-all.min.js` → `gridstack-all.min.js` (NOT gridstack.min.js!)

## Current Configuration

Local files are configured in `src/modules/displayer/core.py`:
```python
'gridstack': {
    'css': ['vendors/gridstack/gridstack.min.css', 'css/gridstack-bootstrap.css'],
    'js': ['vendors/gridstack/gridstack-all.min.js', 'js/user-defined-layout-editor.js']
}
```

## License

GridStack.js is MIT licensed.
