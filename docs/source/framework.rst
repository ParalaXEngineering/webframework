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

   .. code-block:: python

      from src.site_conf import Site_conf
      
      class MySiteHandler(Site_conf):
          def __init__(self):
              super().__init__()
              self.site_name = "My Application"
              self.site_description = "Custom management interface"

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
      
      site = MySiteHandler()
      app.register_blueprint(my_bp)