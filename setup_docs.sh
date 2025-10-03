#!/bin/bash
# Setup script for Sphinx documentation on macOS/Linux

set -e  # Exit on any error

echo "Setting up Sphinx documentation environment..."

# Check if we're in the project root
if [ ! -f "pyproject.toml" ]; then
    echo "Error: This script must be run from the project root directory!"
    echo "Please navigate to the webframework project root first."
    exit 1
fi

# Get the Python executable path
if [ -f ".venv/bin/python" ]; then
    PYTHON_CMD="$(pwd)/.venv/bin/python"
    PIP_CMD="$(pwd)/.venv/bin/pip"
    echo "Found virtual environment at .venv"
elif [ ! -z "$VIRTUAL_ENV" ]; then
    PYTHON_CMD="python"
    PIP_CMD="pip"
    echo "Using active virtual environment: $VIRTUAL_ENV"
else
    echo "No virtual environment found. Creating one..."
    python3 -m venv .venv
    PYTHON_CMD="$(pwd)/.venv/bin/python"
    PIP_CMD="$(pwd)/.venv/bin/pip"
    echo "Created virtual environment at .venv"
fi

# Check if Python executable exists and works
if ! $PYTHON_CMD --version >/dev/null 2>&1; then
    echo "Error: Python executable not found or not working: $PYTHON_CMD"
    echo "Please check your virtual environment setup."
    exit 1
fi

# Check Python version
python_version=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Using Python $python_version"

# Install documentation dependencies
echo "Installing documentation dependencies..."
$PIP_CMD install -e .[docs]

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Setup completed successfully!"
    echo ""
    echo "To build the documentation:"
    if [ -f ".venv/bin/python" ] && [ -z "$VIRTUAL_ENV" ]; then
        echo "  Run: ./build_docs.sh"
        echo ""
        echo "Or manually:"
        echo "  1. Activate the virtual environment: source .venv/bin/activate"
        echo "  2. Run the build script: ./build_docs.sh"
    else
        echo "  Run: ./build_docs.sh"
    fi
    echo ""
    echo "The generated documentation will be in docs/build/html/"
    echo "Open docs/build/html/index.html in your browser to view it."
else
    echo ""
    echo "❌ Error: Failed to install dependencies!"
    echo "Please check your Python environment and try again."
    exit 1
fi
