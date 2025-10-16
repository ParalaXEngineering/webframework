# GridStack.js Installation

GridStack is used for the USER_DEFINED layout editor.

## Download Instructions

1. Go to: https://github.com/gridstack/gridstack.js/releases
2. Download the latest release (v10.x or newer)
3. Extract the following files to this directory:

   - `dist/gridstack.min.css` → `gridstack.min.css`
   - `dist/gridstack-all.min.js` → `gridstack-all.min.js`

## Alternative: CDN Links

If you prefer CDN, update `core.py` RESOURCES to use:
```python
'gridstack': {
    'css_cdn': ['https://cdn.jsdelivr.net/npm/gridstack@10/dist/gridstack.min.css'],
    'js_cdn': ['https://cdn.jsdelivr.net/npm/gridstack@10/dist/gridstack-all.min.js']
}
```

## License

GridStack.js is MIT licensed.
