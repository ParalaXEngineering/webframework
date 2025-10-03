# ParalaX Web Framework

A robust Flask-based web framework designed for display and management applications. This framework provides a comprehensive solution for building web applications with features like user management, threaded actions, real-time updates via WebSocket, and a rich display system.

## Features

- **Flask-based Architecture**: Built on the reliable Flask web framework
- **User Authentication & Authorization**: Complete user management system with group-based permissions
- **Real-time Communication**: WebSocket support via Flask-SocketIO for live updates
- **Threaded Actions**: Background task management with progress tracking
- **Rich Display System**: Flexible display components for building dynamic interfaces
- **Module System**: Extensible architecture for adding custom functionality
- **Template System**: Jinja2-based templating with pre-built components
- **Asset Management**: Integrated static asset handling
- **Logging**: Comprehensive logging system
- **Packaging & Updates**: Built-in packaging and update mechanisms

## Installation

### As a Standalone Framework

1. Clone or download the framework:
```bash
git clone <repository-url>
cd webframework
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the framework:
```bash
python run_standalone.py
```

The framework will start on `http://localhost:5001`

### As a Submodule

To use this framework as a submodule in your project:

1. Add as a submodule:
```bash
git submodule add <repository-url> submodules/framework
```

2. In your main application:
```python
from submodules.framework.src.main import app, setup_app

# Setup the framework
setup_app(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
```

### Using pip (if published)

```bash
pip install paralax-webframework
```

## Project Structure

```
webframework/
├── src/                    # Main source code
│   ├── __init__.py        # Package initialization
│   ├── main.py            # Flask app and main routes
│   ├── access_manager.py  # User authentication & authorization
│   ├── displayer.py       # Display system components
│   ├── scheduler.py       # Task scheduling and real-time updates
│   ├── threaded_action.py # Background task management
│   ├── threaded_manager.py# Thread pool management
│   ├── utilities.py       # Utility functions
│   ├── site_conf.py       # Site configuration
│   ├── workflow.py        # Workflow management
│   ├── settings.py        # Settings module
│   ├── common.py          # Common functionality
│   ├── updater.py         # Update management
│   ├── packager.py        # Package creation
│   ├── bug_tracker.py     # Bug tracking integration
│   ├── SFTPConnection.py  # SFTP functionality
│   └── User_defined_module.py # Base class for custom modules
├── templates/             # Jinja2 templates
├── webengine/            # Static assets (CSS, JS, images)
├── log_config.ini        # Logging configuration
├── run_standalone.py     # Standalone entry point
├── setup.py              # Package setup
├── requirements.txt      # Dependencies
└── README.md            # This file
```

## Quick Start

### Creating a Simple Application

```python
from src.main import app, setup_app
from src import site_conf, displayer

# Setup the framework
setup_app(app)

# Configure your application
site_conf.site_conf_obj.app_details(
    name="My App",
    version="1.0.0",
    icon="fa-home",
    footer="© 2025 My Company"
)

# Add a simple page
@app.route('/hello')
def hello():
    disp = displayer.Displayer()
    disp.add_display_item(
        displayer.DisplayerItemText("Hello, World!")
    )
    return disp.display()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
```

### Creating Custom Modules

```python
from src.User_defined_module import User_defined_module
from src import displayer

class MyCustomModule(User_defined_module):
    def __init__(self):
        super().__init__()
        self.m_name = "My Custom Module"
        self.m_icon = "fa-cog"
        
    def add_display(self, disp):
        disp.add_display_item(
            displayer.DisplayerItemText("Custom functionality here")
        )
        return disp
```

## Configuration

The framework uses several configuration mechanisms:

1. **Site Configuration**: Use `site_conf.py` to configure app details, menus, and modules
2. **Logging**: Configure via `log_config.ini`
3. **Flask Settings**: Standard Flask configuration in `main.py`

## Testing

The framework includes a comprehensive test suite using pytest.

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_startup.py -v

# Run with coverage (if pytest-cov is installed)
pytest tests/ --cov=src
```

### Test Structure

The test suite covers:
- **Startup tests**: Basic initialization and module imports
- **Import tests**: Standalone and submodule import modes
- **Core module tests**: Functionality of key classes and functions

All tests pass successfully, ensuring the framework works in both standalone and submodule modes.

## Documentation

The framework includes comprehensive Sphinx documentation.

### Building Documentation

#### Quick Start

```bash
# Setup documentation environment (first time only)
./setup_docs.sh

# Build the documentation
./build_docs.sh
```

The documentation will be generated in `docs/build/html/` and automatically open in your browser on macOS.

#### Manual Build

```bash
# Install documentation dependencies
pip install -r requirements-docs.txt
# or
pip install -e .[docs]

# Build the docs
cd docs
make clean
make html

# View the documentation
open build/html/index.html  # macOS
# or
xdg-open build/html/index.html  # Linux
```

#### On Windows

```batch
# Setup
setup_docs.bat

# Build
cd docs
make.bat clean
make.bat html
```

### Documentation Contents

The documentation includes:

- **Getting Started Guide**: Installation, configuration, and quick start
- **Framework Architecture**: Detailed explanation of core components
- **API Reference**: Complete API documentation for all modules
- **Class Reference**: Detailed class documentation with examples
- **Code Examples**: Practical examples for common use cases

### Updating Documentation

To update the documentation:

1. Edit RST files in `docs/source/`
2. Add docstrings to your Python code
3. Run `./build_docs.sh` to rebuild
4. Review the output in your browser

The documentation uses:
- **Sphinx**: Documentation generator
- **Read the Docs theme**: Professional appearance
- **MyST Parser**: Support for Markdown and reStructuredText
- **Autodoc**: Automatic API documentation from docstrings
- **Napoleon**: Google and NumPy style docstring support

## Development

### Adding New Features

1. Create new modules in the `src/` directory
2. Use relative imports (e.g., `from . import utilities`)
3. Follow the existing patterns for display components and threaded actions
4. Update this README with new functionality

### Debugging

- The framework includes comprehensive logging
- Use the standalone mode for easier debugging
- Flask debug mode is enabled by default in development

## Migration from Submodule-Only Usage

If you're migrating from the old submodule-only setup:

1. Update imports in your main application:
   ```python
   # Old way
   from submodules.framework.src.main import app
   
   # New way (still works)
   from submodules.framework.src.main import app, setup_app
   setup_app(app)  # Important: call setup_app
   ```

2. The framework can now run independently for testing

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]

## Support

[Add support information here]