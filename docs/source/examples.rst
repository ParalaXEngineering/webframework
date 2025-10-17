Code Examples
=============

Practical code snippets and patterns for common tasks with the ParalaX Web Framework.

.. contents:: Examples Index
   :local:
   :depth: 2

Display System Examples
-----------------------

Basic Page Layout
^^^^^^^^^^^^^^^^^

.. code-block:: python

   from src.modules.displayer import Displayer, DisplayerItemText
   
   def simple_page():
       disp = Displayer()
       
       # Add a module (card)
       disp.add_generic({"id": "main", "title": "My Page"})
       
       # Add text content
       disp.add_display_item(DisplayerItemText("Hello World!"))
       
       return disp.display()

Multi-Column Layout
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from src.modules.displayer import (
       Displayer, DisplayerLayout, Layouts,
       DisplayerItemText, DisplayerItemBadge
   )
   
   def multi_column():
       disp = Displayer()
       disp.add_generic({"title": "Two Column Layout"})
       
       # Create 2-column layout (6 + 6 = 12 total)
       layout = DisplayerLayout(Layouts.HORIZONTAL, columns=[6, 6])
       disp.add_master_layout(layout)
       
       # Left column
       disp.add_display_item(DisplayerItemText("Left content"), column=0)
       
       # Right column
       disp.add_display_item(DisplayerItemBadge("Right badge"), column=1)
       
       return disp.display()

Nested Layouts
^^^^^^^^^^^^^^

.. code-block:: python

   from src.modules.displayer import (
       Displayer, DisplayerLayout, Layouts,
       DisplayerItemText
   )
   
   def nested_layout():
       disp = Displayer()
       disp.add_generic({"title": "Nested Layout"})
       
       # Outer horizontal layout
       outer = DisplayerLayout(Layouts.HORIZONTAL, columns=[8, 4])
       disp.add_master_layout(outer)
       
       # Inner vertical layout in left column
       inner = DisplayerLayout(Layouts.VERTICAL, parent_column=0)
       disp.add_child_layout(inner, parent_layout=outer)
       
       disp.add_display_item(DisplayerItemText("Item 1"))
       disp.add_display_item(DisplayerItemText("Item 2"))
       
       # Right column
       disp.add_display_item(DisplayerItemText("Sidebar"), column=1)
       
       return disp.display()

Display Items Collection
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from src.modules.displayer import (
       Displayer,
       DisplayerItemText, DisplayerItemButton,
       DisplayerItemInput, DisplayerItemSelect,
       DisplayerItemCheckbox, DisplayerItemTextarea,
       DisplayerItemBadge, DisplayerItemProgress,
       DisplayerItemImage, DisplayerItemLink
   )
   
   def showcase_items():
       disp = Displayer()
       disp.add_generic({"title": "Display Items"})
       
       # Text display
       disp.add_display_item(DisplayerItemText("Plain text"))
       
       # Button with callback
       disp.add_display_item(
           DisplayerItemButton("Click Me", callback="alert('Clicked!')")
       )
       
       # Input field
       disp.add_display_item(
           DisplayerItemInput("username", label="Username", placeholder="Enter name")
       )
       
       # Select dropdown
       disp.add_display_item(
           DisplayerItemSelect(
               "country",
               label="Country",
               options=[("us", "United States"), ("uk", "United Kingdom")]
           )
       )
       
       # Checkbox
       disp.add_display_item(
           DisplayerItemCheckbox("agree", label="I agree to terms")
       )
       
       # Textarea
       disp.add_display_item(
           DisplayerItemTextarea("comments", label="Comments", rows=4)
       )
       
       # Badge (colored label)
       disp.add_display_item(
           DisplayerItemBadge("Status", value="Active", color="success")
       )
       
       # Progress bar
       disp.add_display_item(
           DisplayerItemProgress("Progress", value=75, max_value=100)
       )
       
       # Image
       disp.add_display_item(
           DisplayerItemImage("logo.png", alt="Logo", width=200)
       )
       
       # Link
       disp.add_display_item(
           DisplayerItemLink("Visit Site", url="https://example.com")
       )
       
       return disp.display()

Forms Examples
--------------

Login Form
^^^^^^^^^^

.. code-block:: python

   from flask import request, session, redirect, url_for
   from src.modules.displayer import (
       Displayer, DisplayerItemInput, DisplayerItemButton
   )
   from src.modules.auth.auth_manager import auth_manager
   
   @app.route("/login", methods=["GET", "POST"])
   def login():
       if request.method == "POST":
           username = request.form.get("username")
           password = request.form.get("password")
           
           if auth_manager.authenticate(username, password):
               session['username'] = username
               return redirect(url_for('home'))
           else:
               error = "Invalid credentials"
       
       disp = Displayer()
       disp.add_generic({"id": "login", "title": "Login"})
       
       disp.add_display_item(
           DisplayerItemInput("username", label="Username")
       )
       disp.add_display_item(
           DisplayerItemInput("password", label="Password", input_type="password")
       )
       disp.add_display_item(
           DisplayerItemButton("Login", button_type="submit")
       )
       
       return disp.display()

