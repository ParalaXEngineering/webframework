# ParalaX Web Framework

A robust Flask-based web framework for display and management applications featuring user management, real-time updates, threaded actions, and a modular architecture.

## Features

- Flask-based core with Jinja2 templating
- Group-based authentication and authorization
- WebSocket updates via Flask-SocketIO
- Threaded background actions with progress tracking
- Extensible module system and rich display components
- Integrated static asset management and logging
- Packaging and update tooling

## Installation

### Standalone usage

```bash
git clone <repository-url>
cd webframework
pip install -e .
python run_standalone.py
```

The app starts on `http://localhost:5001`.

### As a submodule

```bash
git submodule add <repository-url> submodules/framework
```

Use in your project:

```python
from submodules.framework.src.main import app, setup_app

setup_app(app)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
```

### Optional extras

```bash
pip install .[dev]
pip install .[docs]
```

## Quick Start

```python
from src.main import app, setup_app
from src import site_conf, displayer

setup_app(app)

site_conf.site_conf_obj.app_details(name="My App", footer="© 2025 My Company")

@app.route("/hello")
def hello():
    disp = displayer.Displayer()
    return disp.display()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
```

## Project Structure

```
webframework/
├── src/
├── templates/
├── webengine/
├── docs/
├── run_standalone.py
├── pyproject.toml
└── README.md
```

## Documentation

The docs live in `docs/` and are built with Sphinx.

```bash
# one-time setup
./setup_docs.sh
# build (Unix/macOS)
./build_docs.sh
# manual build
pip install .[docs]
cd docs
sphinx-build -b html source build/html
# Windows manual build
cd docs
make.bat clean
make.bat html
```

Generated HTML is at `docs/build/html/index.html`.

## Testing

```bash
pytest tests/ -v
pytest tests/test_startup.py -v
pytest tests/ --cov=src
```

Tests must run in the order defined in `conftest.py`.