# ParalaX Web Framework

A robust Flask-based web framework designed for building tool management and monitoring applications with real-time capabilities.

## 🌟 Overview

ParalaX Web Framework simplifies the development of web applications that require:
- **Real-time updates** via WebSocket (Flask-SocketIO)
- **Background task management** with threaded actions and progress tracking
- **User authentication & authorization** with role-based permissions
- **Dynamic UI generation** using the powerful Displayer system
- **Modular architecture** that scales from simple tools to complex applications

Whether you're building a monitoring dashboard, a control panel, or a data management interface, ParalaX provides the foundation you need.

## ✨ Key Features

- 🚀 **Flask-based Core**: Built on Flask with Jinja2 templating for flexibility
- 🔐 **Authentication System**: Role-based access control with permission management
- 🔄 **Real-time Updates**: WebSocket support via Flask-SocketIO for live page updates
- ⚙️ **Background Tasks**: Thread management system for long-running operations
- 🎨 **Dynamic UI System**: Generate forms, cards, and layouts programmatically
- 📦 **Modular Design**: Extensible architecture supporting both standalone and submodule usage
- 📊 **Built-in Logging**: Comprehensive logging with per-thread console output
- 🧪 **Testing Support**: Full pytest integration with test fixtures

## 📋 Prerequisites

Before installing, ensure you have:
- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

## 🚀 Installation

### Method 1: Standalone Installation (Recommended for new users)

Perfect for trying out the framework or developing standalone applications.

```bash
# Clone the repository
git clone https://github.com/ParalaXEngineering/webframework.git
cd webframework

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate   # On Windows

# Install the framework in development mode
pip install -e .

# Run the demo application
python tests/manual_test_webapp.py
```

The demo app starts on `http://localhost:5001` and showcases various framework features.

### Method 2: As a Git Submodule

Ideal for integrating the framework into your existing project.

```bash
# In your project root directory
git submodule add https://github.com/ParalaXEngineering/webframework.git submodules/framework
git submodule update --init --recursive

# Install dependencies
pip install -r submodules/framework/requirements.txt
```

Then in your application:

```python
from flask import Flask
from submodules.framework.src.main import setup_app

app = Flask(__name__)
setup_app(app)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
```

### Optional Development Tools

```bash
# Install development dependencies (pytest, coverage, etc.)
pip install -e .[dev]

# Install documentation tools (Sphinx, theme, extensions)
pip install -e .[docs]
```

## 🏃 Quick Start Guide

### Your First Application

Here's a minimal example to get you started:

```python
from flask import Flask
from src.main import setup_app
from src.modules.displayer import Displayer, DisplayerItemText

# Create and configure Flask app
app = Flask(__name__)
app.secret_key = "your-secret-key-change-this"

# Initialize the framework
setup_app(app)

# Create a simple page
@app.route("/")
def home():
    disp = Displayer()
    
    # Add a module (card/form container)
    module = {"id": "welcome", "title": "Welcome"}
    disp.add_generic(module)
    
    # Add content to the module
    item = DisplayerItemText("Hello from ParalaX Framework!")
    disp.add_display_item(item)
    
    # Render the page
    return disp.display()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
```

Visit `http://localhost:5001` to see your page!

### Adding Background Tasks

Create a custom threaded action for long-running operations:

```python
from src.modules.threaded.threaded_action import Threaded_action
import time

class MyBackgroundTask(Threaded_action):
    """Example background task with progress tracking"""
    
    m_default_name = "My Task"
    m_type = "custom_task"
    
    def action(self):
        """The main work happens here"""
        self.console_write("Task started...")
        
        for i in range(100):
            # Simulate work
            time.sleep(0.1)
            
            # Update progress (0-100)
            self.m_running_state = i
            
            # Write to console (visible in UI)
            if i % 10 == 0:
                self.console_write(f"Progress: {i}%")
        
        self.console_write("Task completed!", level="SUCCESS")

# In your route handler:
@app.route("/start_task")
def start_task():
    task = MyBackgroundTask()
    task.start()
    return "Task started!"
```

## 📁 Project Structure

Understanding the framework's organization:

```
webframework/
├── src/                          # Core framework source code
│   ├── main.py                  # Flask app initialization and setup
│   ├── modules/                 # Core modules
│   │   ├── action.py           # Base action class
│   │   ├── site_conf.py        # Site configuration
│   │   ├── displayer/          # UI generation system
│   │   │   ├── displayer.py   # Main displayer class
│   │   │   ├── items/         # Display items (buttons, inputs, etc.)
│   │   │   └── layout.py      # Layout management
│   │   ├── threaded/          # Thread management
│   │   │   ├── threaded_action.py
│   │   │   └── threaded_manager.py
│   │   ├── scheduler/         # Real-time update system
│   │   ├── auth/              # Authentication system
│   │   └── utilities.py       # Helper functions
│   └── pages/                  # Built-in pages (login, admin, etc.)
├── templates/                   # Jinja2 HTML templates
├── webengine/                   # Static assets
│   └── assets/
│       ├── css/                # Stylesheets
│       ├── js/                 # JavaScript files
│       └── images/             # Image assets
├── tests/                       # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── manual_test_webapp.py  # Demo application
├── docs/                        # Sphinx documentation
│   └── source/                 # Documentation source files
├── pyproject.toml              # Project configuration
├── pytest.ini                  # Pytest configuration
└── README.md                   # This file
```

