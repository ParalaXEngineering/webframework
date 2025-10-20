"""
Helper script to generate example_website files.
Called by manage_example_website.bat to avoid batch escaping issues.
"""
import os
import sys


def create_site_conf(example_dir):
    """Create website/site_conf.py"""
    content = '''"""
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
'''
    filepath = os.path.join(example_dir, "website", "site_conf.py")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {filepath}")


def create_config_json(example_dir):
    """Create website/config.json"""
    content = '''{
    "app_name": "Example Website",
    "debug": false,
    "secret_key": "change-this-in-production"
}
'''
    filepath = os.path.join(example_dir, "website", "config.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {filepath}")


def create_home_page(example_dir):
    """Create website/pages/home.py"""
    content = '''"""Home Page for Example Website"""
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
'''
    filepath = os.path.join(example_dir, "website", "pages", "home.py")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {filepath}")


def create_main_py(example_dir):
    """Create main.py"""
    content = '''"""Main Entry Point for Example Website"""
import os
import sys

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

site_conf.m_site_conf = ExampleSiteConf()
setup_app()

app.register_blueprint(home_bp)

if __name__ == '__main__':
    logger.info("Starting Example Website on port 5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
'''
    filepath = os.path.join(example_dir, "main.py")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {filepath}")


def create_readme(example_dir):
    """Create README.md"""
    content = '''# Example Website

This is an example website project using the ParalaX Web Framework as a git submodule.

## Run

```bash
python main.py
```

The website will be available at http://localhost:5001

## Structure

- `main.py` - Entry point
- `website/` - Your website code
  - `site_conf.py` - Site configuration
  - `pages/` - Page blueprints
  - `modules/` - Custom modules
- `submodules/framework/` - ParalaX Web Framework (junction/symlink)
'''
    filepath = os.path.join(example_dir, "README.md")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {filepath}")


def main():
    if len(sys.argv) != 2:
        print("Usage: create_example_files.py <example_directory>")
        sys.exit(1)
    
    example_dir = sys.argv[1]
    
    if not os.path.exists(example_dir):
        print(f"ERROR: Directory does not exist: {example_dir}")
        sys.exit(1)
    
    try:
        create_site_conf(example_dir)
        create_config_json(example_dir)
        create_home_page(example_dir)
        create_main_py(example_dir)
        create_readme(example_dir)
        print("\nAll files created successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
