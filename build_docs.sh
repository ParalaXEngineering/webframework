#!/bin/bash
# Comprehensive documentation build script for macOS/Linux
# This script handles both setup and building in one command

set -e  # Exit on any error

echo "========================================"
echo "Paralax Web Framework - Documentation Builder"
echo "========================================"
echo ""

# ========================================
# STEP 0: Determine Project Root
# ========================================
if [ -f "pyproject.toml" ]; then
    PROJECT_ROOT="$(pwd)"
elif [ -f "../pyproject.toml" ]; then
    PROJECT_ROOT="$(cd .. && pwd)"
else
    echo "Error: Cannot find project root (looking for pyproject.toml)"
    echo "Please run this script from the project root directory."
    exit 1
fi

cd "$PROJECT_ROOT"
echo "Project root: $PROJECT_ROOT"
echo ""

# ========================================
# STEP 1: Setup/Verify Environment
# ========================================
echo "[1/3] Setting up environment..."
echo ""

# Check for virtual environment
if [ -f ".venv/bin/python" ]; then
    PYTHON_CMD="$PROJECT_ROOT/.venv/bin/python"
    PIP_CMD="$PROJECT_ROOT/.venv/bin/pip"
    echo "Found virtual environment at .venv"
elif [ ! -z "$VIRTUAL_ENV" ]; then
    PYTHON_CMD="python"
    PIP_CMD="pip"
    echo "Using active virtual environment: $VIRTUAL_ENV"
else
    echo "No virtual environment found. Creating one..."
    python3 -m venv .venv
    PYTHON_CMD="$PROJECT_ROOT/.venv/bin/python"
    PIP_CMD="$PROJECT_ROOT/.venv/bin/pip"
    echo "Created virtual environment at .venv"
fi

# Verify Python executable works
if ! $PYTHON_CMD --version >/dev/null 2>&1; then
    echo "Error: Python executable not working: $PYTHON_CMD"
    exit 1
fi

# Check Python version
python_version=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Using Python $python_version"
echo ""

# Install/Update documentation dependencies
echo "Installing/updating documentation dependencies..."
$PIP_CMD install -q -e .[docs]

if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies!"
    echo "Please check your Python environment and try again."
    exit 1
fi

echo "Dependencies ready!"
echo ""

# ========================================
# STEP 2: Validate Docstrings
# ========================================
echo "[2/4] Validating docstring completeness..."
echo ""

if [ -f "$PROJECT_ROOT/docs/check_docstrings.py" ]; then
    echo "Running docstring checker..."
    DOCSTRING_OUTPUT=$($PYTHON_CMD "$PROJECT_ROOT/docs/check_docstrings.py" 2>&1)
    DOCSTRING_ERRORS=$(echo "$DOCSTRING_OUTPUT" | grep -E "SUMMARY: [1-9]" || echo "")
    
    if [ ! -z "$DOCSTRING_ERRORS" ]; then
        echo "⚠️  Docstring issues found:"
        echo "$DOCSTRING_OUTPUT"
        echo ""
        echo "Warning: Some functions are missing documentation."
        echo "Continuing with build..."
    else
        echo "✅ All docstrings validated successfully!"
    fi
else
    echo "ℹ️  Docstring checker not found, skipping validation"
fi
echo ""

# ========================================
# STEP 3: Clean Previous Build
# ========================================
echo "[3/4] Cleaning previous build..."
echo ""

if [ -d "$PROJECT_ROOT/docs/build" ]; then
    echo "Removing old build directory..."
    rm -rf "$PROJECT_ROOT/docs/build"
    echo "Previous build cleaned successfully!"
else
    echo "No previous build found (clean slate)"
fi
echo ""

# ========================================
# STEP 4: Build Documentation
# ========================================
echo "[4/4] Building HTML documentation..."
echo ""

# Change to docs directory
cd "$PROJECT_ROOT/docs"

# Build documentation with comprehensive warning filtering
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
fi

# Check if build was successful
if [ -f "build/html/index.html" ]; then
    echo ""
    echo "========================================"
    echo "Documentation built successfully!"
    echo "========================================"
    echo ""
    echo "📍 Location: $PROJECT_ROOT/docs/build/html/index.html"
    echo ""
    
    # Open documentation in browser (macOS)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "🌐 Opening documentation in browser..."
        open "build/html/index.html"
    else
        echo "💡 Open build/html/index.html in your browser to view the documentation."
    fi
    
    if [ ! -z "$FILTERED_OUTPUT" ]; then
        echo ""
        echo "Note: Build completed with some warnings (see above)"
    fi
else
    echo ""
    echo "========================================"
    echo "Documentation build failed!"
    echo "========================================"
    echo ""
    echo "Check the output above for errors."
    exit 1
fi