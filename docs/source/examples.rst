Code Examples
=============

Practical code snippets and patterns for common tasks with the ParalaX Web Framework.

.. contents:: Examples Index
   :local:
   :depth: 2

.. note::

   **Live Examples Available!**
   
   All examples in this document are implemented and testable in the manual test webapp:
   
   .. code-block:: bash
   
      python tests/manual_test_webapp.py
      # Visit http://localhost:5001
   
   The manual test webapp has all framework features enabled and provides interactive demonstrations of every code pattern shown below.

Display System Examples
-----------------------

For comprehensive display system examples including layouts, display items, and forms, 
refer to the **manual test webapp** at ``tests/manual_test_webapp.py``.

This test application provides live demonstrations of:

- Basic page layouts
- Multi-column layouts (2, 3, 4 columns)
- Nested layouts
- All DisplayerItem types
- Form inputs and validation
- Real-world component showcases

**To run the manual test webapp:**

.. code-block:: bash

   python tests/manual_test_webapp.py
   
Then visit ``http://localhost:5001`` to explore all display examples interactively.

Background Tasks Examples
-------------------------

.. note::

   **Live Demo Available:** Visit ``/threading-demo`` in the manual test webapp to see these tasks in action!

Simple Background Task
^^^^^^^^^^^^^^^^^^^^^^

The framework provides `DemoSchedulerAction` as a simple background task example with real-time progress updates:

.. literalinclude:: ../../Manual_Webapp/demo_support/demo_scheduler_action.py
   :language: python
   :pyobject: MySchedulerAction
   :caption: Manual_Webapp/demo_support/demo_scheduler_action.py

This task demonstrates:
- Real-time progress updates via SocketIO
- Button control (disable/enable)
- Popup notifications
- Dynamic content updates

Forms Examples
--------------

.. note::

   **Live Demo Available:** Visit ``/simple-form-demo`` in the manual test webapp to try the interactive form!

Simple Data Entry Form
^^^^^^^^^^^^^^^^^^^^^^

Basic form with text input and submission handling:

.. literalinclude:: ../../tests/demo_support/demo_pages.py
   :language: python
   :pyobject: simple_form_demo
   :caption: tests/demo_support/demo_pages.py - Simple Form Demo

Key concepts demonstrated:
- Using ``util_post_to_json()`` to parse form data
- Accessing form values from nested dictionaries
- Displaying submitted data back to the user
- Basic form validation

Authentication Examples
-----------------------

.. note::

   **Live Demo Available:** Visit ``/auth-demo`` routes in the manual test webapp to see authentication in action!
   
   **Enabling Authentication:** To use authentication features, enable them in your site_conf:
   
   .. code-block:: python
   
      class MySiteConf(Site_conf):
          def __init__(self):
              super().__init__()
              self.enable_authentication()  # Enables auth and adds login pages

Registering Module Permissions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**IMPORTANT:** All modules must register their permissions at the top of their file. This makes permissions visible to developers and allows the admin interface to manage them.

By default, every module has an implicit ``view`` permission. To add custom actions (like ``upload``, ``execute``, ``configure``), register them explicitly:

.. code-block:: python

   """
   File Manager Admin Page - Flask blueprint for file browsing and management UI.
   """
   
   from flask import Blueprint, request, session
   from modules.auth.permission_registry import permission_registry
   from modules.auth.auth_manager import auth_manager
   
   # Register module permissions at the TOP of the file (view is implicit)
   permission_registry.register_module("FileManager", ["upload", "download", "delete", "edit"])
   # This creates permissions: view (implicit), upload, download, delete, edit
   
   bp = Blueprint("file_manager_admin", __name__, url_prefix="/file_manager")
   
   # ... rest of your module code

**Permission Registration Rules:**

* **Always register at file top** - Makes permissions visible and discoverable
* **View is implicit** - Every module automatically has ``view`` permission
* **Use lowercase names** - Convention: ``upload``, ``execute``, ``configure``, ``delete``
* **Module with view only** - Can explicitly register empty list: ``register_module("Reports", [])``
* **No hardcoded CRUD** - Old system auto-added ``read/write/delete``, now you control everything

**Common Permission Patterns:**

.. code-block:: python

   # Simple module (view only)
   permission_registry.register_module("Dashboard", [])
   
   # File management
   permission_registry.register_module("FileManager", ["upload", "download", "delete", "edit"])
   
   # Task execution
   permission_registry.register_module("Scheduler", ["execute", "configure"])
   
   # Threaded operations
   permission_registry.register_module("DataProcessor", ["execute", "abort"])

The framework provides three demo pages showing different access levels:

Public Page (Login Required)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Any logged-in user can access this page:

.. literalinclude:: ../../tests/demo_support/demo_pages.py
   :language: python
   :pyobject: auth_accessible
   :caption: tests/demo_support/demo_pages.py - Public Demo Page

Protected Page (Permission Required)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Requires specific permission to access:

.. literalinclude:: ../../tests/demo_support/demo_pages.py
   :language: python
   :pyobject: auth_restricted
   :caption: tests/demo_support/demo_pages.py - Protected Demo Page