### Key Components Explained

- **main.py**: Entry point that initializes Flask and registers all blueprints
- **displayer/**: System for building UI programmatically without writing HTML
- **threaded/**: Framework for running background tasks with progress tracking
- **scheduler/**: Pushes real-time updates to connected clients via WebSocket
- **auth/**: Role-based permission system for securing your application
- **pages/**: Pre-built pages (login, settings, admin) that you can use or customize

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

## 🧪 Testing

The framework includes a comprehensive test suite.

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/unit/ -v              # Unit tests only
pytest tests/integration/ -v       # Integration tests only

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_scheduler.py -v
```

### Manual Testing

A demo web application is provided for manual testing:

```bash
# Make sure you're in the virtual environment
source .venv/bin/activate

# Run the demo app
python tests/manual_test_webapp.py
```

The demo showcases:
- Display system components (buttons, forms, layouts)
- Threading and background tasks
- Real-time updates via WebSocket
- Authentication and permissions
- Workflow management

Visit `http://localhost:5001` after starting the demo.

## 🔧 Configuration

### Basic Configuration

```python
from flask import Flask
from src.main import setup_app
from src.modules import site_conf

app = Flask(__name__)
app.config.update(
    SECRET_KEY='your-secret-key-here',
    SESSION_TYPE='filesystem',
    DEBUG=True
)

setup_app(app)

# Customize site configuration
site_conf.site_conf_obj.app_details(
    name="My Application",
    version="1.0.0",
    icon="rocket",  # Bootstrap icon name
    footer="© 2025 Your Company"
)
```

### Adding Custom Pages

```python
from flask import Blueprint
from src.modules.displayer import Displayer

# Create a blueprint
custom_bp = Blueprint('custom', __name__)

@custom_bp.route('/custom')
def custom_page():
    disp = Displayer()
    # Build your page...
    return disp.display()

# Register the blueprint
app.register_blueprint(custom_bp)
```

## 🎯 Common Use Cases

### Creating a Dashboard

```python
from src.modules.displayer import (
    Displayer, DisplayerLayout, Layouts,
    DisplayerItemBadge, DisplayerItemCard
)

@app.route("/dashboard")
def dashboard():
    disp = Displayer()
    disp.add_generic({"title": "System Dashboard"})
    
    # Create a horizontal layout with 3 columns
    layout = DisplayerLayout(Layouts.HORIZONTAL, columns=[4, 4, 4])
    disp.add_master_layout(layout)
    
    # Add metric cards
    disp.add_display_item(
        DisplayerItemBadge("CPU Usage", value="45%", color="success"),
        column=0
    )
    disp.add_display_item(
        DisplayerItemBadge("Memory", value="2.1GB", color="info"),
        column=1
    )
    disp.add_display_item(
        DisplayerItemBadge("Disk", value="78%", color="warning"),
        column=2
    )
    
    return disp.display()
```

### Implementing Authentication

```python
from src.modules.auth.auth_manager import auth_manager
from flask import session, redirect, url_for

# Protect a route
@app.route("/admin")
def admin_page():
    username = session.get('username')
    if not username:
        return redirect(url_for('auth.login'))
    
    # Check permissions
    if not auth_manager.has_permission(username, 'Admin', 'view'):
        return "Access Denied", 403
    
    # ... render admin page
```

## 🤝 Contributing

Contributions are welcome! The framework is designed to be extended.

### Adding New Display Items

Create custom UI components by extending `DisplayerItem`:

```python
from src.modules.displayer.items.base_item import DisplayerItem

class DisplayerItemMyWidget(DisplayerItem):
    def __init__(self, label, **kwargs):
        super().__init__(label, "my_widget", **kwargs)
        # Your custom logic
```

### Creating Custom Actions

Extend `Threaded_action` for background tasks:

```python
from src.modules.threaded.threaded_action import Threaded_action

class MyCustomAction(Threaded_action):
    m_default_name = "My Action"
    m_required_permission = "MyModule"  # Optional permission check
    
    def action(self):
        # Your task logic here
        pass
```

## 📖 Learn More

- **Full Documentation**: `docs/build/html/index.html` (build first)
- **Demo Application**: `tests/manual_test_webapp.py`
- **API Reference**: See `docs/source/framework_classes.rst`
- **Examples**: Check `tests/` directory for usage patterns

## 🐛 Troubleshooting

### Common Issues

**"Flask is not available"**
```bash
pip install flask flask-socketio flask-session
```

**Port already in use**
```python
app.run(debug=True, host="0.0.0.0", port=5002)  # Use different port
```

**Import errors**
- Ensure you're in the virtual environment: `source .venv/bin/activate`
- Reinstall in development mode: `pip install -e .`

**Tests failing**
- Tests must run in order (configured in `pytest.ini`)
- Ensure all dependencies are installed: `pip install -e .[dev]`

## 📄 License

[Your License Here]

## 👥 Authors

ParalaX Engineering

---

**Ready to build?** Start with the [Quick Start Guide](#-quick-start-guide) above or dive into the full documentation!