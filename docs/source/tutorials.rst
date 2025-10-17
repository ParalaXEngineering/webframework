Tutorials
=========

Step-by-step guides for common use cases with the ParalaX Web Framework.

.. contents:: Tutorial Topics
   :local:
   :depth: 2

Tutorial 1: Building Your First Application
--------------------------------------------

Let's create a simple web application from scratch.

Step 1: Project Setup
^^^^^^^^^^^^^^^^^^^^^^

Create a new directory and virtual environment:

.. code-block:: bash

   mkdir my_webapp
   cd my_webapp
   python3 -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   # .venv\Scripts\activate   # Windows

Step 2: Install Framework
^^^^^^^^^^^^^^^^^^^^^^^^^^

Install the framework as a dependency:

.. code-block:: bash

   # Clone as submodule (recommended)
   git submodule add https://github.com/ParalaXEngineering/webframework.git framework
   pip install -r framework/requirements.txt
   
   # OR install in development mode
   git clone https://github.com/ParalaXEngineering/webframework.git
   cd webframework
   pip install -e .
   cd ..

Step 3: Create Your App
^^^^^^^^^^^^^^^^^^^^^^^^

Create ``app.py``:

.. code-block:: python

   from flask import Flask
   from src.main import setup_app
   from src.modules.displayer import Displayer, DisplayerItemText, DisplayerItemButton
   
   # Create Flask app
   app = Flask(__name__)
   app.secret_key = "my-secret-key-change-this"
   
   # Initialize framework
   setup_app(app)
   
   # Create home page
   @app.route("/")
   def home():
       disp = Displayer()
       
       # Add a module (card container)
       disp.add_generic({"id": "welcome", "title": "Welcome to My App"})
       
       # Add some content
       disp.add_display_item(
           DisplayerItemText("This is my first ParalaX application!")
       )
       
       disp.add_display_item(
           DisplayerItemButton("Click Me", callback="alert('Hello!')")
       )
       
       return disp.display()
   
   if __name__ == "__main__":
       app.run(debug=True, host="0.0.0.0", port=5001)

Step 4: Run Your App
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   python app.py

Visit ``http://localhost:5001`` in your browser!

Tutorial 2: Adding Background Tasks
------------------------------------

Learn how to run long-running operations without blocking the UI.

Creating a Threaded Action
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create ``my_tasks.py``:

.. code-block:: python

   from src.modules.threaded.threaded_action import Threaded_action
   import time
   
   class DataProcessingTask(Threaded_action):
       """Background task that processes data"""
       
       m_default_name = "Data Processor"
       m_type = "data_processing"
       
       def __init__(self, data_size=100):
           super().__init__()
           self.data_size = data_size
       
       def action(self):
           """Main work happens here"""
           self.console_write(f"Starting to process {self.data_size} items...")
           
           for i in range(self.data_size):
               # Simulate processing
               time.sleep(0.1)
               
               # Update progress (0-100)
               self.m_running_state = int((i + 1) / self.data_size * 100)
               
               # Log progress
               if (i + 1) % 10 == 0:
                   self.console_write(f"Processed {i + 1}/{self.data_size} items")
           
           self.console_write("Processing complete!", level="SUCCESS")
           self.m_running_state = 100

Using the Task in Your App
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add to ``app.py``:

.. code-block:: python

   from my_tasks import DataProcessingTask
   from flask import redirect, url_for
   
   @app.route("/process")
   def process_data():
       """Start background processing"""
       task = DataProcessingTask(data_size=50)
       task.start()
       return redirect(url_for('threads.view'))  # Redirect to threads page

Monitoring Progress
^^^^^^^^^^^^^^^^^^^

The framework automatically provides a threads monitoring page at ``/threads``.
Users can see:

- Active threads and their progress
- Console output from each thread
- Thread status (running, completed, error)

Tutorial 3: Building a Dashboard
---------------------------------

Create a multi-column dashboard with real-time metrics.

Dashboard Page Structure
^^^^^^^^^^^^^^^^^^^^^^^^

Create ``pages/dashboard.py``:

.. code-block:: python

   from flask import Blueprint
   from src.modules.displayer import (
       Displayer, DisplayerLayout, Layouts,
       DisplayerItemBadge, DisplayerItemProgress,
       DisplayerItemText
   )
   import psutil  # pip install psutil
   
   dashboard_bp = Blueprint('dashboard', __name__)
   
   @dashboard_bp.route('/dashboard')
   def dashboard():
       disp = Displayer()
       
       # Page title
       disp.add_generic({"id": "dash", "title": "System Dashboard"})
       
       # Create 3-column layout for metrics
       layout = DisplayerLayout(Layouts.HORIZONTAL, columns=[4, 4, 4])
       disp.add_master_layout(layout)
       
       # CPU metric
       cpu_percent = psutil.cpu_percent(interval=1)
       cpu_color = "success" if cpu_percent < 50 else "warning" if cpu_percent < 80 else "danger"
       disp.add_display_item(
           DisplayerItemBadge("CPU Usage", value=f"{cpu_percent}%", color=cpu_color),
           column=0
       )
       
       # Memory metric
       mem = psutil.virtual_memory()
       mem_color = "success" if mem.percent < 50 else "warning" if mem.percent < 80 else "danger"
       disp.add_display_item(
           DisplayerItemBadge("Memory", value=f"{mem.percent}%", color=mem_color),
           column=1
       )
       
       # Disk metric
       disk = psutil.disk_usage('/')
       disk_color = "success" if disk.percent < 50 else "warning" if disk.percent < 80 else "danger"
       disp.add_display_item(
           DisplayerItemBadge("Disk Usage", value=f"{disk.percent}%", color=disk_color),
           column=2
       )
       
       # Add progress bars in a new vertical layout
       layout2 = DisplayerLayout(Layouts.VERTICAL)
       disp.add_master_layout(layout2)
       
       disp.add_display_item(
           DisplayerItemProgress("CPU", value=cpu_percent, max_value=100)
       )
       disp.add_display_item(
           DisplayerItemProgress("Memory", value=mem.percent, max_value=100)
       )
       disp.add_display_item(
           DisplayerItemProgress("Disk", value=disk.percent, max_value=100)
       )
       
       return disp.display()

