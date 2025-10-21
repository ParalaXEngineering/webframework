Framework Architecture
**********************

Description
===========

The ParalaX Web Framework is a comprehensive Flask-based system designed for building tool management and monitoring web applications. It provides a solid foundation with built-in support for:

* Real-time updates via WebSocket (SocketIO)
* Background task management with threading
* User authentication and authorization
* Dynamic UI generation
* Module-based extensibility

Core Components
===============

Web Engine
----------

The web engine is built on **Flask** with **Jinja2** templates. It handles:

* HTTP request routing
* Template rendering
* Session management (via flask-session)
* WebSocket connections (via flask-socketio)
* Static file serving

The main application is defined in :class:`src.main` and can be initialized with custom configurations.

Scheduler
---------

The :class:`src.scheduler.Scheduler` class provides periodic task execution and real-time communication:

* Runs at configurable intervals
* Refreshes dynamic page elements (buttons, modals, status indicators)
* Uses SocketIO for push updates to clients
* Manages client connections and disconnections

Example usage:

.. code-block:: python

   from src.scheduler import Scheduler
   
   scheduler = Scheduler(app, socketio, interval=1.0)
   scheduler.start()

Thread Manager
--------------

The :class:`src.threaded_manager.Threaded_manager` maintains a registry of background threads:

* Registers new threads with unique identifiers
* Tracks thread status (running, stopped, completed)
* Provides thread lifecycle management
* Cleans up completed threads

This is essential for long-running operations that shouldn't block the web interface.

Threaded Actions
----------------

:class:`src.threaded_action.Threaded_action` provides a framework for creating background tasks (modules):

* Extends the base :class:`src.action.Action` class
* Runs in a separate thread
* Reports progress updates
* Handles errors gracefully
* Integrates with the Thread Manager

Users can create custom modules by inheriting from this class.

Site Configuration
------------------

:class:`src.site_conf.Site_conf` provides base configuration:

* Site metadata (title, description)
* Available modules/actions
* Navigation structure
* Custom settings

Site handlers should inherit from this class to customize behavior.

Optional Features System
------------------------

The framework provides a feature flag system that allows selective activation of components. This enables applications to include only the functionality they need, reducing complexity and resource usage.

Feature Flags
^^^^^^^^^^^^^

Features are controlled by flags set in the :class:`src.site_conf.Site_conf` class:

* **m_enable_authentication**: User authentication and authorization
* **m_enable_threads**: Background task monitoring
* **m_enable_scheduler**: Real-time updates via WebSocket
* **m_enable_long_term_scheduler**: Extended scheduler functionality
* **m_enable_log_viewer**: Web-based log file viewer
* **m_enable_bug_tracker**: Issue tracking integration
* **m_enable_settings**: Settings management interface
* **m_enable_updater**: Automatic update system
* **m_enable_packager**: Resource package creation

All flags default to ``False`` for minimal footprint.

Conditional Blueprint Registration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The framework conditionally registers Flask blueprints based on enabled features. This is controlled by the ``PAGE_FEATURE_REQUIREMENTS`` dictionary in ``src.main.py``:

.. code-block:: python

   PAGE_FEATURE_REQUIREMENTS = {
       "threads": ["m_enable_threads"],
       "scheduler": ["m_enable_scheduler"],
       "log": ["m_enable_log_viewer"],
       "bug_tracker": ["m_enable_bug_tracker"],
       "settings": ["m_enable_settings"],
       "admin": ["m_enable_authentication"],
       "user": ["m_enable_authentication"],
       "updater": ["m_enable_updater"],
       "packager": ["m_enable_packager"],
   }

During initialization, ``setup_app()`` checks each page's requirements and only registers blueprints when all required features are enabled. This prevents unnecessary route registration and reduces memory usage.

.. note::
   The ``common`` blueprint (home page and assets) is always registered regardless of feature flags.

Sidebar Organization
^^^^^^^^^^^^^^^^^^^^

Enabled features are automatically organized into a hierarchical navigation structure under a "System" section:

**System Title**
   - **Monitoring Section**
      - Threads (requires m_enable_threads)
      - Logs (requires m_enable_log_viewer)
   
   - **Tools Section**
      - Bug Tracker (requires m_enable_bug_tracker)
      - Settings (requires m_enable_settings)
   
   - **Deployment Section**
      - Updater (requires m_enable_updater)
      - Packager (requires m_enable_packager)

This organization is created automatically by the ``enable_*()`` methods using the ``_ensure_system_title()`` helper function.

Enabling Features
^^^^^^^^^^^^^^^^^

Features are enabled by calling methods in your ``Site_conf`` subclass:

.. code-block:: python

   from src.site_conf import Site_conf
   
   
   class MyAppConf(Site_conf):
       def __init__(self):
           super().__init__()
           
           # Enable authentication
           self.enable_authentication(add_to_sidebar=True)
           
           # Enable thread monitoring
           self.enable_threads(add_to_sidebar=True)
           
           # Enable scheduler (no sidebar item)
           self.enable_scheduler()
           
           # Or enable everything at once
           # self.enable_all_features(add_to_sidebar=True)

