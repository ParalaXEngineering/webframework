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

*Don't worry if you're new to web development - the framework abstracts most complexity!*

Installation Methods
--------------------

Choose the installation method that best fits your use case.

Method 1: Standalone Installation (Recommended for Beginners)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Best for: Learning the framework, building new applications from scratch.

**Step 1: Clone the Repository**

.. code-block:: bash

   # Clone the framework
   git clone https://github.com/ParalaXEngineering/webframework.git
   cd webframework

**Step 2: Create Virtual Environment**

.. code-block:: bash

   # Create virtual environment
   python3 -m venv .venv
   
   # Activate it
   source .venv/bin/activate  # macOS/Linux
   .venv\Scripts\activate     # Windows
   
   # Verify activation (should show .venv path)
   which python  # macOS/Linux
   where python  # Windows

**Step 3: Install Dependencies**

.. code-block:: bash

   # Install in development mode (editable)
   pip install -e .
   
   # OR install from requirements
   pip install -r requirements.txt

**Step 4: Verify Installation**

.. code-block:: bash

   # Run tests to verify everything works
   pytest tests/ -v
   
   # Should see all tests passing

Method 2: As a Git Submodule (For Existing Projects)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Best for: Integrating the framework into an existing project.

**Step 1: Add as Submodule**

.. code-block:: bash

   # In your project root
   git submodule add https://github.com/ParalaXEngineering/webframework.git framework
   git submodule update --init --recursive

**Step 2: Install Dependencies**

.. code-block:: bash

   # From your project root
   pip install -r framework/requirements.txt

**Step 3: Use in Your Project**

.. code-block:: python

   # your_app.py
   import sys
   sys.path.insert(0, 'framework')
   
   from src.main import app, setup_app
   
   setup_app(app)
   
   if __name__ == "__main__":
       app.run(debug=True, port=5001)

Method 3: Development Installation (For Framework Contributors)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Best for: Contributing to the framework itself.

.. code-block:: bash

   # Fork and clone your fork
   git clone https://github.com/YourUsername/webframework.git
   cd webframework
   
   # Create virtual environment
   python3 -m venv .venv
   source .venv/bin/activate
   
   # Install with development dependencies
   pip install -e .[dev]
   
   # Install documentation tools
   pip install -e .[docs]
   
   # Run tests
   pytest tests/ -v
   
   # Build documentation
   cd docs
   sphinx-build -b html source build/html

Testing the Installation
------------------------

Verify your installation with these steps:

Run the Test Suite
^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Run all tests
   pytest tests/ -v
   
   # Run with coverage
   pytest tests/ --cov=src --cov-report=html
   
   # Run specific test file
   pytest tests/unit/test_scheduler.py -v

All tests should pass ✓. If you see failures:

1. Check you're in the virtual environment
2. Verify all dependencies installed: ``pip list``
3. See :doc:`troubleshooting` for common issues

Run the Demo Application
^^^^^^^^^^^^^^^^^^^^^^^^^

The framework includes a comprehensive demo application:

.. code-block:: bash

   # Ensure virtual environment is activated
   source .venv/bin/activate
   
   # Run the demo
   python tests/manual_test_webapp.py

Visit ``http://localhost:5001`` in your browser. You should see:

* Login page (try username: ``admin``, password: ``admin``)
* Component showcase with all display items
* Layout demonstrations
* Background task examples
* Real-time update demonstrations

Verify Python Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Check Python version
   python --version  # Should be 3.8+
   
   # Verify framework imports
   python -c "from src.main import app; print('✓ Framework imports OK')"
   
   # Check Flask installation
   python -c "import flask; print(f'✓ Flask {flask.__version__}')"

Understanding the Project Structure
------------------------------------

Let's explore what each directory contains:

Directory Layout
^^^^^^^^^^^^^^^^

