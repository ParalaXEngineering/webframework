.. ParalaX Web Framework documentation master file

Welcome to ParalaX Web Framework's documentation!
==================================================

**ParalaX Web Framework** is a robust Flask-based web framework designed to simplify the creation of tool management and monitoring web applications. Built with modularity and extensibility in mind, it provides everything you need to create professional web interfaces quickly.

.. note::

   **New to the framework?** Start with :doc:`getting_started` for installation and your first application!

What Can You Build?
-------------------

ParalaX is perfect for:

* **Monitoring Dashboards**: Real-time system monitoring with live updates
* **Control Panels**: Industrial control interfaces with background task management
* **Data Management Tools**: CRUD applications with role-based access control
* **Automation Interfaces**: Web UIs for scripts and background processes
* **Internal Tools**: Company-specific applications with built-in authentication

Key Features
------------

🚀 **Production-Ready Foundation**
   Built on Flask with battle-tested libraries (SocketIO, Jinja2, bcrypt)

🔄 **Real-Time Updates**
   WebSocket support for live page updates without page refresh

⚙️ **Background Task Management**
   Thread manager for long-running operations with progress tracking

🔐 **Security Built-In**
   Role-based authentication with granular permission control

🎨 **Dynamic UI System**
   Generate professional UIs programmatically - no manual HTML required

📦 **Flexible Architecture**
   Use standalone or integrate as a git submodule

Architecture Overview
---------------------

The framework is organized into two main layers:

**1. Core Framework** (the foundation)
   The base system providing all fundamental functionality. You rarely modify this layer.

**2. Your Application** (your customization)
   Custom pages, actions, and configurations built on top of the framework.

Core Components
^^^^^^^^^^^^^^^

The framework consists of several integrated subsystems:

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Component
     - Purpose
   * - **Web Engine**
     - Flask application with routing, templates, and static assets
   * - **Displayer System**
     - Dynamic UI generation (modules, layouts, items)
   * - **Threaded Actions**
     - Background task execution with progress tracking
   * - **Thread Manager**
     - Registry and lifecycle management for background threads
   * - **Scheduler**
     - Periodic tasks and real-time client updates via WebSocket
   * - **Auth Manager**
     - User authentication and role-based permissions
   * - **Site Configuration**
     - Application metadata and navigation structure
   * - **Utilities**
     - Helper functions for common operations

Data Flow Example
^^^^^^^^^^^^^^^^^

Here's how a typical request flows through the framework:

1. **User visits a page** → Flask routes to your handler
2. **Handler creates Displayer** → Builds UI programmatically
3. **Permission check** → Auth manager validates access
4. **Render template** → Jinja2 generates HTML with your data
5. **Client connects via WebSocket** → Scheduler begins real-time updates
6. **Background tasks** → Thread manager monitors and reports progress

Quick Example
-------------

Here's a complete minimal application:

.. code-block:: python

   from flask import Flask
   from src.main import setup_app
   from src.modules.displayer import Displayer, DisplayerItemText
   
   # Initialize app
   app = Flask(__name__)
   app.secret_key = "change-me-in-production"
   setup_app(app)
   
   # Create a page
   @app.route("/")
   def home():
       disp = Displayer()
       disp.add_generic({"title": "My First Page"})
       disp.add_display_item(DisplayerItemText("Hello World!"))
       return disp.display()
   
   if __name__ == "__main__":
       app.run(debug=True, port=5001)

That's it! You now have a working web application with authentication, real-time updates, and a professional UI.

Documentation Structure
-----------------------

This documentation is organized to help you learn progressively:

**Getting Started** (→ :doc:`getting_started`)
   Installation, prerequisites, and your first application

**Framework Guide** (→ :doc:`framework`)
   Deep dive into architecture, components, and best practices

**Tutorials** (→ :doc:`tutorials`)
   Step-by-step guides for common use cases

**API Reference** (→ :doc:`framework_classes`, :doc:`api_modules`)
   Complete class and method documentation

**Examples** (→ :doc:`examples`)
   Code snippets and patterns for common tasks

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   getting_started
   framework
   file_manager
   i18n
   tutorials
   examples
   
.. toctree::
   :maxdepth: 2
   :caption: API Reference

   framework_classes
   api_modules

Need Help?
----------

* **Examples?** Browse :doc:`examples`
* **API Details?** Explore :doc:`framework_classes`

The framework includes a demo application showcasing all features:

.. code-block:: bash

   python tests/manual_test_webapp.py

Visit http://localhost:5001 to explore components, layouts, and functionality.

Project Status
--------------

.. note::

   This project is actively maintained. The framework has been successfully deployed in production environments and continues to evolve based on real-world usage.

   **Current Version**: 1.0.0

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

