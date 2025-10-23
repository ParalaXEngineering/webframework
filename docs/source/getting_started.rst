Getting Started
===============

This comprehensive guide will help you get started with the ParalaX Web Framework, from installation to creating your first fully functional application.

.. contents:: Quick Navigation
   :local:
   :depth: 2

Prerequisites
-------------

Before you begin, ensure you have:

System Requirements
^^^^^^^^^^^^^^^^^^^

* **Python**: 3.8 or higher (3.11 recommended)
* **pip**: Latest version (``pip install --upgrade pip``)
* **Virtual environment**: venv or conda
* **Git**: For cloning the repository
* **Terminal/Command Prompt**: Basic command line knowledge

Recommended Knowledge
^^^^^^^^^^^^^^^^^^^^^

* **Python basics**: Functions, classes, imports
* **Web concepts**: HTTP requests, sessions, forms
* **Command line**: Basic terminal navigation

Installation
------------

The ParalaX Web Framework is designed to be used as a **Git submodule** in your website project. This keeps your website code separate from the framework code and makes updates easy.

.. note::
   **Framework Development**: If you're contributing to the framework itself (not building a website), clone the repository directly instead of using it as a submodule.

Setting Up Your Website Project
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Step 1: Create Your Project Structure**

.. code-block:: bash

   # Create your website project
   mkdir my_website
   cd my_website
   
   # Initialize git repository
   git init
   
   # Create project structure
   mkdir website website/pages website/modules submodules

Your project structure should look like this:

.. code-block:: text

   my_website/
   ├── main.py                    # Your application entry point
   ├── website/                   # Your website code
   │   ├── __init__.py
   │   ├── site_conf.py          # Your site configuration
   │   ├── config.json           # Configuration file
   │   ├── pages/                # Your custom pages
   │   │   └── __init__.py
   │   └── modules/              # Your custom modules
   │       └── __init__.py
   └── submodules/
       └── framework/            # Git submodule (next step)

**Step 2: Add Framework as Submodule**

.. code-block:: bash

   # Add the framework as a git submodule
   git submodule add https://github.com/ParalaXEngineering/webframework.git submodules/framework
   git submodule update --init --recursive

**Step 3: Install Dependencies**

.. code-block:: bash

   # Create virtual environment
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   
   # Install framework dependencies
   pip install -r submodules/framework/requirements.txt

Testing Your Website
--------------------

Verify everything works:

Run Your Website
^^^^^^^^^^^^^^^^

.. code-block:: bash

   # From your project root
   python main.py

Visit ``http://localhost:5001`` and verify:

- Home page loads without errors
- Navigation sidebar shows your sections
- Your site name appears in the header
- Pages render correctly

