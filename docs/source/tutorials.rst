Tutorials
=========

Step-by-step guides for common use cases with the ParalaX Web Framework.

.. contents:: Tutorial Topics
   :local:
   :depth: 2

Tutorial 1: Creating Your First Page with Displayer
----------------------------------------------------

This tutorial demonstrates the basics of creating a page using the Displayer system.

Complete Example
^^^^^^^^^^^^^^^^

.. code-block:: python

   from flask import Blueprint, render_template, request
   from submodules.framework.src.modules.displayer.displayer import Displayer, DisplayerLayout, Layouts
   from submodules.framework.src.modules.displayer.items import (
       DisplayerItemText, DisplayerItemButton, DisplayerItemBadge, BSstyle
   )
   
   tutorials_bp = Blueprint("tutorials", __name__, url_prefix="/tutorials")
   
   @tutorials_bp.route('/tutorial1', methods=['GET', 'POST'])
   def tutorial1():
       """Tutorial 1: Creating Your First Page with Displayer"""
       
       disp = Displayer()
       
       # Add a module (card container)
       disp.add_generic("welcome")
       disp.set_title("Welcome to My App")
       
       # Add a layout to display items
       disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [6, 6]))
       
       # Handle button click
       if request.method == 'POST':
           disp.add_display_item(
               DisplayerItemBadge("Button was clicked!", BSstyle.SUCCESS),
               column=0
           )
       
       # Add some content
       disp.add_display_item(
           DisplayerItemText("This is my first ParalaX application!"),
           column=0
       )
       
       disp.add_display_item(
           DisplayerItemButton("btn1", "Click Me"),
           column=1
       )
       
       return render_template("base_content.j2", content=disp.display(), target="tutorials.tutorial1")

Key Concepts
^^^^^^^^^^^^

1. **Create a Displayer**: ``disp = Displayer()`` - The main container for your page content
2. **Add a Module**: ``disp.add_generic("welcome")`` - Creates a card container with an ID
3. **Set Title**: ``disp.set_title("Welcome to My App")`` - Sets the module's title
4. **Add Layout**: ``disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [6, 6]))`` - Creates a 2-column layout
5. **Add Items**: Use ``add_display_item()`` to add content, specifying which column with ``column=``
6. **Handle POST**: Check ``request.method == 'POST'`` to respond to form submissions
7. **Render**: Return ``render_template("base_content.j2", content=disp.display(), target="...")``

Tutorial 2: Working with Background Tasks
------------------------------------------

Learn how to create background tasks that run asynchronously with real-time progress updates.

Complete Example
^^^^^^^^^^^^^^^^

.. code-block:: python

   from flask import Blueprint, render_template, request
   from submodules.framework.src.modules.displayer.displayer import Displayer, DisplayerLayout, Layouts
   from submodules.framework.src.modules.displayer.items import DisplayerItemButton, DisplayerItemText
   from submodules.framework.src.modules.threaded.threaded_action import Threaded_action
   from submodules.framework.src.modules.threaded import threaded_manager
   from submodules.framework.src.modules import utilities
   import time
   
   # Define the task class
   class DataProcessingTask(Threaded_action):
       """A background task that processes data"""
       
       m_default_name = "Data Processor"
       m_type = "threaded_action"
       
       def __init__(self, data_size=50):
           super().__init__()
           self.data_size = data_size
       
       def action(self):
           """Main work happens here"""
           self.console_write("Starting to process {} items...".format(self.data_size))
           self.console_write("Task running for user: {}".format(self.username), "INFO")
           
           for i in range(self.data_size):
               # Simulate processing
               time.sleep(0.1)
               
               # Update progress (0-100) and emit status via scheduler
               progress = int((i + 1) / self.data_size * 100)
               self.m_running_state = progress
               
               # Emit status update via SocketIO for real-time UI updates
               if self.m_scheduler:
                   self.m_scheduler.emit_status(
                       self.get_name(),
                       "Processing item {}/{}".format(i + 1, self.data_size),
                       progress,
                       "{}%".format(progress)
                   )
               
               # Log progress every 10 items
               if (i + 1) % 10 == 0:
                   self.console_write(f"Processed {i + 1}/{self.data_size} items")
           
           self.console_write("Processing complete!")
           self.m_running_state = 100
           
           # Emit final completion status
           if self.m_scheduler:
               self.m_scheduler.emit_status(
                   self.get_name(),
                   "Processing complete!",
                   100,
                   "Done"
               )
   
   @tutorials_bp.route('/tutorial2', methods=['GET', 'POST'])
   def tutorial2():
       """Tutorial 2: Background Task Example"""
       
       # Handle POST request to start the task
       if request.method == 'POST':
           data_in = utilities.util_post_to_json(request.form.to_dict())
           if DataProcessingTask.m_default_name in data_in:
               action_data = data_in[DataProcessingTask.m_default_name]
               # Check if task is already running
               thread = threaded_manager.thread_manager_obj.get_thread(DataProcessingTask.m_default_name) if threaded_manager.thread_manager_obj else None
               
               if not thread and 'btn_start' in action_data:
                   # Create and start a new task instance
                   task = DataProcessingTask(data_size=50)
                   task.start()
       
       disp = Displayer()
       # Pass the CLASS, not an instance - this avoids instantiation during page load
       disp.add_module(DataProcessingTask)
       disp.set_title("Background Task Example")
       
       # Add layout with button and instructions
       disp.add_master_layout(DisplayerLayout(Layouts.HORIZONTAL, [12]))
       
       # Add Start Action button
       disp.add_display_item(
           DisplayerItemButton("btn_start", "Start Action", icon="play"),
           column=0
       )
       
       disp.add_display_item(DisplayerItemText(
           "This page demonstrates background task scheduling. "
           "Click the 'Start Action' button above to begin the task. "
           "The progress bar will update in real-time below. "
           "You can also visit <a href='/threads'>Threads Monitor</a> to see all running tasks."
       ), column=0)
       
       return render_template("base_content.j2", content=disp.display(), target="tutorials.tutorial2")

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

