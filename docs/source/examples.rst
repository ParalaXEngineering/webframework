Code Examples
=============

Practical code snippets and patterns for common tasks with the ParalaX Web Framework.

.. contents:: Examples Index
   :local:
   :depth: 2

.. note::

   **Live Examples Available!**
   
   All examples in this document are implemented and testable:
   
   - **Display System Examples**: See ``tests/manual_test_webapp.py`` for comprehensive UI component demonstrations
   - **All Other Examples**: Run the example website with ``python example_website/main.py`` and visit ``/examples``
   
   The example website has all framework features enabled and provides interactive demonstrations of every code pattern shown below.

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

   **Live Demo Available:** Visit ``/examples/threads`` in the example website to see these tasks in action!

Simple Background Task
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from src.modules.threaded.threaded_action import Threaded_action
   import time
   
   class SimpleTask(Threaded_action):
       m_default_name = "Simple Task"
       
       def action(self):
           self.console_write("Starting task...")
           
           for i in range(10):
               time.sleep(1)
               self.console_write(f"Step {i+1}/10")
               self.m_running_state = (i + 1) * 10  # Progress %
           
           self.console_write("Task complete!", level="SUCCESS")

Task with Parameters
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   class ParameterizedTask(Threaded_action):
       m_default_name = "Parameterized Task"
       
       def __init__(self, iterations, delay):
           super().__init__()
           self.iterations = iterations
           self.delay = delay
       
       def action(self):
           self.console_write(
               f"Starting task with {self.iterations} iterations, "
               f"{self.delay}s delay"
           )
           
           for i in range(self.iterations):
               time.sleep(self.delay)
               progress = int((i + 1) / self.iterations * 100)
               self.m_running_state = progress
               self.console_write(f"Progress: {progress}%")
           
           self.console_write("Done!", level="SUCCESS")
   
   # Usage
   @app.route("/start_task")
   def start_task():
       task = ParameterizedTask(iterations=20, delay=0.5)
       task.start()
       return "Task started"

Task with Subprocess
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import subprocess
   
   class CommandTask(Threaded_action):
       m_default_name = "Command Runner"
       
       def __init__(self, command):
           super().__init__()
           self.command = command
       
       def action(self):
           self.console_write(f"Running: {self.command}")
           
           # Start subprocess
           process = subprocess.Popen(
               self.command,
               shell=True,
               stdout=subprocess.PIPE,
               stderr=subprocess.PIPE,
               text=True
           )
           
           # Stream output
           for line in process.stdout:
               self.console_write(line.strip())
           
           # Wait for completion
           process.wait()
           
           if process.returncode == 0:
               self.console_write("Command succeeded!", level="SUCCESS")
           else:
               stderr = process.stderr.read()
               self.console_write(f"Command failed: {stderr}", level="ERROR")

Task with Error Handling
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   class RobustTask(Threaded_action):
       m_default_name = "Robust Task"
       
       def action(self):
           try:
               self.console_write("Starting work...")
               
               # Simulate work that might fail
               result = self.do_work()
               
               self.console_write(f"Result: {result}", level="SUCCESS")
               
           except FileNotFoundError as e:
               self.console_write(f"File not found: {e}", level="ERROR")
               self.m_error = str(e)
               
           except Exception as e:
               self.console_write(f"Unexpected error: {e}", level="ERROR")
               self.m_error = str(e)
               import traceback
               self.console_write(traceback.format_exc(), level="ERROR")
           
           finally:
               self.console_write("Task finished.")
       
       def do_work(self):
           # Your actual work here
           return "success"

Forms Examples
--------------

.. note::

   **Live Demo Available:** Visit ``/examples/forms`` in the example website to try interactive forms!

Data Entry Form
^^^^^^^^^^^^^^^

.. code-block:: python

   from flask import request
   from src.modules.displayer import *
   from src.modules import utilities
   
   @app.route("/add_item", methods=["GET", "POST"])
   def add_item():
       disp = Displayer()
       disp.add_generic("add_item")
       disp.set_title("Add New Item")
       
       if request.method == "POST":
           # Parse form data
           data_in = utilities.util_post_to_json(request.form.to_dict())
           form_data = data_in.get("add_item", {})
           
           name = form_data.get("name", "")
           category = form_data.get("category", "")
           quantity = form_data.get("quantity", "")
           notes = form_data.get("notes", "")
           
           # Show success message
           disp.add_display_item(
               DisplayerItemAlert(
                   text=f"Item '{name}' added successfully!",
                   highlightType=BSstyle.SUCCESS
               )
           )
       else:
           # Show form
           disp.add_display_item(
               DisplayerItemInputString("name", "Item Name *", "")
           )
           disp.add_display_item(
               DisplayerItemInputSelect(
                   "category",
                   "Category",
                   "electronics",
                   ["electronics", "tools", "supplies"],
                   ["Electronics", "Tools", "Supplies"]
               )
           )
           disp.add_display_item(
               DisplayerItemInputString("quantity", "Quantity", "1")
           )
           disp.add_display_item(
               DisplayerItemInputText("notes", "Notes", "")
           )
           disp.add_display_item(
               DisplayerItemButton("btn_submit", "Add Item", icon="plus")
           )
       
       return render_template("base_content.j2", content=disp.display(), target="add_item")

Authentication Examples
-----------------------

.. note::

   **Live Demo Available:** Visit ``/examples/auth`` in the example website to see authentication in action!
   
   **Enabling Authentication:** To use authentication features, enable them in your site_conf:
   
   .. code-block:: python
   
      class MySiteConf(Site_conf):
          def __init__(self):
              super().__init__()
              self.enable_authentication()  # Enables auth and adds login pages

