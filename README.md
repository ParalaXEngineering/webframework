# ParalaX Web Framework

A robust Flask-based web framework designed for building web applications with real-time capabilities, background task management, and dynamic UI generation.

## 🌟 Overview

ParalaX Web Framework provides the foundation for building professional web applications that require:
- **Real-time updates** via WebSocket (Flask-SocketIO)
- **Background task management** with threaded actions and progress tracking
- **User authentication & authorization** with role-based permissions
- **Dynamic UI generation** using the powerful Displayer system
- **Modular architecture** that keeps your code separate from the framework

Perfect for building monitoring dashboards, control panels, data management interfaces, and custom web applications.

## ✨ Key Features

- 🚀 **Flask-based Core**: Built on Flask with Jinja2 templating
- 🔐 **Authentication System**: Role-based access control with permission management
- 🔄 **Real-time Updates**: WebSocket support via Flask-SocketIO for live updates
- ⚙️ **Background Tasks**: Thread management system for long-running operations
- 🎨 **Dynamic UI System**: Generate forms, cards, and layouts programmatically
- 📦 **Git Submodule Design**: Clean separation between framework and your code
- 📊 **Built-in Logging**: Comprehensive logging with per-thread console output
- 🧪 **Testing Support**: Full pytest integration with test fixtures

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git
- Virtual environment (recommended)

## 🚀 Quick Start: Create Your Website

The framework is designed to be used as a **Git submodule** in your website project. This keeps your website code separate from the framework.

### 1. Create Your Project Structure

```bash
# Create your website project
mkdir my_website
cd my_website
git init

# Create directory structure
mkdir -p website/pages website/modules submodules

# Create __init__.py files
touch website/__init__.py website/pages/__init__.py website/modules/__init__.py
```

### 2. Add Framework as Submodule

```bash
git submodule add https://github.com/ParalaXEngineering/webframework.git submodules/framework
git submodule update --init --recursive
```

### 3. Install Dependencies

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install framework dependencies
pip install -r submodules/framework/requirements.txt
```

### 4. Create Your Files

See the [example_website](example_website/) directory for a complete working example, or follow the detailed guide below.

## 📁 Project Structure

Your website project should have this structure:

```
my_website/
├── main.py                    # Application entry point
├── website/                   # Your website code
│   ├── __init__.py
│   ├── site_conf.py          # Site configuration (navigation, branding)
│   ├── config.json           # Optional config file
│   ├── pages/                # Your page blueprints
│   │   ├── __init__.py
│   │   └── home.py          # Example home page
│   └── modules/              # Your custom modules
│       └── __init__.py
└── submodules/
    └── framework/            # Git submodule (the framework)
```

### Key Files

**website/site_conf.py** - Define your site's navigation and settings:

```python
from submodules.framework.src.modules.site_conf import Site_conf

class MySiteConf(Site_conf):
    def __init__(self):
        super().__init__()
        self.m_app = {
            "name": "My Website",
            "version": "1.0.0",
            "icon": "rocket",
            "footer": "2025 © Your Company"
        }
        self.add_sidebar_title("Main")
        self.add_sidebar_section("Home", "house", "home")
```

**website/pages/home.py** - Create your pages:

```python
from flask import Blueprint
from submodules.framework.src.modules.displayer import Displayer, DisplayerItemText

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def index():
    disp = Displayer()
    disp.add_generic({"id": "welcome", "title": "Welcome"})
    disp.add_display_item(DisplayerItemText("Hello from my website!"))
    return disp.display()
```

**main.py** - Wire everything together:

```python
import sys, os

# Setup paths
project_root = os.path.dirname(os.path.abspath(__file__))
framework_root = os.path.join(project_root, 'submodules', 'framework')
sys.path.insert(0, project_root)
sys.path.insert(0, framework_root)
sys.path.insert(0, os.path.join(framework_root, 'src'))

# Import framework
from submodules.framework.src.main import app, setup_app
from submodules.framework.src.modules import site_conf
from website.site_conf import MySiteConf
from website.pages.home import home_bp

# Change to framework directory for templates
os.chdir(framework_root)

