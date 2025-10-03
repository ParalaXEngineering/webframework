Getting Started
===============

This guide will help you get started with the ParalaX Web Framework, whether you want to use it as a standalone package or as a git submodule in your project.

Prerequisites
-------------

* Python 3.8 or higher
* pip (Python package installer)
* Virtual environment (recommended)

Installation Methods
--------------------

Method 1: Standalone Installation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Clone the repository and install dependencies:

.. code-block:: bash

   git clone https://github.com/ParalaXEngineering/webframework.git
   cd webframework
   
   # Create and activate virtual environment
   python3 -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate  # On Windows
   
   # Install dependencies
   pip install -r requirements.txt

Method 2: As a Git Submodule
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add the framework to your existing project:

.. code-block:: bash

   # In your project root
   git submodule add https://github.com/ParalaXEngineering/webframework.git submodules/framework
   git submodule update --init --recursive
   
   # Install dependencies
   pip install -r submodules/framework/requirements.txt

Testing the Installation
------------------------

Run the test suite to verify everything is working:

.. code-block:: bash

   pytest tests/ -v

All tests should pass. If you see any failures, check that all dependencies are properly installed.

Project Structure
-----------------

After installation, you'll have the following structure:

.. code-block:: text

   webframework/
   ├── docs/               # Documentation sources
   ├── src/                # Python source code
   │   ├── __init__.py    # Package initialization
   │   ├── main.py        # Flask app setup
   │   ├── access_manager.py
   │   ├── action.py
   │   ├── displayer.py
   │   ├── scheduler.py
   │   ├── site_conf.py
   │   ├── threaded_action.py
   │   ├── threaded_manager.py
   │   ├── utilities.py
   │   └── ...
   ├── templates/          # Jinja2 templates
   ├── webengine/          # Static assets (CSS, JS, images)
   ├── tests/              # Test suite
   ├── requirements.txt    # Python dependencies
   ├── pytest.ini         # Pytest configuration
   └── README.md          # Project documentation

Creating Your First Application
--------------------------------

Here's a minimal example to get you started:

.. code-block:: python

   from flask import Flask
   from src import setup_app, FLASK_AVAILABLE

   if FLASK_AVAILABLE:
       # Create Flask app
       app = Flask(__name__)
       app.secret_key = "your-secret-key-here"
       
       # Setup the framework
       setup_app(app)
       
       if __name__ == '__main__':
           app.run(debug=True, host='0.0.0.0', port=5000)
   else:
       print("Flask is not available. Please install Flask.")

Configuration
-------------

The framework can be configured through various settings. Create a configuration file or set environment variables:

.. code-block:: python

   # config.py
   import os

   class Config:
       SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
       SESSION_TYPE = 'filesystem'
       DEBUG = True
       
       # Framework-specific settings
       LOG_LEVEL = 'INFO'
       ENABLE_AUTH = True
       DEFAULT_USER = 'admin'

Then use it in your application:

.. code-block:: python

   from flask import Flask
   from config import Config
   from src import setup_app

   app = Flask(__name__)
   app.config.from_object(Config)
   setup_app(app)

Next Steps
----------

* Read the :doc:`framework` documentation to understand core concepts
* Explore the :doc:`framework_classes` API reference
* Check out example implementations in the repository
* Learn about creating custom site handlers

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
