#!/bin/bash
# Build Sphinx documentation on macOS/Linux

set -e  # Exit on any error

echo "Building Sphinx documentation..."

# Determine the project root directory  
if [ -f "pyproject.toml" ]; then
    PROJECT_ROOT="$(pwd)"
elif [ -f "../pyproject.toml" ]; then
    PROJECT_ROOT="$(dirname $(pwd))"
else
    echo "Error: Cannot find project root (looking for pyproject.toml)"
    echo "Please run this script from the project root or docs directory."
    exit 1
fi

echo "Project root: $PROJECT_ROOT"

# Get the Python executable path
if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON_CMD="$PROJECT_ROOT/.venv/bin/python"
    echo "Using virtual environment Python: $PYTHON_CMD"
elif [ ! -z "$VIRTUAL_ENV" ]; then
    PYTHON_CMD="python"
    echo "Using active virtual environment Python"
else
    echo "Error: No virtual environment found!"
    echo "Please run setup_docs.sh first or activate your virtual environment."
    exit 1
fi

# Verify Python executable works
if ! $PYTHON_CMD --version >/dev/null 2>&1; then
    echo "Error: Python executable not working: $PYTHON_CMD"
    exit 1
fi

# Change to docs directory
cd "$PROJECT_ROOT/docs"

# Clean previous build
echo "Cleaning previous build..."
rm -rf build/

# Build documentation with comprehensive warning filtering
echo "Building HTML documentation..."

# Capture build output and filter warnings
BUILD_OUTPUT=$($PYTHON_CMD -m sphinx \
    -b html \
    -W --keep-going \
    -T \
    source build/html \
    2>&1) || BUILD_FAILED=1

# Filter out expected/normal warnings
FILTERED_OUTPUT=$(echo "$BUILD_OUTPUT" | grep -v -E "(duplicate object description|WARNING: duplicate|autosummary: stub file not found|toctree contains reference to document|more than one target found for cross-reference)" | grep -E "(ERROR|WARNING)" || echo "")

# Show only real warnings/errors
if [ ! -z "$FILTERED_OUTPUT" ]; then
    echo "⚠️  Remaining warnings/errors:"
    echo "$FILTERED_OUTPUT"
    echo ""
else
    echo "✅ Build completed with no significant warnings!"
fi

# Check if build was successful
if [ -f "build/html/index.html" ] && [ -z "$BUILD_FAILED" ]; then
    echo ""
    echo "✅ Documentation built successfully!"
    echo "📍 Location: $PROJECT_ROOT/docs/build/html/index.html"
    echo ""
    
    # Open documentation in browser (macOS)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "🌐 Opening documentation in browser..."
        open "build/html/index.html"
    else
        echo "💡 Open build/html/index.html in your browser to view the documentation."
    fi
else
    echo "❌ Documentation build failed!"
    echo "Check the output above for errors."
    exit 1
fi