Data Entry Form
^^^^^^^^^^^^^^^

.. code-block:: python

   from flask import request
   from src.modules.displayer import *
   
   @app.route("/add_item", methods=["GET", "POST"])
   def add_item():
       if request.method == "POST":
           # Process form
           name = request.form.get("name")
           category = request.form.get("category")
           quantity = request.form.get("quantity")
           notes = request.form.get("notes")
           
           # Save to database or process...
           return "Item added successfully!"
       
       disp = Displayer()
       disp.add_generic({"title": "Add New Item"})
       
       disp.add_display_item(
           DisplayerItemInput("name", label="Item Name", required=True)
       )
       disp.add_display_item(
           DisplayerItemSelect(
               "category",
               label="Category",
               options=[
                   ("electronics", "Electronics"),
                   ("tools", "Tools"),
                   ("supplies", "Supplies")
               ]
           )
       )
       disp.add_display_item(
           DisplayerItemInput("quantity", label="Quantity", input_type="number")
       )
       disp.add_display_item(
           DisplayerItemTextarea("notes", label="Notes", rows=3)
       )
       disp.add_display_item(
           DisplayerItemButton("Add Item", button_type="submit")
       )
       
       return disp.display()

Background Tasks Examples
-------------------------

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

Authentication Examples
-----------------------

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

Scheduler Examples
------------------

Periodic Task Registration
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from src.modules.scheduler.scheduler import Scheduler_LongTerm
   
   def cleanup_old_files():
       """Remove files older than 30 days"""
       # Your cleanup logic
       pass
   
   def check_system_health():
       """Check system health metrics"""
       # Your monitoring logic
       pass
   
   # Register long-term tasks
   lt_scheduler = Scheduler_LongTerm()
   lt_scheduler.register_function(cleanup_old_files, period=60)  # Every 60 min
   lt_scheduler.register_function(check_system_health, period=5)  # Every 5 min
   lt_scheduler.start()

Custom Real-Time Updates
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from src.modules import scheduler
   
   class MonitoringTask(Threaded_action):
       def action(self):
           while self.m_running:
               # Collect data
               cpu = get_cpu_usage()
               memory = get_memory_usage()
               
               # Push update to all clients
               if scheduler.scheduler_obj:
                   scheduler.scheduler_obj.emit_log(
                       f"CPU: {cpu}% | Memory: {memory}%",
                       level="info"
                   )
               
               time.sleep(5)  # Update every 5 seconds

Utilities Examples
------------------

File Operations
^^^^^^^^^^^^^^^

.. code-block:: python

   from src.modules.utilities import (
       read_json_file, write_json_file,
       ensure_directory_exists
   )
   
   # Read JSON
   config = read_json_file("config.json")
   
   # Write JSON
   data = {"setting": "value"}
   write_json_file("output.json", data)
   
   # Ensure directory exists
   ensure_directory_exists("data/logs")

Breadcrumbs
^^^^^^^^^^^

.. code-block:: python

   from src.modules.utilities import set_breadcrumbs
   
   @app.route("/admin/users/edit")
   def edit_user():
       breadcrumbs = [
           ("Home", url_for('home')),
           ("Admin", url_for('admin')),
           ("Users", url_for('users')),
           ("Edit", None)  # Current page
       ]
       set_breadcrumbs(breadcrumbs)
       
       # ... render page

Complete Application Example
-----------------------------

Minimal Production App
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from flask import Flask, session, redirect, url_for
   from src.main import setup_app
   from src.modules.displayer import Displayer
   from src.modules.auth.auth_manager import auth_manager
   
   app = Flask(__name__)
   app.secret_key = "production-secret-key-change-this"
   setup_app(app)
   
   # Initialize users
   if auth_manager:
       auth_manager.create_user("admin", "admin123", is_admin=True)
   
   @app.route("/")
   def home():
       if 'username' not in session:
           return redirect(url_for('auth.login'))
       
       disp = Displayer()
       disp.add_generic({"title": f"Welcome, {session['username']}!"})
       return disp.display()
   
   if __name__ == "__main__":
       app.run(debug=False, host="0.0.0.0", port=5001)

More Examples
-------------

For complete working examples, see:

* **Demo Application**: ``tests/manual_test_webapp.py``
* **Component Showcase**: ``tests/demo_support/component_showcase.py``
* **Layout Examples**: ``tests/demo_support/layout_showcase.py``
* **Unit Tests**: ``tests/unit/`` directory

Run the demo to see everything in action:

.. code-block:: bash

   python tests/manual_test_webapp.py

Visit http://localhost:5001 to explore all features interactively.
