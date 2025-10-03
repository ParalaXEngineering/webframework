@echo off
REM Setup script for Sphinx documentation on Windows

echo Setting up Sphinx documentation environment...

REM Check if we're in the project root
if not exist "pyproject.toml" (
    echo Error: This script must be run from the project root directory!
    echo Please navigate to the webframework project root first.
    pause
    exit /b 1
)

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

REM Install documentation dependencies
echo Installing documentation dependencies...
%PIP_CMD% install -e .[docs]

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Setup completed successfully!
    echo.
    echo To build the documentation:
    echo   1. Navigate to the docs directory: cd docs
    echo   2. Run the build command: make.bat html
    echo.
    echo Or use the single command: cd docs ^&^& make.bat html
    echo.
    echo The generated documentation will be in docs\build\html\
    echo Open docs\build\html\index.html in your browser to view it.
) else (
    echo.
    echo Error: Failed to install dependencies!
    echo Please check your Python environment and try again.
)

pause