# Configure BEFORE setup_app
site_conf.site_conf_obj = MySiteConf()
site_conf.site_conf_app_path = framework_root

# Initialize framework
socketio = setup_app(app)

# Register your pages
app.register_blueprint(home_bp)

# Run
if __name__ == "__main__":
    socketio.run(app, debug=False, host='0.0.0.0', port=5001)
```

### Run Your Website

```bash
python main.py
```

Visit `http://localhost:5001`!

## 🔧 Accessing Configuration Settings

The framework provides a safe way to access configuration settings using the `get_config_or_error()` helper function from `utilities.py`. This function handles missing configuration keys gracefully and provides clear error messages to users.

### Why Use get_config_or_error()?

- **Error Handling**: Automatically catches `KeyError` exceptions when config keys are missing
- **User-Friendly**: Returns a properly formatted error page instead of crashing
- **Clean Code**: Supports retrieving multiple config values in a single call
- **Type Safety**: Clearer intent and better error messages

### Basic Usage

```python
from submodules.framework.src.modules.utilities import get_config_or_error
from submodules.framework.src.modules.settings import SettingsManager

# Get settings manager
settings_mgr = SettingsManager("config.json")
settings_mgr.load()

# Single config value
source, error = get_config_or_error(settings_mgr, "updates.source.value")
if error:
    return error  # Returns error page if config missing
# Use source safely here
```

### Multiple Config Values

For cleaner code when accessing multiple configuration values:

```python
# Get multiple values at once
configs, error = get_config_or_error(settings_mgr,
                                     "updates.address.value",
                                     "updates.user.value",
                                     "updates.password.value")
if error:
    return error

# Access values using dot-notation keys
address = configs["updates.address.value"]
user = configs["updates.user.value"]
password = configs["updates.password.value"]
```

### In Route Functions

Typical usage in a Flask route:

```python
@bp.route("/my_page", methods=["GET"])
def my_page():
    # Load all required config at once
    configs, error = get_config_or_error(get_settings_manager(),
                                         "section.key1.value",
                                         "section.key2.value")
    if error:
        return error  # Automatically renders error.j2 template
    
    # Use configs safely
    value1 = configs["section.key1.value"]
    value2 = configs["section.key2.value"]
    
    # ... rest of your route logic
```

### In Background Tasks

When using in threaded actions or background tasks:

```python
def action(self):
    configs, error = get_config_or_error(get_settings_manager(),
                                         "server.host.value",
                                         "server.port.value")
    if error:
        if self.m_logger:
            self.m_logger.error("Failed to get server config")
        return  # Exit gracefully
    
    host = configs["server.host.value"]
    port = configs["server.port.value"]
    # ... continue with your task
```

### Configuration Path Format

Configuration paths use dot notation to navigate nested dictionaries:
- Format: `"topic.key.value"`
- Example: `"updates.source.value"` accesses `config["updates"]["source"]["value"]`

This approach is used throughout `updater.py` and `packager.py` for safe configuration access.

## 📝 Optional Feature Configurations

The framework provides a system for managing configuration sections that are only needed when specific features are enabled. This keeps your `config.json` clean and only includes settings relevant to your enabled features.

### How It Works

When you enable a feature like `enable_updater()` or `enable_bug_tracker()`, the framework automatically adds the necessary configuration sections to your `config.json` if they don't already exist. Default values are defined in `src/modules/default_configs.py`.

### Supported Optional Configurations

- **Bug Tracker (Redmine)**: Requires `enable_bug_tracker()`
  - Redmine server credentials and connection settings
  
- **Updater/Packager**: Requires `enable_updater()` or `enable_packager()`
  - FTP or folder-based maintenance server configuration
  - Update source, credentials, and paths

### Usage in site_conf.py

```python
from submodules.framework.src.modules.site_conf import Site_conf

class MySiteConf(Site_conf):
    def __init__(self):
        super().__init__()
        
        # Enable features - this automatically adds their config sections
        self.enable_bug_tracker()  # Adds 'redmine' section to config
        self.enable_updater()      # Adds 'updates' section to config
        self.enable_packager()     # Also uses 'updates' section
```

