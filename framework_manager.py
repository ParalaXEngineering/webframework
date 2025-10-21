#!/usr/bin/env python3
"""
ParalaX Web Framework Manager

A unified cross-platform CLI tool to manage the framework:
- Update vendor libraries
- Manage example website (create/delete/status/run)
- Build documentation

Usage:
    python framework_manager.py
    python framework_manager.py --help
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path
from typing import Optional, List

# Check Python version early
if sys.version_info < (3, 7):
    print("=" * 70)
    print("ERROR: Python 3.7 or higher is required")
    print("=" * 70)
    print(f"\nYour Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print("\nChecking for virtual environment with newer Python...")
    
    # Try to find and use venv
    script_dir = Path(__file__).parent.resolve()
    venv_python = script_dir / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
    
    if venv_python.exists():
        print(f"\nFound virtual environment: {venv_python}")
        print("Restarting with venv Python...\n")
        os.execv(str(venv_python), [str(venv_python)] + sys.argv)
    else:
        print("\nNo virtual environment found with Python 3.7+")
        print("\nPlease either:")
        print("  1. Create a venv with Python 3.7+:")
        print("     python3.7 -m venv .venv")
        print("     .venv\\Scripts\\activate  (Windows)")
        print("     source .venv/bin/activate  (Unix)")
        print("\n  2. Or use Python 3.7+ directly:")
        print("     python3.7 framework_manager.py")
        print()
        sys.exit(1)

try:
    import requests
except ImportError:
    print("Error: 'requests' library not found.")
    print("Please install it: pip install requests")
    sys.exit(1)


# ============================================================================
# Configuration and Constants
# ============================================================================

SCRIPT_DIR = Path(__file__).parent.resolve()
FRAMEWORK_ROOT = SCRIPT_DIR
EXAMPLE_DIR = FRAMEWORK_ROOT / "example_website"
VENDORS_DIR = FRAMEWORK_ROOT / "webengine" / "assets" / "vendors"
DOCS_DIR = FRAMEWORK_ROOT / "docs"


# ============================================================================
# Utility Functions
# ============================================================================

def log(msg: str, level: str = "info"):
    """Print formatted log message."""
    icons = {
        "info": "ℹ",
        "success": "✓",
        "warning": "⚠",
        "error": "✗",
        "package": "📦",
        "download": "↓"
    }
    icon = icons.get(level, "•")
    print(f"{icon} {msg}", flush=True)


def print_header(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def run_command(cmd: List[str], cwd: Optional[Path] = None, check: bool = True):
    """Run a command and return the result."""
    try:
        # Python 3.6 compatible (capture_output added in 3.7)
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            check=check, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        return result
    except subprocess.CalledProcessError as e:
        log(f"Command failed: {' '.join(cmd)}", "error")
        log(f"Error: {e.stderr}", "error")
        if check:
            sys.exit(1)
        return None


def get_python_executable() -> Path:
    """Get the appropriate Python executable (prefer venv with Python 3.7+)."""
    venv_python = FRAMEWORK_ROOT / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
    
    # If venv exists, verify it's Python 3.7+
    if venv_python.exists():
        try:
            result = subprocess.run(
                [str(venv_python), "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                major, minor = map(int, version.split('.'))
                if major > 3 or (major == 3 and minor >= 7):
                    return venv_python
                else:
                    log(f"Venv Python {version} is too old (need 3.7+)", "warning")
        except Exception as e:
            log(f"Could not check venv Python version: {e}", "warning")
    
    # Check if current Python is 3.7+
    if sys.version_info >= (3, 7):
        return Path(sys.executable)
    
    # Last resort - return current but warn
    log("Warning: Python 3.7+ recommended for all features", "warning")
    return Path(sys.executable)


def ensure_venv():
    """Ensure virtual environment exists with Python 3.7+."""
    venv_dir = FRAMEWORK_ROOT / ".venv"
    python_exe = venv_dir / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
    
    if not python_exe.exists():
        log("Creating virtual environment...")
        
        # Check if current Python is 3.7+
        if sys.version_info < (3, 7):
            log("ERROR: Cannot create venv with Python < 3.7", "error")
            log("Please create a venv manually with Python 3.7+:", "info")
            log("  python3.7 -m venv .venv", "info")
            return False
        
        result = subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=False)
        if result.returncode != 0:
            log("Failed to create virtual environment", "error")
            return False
        log("Virtual environment created", "success")
    return True


# ============================================================================
# Vendor Update Functions
# ============================================================================

def get_latest_version(package: str) -> str:
    """Get latest version of NPM package."""
    url = f"https://registry.npmjs.org/{package}/latest"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json().get("version")


def download_file(url: str, dest: Path):
    """Download file from URL to destination."""
    r = requests.get(url, timeout=20)
    if r.status_code != 200 or not r.content:
        raise RuntimeError(f"Failed download: {url}")
    if b"Couldn't find the requested file" in r.content:
        raise RuntimeError(f"CDN missing file: {url}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(r.content)


def download_library(name: str, version: str, package: str, files: List[str]):
    """Download a library with its files."""
    log(f"{name} v{version}", "package")
    target = VENDORS_DIR / name
    target.mkdir(parents=True, exist_ok=True)

    for f in files:
        url = f"https://cdn.jsdelivr.net/npm/{package}@{version}/{f}"
        dest = target / os.path.basename(f)
        log(f"  {dest.name}", "download")
        try:
            download_file(url, dest)
        except Exception as e:
            log(f"  {e}", "error")
            sys.exit(1)
    log("  Done", "success")


def download_highlightjs() -> str:
    """Download highlight.js with fallback handling."""
    hljs_ver = get_latest_version("highlight.js")
    log(f"highlightjs v{hljs_ver}", "package")
    target = VENDORS_DIR / "highlightjs"
    target.mkdir(parents=True, exist_ok=True)

    # CSS
    base_css = "styles/default.min.css"
    css_url = f"https://cdn.jsdelivr.net/npm/highlight.js@{hljs_ver}/{base_css}"
    log(f"  {Path(base_css).name}", "download")
    try:
        download_file(css_url, target / Path(base_css).name)
    except Exception:
        cdn_css = f"https://cdnjs.cloudflare.com/ajax/libs/highlight.js/{hljs_ver}/styles/default.min.css"
        download_file(cdn_css, target / "default.min.css")

    # JS with fallbacks
    candidates = [
        f"https://cdn.jsdelivr.net/npm/highlight.js@{hljs_ver}/build/highlight.min.js",
        f"https://cdn.jsdelivr.net/npm/highlight.js@{hljs_ver}/lib/highlight.min.js",
        f"https://cdn.jsdelivr.net/npm/highlight.js@{hljs_ver}/highlight.min.js",
        f"https://cdnjs.cloudflare.com/ajax/libs/highlight.js/{hljs_ver}/highlight.min.js",
        f"https://cdn.jsdelivr.net/npm/@highlightjs/cdn-assets@{hljs_ver}/highlight.min.js",
    ]

    for url in candidates:
        js_name = Path(url).name
        log(f"  {js_name}", "download")
        try:
            download_file(url, target / js_name)
            log("  Done", "success")
            return hljs_ver
        except Exception:
            continue

    log(f"  No valid JS found for highlight.js@{hljs_ver}", "error")
    sys.exit(1)


def update_vendors():
    """Update all vendor libraries."""
    print_header("Updating Vendor Libraries")
    
    VENDORS_DIR.mkdir(parents=True, exist_ok=True)
    
    versions = {}
    libs = [
        ("gridstack", "gridstack", ["dist/gridstack-all.min.js", "dist/gridstack.min.css"]),
        ("jquery", "jquery", ["dist/jquery.min.js"]),
        ("datatables.net", "datatables.net-bs5",
            ["css/dataTables.bootstrap5.min.css", "js/dataTables.bootstrap5.min.js"]),
        ("fullcalendar", "@fullcalendar/core", ["index.global.min.js"]),
        ("perfect-scrollbar", "perfect-scrollbar",
            ["dist/perfect-scrollbar.min.js", "css/perfect-scrollbar.css"]),
        ("sweetalert", "sweetalert2", ["dist/sweetalert2.all.min.js", "dist/sweetalert2.min.css"]),
        ("mdi", "@mdi/font", ["css/materialdesignicons.min.css"]),
        ("filepond", "filepond", ["dist/filepond.min.js", "dist/filepond.min.css"]),
        ("filepond-plugin-image-preview", "filepond-plugin-image-preview",
            ["dist/filepond-plugin-image-preview.min.js", "dist/filepond-plugin-image-preview.min.css"]),
        ("filepond-plugin-file-validate-type", "filepond-plugin-file-validate-type",
            ["dist/filepond-plugin-file-validate-type.min.js"]),
    ]

    # Get versions
    for name, pkg, _ in libs:
        versions[name] = get_latest_version(pkg)

    # Download libraries
    for name, pkg, files in libs:
        download_library(name, versions[name], pkg, files)

    # Highlight.js
    hljs_ver = download_highlightjs()
    versions["highlightjs"] = hljs_ver

    # MDI fonts
    mdi_ver = versions["mdi"]
    font_dir = VENDORS_DIR / "mdi" / "fonts"
    font_dir.mkdir(parents=True, exist_ok=True)
    fonts = [
        "materialdesignicons-webfont.woff2",
        "materialdesignicons-webfont.woff",
        "materialdesignicons-webfont.ttf",
    ]
    log("mdi fonts", "package")
    for f in fonts:
        url = f"https://cdn.jsdelivr.net/npm/@mdi/font@{mdi_ver}/fonts/{f}"
        dest = font_dir / f
        log(f"  {f}", "download")
        download_file(url, dest)
    log("  Done", "success")

    # TinyMCE
    tinymce_ver = get_latest_version("tinymce")
    log(f"tinymce v{tinymce_ver}", "package")
    tdir = VENDORS_DIR / "tinymce"
    tdir.mkdir(parents=True, exist_ok=True)
    url = f"https://cdn.jsdelivr.net/npm/tinymce@{tinymce_ver}/tinymce.min.js"
    download_file(url, tdir / "tinymce.min.js")
    log("  Done", "success")

    print_header("Vendor Libraries Updated Successfully!")
    print("Summary of installed versions:")
    for n, v in versions.items():
        print(f"  • {n}: {v}")
    print(f"  • tinymce: {tinymce_ver}\n")


# ============================================================================
# Example Website Functions
# ============================================================================

def create_example_website():
    """Create example website structure."""
    print_header("Creating Example Website")
    
    if EXAMPLE_DIR.exists():
        log(f"Example website already exists at: {EXAMPLE_DIR}", "error")
        log("Delete it first with: python framework_manager.py example --delete", "info")
        return
    
    log("Creating directory structure...")
    (EXAMPLE_DIR / "website" / "pages").mkdir(parents=True, exist_ok=True)
    (EXAMPLE_DIR / "website" / "modules").mkdir(parents=True, exist_ok=True)
    (EXAMPLE_DIR / "submodules").mkdir(parents=True, exist_ok=True)
    
    log("Creating Python package files...")
    (EXAMPLE_DIR / "website" / "__init__.py").touch()
    (EXAMPLE_DIR / "website" / "pages" / "__init__.py").touch()
    (EXAMPLE_DIR / "website" / "modules" / "__init__.py").touch()
    
    log("Creating site_conf.py...")
    (EXAMPLE_DIR / "website" / "site_conf.py").write_text('''"""