Learn how to work with user sessions and authentication information.

Complete Example
^^^^^^^^^^^^^^^^

.. code-block:: python

   from flask import Blueprint, render_template, session
   from submodules.framework.src.modules.displayer.displayer import Displayer, DisplayerLayout, Layouts
   from submodules.framework.src.modules.displayer.items import (
       DisplayerItemText, DisplayerItemBadge, BSstyle
   )
   
   @tutorials_bp.route('/tutorial3')
   def tutorial3():
       """Tutorial 3: Working with Authentication"""
       disp = Displayer()
       disp.add_generic("auth_info")
       disp.set_title("Authentication Info")
       
       # Add layout
       disp.add_master_layout(DisplayerLayout(Layouts.HORIZONTAL, [12]))
       
       # Get current user from session
       username = session.get('username', 'GUEST')
       
       if username and username != "GUEST":
           disp.add_display_item(DisplayerItemText(f"Welcome back, {username}!"), column=0)
           disp.add_display_item(DisplayerItemBadge("Logged In", BSstyle.SUCCESS), column=0)
           disp.add_display_item(DisplayerItemText("You have full access to the system"), column=0)
       else:
           disp.add_display_item(DisplayerItemText(f"Current user: {username}"), column=0)
           disp.add_display_item(DisplayerItemBadge("Guest Mode", BSstyle.INFO), column=0)
           disp.add_display_item(DisplayerItemText("Go to /common/login to authenticate"), column=0)
       
       return render_template("base_content.j2", content=disp.display(), target="tutorials.tutorial3")

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

.. code-block:: python

   from flask import Blueprint, render_template, request
   from submodules.framework.src.modules.displayer.displayer import Displayer, DisplayerLayout, Layouts
   from submodules.framework.src.modules.displayer.items import (
       DisplayerItemText, DisplayerItemButton, DisplayerItemAlert, DisplayerItemSeparator,
       DisplayerItemInputString, DisplayerItemInputSelect, DisplayerItemInputText, BSstyle
   )
   from submodules.framework.src.modules import utilities
   
   @tutorials_bp.route('/tutorial4', methods=['GET', 'POST'])
   def tutorial4():
       """Tutorial 4: Creating and Processing Forms"""
       
       disp = Displayer()
       disp.add_generic("contact_form")
       disp.set_title("Contact Form")
       
       # Add layout - full width
       disp.add_master_layout(DisplayerLayout(Layouts.HORIZONTAL, [12]))
       
       # Handle form submission
       if request.method == 'POST':
           data_in = utilities.util_post_to_json(request.form.to_dict())
           data_in = data_in["contact_form"]
           
           name = data_in.get('name', '')
           email = data_in.get('email', '')
           subject = data_in.get('subject', 'General')
           message = data_in.get('message', '')
           
           # Show success message
           disp.add_display_item(
               DisplayerItemAlert(
                   text=f"Thank you {name}! We received your message.",
                   highlightType=BSstyle.SUCCESS,
                   title="Form Submitted Successfully!",
                   icon="check-circle"
               ),
               column=0
           )
           
           # Display submitted data
           disp.add_display_item(DisplayerItemSeparator(), column=0)
           disp.add_display_item(DisplayerItemText("<h6>Submitted Data</h6>"), column=0)
           disp.add_display_item(DisplayerItemText(f"<b>Name:</b> {name}"), column=0)
           disp.add_display_item(DisplayerItemText(f"<b>Email:</b> {email}"), column=0)
           disp.add_display_item(DisplayerItemText(f"<b>Subject:</b> {subject}"), column=0)
           disp.add_display_item(DisplayerItemText(f"<b>Message:</b> {message}"), column=0)
           
           # Add link to go back to form
           disp.add_display_item(DisplayerItemSeparator(), column=0)
           disp.add_display_item(
               DisplayerItemText('<a href="/tutorials/tutorial4" class="btn btn-primary"><i class="mdi mdi-arrow-left"></i> Submit Another</a>'),
               column=0
           )
       else:
           # Display the form
           disp.add_display_item(DisplayerItemText("<h5>Contact Us</h5>"), column=0)
           
           # Name input
           disp.add_display_item(
               DisplayerItemInputString(
                   "name",
                   "Name *",
                   "",
                   focus=True
               ),
               column=0
           )
           
           # Email input
           disp.add_display_item(
               DisplayerItemInputString(
                   "email",
                   "Email *",
                   ""
               ),
               column=0
           )
           
           # Subject dropdown
           disp.add_display_item(
               DisplayerItemInputSelect(
                   "subject",
                   "Subject",
                   "General",
                   ["General", "Support", "Feedback", "Bug"],
                   ["General Inquiry", "Technical Support", "Feedback", "Bug Report"]
               ),
               column=0
           )
           
           # Message textarea (multi-line text input)
           disp.add_display_item(
               DisplayerItemInputText(
                   "message",
                   "Message *",
                   ""
               ),
               column=0
           )
           
           # Submit button
           disp.add_display_item(
               DisplayerItemButton("btn_submit", "Submit", icon="send"),
               column=0
           )
       
       return render_template("base_content.j2", content=disp.display(), target="tutorials.tutorial4")

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