Run Framework Tests (Optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you want to verify the framework itself:

.. code-block:: bash

   # Navigate to framework directory
   cd submodules/framework
   
   # Run tests
   pytest tests/ -v

Explore the Framework Demo
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The framework includes a comprehensive demo showing all features:

.. code-block:: bash

   cd submodules/framework
   python tests/manual_test_webapp.py

This demo showcases:

- All display components (forms, tables, cards, etc.)
- Background tasks and threading
- Real-time updates via WebSocket
- Authentication and permissions
- Layout systems

Understanding the Project Structure
------------------------------------

Let's explore what each directory contains:

Directory Layout
^^^^^^^^^^^^^^^^

.. code-block:: text

   webframework/
   ├── docs/                        # Sphinx documentation
   │   ├── source/                  # RST source files
   │   └── build/                   # Generated HTML (after build)
   │
   ├── src/                         # Core framework code
   │   ├── main.py                  # Flask app initialization
   │   ├── __init__.py              # Package exports
   │   │
   │   ├── modules/                 # Core framework modules
   │   │   ├── action.py            # Base action class
   │   │   ├── site_conf.py         # Site configuration
   │   │   ├── utilities.py         # Helper functions
   │   │   │
   │   │   ├── auth/                # Authentication system
   │   │   │   ├── auth_manager.py
   │   │   │   └── permission_registry.py
   │   │   │
   │   │   ├── displayer/           # UI generation system
   │   │   │   ├── displayer.py     # Main displayer class
   │   │   │   ├── layout.py        # Layout management
   │   │   │   ├── core.py          # Core utilities
   │   │   │   └── items/           # Display items
   │   │   │       ├── base_item.py
   │   │   │       ├── text.py
   │   │   │       ├── button.py
   │   │   │       └── ...
   │   │   │
   │   │   ├── threaded/            # Background task system
   │   │   │   ├── threaded_action.py
   │   │   │   └── threaded_manager.py
   │   │   │
   │   │   ├── scheduler/           # Real-time update system
   │   │   │   ├── scheduler.py
   │   │   │   ├── message_queue.py
   │   │   │   └── emitter.py
   │   │   │
   │   │   └── log/                 # Logging infrastructure
   │   │       └── logger_factory.py
   │   │
   │   └── pages/                   # Built-in pages
   │       ├── common.py            # Home page
   │       ├── admin.py             # Admin panel
   │       ├── user.py              # User profile
   │       └── threads.py           # Thread monitor
   │
   ├── templates/                   # Jinja2 templates
   │   ├── base.j2                  # Base template
   │   ├── index.j2                 # Home page
   │   ├── login.j2                 # Login page
   │   └── displayer_items/         # Item templates
   │
   ├── webengine/                   # Static assets
   │   └── assets/
   │       ├── css/                 # Stylesheets
   │       ├── js/                  # JavaScript
   │       └── images/              # Images/icons
   │
   ├── tests/                       # Test suite
   │   ├── unit/                    # Unit tests
   │   ├── integration/             # Integration tests
   │   ├── conftest.py              # Pytest fixtures
   │   ├── manual_test_webapp.py    # Demo application
   │   └── demo_support/            # Demo pages
   │
   ├── logs/                        # Application logs (auto-created)
   ├── flask_session/               # Session files (auto-created)
   ├── auth/                        # User data (auto-created)
   │
   ├── pyproject.toml               # Project metadata
   ├── requirements.txt             # Python dependencies
   ├── pytest.ini                   # Pytest configuration
   └── README.md                    # Overview documentation

Key Files Explained
^^^^^^^^^^^^^^^^^^^

**main.py**
   Flask application initialization, blueprint registration, SocketIO setup

**displayer.py**
   Core UI generation class - creates pages programmatically

**threaded_action.py**
   Base class for background tasks with progress tracking

**scheduler.py**
   Manages periodic tasks and real-time client updates

**auth_manager.py**
   User authentication and permission management

**site_conf.py**
   Application configuration and navigation structure

Enabling Optional Features
--------------------------

The framework provides several optional system components that can be enabled selectively based on your needs. These features add powerful functionality like authentication, background tasks, real-time updates, and management tools.

Available Optional Features
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following system features can be enabled in your site configuration:

**Authentication System**
   User login, permissions, and role-based access control
   
**Thread Monitor**
   Real-time monitoring of background tasks and threaded actions
   
**Scheduler**
   Periodic task execution and real-time client updates via WebSocket
   
**Log Viewer**
   Web-based log file viewer with filtering and search
   
**Bug Tracker**
   Issue tracking integration (requires Redmine or compatible system)
   
**Settings Manager**
   Web interface for managing application settings
   
**Updater**
   Automatic application update system
   
**Packager**
   Tools for creating distributable resource packages

Enabling Features
^^^^^^^^^^^^^^^^^

To enable optional features, call the corresponding ``enable_*()`` methods in your ``Site_conf`` subclass's ``__init__()`` method:

.. code-block:: python

   from submodules.framework.src.modules.site_conf import Site_conf
   
   
   class MySiteConf(Site_conf):
       def __init__(self):
           super().__init__()
           
           # Enable authentication
           self.enable_authentication(add_to_sidebar=True)
           
           # Enable thread monitoring
           self.enable_threads(add_to_sidebar=True)
           
           # Enable scheduler for real-time updates
           self.enable_scheduler()
           
           # Enable log viewer
           self.enable_log_viewer(add_to_sidebar=True)

The ``add_to_sidebar`` parameter controls whether a navigation link is added to the sidebar. Set it to ``False`` if you want the feature enabled but don't want it in the navigation.

.. tip::
   If you don't enable the scheduler, the framework will still work but pages won't receive real-time updates via WebSocket.

Feature Methods Reference
^^^^^^^^^^^^^^^^^^^^^^^^^

**enable_authentication(add_to_sidebar=True)**
   Enables user authentication system. Adds "Admin" and "My Profile" links to sidebar if ``add_to_sidebar=True``.
   
   .. code-block:: python
   
      self.enable_authentication(add_to_sidebar=True)

**enable_threads(add_to_sidebar=True, add_to_topbar=True, topbar_icon="cog-sync", topbar_area="right")**
   Enables background task monitoring. Adds "Threads" page to System > Monitoring section if ``add_to_sidebar=True``.
   Adds thread status indicator to topbar if ``add_to_topbar=True``.
   
   .. code-block:: python
   
      # Enable with both sidebar and topbar (default)
      self.enable_threads(add_to_sidebar=True)
      
      # Customize topbar icon and position
      self.enable_threads(topbar_icon="loading", topbar_area="center")
      
      # Enable only sidebar, no topbar indicator
      self.enable_threads(add_to_topbar=False)

**enable_scheduler()**
   Enables periodic task scheduler and WebSocket real-time updates. Does not add sidebar items.
   
   .. code-block:: python
   
      self.enable_scheduler()

**enable_log_viewer(add_to_sidebar=True)**
   Enables web-based log file viewer. Adds "Logs" page to System > Monitoring section if ``add_to_sidebar=True``.
   
   .. code-block:: python
   
      self.enable_log_viewer(add_to_sidebar=True)

**enable_bug_tracker(add_to_sidebar=True)**
   Enables issue tracking integration. Adds "Bug Tracker" to System > Tools section if ``add_to_sidebar=True``.
   
   .. code-block:: python
   
      self.enable_bug_tracker(add_to_sidebar=True)

**enable_settings(add_to_sidebar=True)**
   Enables settings management interface. Adds "Settings" to System > Tools section if ``add_to_sidebar=True``.
   
   .. code-block:: python
   
      self.enable_settings(add_to_sidebar=True)

**enable_updater(add_to_sidebar=True)**
   Enables automatic update system. Adds "Updater" to System > Deployment section if ``add_to_sidebar=True``.
   
   .. code-block:: python
   
      self.enable_updater(add_to_sidebar=True)

**enable_packager(add_to_sidebar=True)**
   Enables resource package creation. Adds "Packager" to System > Deployment section if ``add_to_sidebar=True``.
   
   .. code-block:: python
   
      self.enable_packager(add_to_sidebar=True)

**enable_all_features(add_to_sidebar=True, add_to_topbar=True)**
   Convenience method that enables all optional features at once. This includes authentication,
   scheduler, threads, log viewer, bug tracker, settings, updater, and packager.
   
   .. code-block:: python
   
      # Enable everything with sidebar and topbar (default)
      self.enable_all_features(add_to_sidebar=True)
      
      # Enable features without topbar elements
      self.enable_all_features(add_to_sidebar=True, add_to_topbar=False)

Sidebar Organization
^^^^^^^^^^^^^^^^^^^^

When you enable features with ``add_to_sidebar=True``, they are automatically organized into logical sections under a "System" title in the navigation sidebar:

**System** (title)
   - **Monitoring** (section)
      - Threads - Monitor background tasks
      - Logs - View application logs
   
   - **Tools** (section)
      - Bug Tracker - Issue tracking
      - Settings - Application settings
   
   - **Deployment** (section)
      - Updater - Application updates
      - Packager - Package creation

This organization keeps system utilities separate from your application pages.

Creating Your Website Files
---------------------------

Now let's create the essential files for your website.

**Step 1: Create Site Configuration** (``website/site_conf.py``)

This file defines your site's navigation, branding, and settings. Here's a complete example from the manual test webapp:

.. literalinclude:: ../../tests/manual_test_webapp.py
   :language: python
   :pyobject: TestSiteConf
   :caption: tests/manual_test_webapp.py - Complete Site Configuration Example

This example demonstrates:
- Configuring application metadata (name, version, icon)
- Building sidebar navigation with titles, sections, and submenus
- Enabling all framework features with ``enable_all_features()``
- Customizing topbar settings

For a simpler starting point, you might want:

.. code-block:: python

   """
   Site Configuration for Your Website
   """
   from submodules.framework.src.modules.site_conf import Site_conf
   
   
   class MySiteConf(Site_conf):
       """Custom site configuration"""
       
       def __init__(self):
           super().__init__()
           
           # Configure application details
           self.m_app = {
               "name": "My Website",
               "version": "1.0.0",
               "icon": "rocket",
               "footer": "2025 &copy; Your Company"
           }
           
           # Set welcome message
           self.m_index = "Welcome to My Website"
           
           # Enable optional features (as needed)
           self.enable_authentication(add_to_sidebar=True)
           self.enable_threads(add_to_sidebar=True)
           self.enable_scheduler()  # For real-time updates
           
           # Configure sidebar navigation
           self.add_sidebar_title("Main")
           self.add_sidebar_page("Home", "house", "home.index")
           self.add_sidebar_page("About", "information", "home.about")
           
           # Configure topbar
           self.m_topbar = {
               "display": True,
               "left": [],
               "center": [],
               "right": [],
               "login": True
           }

**Step 2: Create Your Home Page** (``website/pages/home.py``)

.. code-block:: python

   """
   Home Page
   """
   from flask import Blueprint
   from submodules.framework.src.modules.displayer import (
       Displayer, DisplayerItemText
   )
   
   home_bp = Blueprint('home', __name__)
   
   
   @home_bp.route('/')
   def index():
       disp = Displayer()
       
       disp.add_generic({
           "id": "welcome",
           "title": "Welcome"
       })
       
       disp.add_display_item(
           DisplayerItemText("Welcome to your website!")
       )
       
       return disp.display()

**Step 3: Create Main Entry Point** (``main.py`` in project root)

.. code-block:: python

   """
   Main Application Entry Point
   """
   import sys
   import os
   
   # Setup paths
   project_root = os.path.dirname(os.path.abspath(__file__))
   framework_root = os.path.join(project_root, 'submodules', 'framework')
   
   sys.path.insert(0, project_root)
   sys.path.insert(0, framework_root)
   sys.path.insert(0, os.path.join(framework_root, 'src'))
   
   # Import framework
   from submodules.framework.src.main import app, setup_app
   from submodules.framework.src.modules import site_conf
   
   # Import your configuration
   from website.site_conf import MySiteConf
   from website.pages.home import home_bp
   
   # Change to framework directory for templates
   os.chdir(framework_root)
   
   # STEP 1: Configure site BEFORE setup_app
   site_conf.site_conf_obj = MySiteConf()
   site_conf.site_conf_app_path = framework_root
   
   # STEP 2: Initialize framework
   socketio = setup_app(app)
   
   # STEP 3: Register your pages
   app.register_blueprint(home_bp)
   
   # STEP 4: Run
   if __name__ == "__main__":
       print("Starting server on http://localhost:5001")
       socketio.run(app, debug=False, host='0.0.0.0', port=5001)

**Step 4: Run Your Website**

.. code-block:: bash

   python main.py

Visit ``http://localhost:5001`` to see your website!

Adding More Pages
^^^^^^^^^^^^^^^^^^

To add an "About" page to your website:

**1. Add route to your site configuration** (``website/site_conf.py``):

.. code-block:: python

   # In MySiteConf.__init__():
   self.add_sidebar_page("About", "information", "home.about")

**2. Add the route to your home page blueprint** (``website/pages/home.py``):

.. code-block:: python

   @home_bp.route('/about')
   def about():
       disp = Displayer()
       
       disp.add_generic({
           "id": "about",
           "title": "About Us"
       })
       
       disp.add_display_item(
           DisplayerItemText("This is my website built with ParalaX!")
       )
       
       return disp.display()

Or create a separate blueprint file (``website/pages/about.py``) and register it in ``main.py``.

Handling Form Data
^^^^^^^^^^^^^^^^^^

To create a form that handles user input, here's a complete working example from the manual test webapp:

.. literalinclude:: ../../tests/demo_support/demo_pages.py
   :language: python
   :pyobject: simple_form_demo
   :caption: tests/demo_support/demo_pages.py - Simple Form Example

This example demonstrates:
- Handling GET (show form) and POST (process submission) requests
- Using ``util_post_to_json()`` to parse form data
- Extracting values from the nested dictionary structure
- Displaying feedback to the user
- Creating a complete form with input and submit button

.. important::
   Always use ``util_post_to_json()`` to parse form data. The Displayer system creates hierarchical form field names (``module_id.field_name``), and this utility properly converts them to nested dictionaries.

Understanding the Project Structure
------------------------------------

Your website project has a specific structure that separates your code from the framework:

File Organization
^^^^^^^^^^^^^^^^^

.. code-block:: text

   my_website/
   ├── main.py                    # Entry point - configures and starts app
   │
   ├── website/                   # YOUR code lives here
   │   ├── site_conf.py          # Site configuration (navigation, branding)
   │   ├── config.json           # App settings (optional)
   │   ├── pages/                # Your page blueprints
   │   │   ├── __init__.py
   │   │   └── home.py          # Example: home page routes
   │   └── modules/              # Your custom modules
   │       ├── __init__.py
   │       └── my_action.py     # Example: custom threaded actions
   │
   └── submodules/
       └── framework/            # Framework code (git submodule)
           ├── src/              # Framework source
           ├── templates/        # Framework templates
           └── webengine/        # Framework static assets

Key Concepts
^^^^^^^^^^^^

**1. Separation of Concerns**

- **Your Code** (``website/``): Site-specific pages, logic, and configuration
- **Framework Code** (``submodules/framework/``): Reusable components, never modified

**2. Site Configuration**

Your ``website/site_conf.py`` must:

- Inherit from ``Site_conf``
- Define navigation, branding, and settings
- Be set **before** calling ``setup_app()``

**3. Path Management**

``main.py`` handles paths so your code and framework code can find each other:

.. code-block:: python

   # Setup Python import paths
   sys.path.insert(0, project_root)
   sys.path.insert(0, framework_root)
   
   # Change to framework directory for templates
   os.chdir(framework_root)

Troubleshooting
---------------

Template Not Found Error
^^^^^^^^^^^^^^^^^^^^^^^^^

**Error**: ``jinja2.exceptions.TemplateNotFound: 'base_content_reloader.j2'``

**Cause**: The working directory is not set to the framework root.

**Solution**: Ensure ``main.py`` includes:

.. code-block:: python

   import os
   framework_root = os.path.join(project_root, 'submodules', 'framework')
   os.chdir(framework_root)  # Must be done before setup_app()

Module Import Errors
^^^^^^^^^^^^^^^^^^^^

**Error**: ``ModuleNotFoundError: No module named 'submodules.framework.src'``

**Cause**: Python can't find the framework or your website code.

**Solution**: Verify ``main.py`` has correct path setup:

.. code-block:: python

   import sys
   import os
   
   project_root = os.path.dirname(os.path.abspath(__file__))
   framework_root = os.path.join(project_root, 'submodules', 'framework')
   
   sys.path.insert(0, project_root)
   sys.path.insert(0, framework_root)
   sys.path.insert(0, os.path.join(framework_root, 'src'))

Form Data Not Parsing
^^^^^^^^^^^^^^^^^^^^^

**Issue**: Form values are ``None`` or not accessible.

**Cause**: Not using ``util_post_to_json()`` to parse form data.

**Solution**: Always use the framework utility:

.. code-block:: python

   from submodules.framework.src.modules.utilities import util_post_to_json
   
   @home_bp.route("/submit", methods=["POST"])
   def submit():
       data_in = util_post_to_json(request.form.to_dict())
       my_data = data_in.get("my_module_id", {})

Site Configuration Not Applied
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Issue**: Site name, navigation not showing correctly.

**Cause**: Site configuration not set before ``setup_app()``.

**Solution**: In ``main.py``, always set configuration first:

.. code-block:: python

   # 1. Import and set site_conf BEFORE setup_app
   from website.site_conf import MySiteConf
   site_conf.site_conf_obj = MySiteConf()
   
   # 2. THEN call setup_app
   socketio = setup_app(app)
   
   # 3. THEN register your blueprints
   app.register_blueprint(home_bp)

Next Steps
----------

Congratulations! You now have the framework installed and have created your first application. Here's what to learn next:

1. **Explore Components**
   
   Run the demo app to see all available display items:
   
   .. code-block:: bash
   
      python tests/manual_test_webapp.py

2. **Learn the Display System**
   
   Read :doc:`tutorials` → "Building Your First Application" for detailed examples.

3. **Add Background Tasks**
   
   See :doc:`tutorials` → "Adding Background Tasks" to learn threaded actions.

4. **Implement Authentication**
   
   Follow :doc:`tutorials` → "Implementing Authentication" for user management.

5. **Study the Architecture**
   
   Read :doc:`framework` to understand how components work together.

6. **Browse Examples**
   
   Check :doc:`examples` for code patterns and recipes.

7. **API Reference**
   
   Explore :doc:`framework_classes` for complete class documentation.

Tips for Beginners
^^^^^^^^^^^^^^^^^^

1. **Start Simple**: Begin with single-page apps before adding complexity
2. **Use the Demo**: The demo app (``tests/manual_test_webapp.py``) is your best reference
3. **Check Logs**: Application logs are in ``logs/`` directory
4. **Read Docstrings**: Framework classes have detailed docstrings
5. **Run Tests**: Use tests as examples of correct usage