Each ``enable_*()`` method:

1. Sets the corresponding flag to ``True``
2. Optionally adds navigation items to the sidebar
3. Ensures proper section hierarchy

Configuration Timing
^^^^^^^^^^^^^^^^^^^^

The site configuration must be set **before** calling ``setup_app()`` to ensure conditional registration works correctly:

.. code-block:: python

   # In main.py
   from src.main import app, setup_app
   from src.modules import site_conf
   from website.site_conf import MyAppConf
   
   # STEP 1: Set configuration BEFORE setup
   site_conf.site_conf_obj = MyAppConf()
   
   # STEP 2: Initialize framework
   socketio = setup_app(app)
   
   # STEP 3: Register custom blueprints
   app.register_blueprint(my_custom_bp)

.. important::
   If ``site_conf.site_conf_obj`` is already set when ``setup_app()`` is called, the framework will **not** overwrite it. This allows pre-configuration of the site before framework initialization.

Display System
--------------

The :class:`src.displayer.Displayer` class creates dynamic UI elements:

* **Modules**: Top-level containers (forms, cards)
* **Layouts**: Organizational structures (vertical, horizontal, grid)
* **Items**: Individual UI components (buttons, inputs, displays)

All elements are rendered in the order they're added, providing predictable layouts.

Example:

.. code-block:: python

   from src.modules.displayer import Displayer, DisplayerItem
   
   disp = Displayer()
   module = {"id": "main", "title": "Control Panel"}
   disp.add_module(module)
   
   # Add items to the module
   item = DisplayerItem("btn_start", "Start", "button")
   disp.add_item(item)

Access Manager
--------------

The :class:`src.access_manager.Access_manager` handles authentication and authorization:

* User login/logout
* Password hashing (bcrypt)
* Role-based access control
* Session management

Configuration is done through application settings, not directly accessed by site handlers.

Utilities
---------

The :mod:`src.utilities` module provides helper functions:

* Breadcrumb navigation management
* Serial port enumeration
* JSON file I/O
* Form data processing
* File system operations
* Modal and dynamic content creation

Additional Features
===================

Updater
-------

The :class:`src.updater.Updater` can check for and apply updates:

* Connects to FTP/SFTP servers
* Downloads new versions
* Applies updates automatically
* Supports rollback on failure

Bug Tracker
-----------

Integration with issue tracking systems (e.g., Redmine) via :mod:`src.bug_tracker`.

Packager
--------

Tools for creating and managing resource packages for distribution.

Import Strategy
===============

The framework supports both standalone and submodule usage through a dual-import pattern:

.. code-block:: python

   # In each module
   try:
       from . import utilities  # Relative import (package mode)
   except ImportError:
       import utilities         # Absolute import (submodule mode)

This allows the framework to work in both scenarios without modification.

Optional Dependencies
=====================

Some features require optional dependencies:

* **pyserial**: For serial port communication
* **paramiko**: For SFTP connections
* **markdown**: For Markdown rendering
* **bcrypt**: For password hashing
* **python-redmine**: For Redmine integration

The framework gracefully handles missing dependencies, disabling related features.

Creating a Site Handler
=======================

To create a custom site handler:

1. **Inherit from Site_conf**:

   Here's a complete example from the manual test webapp:

   .. literalinclude:: ../../tests/manual_test_webapp.py
      :language: python
      :pyobject: TestSiteConf
      :caption: tests/manual_test_webapp.py - Complete Site Configuration

   This example demonstrates:
   - Setting application metadata
   - Building complex sidebar navigation with sections and submenus
   - Enabling all framework features with ``enable_all_features()``
   - Customizing static file paths
   - Adding context processors

   For a simpler starting point:

   .. code-block:: python

      from src.site_conf import Site_conf
      
      class MySiteHandler(Site_conf):
          def __init__(self):
              super().__init__()
              self.m_app = {
                  "name": "My Application",
                  "version": "1.0.0",
                  "icon": "rocket"
              }
              self.m_index = "Welcome to my application"
              
              # Enable only needed features
              self.enable_authentication(add_to_sidebar=True)
              self.enable_threads(add_to_sidebar=True)

2. **Define custom actions**:

   .. code-block:: python

      from src.threaded_action import Threaded_action
      
      class MyAction(Threaded_action):
          def run(self):
              # Your background task logic
              pass

3. **Register routes**:

   .. code-block:: python

      from flask import Blueprint
      
      my_bp = Blueprint('myapp', __name__)
      
      @my_bp.route('/custom')
      def custom_page():
          # Your route logic
          pass

4. **Initialize in main.py**:

   .. code-block:: python

      from my_site_handler import MySiteHandler
      from src.main import app, setup_app
      from src.modules import site_conf
      
      # Set configuration BEFORE setup_app
      site_conf.site_conf_obj = MySiteHandler()
      
      # Initialize framework
      socketio = setup_app(app)
      
      # Register custom blueprints
      app.register_blueprint(my_bp)