Site Configuration for Example Website
"""
from submodules.framework.src.modules.site_conf import Site_conf


class ExampleSiteConf(Site_conf):
    """Custom site configuration for the example website."""
    
    def __init__(self):
        super().__init__()
        
        self.m_app = {
            "name": "Example Website",
            "version": "1.0.0",
            "icon": "rocket",
            "footer": "2025 &copy; Example Company"
        }
        
        self.m_index = "Welcome to the Example Website"
        
        self.add_sidebar_title("Main")
        self.add_sidebar_section("Home", "house", "home")
        self.add_sidebar_section("About", "information", "about")
        
        self.m_topbar = {
            "display": True,
            "left": [],
            "center": [],
            "right": [],
            "login": True
        }
''')
    
    log("Creating config.json...")
    (EXAMPLE_DIR / "website" / "config.json").write_text('''{
    "app_name": "Example Website",
    "debug": false,
    "secret_key": "change-this-in-production"
}
''')
    
    log("Creating home.py...")
    (EXAMPLE_DIR / "website" / "pages" / "home.py").write_text('''"""Home Page for Example Website"""
from flask import Blueprint
from submodules.framework.src.modules.displayer import (
    Displayer, DisplayerItemText, DisplayerItemCard
)

home_bp = Blueprint('home', __name__)


@home_bp.route('/')
def index():
    disp = Displayer()
    disp.add_generic({"id": "welcome", "title": "Welcome"})
    disp.add_display_item(DisplayerItemText("Welcome to the Example Website!"))
    return disp.display()


@home_bp.route('/about')
def about():
    disp = Displayer()
    disp.add_generic({"id": "about", "title": "About"})
    disp.add_display_item(DisplayerItemText("This is an example website."))
    return disp.display()
''')
    
    log("Creating main.py...")
    (EXAMPLE_DIR / "main.py").write_text('''"""Main Application Entry Point for Example Website"""
import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
framework_root = os.path.join(project_root, 'submodules', 'framework')

sys.path.insert(0, project_root)
sys.path.insert(0, framework_root)
sys.path.insert(0, os.path.join(framework_root, 'src'))

from submodules.framework.src.main import app, setup_app
from submodules.framework.src.modules import site_conf
from submodules.framework.src.modules.log.logger_factory import get_logger
from website.site_conf import ExampleSiteConf
from website.pages.home import home_bp

logger = get_logger("main")
os.chdir(framework_root)

site_conf.site_conf_obj = ExampleSiteConf()
site_conf.site_conf_app_path = framework_root
socketio = setup_app(app)
app.register_blueprint(home_bp)

if __name__ == "__main__":
    print("="*70)
    print("  Example Website - ParalaX Web Framework")
    print("="*70)
    print("  Visit: http://localhost:5001")
    print("  Press CTRL+C to stop")
    print("="*70)
    socketio.run(app, debug=False, host='0.0.0.0', port=5001)
''')
    
    log("Creating README.md...")
    (EXAMPLE_DIR / "README.md").write_text('''# Example Website

This is an example website project using the ParalaX Web Framework.

## Run

```bash
python main.py
```

Visit http://localhost:5001
''')
    
    log("Creating link to framework...")
    framework_link = EXAMPLE_DIR / "submodules" / "framework"
    
    try:
        if os.name == "nt":
            # Windows: use junction
            subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(framework_link), str(FRAMEWORK_ROOT)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        else:
            # Unix: use symlink
            framework_link.symlink_to(FRAMEWORK_ROOT)
        log("Framework link created successfully", "success")
    except Exception as e:
        log(f"Could not create link: {e}", "warning")
        log("You can create it manually:", "info")
        if os.name == "nt":
            print(f"  cd {EXAMPLE_DIR / 'submodules'}")
            print(f"  mklink /J framework {FRAMEWORK_ROOT}")
        else:
            print(f"  cd {EXAMPLE_DIR / 'submodules'}")
            print(f"  ln -s {FRAMEWORK_ROOT} framework")
    
    print_header("Example Website Created Successfully!")
    print(f"  Location: {EXAMPLE_DIR}")
    print("\n  To run it:")
    print("    cd example_website")
    print("    python main.py")
    print("\n  Then visit: http://localhost:5001\n")


def delete_example_website():
    """Delete example website."""
    print_header("Deleting Example Website")
    
    if not EXAMPLE_DIR.exists():
        log(f"Example website does not exist at: {EXAMPLE_DIR}", "error")
        return
    
    print(f"This will DELETE: {EXAMPLE_DIR}\n")
    confirm = input("Are you sure? (yes/no): ").strip().lower()
    
    if confirm != "yes":
        print("Deletion cancelled.")
        return
    
    log("Removing framework link...")
    framework_link = EXAMPLE_DIR / "submodules" / "framework"
    if framework_link.exists():
        try:
            if os.name == "nt" and framework_link.is_dir():
                subprocess.run(
                    ["cmd", "/c", "rmdir", str(framework_link)],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            else:
                framework_link.unlink()
        except Exception as e:
            log(f"Could not remove link: {e}", "warning")
    
    log("Deleting directory tree...")
    shutil.rmtree(EXAMPLE_DIR, ignore_errors=True)
    
    if EXAMPLE_DIR.exists():
        log("Could not delete example website", "error")
        log("You may need to close any programs using files in that directory", "info")
        return
    
    print_header("Example Website Deleted Successfully!")


def show_example_status():
    """Show example website status."""
    print_header("Example Website Status")
    print(f"  Framework Root: {FRAMEWORK_ROOT}")
    print(f"  Example Directory: {EXAMPLE_DIR}\n")
    
    if EXAMPLE_DIR.exists():
        log("Status: EXISTS", "success")
        print("\n  Files:")
        files_to_check = [
            ("main.py", EXAMPLE_DIR / "main.py"),
            ("website/site_conf.py", EXAMPLE_DIR / "website" / "site_conf.py"),
            ("website/pages/home.py", EXAMPLE_DIR / "website" / "pages" / "home.py"),
            ("submodules/framework", EXAMPLE_DIR / "submodules" / "framework"),
        ]
        
        for label, path in files_to_check:
            if path.exists():
                print(f"    [✓] {label}")
            else:
                print(f"    [ ] {label} (MISSING!)")
        print()
    else:
        log("Status: DOES NOT EXIST", "warning")
        print()


def run_example_website():
    """Run the example website."""
    print_header("Running Example Website")
    
    main_py = EXAMPLE_DIR / "main.py"
    if not main_py.exists():
        log("main.py not found in example_website", "error")
        return
    
    python_exe = get_python_executable()
    os.chdir(EXAMPLE_DIR)
    subprocess.run([str(python_exe), "main.py"])


# ============================================================================
# Documentation Functions
# ============================================================================

def build_documentation():
    """Build Sphinx documentation."""
    print_header("Building Documentation")
    
    # Check project root
    if not (FRAMEWORK_ROOT / "pyproject.toml").exists():
        log("Error: pyproject.toml not found in project root", "error")
        return
    
    # Ensure virtual environment
    if not ensure_venv():
        log("Virtual environment setup failed", "error")
        return
    
    python_exe = get_python_executable()
    pip_exe = python_exe.parent / ("pip.exe" if os.name == "nt" else "pip")
    
    log("Installing documentation dependencies...")
    result = subprocess.run(
        [str(pip_exe), "install", "-q", "-e", ".[docs]"], 
        cwd=FRAMEWORK_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    if result.returncode != 0:
        log("Failed to install dependencies", "error")
        stderr_msg = result.stderr.decode() if isinstance(result.stderr, bytes) else result.stderr
        log(stderr_msg, "error")
        return
    
    log("Dependencies ready", "success")
    
    # Validate docstrings
    docstring_checker = DOCS_DIR / "check_docstrings.py"
    if docstring_checker.exists():
        log("Validating docstrings...")
        result = subprocess.run(
            [str(python_exe), str(docstring_checker)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        if "SUMMARY:" in result.stdout and any(c.isdigit() and c != '0' for c in result.stdout.split("SUMMARY:")[1][:10]):
            log("Some functions are missing documentation", "warning")
        else:
            log("All docstrings validated", "success")
    
    # Clean previous build
    build_dir = DOCS_DIR / "build"
    if build_dir.exists():
        log("Cleaning previous build...")
        shutil.rmtree(build_dir, ignore_errors=True)
        log("Previous build cleaned", "success")
    
    # Build documentation
    log("Building HTML documentation...")
    result = subprocess.run(
        [str(python_exe), "-m", "sphinx", "-b", "html", "-W", "--keep-going", "-T", 
         "source", "build/html"],
        cwd=DOCS_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    
    index_html = DOCS_DIR / "build" / "html" / "index.html"
    
    if index_html.exists():
        print_header("Documentation Built Successfully!")
        print(f"  Location: {index_html}\n")
        
        # Open in browser
        try:
            if sys.platform == "darwin":
                subprocess.run(["open", str(index_html)])
            elif sys.platform == "win32":
                os.startfile(str(index_html))
            elif sys.platform.startswith("linux"):
                subprocess.run(["xdg-open", str(index_html)])
            log("Opening documentation in browser...", "info")
        except Exception as e:
            log(f"Could not open browser: {e}", "warning")
            log(f"Please open {index_html} manually", "info")
    else:
        log("Documentation build failed - no HTML files generated", "error")
        if result.stderr:
            print(result.stderr)


# ============================================================================
# Main CLI Interface
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="ParalaX Web Framework Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python framework_manager.py vendors
  python framework_manager.py example --create
  python framework_manager.py example --run
  python framework_manager.py docs
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Vendors command
    subparsers.add_parser("vendors", help="Update vendor libraries")
    
    # Example command
    example_parser = subparsers.add_parser("example", help="Manage example website")
    example_group = example_parser.add_mutually_exclusive_group()
    example_group.add_argument("--create", action="store_true", help="Create example website")
    example_group.add_argument("--delete", action="store_true", help="Delete example website")
    example_group.add_argument("--status", action="store_true", help="Show example status")
    example_group.add_argument("--run", action="store_true", help="Run example website")
    
    # Docs command
    subparsers.add_parser("docs", help="Build documentation")
    
    args = parser.parse_args()
    
    # Interactive mode if no command
    if not args.command:
        print_header("ParalaX Web Framework Manager")
        print("What would you like to do?\n")
        print("  [1] Update vendor libraries")
        print("  [2] Manage example website")
        print("  [3] Build documentation")
        print("  [Q] Quit\n")
        
        choice = input("Choose action: ").strip().upper()
        
        if choice == "1":
            update_vendors()
        elif choice == "2":
            manage_example_interactive()
        elif choice == "3":
            build_documentation()
        elif choice == "Q":
            sys.exit(0)
        else:
            print("Invalid choice.")
        return
    
    # Execute command
    if args.command == "vendors":
        update_vendors()
    elif args.command == "example":
        if args.create:
            create_example_website()
        elif args.delete:
            delete_example_website()
        elif args.status:
            show_example_status()
        elif args.run:
            run_example_website()
        else:
            manage_example_interactive()
    elif args.command == "docs":
        build_documentation()


def manage_example_interactive():
    """Interactive example management menu."""
    print_header("Example Website Manager")
    print(f"  Framework Root: {FRAMEWORK_ROOT}\n")
    
    if EXAMPLE_DIR.exists():
        print("  Status: Example website EXISTS\n")
        print("  [D] Delete example website")
        print("  [S] Show status")
        print("  [R] Run example website")
        print("  [Q] Back to main menu\n")
        
        choice = input("Choose action: ").strip().upper()
        
        if choice == "D":
            delete_example_website()
        elif choice == "S":
            show_example_status()
        elif choice == "R":
            run_example_website()
        elif choice == "Q":
            return
        else:
            print("Invalid choice.")
    else:
        print("  Status: Example website does NOT exist\n")
        print("  [C] Create example website")
        print("  [Q] Back to main menu\n")
        
        choice = input("Choose action: ").strip().upper()
        
        if choice == "C":
            create_example_website()
        elif choice == "Q":
            return
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(1)
    except Exception as e:
        log(f"Unexpected error: {e}", "error")
        import traceback
        traceback.print_exc()
        sys.exit(1)