.. code-block:: text

   webframework/
   ├── docs/                        # Sphinx documentation
   │   ├── source/                 # RST source files
   │   └── build/                  # Generated HTML (after build)
   │
   ├── src/                         # Core framework code
   │   ├── main.py                 # Flask app initialization
   │   ├── __init__.py             # Package exports
   │   │
   │   ├── modules/                # Core framework modules
   │   │   ├── action.py          # Base action class
   │   │   ├── site_conf.py       # Site configuration
   │   │   ├── utilities.py       # Helper functions
   │   │   │
   │   │   ├── auth/              # Authentication system
   │   │   │   ├── auth_manager.py
   │   │   │   └── permission_registry.py
   │   │   │
   │   │   ├── displayer/         # UI generation system
   │   │   │   ├── displayer.py  # Main displayer class
   │   │   │   ├── layout.py     # Layout management
   │   │   │   ├── core.py       # Core utilities
   │   │   │   └── items/        # Display items
   │   │   │       ├── base_item.py
   │   │   │       ├── text.py
   │   │   │       ├── button.py
   │   │   │       └── ...
   │   │   │
   │   │   ├── threaded/          # Background task system
   │   │   │   ├── threaded_action.py
   │   │   │   └── threaded_manager.py
   │   │   │
   │   │   ├── scheduler/         # Real-time update system
   │   │   │   ├── scheduler.py
   │   │   │   ├── message_queue.py
   │   │   │   └── emitter.py
   │   │   │
   │   │   └── log/               # Logging infrastructure
   │   │       └── logger_factory.py
   │   │
   │   └── pages/                  # Built-in pages
   │       ├── common.py          # Home page
   │       ├── admin.py           # Admin panel
   │       ├── user.py            # User profile
   │       └── threads.py         # Thread monitor
   │
   ├── templates/                   # Jinja2 templates
   │   ├── base.j2                 # Base template
   │   ├── index.j2                # Home page
   │   ├── login.j2                # Login page
   │   └── displayer_items/        # Item templates
   │
   ├── webengine/                   # Static assets
   │   └── assets/
   │       ├── css/                # Stylesheets
   │       ├── js/                 # JavaScript
   │       └── images/             # Images/icons
   │
   ├── tests/                       # Test suite
   │   ├── unit/                   # Unit tests
   │   ├── integration/            # Integration tests
   │   ├── conftest.py             # Pytest fixtures
   │   ├── manual_test_webapp.py   # Demo application
   │   └── demo_support/           # Demo pages
   │
   ├── logs/                        # Application logs (auto-created)
   ├── flask_session/               # Session files (auto-created)
   ├── auth/                        # User data (auto-created)
   │
   ├── pyproject.toml              # Project metadata
   ├── requirements.txt             # Python dependencies
   ├── pytest.ini                  # Pytest configuration
   └── README.md                   # Overview documentation

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

Creating Your First Application
--------------------------------

Let's build a complete working application step by step.

Example 1: Hello World
^^^^^^^^^^^^^^^^^^^^^^^

The simplest possible application:

.. code-block:: python

   # hello.py
   from flask import Flask
   from src.main import setup_app
   from src.modules.displayer import Displayer, DisplayerItemText
   
   # Create Flask app
   app = Flask(__name__)
   app.secret_key = "change-this-secret-key"
   
   # Initialize framework
   setup_app(app)
   
   # Create home page
   @app.route("/")
   def home():
       disp = Displayer()
       disp.add_generic({"id": "main", "title": "Hello World"})
       disp.add_display_item(DisplayerItemText("Welcome to ParalaX!"))
       return disp.display()
   
   if __name__ == "__main__":
       app.run(debug=True, host="0.0.0.0", port=5001)

Run it:

.. code-block:: bash

   python hello.py

Visit ``http://localhost:5001`` - you'll see a card with your text!

Example 2: Multi-Page Application
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add navigation and multiple pages:

