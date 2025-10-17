Changelog
=========

All notable changes to the ParalaX Web Framework.

Version 1.0.0 (Current)
-----------------------

**Release Date**: 2025

Major Features
^^^^^^^^^^^^^^

* **Modular Architecture**: Complete separation between framework core and application code
* **Authentication System**: Role-based access control with permission management
* **Background Tasks**: Thread manager with progress tracking and console output
* **Real-Time Updates**: WebSocket support via Flask-SocketIO for live page updates
* **Dynamic UI System**: Programmatic UI generation with Displayer, layouts, and items
* **Multi-User Support**: Session isolation for concurrent users
* **Comprehensive Testing**: Full pytest suite with fixtures and integration tests
* **Documentation**: Complete Sphinx documentation with tutorials and examples

Core Components
^^^^^^^^^^^^^^^

Web Engine
""""""""""

* Flask-based application with Jinja2 templating
* Automatic blueprint registration for pages
* Session management with filesystem storage
* Static asset serving with cache control

Authentication
""""""""""""""

* User management with bcrypt password hashing
* Permission-based access control (module + action)
* GUEST user support with restricted permissions
* Admin user capabilities
* JSON-based user storage with atomic writes

Displayer System
""""""""""""""""

* Module-based page organization (cards/forms)
* Multiple layout types (Vertical, Horizontal, Grid, Tabs, Accordion)
* Rich display items library (20+ component types)
* Automatic permission checking for modules
* Resource registry for CSS/JS dependencies
* Responsive Bootstrap 5 styling

Background Tasks
""""""""""""""""

* Threaded action base class with lifecycle management
* Console output capture (process and custom)
* Progress tracking (0-100%)
* Per-user thread isolation
* Thread manager registry
* Automatic cleanup of completed threads

Scheduler
"""""""""

* Real-time updates via SocketIO
* Short-term scheduler (1s intervals)
* Long-term scheduler (minute-based intervals)
* Message queue system for user isolation
* Dynamic button/modal/badge updates
* Log message broadcasting

Utilities
"""""""""

* JSON file I/O with error handling
* Breadcrumb navigation management
* Serial port enumeration (optional)
* Form data processing helpers
* Directory and file operations

Built-in Pages
^^^^^^^^^^^^^^

* ``/`` - Home page (customizable)
* ``/login`` - User authentication
* ``/admin`` - User and permission management
* ``/threads`` - Background task monitoring
* ``/settings`` - Application settings
* ``/user`` - User profile management
* ``/packager`` - Resource packaging (optional)
* ``/updater`` - Application updates (optional)

Known Issues
^^^^^^^^^^^^

* SQLite database locking with high concurrency (use WAL mode)
* Thread manager doesn't persist across restarts
* Large console outputs may consume memory (capped at 1000 lines)
* WebSocket connections require manual cleanup on disconnect

Roadmap
-------

Planned for Future Releases
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* **Database Integration**: Built-in ORM support with migrations
* **RESTful API**: Automatic API generation for data models
* **Enhanced Workflows**: Visual workflow builder and editor
* **Plugin System**: Hot-loadable plugins without restart
* **Containerization**: Official Docker images
* **Cloud Deployment**: AWS/Azure/GCP deployment guides
* **Advanced Monitoring**: Built-in metrics and performance tracking
* **Theme System**: Customizable themes beyond Bootstrap
* **i18n Support**: Multi-language interface
* **Mobile Responsive**: Enhanced mobile layouts

Under Consideration
^^^^^^^^^^^^^^^^^^^

* GraphQL API support
* WebAssembly component integration
* Real-time collaboration features
* Advanced caching mechanisms
* Task scheduling persistence
* Distributed task execution
* SSO/OAuth integration
* Audit logging system

Migration Notes
---------------

From Pre-1.0 Versions
^^^^^^^^^^^^^^^^^^^^^^

If you're upgrading from development versions:

**Import Changes**

Old:

.. code-block:: python

   from src import displayer
   from src import threaded_action

New:

.. code-block:: python

   from src.modules.displayer import Displayer
   from src.modules.threaded.threaded_action import Threaded_action

**Authentication Changes**

Old:

.. code-block:: python

   from src.access_manager import Access_manager

New:

.. code-block:: python

   from src.modules.auth.auth_manager import auth_manager

**Module Structure**

* Modules now organized in ``src/modules/`` directory
* Each subsystem in its own package (auth, displayer, threaded, etc.)
* Pages moved to ``src/pages/`` directory
* Utilities consolidated in ``src/modules/utilities.py``

**Permission System**

* New granular permission system (module + action)
* GUEST user treated as regular user with restricted permissions
* Automatic permission checking in Displayer
* User context injection into Action and Threaded_action

**Breaking Changes**

1. **Module imports**: Must update all import statements
2. **Auth manager**: Now a singleton instance, not a class
3. **Displayer**: Automatic permission checks may affect existing pages
4. **Threaded actions**: New user context properties

**Migration Steps**

1. Update imports throughout your codebase
2. Test authentication flows
3. Review permission assignments
4. Update custom display items if any
5. Test background tasks
6. Run full test suite

Deprecation Policy
------------------

The framework follows semantic versioning:

* **Major versions** (X.0.0): Breaking changes, major features
* **Minor versions** (1.X.0): New features, backward compatible
* **Patch versions** (1.0.X): Bug fixes, security updates

Deprecated features will be:

1. Marked as deprecated in documentation
2. Logged with warnings when used
3. Maintained for at least one minor version
4. Removed in next major version

Contributing
------------

To suggest features or report issues:

1. Check existing issues on GitHub
2. Submit detailed bug reports with reproduction steps
3. Propose features with use cases and examples
4. Submit pull requests with tests

Development workflow:

.. code-block:: bash

   # Fork and clone
   git clone https://github.com/YourUsername/webframework.git
   cd webframework
   
   # Create virtual environment
   python3 -m venv .venv
   source .venv/bin/activate
   
   # Install in development mode
   pip install -e .[dev]
   
   # Run tests
   pytest tests/
   
   # Build docs
   cd docs
   sphinx-build -b html source build/html

See ``CONTRIBUTING.md`` for detailed guidelines.

Version History Summary
-----------------------

* **1.0.0** (2025) - Initial stable release with full feature set
* **0.9.0** (2024) - Beta release with core functionality
* **0.5.0** (2024) - Alpha release with basic framework
* **0.1.0** (2023) - Initial development version

For detailed changes, see the Git commit history.
