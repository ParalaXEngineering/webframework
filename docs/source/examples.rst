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

.. literalinclude:: ../../tests/demo_support/demo_scheduler_action.py
   :language: python
   :pyobject: DemoSchedulerAction
   :caption: tests/demo_support/demo_scheduler_action.py

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
