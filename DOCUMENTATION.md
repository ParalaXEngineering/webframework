# Documentation System

This document describes the documentation system for the ParalaX Web Framework.

## Overview

The documentation is built using **Sphinx**, a powerful documentation generator that creates professional HTML documentation from reStructuredText (RST) and Markdown files, along with automatic API documentation extracted from Python docstrings.

## Quick Start

### Setup (First Time Only)

```bash
./setup_docs.sh
```

This will:
- Check for or create a virtual environment
- Install Sphinx and all documentation dependencies
- Prepare the environment for building docs

### Build Documentation

```bash
./build_docs.sh
```

This will:
- Clean previous builds
- Generate HTML documentation from source files
- Open the documentation in your browser (on macOS)

The generated documentation is located at: `docs/build/html/index.html`

## Documentation Structure

```
docs/
├── source/                    # Documentation source files
│   ├── conf.py               # Sphinx configuration
│   ├── index.rst             # Main documentation page
│   ├── getting_started.rst   # Installation and quick start guide
│   ├── framework.rst         # Framework architecture overview
│   ├── framework_classes.rst # Core class reference
│   ├── api_modules.rst       # Complete API documentation
│   ├── images/               # Documentation images
│   └── legacy/               # Legacy documentation (archived)
├── build/                     # Generated documentation (git-ignored)
│   └── html/                 # HTML output
├── Makefile                   # Build automation (Unix)
└── make.bat                   # Build automation (Windows)
```

## Documentation Contents

### 1. Getting Started (`getting_started.rst`)
- Installation instructions (standalone and submodule)
- Prerequisites and dependencies
- Quick start examples
- Project structure overview
- Configuration guide
- Troubleshooting

### 2. Framework Architecture (`framework.rst`)
- Core component descriptions
- Web engine overview
- Scheduler system
- Thread management
- Display system
- Access control
- Utilities and helpers
- File structure
- Import strategy
- Best practices

### 3. Framework Classes (`framework_classes.rst`)
- Core classes reference
- Access Manager
- Site Configuration
- Thread Manager
- Action classes
- Scheduler
- Display system components

### 4. API Modules (`api_modules.rst`)
- Complete API reference for all modules
- Automatically generated from docstrings
- Includes all public functions and classes

## Writing Documentation

### Adding New Pages

1. Create a new `.rst` file in `docs/source/`
2. Add it to the `toctree` in `index.rst`
3. Write content using reStructuredText syntax
4. Rebuild documentation

Example:
```rst
My New Page
===========

Introduction
------------

This is a new documentation page.

Code Example
------------

.. code-block:: python

   from src import utilities
   
   # Your code here
```

### Documenting Code

Use docstrings in your Python code. Sphinx will automatically extract them:

```python
class MyClass:
    """Brief description of the class.
    
    Longer description with more details about what this class does
    and how to use it.
    
    :param name: The name parameter
    :type name: str
    :param value: The value parameter
    :type value: int
    """
    
    def my_method(self, arg1, arg2):
        """Brief description of the method.
        
        :param arg1: First argument
        :type arg1: str
        :param arg2: Second argument
        :type arg2: int
        :return: Description of return value
        :rtype: bool
        """
        pass
```

Or use Google/NumPy style (also supported):

```python
def my_function(arg1, arg2):
    """Brief description of function.
    
    Args:
        arg1 (str): First argument description
        arg2 (int): Second argument description
        
    Returns:
        bool: Description of return value
        
    Raises:
        ValueError: When arg1 is empty
    """
    pass
```

## Sphinx Configuration

Key configuration in `docs/source/conf.py`:

- **Extensions**:
  - `sphinx.ext.autodoc`: Auto-generate API docs from docstrings
  - `sphinx.ext.napoleon`: Support Google/NumPy docstring styles
  - `sphinx.ext.viewcode`: Add links to source code
  - `sphinx.ext.intersphinx`: Link to external documentation
  - `sphinx_rtd_theme`: Read the Docs theme
  - `myst_parser`: Markdown support

- **Autodoc Settings**: Configured to include all members by default
- **Mock Imports**: Optional dependencies are mocked during doc build
- **Theme Options**: Navigation depth, collapsible sections, etc.

## Manual Building

If you prefer to build manually:

```bash
# Install dependencies
pip install -r requirements-docs.txt

# Build
cd docs
sphinx-build -b html source build/html

# Or use make
make clean
make html
```

On Windows:
```batch
cd docs
make.bat clean
make.bat html
```

## Continuous Integration

To build documentation in CI/CD:

```yaml
# Example for GitHub Actions
- name: Install documentation dependencies
  run: pip install -r requirements-docs.txt

- name: Build documentation
  run: |
    cd docs
    make html
    
- name: Deploy to GitHub Pages
  uses: peaceiris/actions-gh-pages@v3
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./docs/build/html
```

## Troubleshooting

### Build Fails with Import Errors

If modules can't be imported during doc build:
1. Check that paths are correct in `conf.py`
2. Add missing packages to `autodoc_mock_imports` in `conf.py`
3. Ensure all dependencies are installed

### Warnings About Missing References

If you see warnings about missing cross-references:
- Check that class/function names are spelled correctly
- Verify the module is being documented
- Use full paths (e.g., `src.utilities.my_function`)

### Theme Not Loading

If the RTD theme doesn't load:
```bash
pip install --upgrade sphinx-rtd-theme
```

### Cached Content Issues

If changes don't appear:
```bash
cd docs
make clean
make html
```

## Best Practices

1. **Write docstrings for all public APIs**: Classes, functions, and methods
2. **Use consistent style**: Choose Google or NumPy style and stick to it
3. **Include examples**: Code examples help users understand usage
4. **Keep it updated**: Update docs when code changes
5. **Review generated docs**: Always check the HTML output
6. **Use appropriate markup**: RST for structure, code blocks for examples
7. **Link between pages**: Use cross-references to connect related content

## Resources

- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [reStructuredText Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)
- [Read the Docs Theme](https://sphinx-rtd-theme.readthedocs.io/)
- [Napoleon Extension](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html)
- [Autodoc Extension](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html)

## Maintenance

Regular documentation maintenance tasks:

1. **Update after major changes**: Framework updates, API changes
2. **Fix broken links**: Check for and fix dead links
3. **Update examples**: Ensure code examples still work
4. **Review warnings**: Address Sphinx build warnings
5. **Gather feedback**: Ask users what's unclear or missing
