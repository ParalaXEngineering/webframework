# Vendor Library Updates

This project includes several third-party JavaScript/CSS libraries in `webengine/assets/vendors/` for offline use.

## Automatic Update Script

Use the `update_vendors.sh` script to automatically download the latest versions of all vendor libraries:

```bash
./update_vendors.sh
```

### What Gets Updated

The script automatically fetches the latest versions from npm/CDN for:

- **GridStack** - Drag-and-drop grid layout library
- **jQuery** - JavaScript utility library
- **DataTables** - Advanced table plugin
- **FullCalendar** - Calendar/scheduling library
- **Highlight.js** - Syntax highlighting
- **Perfect Scrollbar** - Custom scrollbar styling
- **SweetAlert2** - Beautiful alert/modal dialogs
- **Material Design Icons** - Icon font
- **FilePond** - File upload library (with plugins)
- **TinyMCE** - Rich text editor

### How It Works

1. Queries npm registry API to get the latest version of each package
2. Downloads minified files from jsDelivr CDN
3. Places files in appropriate subdirectories under `webengine/assets/vendors/`
4. Reports the installed versions at the end

### Manual Updates

If you need to use a specific version instead of the latest:

1. Edit `update_vendors.sh`
2. Change the version in the `get_latest_version` call to a hardcoded version string
3. Run the script

Example:
```bash
# Instead of:
GRIDSTACK_VERSION=$(get_latest_version "gridstack")

# Use:
GRIDSTACK_VERSION="12.3.3"
```

### Requirements

- `curl` - for downloading files
- `grep` - for parsing JSON responses
- Internet connection

### Notes

- The script uses jsDelivr CDN which mirrors npm packages
- All files are downloaded as minified versions for production use
- TinyMCE may require additional files/themes - download manually if needed
- Material Design Icons includes web font files (woff2, woff, ttf)

### Troubleshooting

If a download fails:
1. Check your internet connection
2. Verify the package exists on npm: `https://www.npmjs.com/package/<package-name>`
3. Check jsDelivr is accessible: `https://cdn.jsdelivr.net/`
4. Run with verbose output: `bash -x ./update_vendors.sh`
