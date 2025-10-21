Tutorials
=========

Step-by-step guides for common use cases with the ParalaX Web Framework.

.. contents:: Tutorial Topics
   :local:
   :depth: 2

Tutorial 1: Creating Your First Page with Displayer
----------------------------------------------------

This tutorial demonstrates the basics of creating a page using the Displayer system with a simple form.

Complete Example
^^^^^^^^^^^^^^^^

The simple form demo shows the essential concepts:

.. literalinclude:: ../../tests/demo_support/demo_pages.py
   :language: python
   :pyobject: simple_form_demo
   :caption: tests/demo_support/demo_pages.py - Simple Form Demo

**To run and test this example:**

.. code-block:: bash

   python tests/manual_test_webapp.py
   # Visit http://localhost:5001/simple-form-demo

Key Concepts
^^^^^^^^^^^^

1. **Create a Displayer**: ``disp = Displayer()`` - The main container for your page content
2. **Add a Module**: ``disp.add_generic("Simple Form Demo")`` - Creates a card container with an ID
3. **Set Title**: ``disp.set_title("Simple Form Example")`` - Sets the module's title
4. **Add Breadcrumbs**: ``disp.add_breadcrumb()`` - Navigation breadcrumbs
5. **Add Layout**: ``disp.add_master_layout(DisplayerLayout(...))`` - Organizes content into columns
6. **Add Items**: Use ``add_display_item()`` to add content, specifying which column with ``column=``
7. **Handle POST**: Check ``request.method == 'POST'`` to respond to form submissions
8. **Parse Form Data**: Use ``utilities.util_post_to_json(request.form.to_dict())`` to parse POST data
9. **Render**: Return ``render_template("base_content.j2", content=disp.display(), target="...")``

Tutorial 2: Working with Background Tasks
------------------------------------------

Learn how to create background tasks that run asynchronously with real-time progress updates.

Complete Example
^^^^^^^^^^^^^^^^

The threading demo demonstrates comprehensive background task functionality:

.. literalinclude:: ../../tests/demo_support/demo_pages.py
   :language: python
   :pyobject: threading_demo
   :caption: tests/demo_support/demo_pages.py - Threading Demo

The demo also uses the ``DemoThreadedAction`` class which shows different threading patterns:

.. literalinclude:: ../../tests/demo_support/demo_threaded_complete.py
   :language: python
   :pyobject: DemoThreadedAction
   :caption: tests/demo_support/demo_threaded_complete.py

**To run and test this example:**

.. code-block:: bash

   python tests/manual_test_webapp.py
   # Visit http://localhost:5001/threading-demo

Key Concepts
^^^^^^^^^^^^

1. **Threaded_action Class**: Inherit from ``Threaded_action`` to create background tasks
2. **Class Attributes**:
   - ``m_default_name``: Unique identifier for the task
   - ``m_type``: Task type classification
3. **action() Method**: Contains the main work logic executed in the background
4. **Progress Tracking**: 
   - Set ``self.m_running_state`` to a value between 0-100
   - Use ``self.m_scheduler.emit_status()`` for real-time UI updates
5. **Console Logging**: Use ``self.console_write()`` to log messages
6. **Add Module as Class**: Pass the class itself to ``disp.add_module(DataProcessingTask)``, not an instance
7. **Start Task**: Create an instance and call ``task.start()`` when ready to execute
8. **Check Running Tasks**: Use ``threaded_manager.thread_manager_obj.get_thread()`` to check if a task is already running
9. **Parse POST Data**: Use ``utilities.util_post_to_json(request.form.to_dict())`` to handle form submissions

Tutorial 3: Authentication and User Management
-----------------------------------------------

Learn how to work with user sessions and authentication information. See the authentication demo pages for complete examples:

- ``/auth/accessible`` - Public page (any logged-in user)
- ``/auth/restricted`` - Protected page (requires specific permission)
- ``/auth/admin`` - Admin-only page (requires admin group)

Complete Examples
^^^^^^^^^^^^^^^^^

**Public Page Example:**

.. literalinclude:: ../../tests/demo_support/demo_pages.py
   :language: python
   :pyobject: auth_accessible
   :caption: tests/demo_support/demo_pages.py - Public Page

**Protected Page Example:**

.. literalinclude:: ../../tests/demo_support/demo_pages.py
   :language: python
   :pyobject: auth_restricted
   :caption: tests/demo_support/demo_pages.py - Protected Page

**To run and test these examples:**

.. code-block:: bash

   python tests/manual_test_webapp.py
   # Visit http://localhost:5001/auth/accessible

Key Concepts
^^^^^^^^^^^^

1. **Session Access**: Use ``session.get('username', 'GUEST')`` to retrieve the current user
2. **Check Login Status**: Compare username against 'GUEST' or check if username exists
3. **Conditional Display**: Show different content based on authentication status
4. **DisplayerItemBadge**: Use badges with ``BSstyle`` (SUCCESS, INFO, WARNING, DANGER) to highlight status
5. **Login Page**: Direct users to ``/common/login`` for authentication

Tutorial 4: Creating and Processing Forms
------------------------------------------

Learn how to build interactive forms with various input types and handle form submissions.

Complete Example
^^^^^^^^^^^^^^^^

The simple form demo provides a complete working example:

.. literalinclude:: ../../tests/demo_support/demo_pages.py
   :language: python
   :pyobject: simple_form_demo
   :caption: tests/demo_support/demo_pages.py - Simple Form Demo

**To run and test this example:**

.. code-block:: bash

   python tests/manual_test_webapp.py
   # Visit http://localhost:5001/simple-form-demo

Key Concepts
^^^^^^^^^^^^

1. **Form Input Types**:
   - ``DisplayerItemInputString``: Single-line text input
   - ``DisplayerItemInputSelect``: Dropdown selection
   - ``DisplayerItemInputText``: Multi-line text area
   
2. **Input Parameters**:
   - First parameter: field name/ID
   - Second parameter: field label
   - Third parameter: default value
   - Additional parameters: options for select, focus flag, etc.

3. **Parse Form Data**: 
   - Use ``utilities.util_post_to_json(request.form.to_dict())`` to parse POST data
   - Access data by module ID: ``data_in["contact_form"]``
   - Extract values with ``.get()`` for safe access

4. **Display Alerts**: Use ``DisplayerItemAlert`` with:
   - ``text``: Alert message
   - ``highlightType``: BSstyle (SUCCESS, INFO, WARNING, DANGER)
   - ``title``: Alert title
   - ``icon``: Optional icon name

5. **Form Feedback**: Show success messages and submitted data after POST

6. **Visual Separators**: Use ``DisplayerItemSeparator()`` to add visual breaks

7. **HTML in Text**: ``DisplayerItemText`` accepts HTML for rich formatting and links