.. code-block:: python

   # multipage.py
   from flask import Flask
   from src.main import setup_app
   from src.modules.displayer import (
       Displayer, DisplayerItemText, DisplayerItemButton, DisplayerItemLink
   )
   from src.modules import site_conf
   
   app = Flask(__name__)
   app.secret_key = "change-this-secret-key"
   setup_app(app)
   
   # Configure site
   site_conf.site_conf_obj.app_details(
       name="My Application",
       version="1.0.0",
       footer="© 2025 My Company"
   )
   
   # Add navigation items
   site_conf.site_conf_obj.add_sidebar_title("Main")
   site_conf.site_conf_obj.add_sidebar_section("Home", "house", "home")
   site_conf.site_conf_obj.add_sidebar_section("About", "info-circle", "about")
   
   @app.route("/")
   def home():
       disp = Displayer()
       disp.add_generic({"title": "Home Page"})
       disp.add_display_item(DisplayerItemText("Welcome to the home page!"))
       disp.add_display_item(
           DisplayerItemLink("Visit About", url="/about")
       )
       return disp.display()
   
   @app.route("/about")
   def about():
       disp = Displayer()
       disp.add_generic({"title": "About Us"})
       disp.add_display_item(
           DisplayerItemText("This is a ParalaX application.")
       )
       return disp.display()
   
   if __name__ == "__main__":
       app.run(debug=True, port=5001)

Example 3: Interactive Form
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Handle user input with forms:

.. code-block:: python

   # form_app.py
   from flask import Flask, request
   from src.main import setup_app
   from src.modules.displayer import (
       Displayer, DisplayerItemText, DisplayerItemInput,
       DisplayerItemTextarea, DisplayerItemButton
   )
   
   app = Flask(__name__)
   app.secret_key = "change-this-secret-key"
   setup_app(app)
   
   @app.route("/", methods=["GET", "POST"])
   def contact_form():
       if request.method == "POST":
           # Process form submission
           name = request.form.get("name")
           email = request.form.get("email")
           message = request.form.get("message")
           
           # Show confirmation
           disp = Displayer()
           disp.add_generic({"title": "Thank You"})
           disp.add_display_item(
               DisplayerItemText(f"Thanks, {name}! We received your message.")
           )
           return disp.display()
       
       # Show form
       disp = Displayer()
       disp.add_generic({"id": "contact", "title": "Contact Us"})
       
       disp.add_display_item(
           DisplayerItemInput("name", label="Your Name", required=True)
       )
       disp.add_display_item(
           DisplayerItemInput("email", label="Email", input_type="email", required=True)
       )
       disp.add_display_item(
           DisplayerItemTextarea("message", label="Message", rows=5)
       )
       disp.add_display_item(
           DisplayerItemButton("Send", button_type="submit", color="primary")
       )
       
       return disp.display()
   
   if __name__ == "__main__":
       app.run(debug=True, port=5001)
       app.secret_key = "your-secret-key-here"
       
       # Setup the framework
       setup_app(app)
       
       if __name__ == '__main__':
           app.run(debug=True, host='0.0.0.0', port=5000)
   else:
       print("Flask is not available. Please install Flask.")

Configuration
-------------

Basic Configuration
^^^^^^^^^^^^^^^^^^^

Every application needs basic configuration:

.. code-block:: python

   from flask import Flask
   from src.main import setup_app
   from src.modules import site_conf
   
   app = Flask(__name__)
   
   # Security - CHANGE IN PRODUCTION!
   app.secret_key = "your-unique-secret-key-here"
   
   # Session configuration
   app.config['SESSION_TYPE'] = 'filesystem'
   app.config['DEBUG'] = True  # Set False in production
   
   # Initialize framework
   setup_app(app)
   
   # Configure site details
   site_conf.site_conf_obj.app_details(
       name="My Application",
       version="1.0.0",
       icon="rocket",
       footer="© 2025 Your Company"
   )

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

Common Next Steps
^^^^^^^^^^^^^^^^^

**Add User Authentication**

.. code-block:: python

   from src.modules.auth.auth_manager import auth_manager
   
   # Create users
   auth_manager.create_user("admin", "password", is_admin=True)
   auth_manager.create_user("user", "password")
   
   # Grant permissions
   auth_manager.grant_permission("user", "Dashboard", "view")

