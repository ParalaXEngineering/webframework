# Example Website Management Scripts

This document describes the automation scripts for managing the `example_website` demonstration project.

## Overview

The ParalaX Web Framework includes automation scripts to quickly create and manage a working example website that demonstrates proper framework usage as a git submodule.

## Files

- `manage_example_website.bat` - Windows batch script
- `manage_example_website.sh` - Linux/macOS shell script  
- `create_example_files.py` - Python helper script (creates file content)

## Windows: manage_example_website.bat

### Usage

```cmd
manage_example_website.bat [command]
```

### Commands

- `create` - Create the example website
- `delete` - Delete the example website
- `status` - Show status of example website
- `help` - Show help
- *(no command)* - Interactive menu

### Examples

```cmd
REM Create example
manage_example_website.bat create

REM Check status
manage_example_website.bat status

REM Delete example
manage_example_website.bat delete

REM Interactive menu
manage_example_website.bat
```

### Features

- **Auto-discovery**: Automatically detects framework root
- **Junction creation**: Creates Windows junction to framework (no admin required)
- **Error handling**: Checks for existing examples, validates operations
- **Interactive mode**: Menu-driven interface when run without arguments

## Linux/macOS: manage_example_website.sh

### Usage

```bash
./manage_example_website.sh [command]
```

### Commands

Same as Windows version (create, delete, status, help)

### Examples

```bash
# Make executable (first time only)
chmod +x manage_example_website.sh

# Create example
./manage_example_website.sh create

# Check status
./manage_example_website.sh status

# Delete example
./manage_example_website.sh delete

# Interactive menu
./manage_example_website.sh
```

### Features

- **Colored output**: Uses ANSI colors for better readability
- **Symbolic links**: Creates symlink to framework
- **Cross-platform**: Works on Linux, macOS, WSL

## Python Helper: create_example_files.py

This script is called by the batch/shell scripts to generate file content. It avoids complex escaping issues in shell scripts.

### Usage (internal)

```python
python create_example_files.py <example_directory>
```

Creates:
- `website/site_conf.py` - Site configuration class
- `website/config.json` - JSON configuration
- `website/pages/home.py` - Home page blueprint
- `main.py` - Application entry point
- `README.md` - Project documentation

## Created Example Structure

```
example_website/
├── main.py                    # Entry point
├── README.md                  # Documentation
├── website/
│   ├── __init__.py
│   ├── site_conf.py          # ExampleSiteConf class
│   ├── config.json           # Configuration
│   ├── pages/
│   │   ├── __init__.py
│   │   └── home.py           # Home routes
│   └── modules/
│       └── __init__.py
└── submodules/
    └── framework/            # Junction/symlink to framework
```

## Testing the Example

After creation:

```bash
cd example_website
python main.py
```

Visit http://localhost:5001

## Troubleshooting

### Windows: Junction Creation Failed

If you see "WARNING: Could not create junction":

```cmd
cd example_website\submodules
mklink /J framework "C:\path\to\framework"
```

### Linux/macOS: Symlink Issues

Ensure script is executable:

```bash
chmod +x manage_example_website.sh
```

### Python Import Errors

Ensure you're running from the example_website directory and the junction/symlink exists:

```bash
cd example_website
ls -la submodules/framework  # Should show link
python main.py
```

## Notes

- The example demonstrates the **correct** way to use ParalaX as a git submodule
- Junction (Windows) and symlink (Linux) allow the example to reference the framework
- The Python helper script avoids batch escaping issues with special characters
- All scripts use auto-discovery to find the framework root

## For Framework Developers

To add new files to the example:

1. Edit `create_example_files.py`
2. Add a new `create_xxx()` function
3. Call it from `main()` function
4. Files are automatically created when scripts run

The batch/shell scripts handle directory structure and junctions/symlinks.