### Configuration Merging Behavior

When a feature is enabled:

1. **First time**: The entire default configuration section is added to `config.json`
2. **Subsequent runs**: Only missing keys are added (existing values are preserved)
3. **Persistent settings**: Values marked `"persistent": true` survive updates
4. **User modifications**: Your custom values are never overwritten

### Example Configuration Sections

**Redmine (Bug Tracker)**:
```json
{
    "redmine": {
        "friendly": "Redmine credentials",
        "user": {
            "type": "string",
            "friendly": "User",
            "value": "",
            "persistent": true
        },
        "password": {
            "type": "string",
            "friendly": "Password",
            "value": "",
            "persistent": true
        },
        "address": {
            "type": "string",
            "friendly": "Address",
            "value": "https://redmine.example.com/",
            "persistent": true
        }
    }
}
```

**Updates (Updater/Packager)**:
```json
{
    "updates": {
        "friendly": "Maintenance server configuration",
        "source": {
            "type": "select",
            "friendly": "Source",
            "value": "FTP",
            "options": ["FTP", "Folder"],
            "persistent": false
        },
        "address": {
            "type": "string",
            "friendly": "FTP Address",
            "value": "",
            "persistent": true
        },
        "user": {
            "type": "string",
            "friendly": "FTP User",
            "value": "",
            "persistent": true
        },
        "password": {
            "type": "string",
            "friendly": "FTP Password",
            "value": "",
            "persistent": true
        }
    }
}
```

### Adding Custom Optional Configurations

You can add your own optional configurations in `default_configs.py`:

```python
# In src/modules/default_configs.py

MY_FEATURE_CONFIG = {
    "my_feature": {
        "friendly": "My Feature Settings",
        "api_key": {
            "type": "string",
            "friendly": "API Key",
            "value": "",
            "persistent": true
        }
    }
}

# Add to FEATURE_CONFIGS map
FEATURE_CONFIGS = {
    "bug_tracker": REDMINE_CONFIG,
    "updater": UPDATES_CONFIG,
    "packager": UPDATES_CONFIG,
    "my_custom_feature": MY_FEATURE_CONFIG,  # Your feature
}
```

Then in your site_conf, you can control when it appears:

```python
class MySiteConf(Site_conf):
    def __init__(self):
        super().__init__()
        
        # Add custom feature flag
        self.m_enable_my_custom_feature = True
        
        # The merge_optional_configs will check this flag
```

### Benefits

- **Clean config files**: Only see settings for features you use
- **Easy onboarding**: New users don't see overwhelming configuration
- **Automatic updates**: New features automatically add their settings
- **Version control friendly**: Minimal config diffs when adding features
- **User-friendly**: Settings page only shows relevant sections

## 🎯 Complete Example

See the [example_website](example_website/) directory for a fully working example project that demonstrates:
- Proper project structure
- Site configuration
- Custom pages
- Framework integration

You can run it:

```bash
cd example_website
python main.py
```

## 🔧 Framework Development

**Only for framework contributors**: If you're developing the framework itself (not building a website):

```bash
# Clone the framework repository
git clone https://github.com/ParalaXEngineering/webframework.git
cd webframework

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e .[dev]

# Run tests
pytest tests/ -v

# Run demo app
python tests/manual_test_webapp.py
```

## �️ Framework Manager

The framework includes a unified management tool that simplifies common tasks. The Framework Manager automatically detects and uses your virtual environment with Python 3.7+.

### Requirements

- Python 3.7 or higher (the script will auto-detect and use your `.venv` if available)
- `requests` library for vendor updates

### Usage

**Interactive Mode** (recommended for beginners):
```bash
python framework_manager.py
```

**Command Line Mode**:

```bash
# Update vendor libraries (jQuery, Bootstrap, etc.)
python framework_manager.py vendors

# Create example website
python framework_manager.py example --create

# Run example website
python framework_manager.py example --run

# Check example website status
python framework_manager.py example --status

# Delete example website
python framework_manager.py example --delete

# Build documentation
python framework_manager.py docs

# Get help
python framework_manager.py --help
python framework_manager.py example --help
```

