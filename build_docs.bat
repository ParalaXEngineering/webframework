@echo off
REM Comprehensive documentation build script for Windows
REM This script handles both setup and building in one command

setlocal enabledelayedexpansion

echo ========================================
echo Paralax Web Framework - Documentation Builder
echo ========================================
echo.

REM Check if we're in the project root
if not exist "pyproject.toml" (
    echo Error: This script must be run from the project root directory!
    echo Please navigate to the webframework project root first.
    pause
    exit /b 1
)

REM ========================================
REM STEP 1: Setup/Verify Environment
REM ========================================
echo [1/3] Setting up environment...
echo.

REM Check for virtual environment
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_CMD=.venv\Scripts\python.exe"
    set "PIP_CMD=.venv\Scripts\pip.exe"
    echo Found virtual environment at .venv
) else if defined VIRTUAL_ENV (
    set "PYTHON_CMD=python"
    set "PIP_CMD=pip"
    echo Using active virtual environment: %VIRTUAL_ENV%
) else (
    echo No virtual environment found. Creating one...
    python -m venv .venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment!
        pause
        exit /b 1
    )
    set "PYTHON_CMD=.venv\Scripts\python.exe"
    set "PIP_CMD=.venv\Scripts\pip.exe"
    echo Created virtual environment at .venv
)

REM Check if Python executable exists and works
%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python executable not found or not working: %PYTHON_CMD%
    echo Please check your virtual environment setup.
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=*" %%i in ('%PYTHON_CMD% -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set PYTHON_VERSION=%%i
echo Using Python %PYTHON_VERSION%
echo.

REM Install/Update documentation dependencies
echo Installing/updating documentation dependencies...
%PIP_CMD% install -q -e .[docs]

if errorlevel 1 (
    echo Error: Failed to install dependencies!
    echo Please check your Python environment and try again.
    pause
    exit /b 1
)

echo Dependencies ready!
echo.

REM ========================================
REM STEP 2: Clean Previous Build
REM ========================================
echo [2/3] Cleaning previous build...
echo.

if exist "docs\build" (
    echo Removing old build directory...
    rmdir /s /q "docs\build" 2>nul
    if exist "docs\build" (
        echo Warning: Could not fully clean build directory
    ) else (
        echo Previous build cleaned successfully!
    )
) else (
    echo No previous build found (clean slate)
)
echo.

REM ========================================
REM STEP 3: Build Documentation
REM ========================================
echo [3/3] Building HTML documentation...
echo.

REM Change to docs directory
cd docs

REM Build documentation using sphinx-build directly with the venv Python
..\%PYTHON_CMD% -m sphinx -b html -W --keep-going -T source build\html 2>&1

if errorlevel 1 (
    echo.
    echo ========================================
    echo Build completed with warnings/errors
    echo ========================================
    echo.
    
    REM Check if index.html was still generated
    if exist "build\html\index.html" (
        echo Despite warnings, HTML files were generated.
        echo Location: %CD%\build\html\index.html
        echo.
        
        REM Ask user if they want to open it
        set /p "OPEN_BROWSER=Do you want to open the documentation? (Y/N): "
        if /i "!OPEN_BROWSER!"=="Y" (
            start "" "build\html\index.html"
        )
    ) else (
        echo Build failed - no HTML files generated!
        cd ..
        pause
        exit /b 1
    )
) else (
    echo.
    echo ========================================
    echo Documentation built successfully!
    echo ========================================
    echo.
    echo Location: %CD%\build\html\index.html
    echo.
    
    REM Automatically open in browser
    echo Opening documentation in browser...
    start "" "build\html\index.html"
)

REM Return to project root
cd ..

echo.
echo Done! Press any key to exit...
pause >nul