Creating Users
^^^^^^^^^^^^^^

.. code-block:: python

   from src.modules.auth.auth_manager import auth_manager
   
   def setup_users():
       # Create admin
       auth_manager.create_user("admin", "secure_password", is_admin=True)
       
       # Create regular users
       auth_manager.create_user("john", "john123")
       auth_manager.create_user("jane", "jane456")
       
       # Grant permissions
       auth_manager.grant_permission("john", "Dashboard", "view")
       auth_manager.grant_permission("jane", "Dashboard", "view")
       auth_manager.grant_permission("jane", "Dashboard", "edit")

Checking Authentication Status
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from flask import session
   
   @app.route("/profile")
   def profile():
       # Get current user from session
       username = session.get('username', 'GUEST')
       
       if username and username != "GUEST":
           # User is authenticated
           return f"Welcome, {username}!"
       else:
           # User is not logged in
           return "Please log in to view your profile."

Login/Logout
^^^^^^^^^^^^

.. code-block:: python

   from flask import session, redirect, url_for
   
   @app.route("/login", methods=["POST"])
   def do_login():
       username = request.form.get("username")
       password = request.form.get("password")
       
       if auth_manager.authenticate(username, password):
           session['username'] = username
           session['user_session_id'] = str(uuid.uuid4())
           return redirect(url_for('home'))
       else:
           return "Login failed", 401
   
   @app.route("/logout")
   def logout():
       session.pop('username', None)
       session.pop('user_session_id', None)
       return redirect(url_for('login'))

Permission Checking
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from flask import abort
   
   def require_permission(module_name, action):
       """Decorator to check permissions"""
       def decorator(f):
           @wraps(f)
           def decorated(*args, **kwargs):
               username = session.get('username')
               if not username:
                   abort(401)  # Unauthorized
               
               if not auth_manager.has_permission(username, module_name, action):
                   abort(403)  # Forbidden
               
               return f(*args, **kwargs)
           return decorated
       return decorator
   
   @app.route("/admin/settings")
   @require_permission("Settings", "edit")
   def admin_settings():
       return "Admin settings page"

Automatic Module Protection
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   class ProtectedModule:
       m_default_name = "Protected Module"
       m_required_permission = "AdminPanel"
       m_required_action = "view"
   
   @app.route("/protected")
   def protected_page():
       module = ProtectedModule()
       
       disp = Displayer()
       disp.add_module(module)  # Automatically checks permissions
       
       # Only users with AdminPanel:view permission will see content
       disp.add_display_item(DisplayerItemText("Sensitive data"))
       
       return disp.display()

Feature Activation in Site_conf
--------------------------------

The framework provides feature flags to enable/disable components as needed.

Enabling Individual Features
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from src.modules.site_conf import Site_conf
   
   class MySiteConf(Site_conf):
       def __init__(self):
           super().__init__()
           
           # Enable specific features
           self.enable_authentication()      # Login/logout + auth pages
           self.enable_threads()             # Thread monitor
           self.enable_scheduler()           # Real-time SocketIO updates
           self.enable_long_term_scheduler() # Periodic tasks
           self.enable_log_viewer()          # Log viewing page
           self.enable_admin_panel()         # Admin tools
           
           # Each enable_* method:
           # 1. Sets the feature flag
           # 2. Initializes the feature in setup_app()
           # 3. Optionally adds related pages to sidebar

Enabling All Features
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   class DemoSiteConf(Site_conf):
       def __init__(self):
           super().__init__()
           
           # Enable everything for demo/testing
           self.enable_all_features()
           
           # Customize as needed
           self.app_details(
               name="Demo App",
               version="1.0.0",
               icon="test-tube"
           )

Feature Flags Reference
^^^^^^^^^^^^^^^^^^^^^^^

Available feature flags in ``Site_conf``:

- ``m_enable_authentication`` - Auth system and login pages
- ``m_enable_threads`` - Thread monitoring and management
- ``m_enable_scheduler`` - Real-time SocketIO scheduler
- ``m_enable_long_term_scheduler`` - Periodic task scheduler
- ``m_enable_log_viewer`` - Log viewing interface
- ``m_enable_admin_panel`` - Admin control panel
- ``m_enable_bug_tracker`` - Bug reporting system
- ``m_enable_settings`` - Settings configuration page

By default, **all features are disabled** (opt-in model). Enable only what you need.

More Examples
-------------

For complete working examples, see:

* **Example Website**: ``example_website/`` - Full demonstration with all features enabled
  
  - Run with: ``python example_website/main.py``
  - Visit: ``http://localhost:5000/examples`` for interactive code examples
  - All tutorials and examples from documentation are implemented

* **Manual Test Webapp**: ``tests/manual_test_webapp.py`` - Comprehensive display system showcase
  
  - Run with: ``python tests/manual_test_webapp.py``
  - Visit: ``http://localhost:5001`` to explore all UI components

* **Component Showcase**: ``tests/demo_support/component_showcase.py`` - All DisplayerItem types

* **Layout Examples**: ``tests/demo_support/layout_showcase.py`` - Various layout patterns

* **Unit Tests**: ``tests/unit/`` directory - Test examples for each module

.. tip::

   The example website demonstrates the feature activation system. Check ``example_website/website/site_conf.py`` 
   to see how ``enable_all_features()`` is used to activate authentication, threads, logging, and other framework features.
