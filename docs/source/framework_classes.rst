Framework Classes Reference
############################

This page provides detailed API documentation for the main classes in the ParalaX Web Framework.

.. note::

   This documentation is auto-generated from the source code docstrings. For code examples, see :doc:`examples` and :doc:`tutorials`.

Core Classes
============

Authentication
--------------

.. autoclass:: src.modules.auth.auth_manager.AuthManager
    :members:
    :undoc-members:
    :show-inheritance:
    :special-members: __init__

Site Configuration
------------------

.. autoclass:: src.modules.site_conf.Site_conf
    :members:
    :undoc-members:
    :show-inheritance:
    :special-members: __init__

Thread Manager
--------------

.. autoclass:: src.modules.threaded.threaded_manager.Threaded_manager
    :members:
    :undoc-members:
    :show-inheritance:
    :special-members: __init__

Action Classes
==============

Base Action
-----------

.. autoclass:: src.modules.action.Action
    :members:
    :undoc-members:
    :show-inheritance:

Threaded Action
---------------

.. autoclass:: src.modules.threaded.threaded_action.Threaded_action
    :members:
    :undoc-members:
    :show-inheritance:
    :special-members: __init__

Scheduler
=========

Main Scheduler
--------------

.. autoclass:: src.modules.scheduler.scheduler.Scheduler
    :members:
    :undoc-members:
    :show-inheritance:
    :special-members: __init__

Long-Term Scheduler
-------------------

.. autoclass:: src.modules.scheduler.scheduler.Scheduler_LongTerm
    :members:
    :undoc-members:
    :show-inheritance:

Display System
==============

Displayer
---------

.. autoclass:: src.modules.displayer.displayer.Displayer
    :members:
    :undoc-members:
    :show-inheritance:
    :special-members: __init__

Display Layout
--------------

.. autoclass:: src.modules.displayer.layout.DisplayerLayout
    :members:
    :undoc-members:
    :show-inheritance:
    :special-members: __init__

Display Items
-------------

Base Item
^^^^^^^^^

.. autoclass:: src.modules.displayer.items.DisplayerItem
    :members:
    :undoc-members:
    :show-inheritance:
    :special-members: __init__

Text Items
^^^^^^^^^^

.. autoclass:: src.modules.displayer.items.DisplayerItemText
    :members:
    :show-inheritance:

Input Items
^^^^^^^^^^^

.. autoclass:: src.modules.displayer.items.DisplayerItemInputBox
    :members:
    :show-inheritance:

.. autoclass:: src.modules.displayer.items.DisplayerItemInputSelect
    :members:
    :show-inheritance:

.. autoclass:: src.modules.displayer.items.DisplayerItemInputMultiSelect
    :members:
    :show-inheritance:

Button Items
^^^^^^^^^^^^

.. autoclass:: src.modules.displayer.items.DisplayerItemButton
    :members:
    :show-inheritance:

.. autoclass:: src.modules.displayer.items.DisplayerItemButtonLink
    :members:
    :show-inheritance:

Display Items
^^^^^^^^^^^^^

.. autoclass:: src.modules.displayer.items.DisplayerItemBadge
    :members:
    :show-inheritance:

.. autoclass:: src.modules.displayer.items.DisplayerItemImage
    :members:
    :show-inheritance:

.. autoclass:: src.modules.displayer.items.DisplayerItemAlert
    :members:
    :show-inheritance:

Utility Functions
=================

.. automodule:: src.modules.utilities
    :members:
    :undoc-members:
    :show-inheritance:

Built-in Pages
==============

Common Pages
------------

.. automodule:: src.pages.common
    :members:
    :undoc-members:
    :show-inheritance:

Admin Pages
-----------

.. automodule:: src.pages.admin
    :members:
    :undoc-members:
    :show-inheritance:

Thread Monitoring
-----------------

.. automodule:: src.pages.threads
    :members:
    :undoc-members:
    :show-inheritance:

User Profile
------------

.. automodule:: src.pages.user
    :members:
    :undoc-members:
    :show-inheritance:

Optional Modules
================

Workflow System
---------------

.. automodule:: src.modules.workflow
    :members:
    :undoc-members:
    :show-inheritance:

Configuration Manager
---------------------

.. automodule:: src.modules.config_manager
    :members:
    :undoc-members:
    :show-inheritance:

.. note::

   Some modules may not have full documentation yet. We're continuously improving the documentation. See the source code for implementation details.