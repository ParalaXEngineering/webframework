API Reference - Core Modules
=============================

This section provides detailed API documentation for all core modules in the ParalaX Web Framework.

.. note::

   For detailed class documentation, see :doc:`framework_classes`. This page covers module-level functions and utilities.

Main Application
----------------

.. automodule:: src.main
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Core Modules
------------

Actions
^^^^^^^

.. automodule:: src.modules.action
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Site Configuration
^^^^^^^^^^^^^^^^^^

.. automodule:: src.modules.site_conf
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Utilities
^^^^^^^^^

.. automodule:: src.modules.utilities
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Authentication System
---------------------

Auth Manager
^^^^^^^^^^^^

.. automodule:: src.modules.auth.auth_manager
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Permission Registry
^^^^^^^^^^^^^^^^^^^

.. automodule:: src.modules.auth.permission_registry
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Display System
--------------

Main Displayer
^^^^^^^^^^^^^^

.. automodule:: src.modules.displayer.displayer
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Layout Management
^^^^^^^^^^^^^^^^^

.. automodule:: src.modules.displayer.layout
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Core Display Utilities
^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: src.modules.displayer.core
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

.. note::

   Display items (buttons, inputs, etc.) are documented in :doc:`framework_classes`. See the DisplayerItem classes.

Threading System
----------------

Threaded Actions
^^^^^^^^^^^^^^^^

.. automodule:: src.modules.threaded.threaded_action
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Thread Manager
^^^^^^^^^^^^^^

.. automodule:: src.modules.threaded.threaded_manager
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Scheduler System
----------------

Main Scheduler
^^^^^^^^^^^^^^

.. automodule:: src.modules.scheduler.scheduler
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Message Queue
^^^^^^^^^^^^^

.. automodule:: src.modules.scheduler.message_queue
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Message Emitter
^^^^^^^^^^^^^^^

.. automodule:: src.modules.scheduler.emitter
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

SocketIO Manager
----------------

.. automodule:: src.modules.socketio_manager
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Workflow System
---------------

.. automodule:: src.modules.workflow
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Configuration Manager
---------------------

.. automodule:: src.modules.config_manager
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Logging
-------

Logger Factory
^^^^^^^^^^^^^^

.. automodule:: src.modules.log.logger_factory
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Built-in Pages
--------------

Common Pages
^^^^^^^^^^^^

.. automodule:: src.pages.common
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Admin Pages
^^^^^^^^^^^

.. automodule:: src.pages.admin
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

User Pages
^^^^^^^^^^

.. automodule:: src.pages.user
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Thread Monitoring
^^^^^^^^^^^^^^^^^

.. automodule:: src.pages.threads
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Settings Pages
^^^^^^^^^^^^^^

.. automodule:: src.pages.settings
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Logging Pages
^^^^^^^^^^^^^

.. automodule:: src.pages.logging
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

.. note::

   **Optional Modules**: The following modules may be available in some ParalaX applications but are not part of the core framework:
   
   - ``updater``: Application update functionality
   - ``bug_tracker``: Bug tracking and reporting
   - ``packager``: Application packaging utilities
   - ``SFTPConnection``: SFTP connection management
   - ``User_defined_module``: Custom user-defined functionality
   
   These modules are application-specific and should be documented in your application's documentation.