### Features

**1. Vendor Management** (`vendors`)
- Downloads latest versions of all frontend libraries
- Includes: jQuery, GridStack, DataTables, FullCalendar, SweetAlert2, MDI icons, FilePond, TinyMCE, Highlight.js
- Automatic CDN fallback handling
- Shows version summary after update

**2. Example Website** (`example`)
- `--create`: Creates a complete example website with proper structure
- `--delete`: Safely removes the example website
- `--status`: Shows what files exist and their status
- `--run`: Launches the example website server
- Interactive menu for step-by-step guidance

**3. Documentation** (`docs`)
- Automatically sets up virtual environment
- Installs documentation dependencies
- Validates docstrings
- Builds Sphinx HTML documentation
- Opens result in your browser

### Python Version Handling

The Framework Manager is smart about Python versions:

- **Python 3.6 detected**: Automatically switches to `.venv` if available
- **Python 3.7+**: Runs directly with full features
- **No suitable Python**: Shows helpful error with instructions

Example output when running with Python 3.6:
```
======================================================================
ERROR: Python 3.7 or higher is required
======================================================================

Your Python version: 3.6.5

Checking for virtual environment with newer Python...
Found virtual environment: .venv\Scripts\python.exe
Restarting with venv Python...
```

### Cross-Platform Support

Works identically on:
- ✅ Windows (PowerShell, CMD)
- ✅ macOS
- ✅ Linux

The script handles all platform differences automatically (symlinks vs junctions, path separators, etc.)

## 📚 Documentation

Comprehensive API documentation is available via Sphinx.

### Quick Build

```bash
# Use the Framework Manager (recommended)
python framework_manager.py docs
```

This will:
1. Verify/create virtual environment
2. Install documentation dependencies
3. Validate docstrings
4. Build HTML documentation
5. Open in your browser automatically

### Manual Build

```bash
# Install dependencies
pip install -e .[docs]

# Build (any platform)
cd docs
sphinx-build -b html source build/html

# View
# Open docs/build/html/index.html in your browser
```

### Documentation Contents

- **Getting Started**: Step-by-step installation and first application
- **Framework Architecture**: Deep dive into core components and their interactions
- **API Reference**: Complete class and method documentation
- **Tutorials**: Practical guides for common use cases
- **Examples**: Real-world code snippets and patterns

## 🧪 Testing Your Website

```bash
# Run your website
python main.py

# Visit http://localhost:5001 and verify:
# - Home page loads
# - Navigation works
# - Your pages render correctly
```

To test the framework itself (for contributors):

```bash
cd submodules/framework
pytest tests/ -v
```

## ⚠️ Important Notes

### Working Directory
Your `main.py` must change to the framework directory so templates can be found:

```python
os.chdir(framework_root)  # Required before setup_app()
```

### Site Configuration Order
Always set site configuration BEFORE calling `setup_app()`:

```python
# 1. Set configuration
site_conf.site_conf_obj = MySiteConf()

# 2. Then setup
socketio = setup_app(app)

# 3. Then register blueprints
app.register_blueprint(home_bp)
```

### Form Data Parsing
Always use `util_post_to_json()` to handle form submissions:

```python
from submodules.framework.src.modules.utilities import util_post_to_json

@home_bp.route('/submit', methods=['POST'])
def submit():
    data_in = util_post_to_json(request.form.to_dict())
    my_data = data_in.get("module_id", {})
```

## 🐛 Troubleshooting

**Template Not Found Error**
- Ensure `os.chdir(framework_root)` is called before `setup_app()`

**Module Import Errors**
- Verify sys.path setup in `main.py`
- Check that submodule was initialized: `git submodule update --init`

**Form Values Are None**
- Use `util_post_to_json()` instead of `request.form.get()`

## 🤝 Contributing

Contributions to the framework are welcome! See the [contributing guide](CONTRIBUTING.md) for details.

For framework development:
1. Fork and clone the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

[Your License Here]

## 👥 Authors

ParalaX Engineering

---

**Ready to build?** Start with the [Quick Start Guide](#-quick-start-guide) above or dive into the full documentation!