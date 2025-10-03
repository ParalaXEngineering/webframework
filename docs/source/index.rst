.. ParalaX Web Framework documentation master file

Welcome to ParalaX Web Framework's documentation!
==================================================

**ParalaX Web Framework** is a robust Flask-based web framework designed to make the creation of tool management websites easier. The project has been designed with modularity in mind to be easily extended across different projects and with more tools.

Key Features
------------

* **Modular Architecture**: Clean separation between framework and site handlers
* **Asynchronous Task Management**: Built-in thread manager for background operations
* **Real-time Updates**: WebSocket support via Flask-SocketIO
* **User Authentication**: Integrated access manager with role-based permissions
* **Dynamic UI**: Powerful display system with form and layout management
* **Testing Support**: Comprehensive test suite with pytest integration
* **Standalone & Submodule**: Can be used as a standalone package or as a git submodule

Architecture Overview
---------------------

The framework consists of two main parts:

1. **Core Framework**: The base system providing all fundamental functionality
2. **Site Handlers**: Custom implementations that extend the framework for specific use cases

Framework Components
^^^^^^^^^^^^^^^^^^^^

* **Web Engine**: Flask-based engine with Jinja2 templates for HTML generation
* **Scheduler**: Manages periodic tasks and real-time updates via SocketIO
* **Thread Manager**: Registers and maintains background threads
* **Threaded Actions**: Framework for asynchronous work modules
* **Access Manager**: User authentication and authorization system
* **Displayer System**: Dynamic UI generation with layouts and items
* **Site Configuration**: Base configuration class for customization

.. toctree::
   :maxdepth: 2
   :caption: User Guide:

   getting_started
   framework
   
.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   framework_classes
   api_modules

.. note::

   This project is under active development. The framework has been recently refactored to support both standalone and submodule usage.
-----------

Installation
^^^^^^^^^^^^

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/ParalaXEngineering/webframework.git
   cd webframework

   # Install dependencies
   pip install -r requirements.txt

   # Run tests
   pytest tests/

Basic Usage
^^^^^^^^^^^

.. code-block:: python

   from src import setup_app
   from flask import Flask

   # Create and configure your app
   app = Flask(__name__)
   setup_app(app)

   # Run the application
   if __name__ == '__main__':
       app.run(debug=True)

.. note::

   This project is under active development. The framework has been recently refactored to support both standalone and submodule usage.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