The framework automatically checks permissions when ``add_module()`` is called with an action that has ``m_required_permission`` set.

Checking Permissions in Routes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use decorators to protect routes with specific permissions:

.. code-block:: python

   from modules.auth.auth_manager import auth_manager
   
   # Protect route with module permission
   @bp.route("/upload", methods=["GET", "POST"])
   @auth_manager.require_permission("FileManager", "upload")
   def upload_page():
       """Only users with 'upload' permission can access."""
       return render_template("upload.html")
   
   # Protect with view permission (default)
   @bp.route("/files")
   @auth_manager.require_permission("FileManager", "view")
   def list_files():
       """Any user with access to FileManager can view."""
       return render_template("files.html")

For API endpoints, check permissions manually and return appropriate errors:

.. code-block:: python

   @bp.route("/api/upload", methods=["POST"])
   def api_upload():
       current_user = session.get('user')
       
       # Check permission manually
       if not auth_manager.has_permission(current_user, "FileManager", "upload"):
           return jsonify({
               "error": "Permission denied: You need 'upload' permission. Contact your administrator."
           }), 403
       
       # Process upload...
       return jsonify({"success": True})

Conditional UI Elements Based on Permissions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Show or hide UI elements based on user permissions:

.. code-block:: python

   from modules.auth.auth_manager import auth_manager
   from modules.displayer import Displayer, DisplayerItemButton, DisplayerItemAlert, BSstyle
   
   @bp.route("/files")
   @auth_manager.require_permission("FileManager", "view")
   def file_list():
       disp = Displayer()
       
       # Check user permissions
       current_user = session.get('user', 'GUEST')
       can_upload = auth_manager.has_permission(current_user, "FileManager", "upload")
       can_delete = auth_manager.has_permission(current_user, "FileManager", "delete")
       
       # Show upload button only if permitted
       if can_upload:
           disp.add_display_item(DisplayerItemButton("upload_btn", "Upload File"))
       else:
           disp.add_display_item(DisplayerItemAlert(
               "You need 'upload' permission to upload files. Contact your administrator.",
               BSstyle.WARNING
           ))
       
       # Conditionally add delete actions to file list
       for file in files:
           actions = [{"icon": "download", "url": f"/download/{file.id}"}]
           
           if can_delete:
               actions.append({"icon": "trash", "url": f"/delete/{file.id}"})
           
           # Add file row with conditional actions...
       
       return disp.display()

Admin-Only Page (Group Required)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Requires admin group membership:

.. literalinclude:: ../../tests/demo_support/demo_pages.py
   :language: python
   :pyobject: auth_admin
   :caption: tests/demo_support/demo_pages.py - Admin Demo Page

Feature Activation in Site_conf
--------------------------------

The framework provides feature flags to enable/disable components as needed.

Enabling All Features
^^^^^^^^^^^^^^^^^^^^^

The manual test webapp demonstrates enabling all features at once:

.. literalinclude:: ../../tests/manual_test_webapp.py
   :language: python
   :pyobject: TestSiteConf
   :caption: tests/manual_test_webapp.py - Complete Feature Set

This configuration:
- Enables all framework features
- Adds all pages to sidebar with organized sections
- Configures application metadata

Enabling Individual Features
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For production applications, enable only the features you need:

.. code-block:: python

   from src.modules.site_conf import Site_conf
   
   class MySiteConf(Site_conf):
       def __init__(self):
           super().__init__()
           
           # Enable specific features
           self.enable_authentication(add_to_sidebar=True)
           self.enable_threads(add_to_sidebar=True)
           self.enable_scheduler()  # No sidebar item
           self.enable_log_viewer(add_to_sidebar=True)

Each ``enable_*()`` method:
1. Sets the corresponding feature flag to ``True``
2. Initializes required components
3. Optionally adds navigation items to the sidebar (organized into System > sections)

More Examples
-------------

For complete working examples, see:

* **Manual Test Webapp**: ``tests/manual_test_webapp.py`` - Comprehensive framework demonstration
  
  - Run with: ``python tests/manual_test_webapp.py``
  - Visit: ``http://localhost:5001`` to explore all features
  - Includes all examples from this documentation

* **Demo Pages**: ``tests/demo_support/demo_pages.py`` - Interactive code examples
  
  - Simple Form Demo: ``/simple-form-demo``
  - Threading Demo: ``/threading-demo``
  - Scheduler Demo: ``/scheduler-demo``
  - Workflow Demo: ``/workflow-demo``
  - Auth Demos: ``/auth/accessible``, ``/auth/restricted``, ``/auth/admin``

* **Component Showcase**: ``tests/demo_support/component_showcase.py`` - All DisplayerItem types

* **Layout Examples**: ``tests/demo_support/layout_showcase.py`` - Various layout patterns
  
  - Vertical layouts
  - Horizontal layouts
  - Table layouts
  - Tab layouts
  - Spacer layouts

* **Unit Tests**: ``tests/unit/`` and ``tests/integration/`` - Test examples for each module

.. tip::

   All demo files are heavily commented and designed to be used as reference implementations. 
   They demonstrate best practices and proper usage patterns for the framework.
