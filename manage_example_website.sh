#!/bin/bash
################################################################################
# Example Website Manager for ParalaX Web Framework
#
# This script manages the example_website demonstration project.
# Usage: ./manage_example_website.sh [create|delete|status|run]
################################################################################

set -e

# Auto-discover framework root (script location)
FRAMEWORK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLE_DIR="$FRAMEWORK_ROOT/example_website"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line argument
ACTION="${1:-}"

################################################################################
# Functions
################################################################################

print_header() {
    echo ""
    echo "============================================================================"
    echo "  $1"
    echo "============================================================================"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

################################################################################
# Commands
################################################################################

create_example() {
    print_header "Creating Example Website"
    
    if [ -d "$EXAMPLE_DIR" ]; then
        print_error "Example website already exists at: $EXAMPLE_DIR"
        echo ""
        echo "Delete it first with: $0 delete"
        exit 1
    fi
    
    print_info "Creating directory structure..."
    mkdir -p "$EXAMPLE_DIR/website/pages"
    mkdir -p "$EXAMPLE_DIR/website/modules"
    mkdir -p "$EXAMPLE_DIR/submodules"
    
    print_info "Creating Python package files..."
    touch "$EXAMPLE_DIR/website/__init__.py"
    touch "$EXAMPLE_DIR/website/pages/__init__.py"
    touch "$EXAMPLE_DIR/website/modules/__init__.py"
    
    print_info "Creating site_conf.py..."
    cat > "$EXAMPLE_DIR/website/site_conf.py" << 'EOF'
"""
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
EOF
    
    print_info "Creating config.json..."
    cat > "$EXAMPLE_DIR/website/config.json" << 'EOF'
{
    "app_name": "Example Website",
    "debug": false,
    "secret_key": "change-this-in-production"
}
EOF
    
    print_info "Creating home.py..."
    cat > "$EXAMPLE_DIR/website/pages/home.py" << 'EOF'
"""Home Page for Example Website"""
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
EOF
    
    print_info "Creating main.py..."
    cat > "$EXAMPLE_DIR/main.py" << 'EOF'
"""Main Application Entry Point for Example Website"""
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
EOF
    
    print_info "Creating README.md..."
    cat > "$EXAMPLE_DIR/README.md" << 'EOF'
# Example Website

This is an example website project using the ParalaX Web Framework as a git submodule.

## Run

```bash
python main.py
```

Visit http://localhost:5001
EOF
    
    print_info "Creating symbolic link to framework..."
    ln -s "$FRAMEWORK_ROOT" "$EXAMPLE_DIR/submodules/framework"
    
    if [ $? -eq 0 ]; then
        print_success "Symbolic link created successfully"
    else
        print_warning "Could not create symbolic link"
        echo "You can create it manually:"
        echo "  cd $EXAMPLE_DIR/submodules"
        echo "  ln -s $FRAMEWORK_ROOT framework"
    fi
    
    echo ""
    print_header "Example Website Created Successfully!"
    echo "  Location: $EXAMPLE_DIR"
    echo ""
    echo "  To run it:"
    echo "    cd example_website"
    echo "    python main.py"
    echo ""
    echo "  Then visit: http://localhost:5001"
    echo ""
}

delete_example() {
    print_header "Deleting Example Website"
    
    if [ ! -d "$EXAMPLE_DIR" ]; then
        print_error "Example website does not exist at: $EXAMPLE_DIR"
        exit 1
    fi
    
    echo "This will DELETE: $EXAMPLE_DIR"
    echo ""
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "Deletion cancelled."
        exit 0
    fi
    
    echo ""
    print_info "Removing symbolic link..."
    if [ -L "$EXAMPLE_DIR/submodules/framework" ]; then
        rm "$EXAMPLE_DIR/submodules/framework"
    fi
    
    print_info "Deleting directory tree..."
    rm -rf "$EXAMPLE_DIR"
    
    if [ -d "$EXAMPLE_DIR" ]; then
        print_error "Could not delete example website"
        exit 1
    fi
    
    echo ""
    print_header "Example Website Deleted Successfully!"
}

show_status() {
    print_header "Example Website Status"
    echo "  Framework Root: $FRAMEWORK_ROOT"
    echo "  Example Directory: $EXAMPLE_DIR"
    echo ""
    
    if [ -d "$EXAMPLE_DIR" ]; then
        print_success "Status: EXISTS"
        echo ""
        echo "  Files:"
        [ -f "$EXAMPLE_DIR/main.py" ] && echo "    [✓] main.py" || echo "    [ ] main.py"
        [ -f "$EXAMPLE_DIR/website/site_conf.py" ] && echo "    [✓] website/site_conf.py" || echo "    [ ] website/site_conf.py"
        [ -f "$EXAMPLE_DIR/website/pages/home.py" ] && echo "    [✓] website/pages/home.py" || echo "    [ ] website/pages/home.py"
        
        if [ -L "$EXAMPLE_DIR/submodules/framework" ]; then
            echo "    [✓] submodules/framework (symlink)"
        else
            echo "    [ ] submodules/framework (MISSING!)"
        fi
        echo ""
    else
        print_warning "Status: DOES NOT EXIST"
        echo ""
    fi
}

run_example() {
    print_header "Running Example Website"
    
    if [ ! -f "$EXAMPLE_DIR/main.py" ]; then
        print_error "main.py not found in example_website"
        exit 1
    fi
    
    cd "$EXAMPLE_DIR"
    python main.py
}

show_menu() {
    print_header "ParalaX Web Framework - Example Website Manager"
    echo "  Framework Root: $FRAMEWORK_ROOT"
    echo ""
    
    if [ -d "$EXAMPLE_DIR" ]; then
        echo "  Status: Example website EXISTS"
        echo ""
        echo "  [D] Delete example website"
        echo "  [S] Show status"
        echo "  [R] Run example website"
        echo "  [Q] Quit"
        echo ""
        read -p "Choose action: " choice
        
        case "$choice" in
            d|D) delete_example ;;
            s|S) show_status ;;
            r|R) run_example ;;
            q|Q) exit 0 ;;
            *) echo "Invalid choice."; show_menu ;;
        esac
    else
        echo "  Status: Example website does NOT exist"
        echo ""
        echo "  [C] Create example website"
        echo "  [Q] Quit"
        echo ""
        read -p "Choose action: " choice
        
        case "$choice" in
            c|C) create_example ;;
            q|Q) exit 0 ;;
            *) echo "Invalid choice."; show_menu ;;
        esac
    fi
}

show_help() {
    print_header "Example Website Manager - Help"
    echo "Usage:"
    echo "  $0 [command]"
    echo ""
    echo "Commands:"
    echo "  create    Create the example website"
    echo "  delete    Delete the example website"
    echo "  status    Show status of example website"
    echo "  run       Run the example website"
    echo "  help      Show this help"
    echo "  (none)    Interactive menu"
    echo ""
    echo "Examples:"
    echo "  $0 create"
    echo "  $0 delete"
    echo "  $0 run"
    echo "  $0"
    echo ""
}

################################################################################
# Main
################################################################################

case "$ACTION" in
    create) create_example ;;
    delete) delete_example ;;
    status) show_status ;;
    run) run_example ;;
    help) show_help ;;
    "") show_menu ;;
    *) 
        echo "Unknown command: $ACTION"
        show_help
        exit 1
        ;;
esac
