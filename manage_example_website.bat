@echo off
REM ============================================================================
REM Example Website Manager for ParalaX Web Framework
REM
REM This script manages the example_website demonstration project.
REM Usage: manage_example_website.bat [create|delete|status]
REM ============================================================================

setlocal enabledelayedexpansion

REM Auto-discover framework root (script location)
set "FRAMEWORK_ROOT=%~dp0"
set "FRAMEWORK_ROOT=%FRAMEWORK_ROOT:~0,-1%"

set "EXAMPLE_DIR=%FRAMEWORK_ROOT%\example_website"

REM Parse command line argument
set "ACTION=%1"

if "%ACTION%"=="" (
    goto :MENU
)

if /i "%ACTION%"=="create" goto :CREATE
if /i "%ACTION%"=="delete" goto :DELETE
if /i "%ACTION%"=="status" goto :STATUS
if /i "%ACTION%"=="help" goto :HELP

echo Unknown command: %ACTION%
goto :HELP

REM ============================================================================
:MENU
REM ============================================================================
echo.
echo ============================================================================
echo   ParalaX Web Framework - Example Website Manager
echo ============================================================================
echo.
echo   Framework Root: %FRAMEWORK_ROOT%
echo.

REM Check if example exists
if exist "%EXAMPLE_DIR%" (
    echo   Status: Example website EXISTS
    echo.
    echo   [D] Delete example website
    echo   [S] Show status
    echo   [R] Run example website
    echo   [Q] Quit
    echo.
    set /p "choice=Choose action: "
    
    if /i "!choice!"=="D" goto :DELETE
    if /i "!choice!"=="S" goto :STATUS
    if /i "!choice!"=="R" goto :RUN
    if /i "!choice!"=="Q" goto :EOF
    
    echo Invalid choice.
    goto :MENU
) else (
    echo   Status: Example website does NOT exist
    echo.
    echo   [C] Create example website
    echo   [Q] Quit
    echo.
    set /p "choice=Choose action: "
    
    if /i "!choice!"=="C" goto :CREATE
    if /i "!choice!"=="Q" goto :EOF
    
    echo Invalid choice.
    goto :MENU
)

REM ============================================================================
:CREATE
REM ============================================================================
echo.
echo ============================================================================
echo   Creating Example Website
echo ============================================================================
echo.

if exist "%EXAMPLE_DIR%" (
    echo ERROR: Example website already exists at:
    echo   %EXAMPLE_DIR%
    echo.
    echo Delete it first or choose a different location.
    goto :ERROR
)

echo Creating directory structure...
mkdir "%EXAMPLE_DIR%\website\pages" 2>nul
mkdir "%EXAMPLE_DIR%\website\modules" 2>nul
mkdir "%EXAMPLE_DIR%\submodules" 2>nul

echo Creating Python package files...

REM Create __init__.py files
type nul > "%EXAMPLE_DIR%\website\__init__.py"
type nul > "%EXAMPLE_DIR%\website\pages\__init__.py"
type nul > "%EXAMPLE_DIR%\website\modules\__init__.py"

echo Creating project files...

REM Use Python helper script to create files (avoids batch escaping issues)
python "%FRAMEWORK_ROOT%\create_example_files.py" "%EXAMPLE_DIR%"
if errorlevel 1 (
    echo ERROR: Failed to create example files.
    goto :ERROR
)

REM Create junction to framework
echo Creating junction to framework...
cd "%EXAMPLE_DIR%\submodules"
mklink /J framework "%FRAMEWORK_ROOT%" >nul 2>&1

if errorlevel 1 (
    echo WARNING: Could not create junction. You may need to run as administrator.
    echo You can create it manually:
    echo   cd %EXAMPLE_DIR%\submodules
    echo   mklink /J framework "%FRAMEWORK_ROOT%"
    echo.
) else (
    echo Junction created successfully.
)

echo.
echo ============================================================================
echo   Example Website Created Successfully!
echo ============================================================================
echo.
echo   Location: %EXAMPLE_DIR%
echo.
echo   To run it:
echo     cd example_website
echo     python main.py
echo.
echo   Then visit: http://localhost:5001
echo.
goto :SUCCESS

REM ============================================================================
:DELETE
REM ============================================================================
echo.
echo ============================================================================
echo   Deleting Example Website
echo ============================================================================
echo.

if not exist "%EXAMPLE_DIR%" (
    echo ERROR: Example website does not exist at:
    echo   %EXAMPLE_DIR%
    goto :ERROR
)

echo This will DELETE:
echo   %EXAMPLE_DIR%
echo.
set /p "confirm=Are you sure? (yes/no): "

if /i not "!confirm!"=="yes" (
    echo Deletion cancelled.
    goto :EOF
)

echo.
echo Removing junction...
if exist "%EXAMPLE_DIR%\submodules\framework" (
    rmdir "%EXAMPLE_DIR%\submodules\framework" 2>nul
)

echo Deleting directory tree...
rmdir /s /q "%EXAMPLE_DIR%" 2>nul

if exist "%EXAMPLE_DIR%" (
    echo ERROR: Could not delete example website.
    echo You may need to close any programs using files in that directory.
    goto :ERROR
)

echo.
echo ============================================================================
echo   Example Website Deleted Successfully!
echo ============================================================================
echo.
goto :SUCCESS

REM ============================================================================
:STATUS
REM ============================================================================
echo.
echo ============================================================================
echo   Example Website Status
echo ============================================================================
echo.
echo   Framework Root: %FRAMEWORK_ROOT%
echo   Example Directory: %EXAMPLE_DIR%
echo.

if exist "%EXAMPLE_DIR%" (
    echo   Status: EXISTS
    echo.
    echo   Files:
    if exist "%EXAMPLE_DIR%\main.py" echo     [X] main.py
    if exist "%EXAMPLE_DIR%\website\site_conf.py" echo     [X] website\site_conf.py
    if exist "%EXAMPLE_DIR%\website\pages\home.py" echo     [X] website\pages\home.py
    if exist "%EXAMPLE_DIR%\submodules\framework" (
        echo     [X] submodules\framework ^(junction^)
    ) else (
        echo     [ ] submodules\framework ^(MISSING!^)
    )
    echo.
) else (
    echo   Status: DOES NOT EXIST
    echo.
)
goto :SUCCESS

REM ============================================================================
:RUN
REM ============================================================================
echo.
echo ============================================================================
echo   Running Example Website
echo ============================================================================
echo.

if not exist "%EXAMPLE_DIR%\main.py" (
    echo ERROR: main.py not found in example_website
    goto :ERROR
)

cd "%EXAMPLE_DIR%"
python main.py
goto :EOF

REM ============================================================================
:HELP
REM ============================================================================
echo.
echo ============================================================================
echo   Example Website Manager - Help
echo ============================================================================
echo.
echo Usage:
echo   manage_example_website.bat [command]
echo.
echo Commands:
echo   create    Create the example website
echo   delete    Delete the example website
echo   status    Show status of example website
echo   help      Show this help
echo   ^(none^)    Interactive menu
echo.
echo Examples:
echo   manage_example_website.bat create
echo   manage_example_website.bat delete
echo   manage_example_website.bat
echo.
goto :SUCCESS

REM ============================================================================
:SUCCESS
REM ============================================================================
exit /b 0

REM ============================================================================
:ERROR
REM ============================================================================
echo.
echo Operation failed.
echo.
exit /b 1