Register the Blueprint
^^^^^^^^^^^^^^^^^^^^^^

In ``app.py``:

.. code-block:: python

   from pages.dashboard import dashboard_bp
   
   app.register_blueprint(dashboard_bp)

Tutorial 4: Implementing Authentication
----------------------------------------

Secure your application with role-based access control.

Setting Up Users and Permissions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The auth system is automatically initialized. Create users programmatically:

.. code-block:: python

   from src.modules.auth.auth_manager import auth_manager
   
   # In your app initialization
   if auth_manager:
       # Create admin user
       auth_manager.create_user("admin", "admin123", is_admin=True)
       
       # Create regular user
       auth_manager.create_user("user1", "password")
       
       # Grant permissions
       auth_manager.grant_permission("user1", "Dashboard", "view")
       auth_manager.grant_permission("admin", "Dashboard", "view")
       auth_manager.grant_permission("admin", "Dashboard", "edit")

Protecting Routes
^^^^^^^^^^^^^^^^^

Use session checks to protect routes:

.. code-block:: python

   from flask import session, redirect, url_for
   from functools import wraps
   
   def login_required(f):
       """Decorator to require login"""
       @wraps(f)
       def decorated_function(*args, **kwargs):
           if 'username' not in session:
               return redirect(url_for('auth.login'))
           return f(*args, **kwargs)
       return decorated_function
   
   @app.route("/admin")
   @login_required
   def admin_page():
       # Only logged-in users can access
       return "Admin panel"

Permission-Based Access
^^^^^^^^^^^^^^^^^^^^^^^

Check specific permissions:

.. code-block:: python

   from src.modules.auth.auth_manager import auth_manager
   from flask import session, abort
   
   @app.route("/settings")
   @login_required
   def settings_page():
       username = session.get('username')
       
       # Check if user has permission
       if not auth_manager.has_permission(username, 'Settings', 'edit'):
           abort(403)  # Forbidden
       
       # User has permission, show settings
       disp = Displayer()
       # ... build settings page
       return disp.display()

Automatic Permission Checks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Displayer system can automatically check permissions:

.. code-block:: python

   class MySecureModule:
       m_default_name = "Secure Module"
       m_required_permission = "SecureModule"  # Module name for permission
       m_required_action = "view"  # Required action
   
   @app.route("/secure")
   @login_required
   def secure_page():
       module = MySecureModule()
       
       disp = Displayer()
       disp.add_module(module)  # Automatically checks permissions!
       
       # If user lacks permission, an access denied message is shown
       return disp.display()

Tutorial 5: Working with Forms
-------------------------------

Create interactive forms with validation.

Basic Form
^^^^^^^^^^

.. code-block:: python

   from src.modules.displayer import (
       Displayer, DisplayerItemInput, 
       DisplayerItemTextarea, DisplayerItemButton
   )
   from flask import request
   
   @app.route("/contact", methods=["GET", "POST"])
   def contact_form():
       if request.method == "POST":
           name = request.form.get("name")
           email = request.form.get("email")
           message = request.form.get("message")
           
           # Process form data
           print(f"Contact from {name} ({email}): {message}")
           
           # Show confirmation
           disp = Displayer()
           disp.add_generic({"title": "Thank You"})
           disp.add_display_item(
               DisplayerItemText(f"Thank you, {name}! We'll be in touch.")
           )
           return disp.display()
       
       # Show form
       disp = Displayer()
       disp.add_generic({"id": "contact", "title": "Contact Us"})
       
       disp.add_display_item(
           DisplayerItemInput("name", label="Your Name", placeholder="John Doe")
       )
       disp.add_display_item(
           DisplayerItemInput("email", label="Email", placeholder="john@example.com")
       )
       disp.add_display_item(
           DisplayerItemTextarea("message", label="Message", rows=5)
       )
       disp.add_display_item(
           DisplayerItemButton("Submit", button_type="submit")
       )
       
       return disp.display()

Tutorial 6: Real-Time Updates
------------------------------

Use the scheduler to push live updates to clients.

Custom Scheduler Updates
^^^^^^^^^^^^^^^^^^^^^^^^^

Extend the scheduler to add custom update logic:

.. code-block:: python

   from src.modules.scheduler import scheduler
   
   # In your threaded action
   class LiveDataTask(Threaded_action):
       def action(self):
           for i in range(100):
               # Do work
               time.sleep(1)
               
               # Push update to clients
               if scheduler.scheduler_obj:
                   scheduler.scheduler_obj.emit_log(
                       f"Progress: {i}%", 
                       level="info"
                   )
                   scheduler.scheduler_obj.emit_button_update(
                       "my_button",
                       {"disabled": False, "text": f"Progress: {i}%"}
                   )

The framework automatically handles WebSocket connections and delivers updates to connected clients.

Next Steps
----------

Now that you've completed these tutorials, you can:

1. Explore the :doc:`framework` for deeper understanding
2. Check :doc:`examples` for more code patterns
3. Read the :doc:`framework_classes` API reference
4. Build your own custom application!

.. tip::

   The demo application (``tests/manual_test_webapp.py``) showcases all these concepts in action. Run it to see live examples!