**Create a Background Task**

.. code-block:: python

   from src.modules.threaded.threaded_action import Threaded_action
   import time
   
   class MyTask(Threaded_action):
       m_default_name = "My Task"
       
       def action(self):
           for i in range(10):
               self.console_write(f"Step {i+1}/10")
               time.sleep(1)
               self.m_running_state = (i + 1) * 10

**Build a Multi-Column Layout**

.. code-block:: python

   from src.modules.displayer import DisplayerLayout, Layouts
   
   disp = Displayer()
   disp.add_generic({"title": "Dashboard"})
   
   layout = DisplayerLayout(Layouts.HORIZONTAL, columns=[4, 8])
   disp.add_master_layout(layout)
   
   # Add items to columns 0 and 1
   disp.add_display_item(item1, column=0)
   disp.add_display_item(item2, column=1)

Tips for Beginners
^^^^^^^^^^^^^^^^^^

1. **Start Simple**: Begin with single-page apps before adding complexity
2. **Use the Demo**: The demo app (``tests/manual_test_webapp.py``) is your best reference
3. **Check Logs**: Application logs are in ``logs/`` directory
4. **Read Docstrings**: Framework classes have detailed docstrings
5. **Run Tests**: Use tests as examples of correct usage
6. **Ask for Help**: Check :doc:`faq` and :doc:`troubleshooting`

Development Workflow
^^^^^^^^^^^^^^^^^^^^

Recommended workflow for development:

.. code-block:: bash

   # 1. Activate virtual environment
   source .venv/bin/activate
   
   # 2. Make changes to your code
   
   # 3. Test your changes
   pytest tests/
   
   # 4. Run your app
   python your_app.py
   
   # 5. Check logs if issues
   tail -f logs/app.log
   
   # 6. Commit changes
   git add .
   git commit -m "Description of changes"

Troubleshooting Installation
-----------------------------

If you encounter issues during installation:

**Import Errors**

.. code-block:: bash

   # Ensure you're in virtual environment
   which python  # Should show .venv path
   
   # Reinstall dependencies
   pip install -e .

**Port In Use**

.. code-block:: python

   # Use different port
   app.run(debug=True, port=5002)

**Permission Denied**

.. code-block:: bash

   # Check directory permissions
   chmod -R 755 webframework/

**Missing Dependencies**

.. code-block:: bash

   # Install all dependencies
   pip install flask flask-socketio flask-session python-socketio bcrypt

For more help, see :doc:`troubleshooting` or :doc:`faq`.

Ready to Build!
---------------

You're all set! Choose your path:

* **Quick learner?** → Jump to :doc:`tutorials`
* **Need examples?** → Browse :doc:`examples`
* **Want details?** → Read :doc:`framework`
* **API reference?** → See :doc:`framework_classes`

The framework is designed to be intuitive - explore and experiment! The demo application showcases everything the framework can do.

.. tip::

   **Pro tip**: Keep the demo app running in one terminal while developing. It's the best way to learn what's possible and see live examples of every feature!

Development Workflow
--------------------

1. **Start the development server**:

   .. code-block:: bash

      python src/main.py

2. **Run tests during development**:

   .. code-block:: bash

      pytest tests/ -v --tb=short

3. **Build documentation**:

   .. code-block:: bash

      ./build_docs.sh

4. **Access the application**:

   Open http://localhost:5000 in your browser

Troubleshooting
---------------

Common issues and solutions:

**Import Errors**
   Make sure you're in the correct directory and have activated your virtual environment.

**Missing Dependencies**
   Run ``pip install -r requirements.txt`` to install all required packages.

**Test Failures**
   Some tests may require optional dependencies. Install them with ``pip install pyserial bcrypt markdown``.

**Port Already in Use**
   Change the port in ``main.py`` or kill the process using port 5000.

Getting Help
------------

* Check the :doc:`framework_classes` for detailed API documentation
* Review test files in ``tests/`` for usage examples
* Open an issue on GitHub for bugs or feature requests
