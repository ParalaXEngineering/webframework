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

## 📚 Documentation

Comprehensive documentation is available via Sphinx.

### Building the Documentation

```bash
# One-time setup (install dependencies)
pip install -e .[docs]

# Build documentation (macOS/Linux)
./build_docs.sh

# Build documentation (Windows)
cd docs
make.bat clean
make.bat html

# Manual build (any platform)
cd docs
sphinx-build -b html source build/html
```

View the generated documentation by opening `docs/build/html/index.html` in your browser.

### Documentation Contents

- **Getting Started**: Step-by-step installation and first application
- **Framework Architecture**: Deep dive into core components and their interactions
- **API Reference**: Complete class and method documentation
- **Tutorials**: Practical guides for common use cases
- **Examples**: Real-world code snippets and patterns

## 📚 Documentation

Comprehensive documentation is available:

```bash
# Build documentation
cd submodules/framework/docs
sphinx-build -b html source build/html
```

Or view online: [Documentation Link]

Key documentation sections:
- **Getting Started**: Step-by-step setup guide
- **Framework Architecture**: Understanding core components
- **API Reference**: Complete class and method documentation
- **Tutorials**: Practical guides for common tasks
- **Examples**: Real-world code snippets

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