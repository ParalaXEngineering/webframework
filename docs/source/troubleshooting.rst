Troubleshooting Guide
=====================

Common issues and their solutions when working with ParalaX Web Framework.

Installation Issues
-------------------

"Module not found" errors
^^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem**: Import errors when running the application.

**Solution**:

1. Ensure you're in the virtual environment:

   .. code-block:: bash

      source .venv/bin/activate  # macOS/Linux
      .venv\Scripts\activate     # Windows

2. Reinstall dependencies:

   .. code-block:: bash

      pip install -e .
      # or
      pip install -r requirements.txt

3. Check Python path:

   .. code-block:: python

      import sys
      print(sys.path)

"Flask is not available"
^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem**: Error message when importing framework.

**Solution**: Install Flask and dependencies:

.. code-block:: bash

   pip install flask flask-socketio flask-session python-socketio

"No module named 'src'"
^^^^^^^^^^^^^^^^^^^^^^^

**Problem**: Cannot import from ``src`` package.

**Solutions**:

1. **If running as package**: Install in editable mode:

   .. code-block:: bash

      pip install -e .

2. **If running directly**: Adjust Python path in your script:

   .. code-block:: python

      import sys
      import os
      sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

3. **Check directory structure**: Ensure you're in the project root.

Runtime Errors
--------------

"Address already in use"
^^^^^^^^^^^^^^^^^^^^^^^^

**Problem**: Port 5001 is already in use.

**Solutions**:

1. **Use a different port**:

   .. code-block:: python

      app.run(debug=True, port=5002)

2. **Find and kill the process** (macOS/Linux):

   .. code-block:: bash

      lsof -i :5001
      kill -9 <PID>

3. **Find and kill the process** (Windows):

   .. code-block:: bash

      netstat -ano | findstr :5001
      taskkill /PID <PID> /F

"Working outside of application context"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem**: Flask errors about application context.

**Solution**: Use application context:

.. code-block:: python

   with app.app_context():
       # Your code here
       pass

Or ensure setup_app() is called before accessing app features.

"Session not found" or "KeyError: 'username'"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem**: Session data not persisting.

**Solutions**:

1. **Set secret key**:

   .. code-block:: python

      app.secret_key = "your-secret-key"

2. **Configure session type**:

   .. code-block:: python

      app.config['SESSION_TYPE'] = 'filesystem'
      Session(app)

3. **Check session directory permissions**: Ensure ``flask_session/`` is writable.

4. **Clear old sessions**:

   .. code-block:: bash

      rm -rf flask_session/*

SocketIO Issues
---------------

WebSocket connection fails
^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem**: Real-time updates not working.

**Solutions**:

1. **Check SocketIO initialization**:

   .. code-block:: python

      from flask_socketio import SocketIO
      socketio = SocketIO(app)
      
      if __name__ == "__main__":
           socketio.run(app, debug=True, port=5001)

2. **Use correct transport**:

   .. code-block:: python

      socketio = SocketIO(app, cors_allowed_origins="*")

3. **Check browser console** for connection errors.

4. **Verify firewall** isn't blocking WebSocket connections.

"Multiple socket.io instances"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem**: Duplicate SocketIO initialization errors.

**Solution**: Ensure SocketIO is initialized only once:

.. code-block:: python

   # In src/main.py or your app setup
   socketio_obj = SocketIO(app)  # Only once!
   
   # Don't create another instance elsewhere

CORS errors with WebSockets
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem**: Cross-origin WebSocket errors.

**Solution**: Configure CORS:

.. code-block:: python

   socketio = SocketIO(app, cors_allowed_origins="*")
   # or specify domains:
   socketio = SocketIO(app, cors_allowed_origins=["https://example.com"])

Authentication Issues
---------------------

"Invalid credentials" always fails
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem**: Authentication never succeeds.

**Solutions**:

1. **Verify user exists**:

   .. code-block:: python

      from src.modules.auth.auth_manager import auth_manager
      users = auth_manager.list_users()
      print(users)

2. **Check password hashing**: Ensure bcrypt is installed:

   .. code-block:: bash

      pip install bcrypt

3. **Reset user password**:

   .. code-block:: python

      auth_manager.update_password("username", "newpassword")

4. **Check auth directory**: Ensure ``auth/users.json`` exists and is readable.

"Permission denied" for valid user
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem**: User has permission but still denied.

**Solutions**:

1. **Check exact permission name**:

   .. code-block:: python

      perms = auth_manager.get_user_permissions("username", "ModuleName")
      print(perms)

2. **Verify permission was granted**:

   .. code-block:: python

      auth_manager.grant_permission("username", "ModuleName", "view")

3. **Check session username**:

   .. code-block:: python

      from flask import session
      print(session.get('username'))

4. **Case sensitivity**: Permission names are case-sensitive.

Cannot create admin user
^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem**: Admin user creation fails.

**Solution**: Create with is_admin flag:

.. code-block:: python

   auth_manager.create_user("admin", "password", is_admin=True)

Or manually edit ``auth/users.json``:

.. code-block:: json

   {
       "admin": {
           "password_hash": "...",
           "is_admin": true
       }
   }

Background Task Issues
----------------------

Task doesn't start
^^^^^^^^^^^^^^^^^^

**Problem**: Threaded action doesn't execute.

**Solutions**:

1. **Call start() method**:

   .. code-block:: python

      task = MyTask()
      task.start()  # Don't forget this!

2. **Check thread manager**:

   .. code-block:: python

      from src.modules.threaded import threaded_manager
      running = threaded_manager.thread_manager_obj.m_running_threads
      print(len(running))

3. **Override action() not run()**:

   .. code-block:: python

      class MyTask(Threaded_action):
          def action(self):  # Correct method name
              # Your code here
              pass

Task runs but no output
^^^^^^^^^^^^^^^^^^^^^^^

**Problem**: Console output not showing.

**Solutions**:

1. **Use console_write()**:

   .. code-block:: python

      self.console_write("Message here")  # Not print()

2. **Check threads page**: Visit ``/threads`` to see console output.

3. **Flush stdout**:

   .. code-block:: python

      import sys
      print("message", flush=True)

Task hangs or never completes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem**: Task runs indefinitely.

**Solutions**:

1. **Check for infinite loops**:

   .. code-block:: python

      while self.m_running:  # Add stop condition
          # work
          time.sleep(1)

2. **Add timeout**:

   .. code-block:: python

      import signal
      signal.alarm(300)  # 5 minute timeout

3. **Use thread join with timeout**:

   .. code-block:: python

      task.m_thread_action.join(timeout=60)

4. **Check for deadlocks**: Review thread synchronization code.

Display/UI Issues
-----------------

Page shows no content
^^^^^^^^^^^^^^^^^^^^^

**Problem**: Blank page or empty module.

**Solutions**:

1. **Check display() call**:

   .. code-block:: python

      disp = Displayer()
      disp.add_generic({"title": "Test"})
      disp.add_display_item(DisplayerItemText("Content"))
      return disp.display()  # Don't forget this!

2. **Verify items added**:

   .. code-block:: python

      print(len(disp.m_modules))  # Should be > 0

3. **Check template exists**: Ensure ``templates/base.j2`` exists.

4. **Browser console**: Check for JavaScript errors.

Layouts not displaying correctly
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem**: Items not arranged as expected.

**Solutions**:

1. **Verify column sum = 12**:

   .. code-block:: python

      # Wrong: columns=[4, 4, 4, 4]  # Sum = 16
      # Right:
      layout = DisplayerLayout(Layouts.HORIZONTAL, columns=[3, 3, 3, 3])

2. **Check parent-child relationships**:

   .. code-block:: python

      parent_layout = disp.add_master_layout(layout1)
      child_layout = disp.add_child_layout(layout2, parent_layout=parent_layout)

3. **Use correct column index**:

   .. code-block:: python

      disp.add_display_item(item, column=0)  # 0-indexed!

CSS/JavaScript not loading
^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem**: Styling or functionality missing.

**Solutions**:

1. **Check static folder path**:

   .. code-block:: python

      app = Flask(__name__, static_folder="webengine/assets")

2. **Clear browser cache**: Hard refresh (Ctrl+Shift+R / Cmd+Shift+R).

3. **Verify file exists**:

   .. code-block:: bash

      ls webengine/assets/css/
      ls webengine/assets/js/

4. **Check console**: Browser developer tools → Console/Network tabs.

Database Issues
---------------

SQLite "database is locked"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem**: Concurrent access errors with SQLite.

**Solutions**:

1. **Use WAL mode**:

   .. code-block:: python

      import sqlite3
      conn = sqlite3.connect('database.db')
      conn.execute('PRAGMA journal_mode=WAL')

2. **Add timeout**:

   .. code-block:: python

      conn = sqlite3.connect('database.db', timeout=10.0)

3. **Use connection pooling** or switch to PostgreSQL/MySQL for concurrent access.

"No such table" error
^^^^^^^^^^^^^^^^^^^^^

**Problem**: Database table doesn't exist.

**Solutions**:

1. **Create tables**:

   .. code-block:: python

      with app.app_context():
           db.create_all()

2. **Run migrations**:

   .. code-block:: bash

      flask db upgrade

3. **Check database file exists**:

   .. code-block:: bash

      ls -la *.db

Testing Issues
--------------

Tests fail with import errors
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem**: Tests can't import modules.

**Solutions**:

1. **Install test dependencies**:

   .. code-block:: bash

      pip install -e .[dev]

2. **Run from project root**:

   .. code-block:: bash

      cd /path/to/webframework
      pytest tests/

3. **Check conftest.py**: Ensure pytest configuration is correct.

Tests pass individually but fail together
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem**: Test order dependencies.

**Solutions**:

1. **Use fixtures** for setup/teardown:

   .. code-block:: python

      @pytest.fixture
      def clean_db():
          # Setup
          yield
          # Teardown

2. **Isolate test state**: Don't rely on global variables.

3. **Check pytest.ini**: Verify test ordering configuration.

Fixture not found
^^^^^^^^^^^^^^^^^

**Problem**: pytest can't find fixture.

**Solutions**:

1. **Define in conftest.py**: Place fixtures in ``tests/conftest.py``.

2. **Check fixture scope**:

   .. code-block:: python

      @pytest.fixture(scope="session")  # Available to all tests

3. **Import fixture**: Ensure conftest.py is in Python path.

Performance Issues
------------------

Slow page load times
^^^^^^^^^^^^^^^^^^^^

**Problem**: Pages take too long to render.

**Solutions**:

1. **Profile the code**:

   .. code-block:: python

      import cProfile
      cProfile.run('disp.display()')

2. **Reduce display items**: Limit items per page.

3. **Cache expensive operations**:

   .. code-block:: python

      from functools import lru_cache
      
      @lru_cache(maxsize=100)
      def expensive_calculation(param):
          # ...

4. **Use pagination** for large datasets.

5. **Optimize database queries**: Add indexes, use eager loading.

High memory usage
^^^^^^^^^^^^^^^^^

**Problem**: Application consuming too much memory.

**Solutions**:

1. **Check for memory leaks**:

   .. code-block:: bash

      pip install memory_profiler
      python -m memory_profiler app.py

2. **Limit thread count**: Don't create unlimited threads.

3. **Clean up completed threads**:

   .. code-block:: python

      threaded_manager.thread_manager_obj.cleanup_old_threads()

4. **Use generators** for large data processing.

WebSocket connections accumulating
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem**: Too many open WebSocket connections.

**Solutions**:

1. **Implement disconnect handler**:

   .. code-block:: python

      @socketio.on('disconnect')
      def handle_disconnect():
          # Cleanup

2. **Set connection timeout**:

   .. code-block:: python

      socketio = SocketIO(app, ping_timeout=60, ping_interval=25)

3. **Monitor connections**: Check ``/threads`` for active connections.

Documentation Issues
--------------------

Sphinx build fails
^^^^^^^^^^^^^^^^^^

**Problem**: Documentation won't build.

**Solutions**:

1. **Install doc dependencies**:

   .. code-block:: bash

      pip install -e .[docs]

2. **Check for syntax errors** in .rst files.

3. **Clear build directory**:

   .. code-block:: bash

      cd docs
      make clean
      make html

4. **Check conf.py**: Verify Sphinx configuration.

Autodoc not finding modules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem**: API documentation incomplete.

**Solutions**:

1. **Check sys.path** in ``docs/source/conf.py``:

   .. code-block:: python

      sys.path.insert(0, os.path.abspath('../..'))

2. **Install package**:

   .. code-block:: bash

      pip install -e .

3. **Mock dependencies** in conf.py:

   .. code-block:: python

      autodoc_mock_imports = ['expensive_module']

Production Deployment Issues
-----------------------------

Gunicorn worker timeout
^^^^^^^^^^^^^^^^^^^^^^^

**Problem**: Workers timing out under load.

**Solutions**:

1. **Increase timeout**:

   .. code-block:: bash

      gunicorn --timeout 120 app:app

2. **Use async workers** for I/O bound tasks:

   .. code-block:: bash

      gunicorn -k gevent app:app

3. **Optimize slow endpoints**: Profile and cache.

502 Bad Gateway with Nginx
^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem**: Nginx can't reach application.

**Solutions**:

1. **Check application is running**:

   .. code-block:: bash

      ps aux | grep gunicorn

2. **Verify port matches** Nginx proxy_pass.

3. **Check application logs**:

   .. code-block:: bash

      tail -f logs/app.log

4. **Test direct access**:

   .. code-block:: bash

      curl http://127.0.0.1:5001

Static files not serving in production
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Problem**: CSS/JS missing in production.

**Solutions**:

1. **Configure Nginx** to serve static files:

   .. code-block:: nginx

      location /assets {
          alias /path/to/webengine/assets;
      }

2. **Use absolute paths** in templates.

3. **Check file permissions**:

   .. code-block:: bash

      chmod -R 755 webengine/assets

Still Having Issues?
--------------------

If you're still experiencing problems:

1. **Check logs**: Review ``logs/`` directory for errors
2. **Enable debug mode**: Set ``DEBUG=True`` for detailed error messages
3. **Review examples**: Check ``tests/manual_test_webapp.py`` for working code
4. **Simplify**: Create minimal reproduction case
5. **Check versions**: Ensure dependencies are up to date

.. code-block:: bash

   pip list  # Check installed versions
   pip install --upgrade -r requirements.txt  # Update dependencies

Common Debug Commands
---------------------

.. code-block:: bash

   # Check Python path
   python -c "import sys; print('\n'.join(sys.path))"
   
   # Verify imports
   python -c "from src.main import app; print('OK')"
   
   # Check port
   lsof -i :5001  # macOS/Linux
   netstat -ano | findstr :5001  # Windows
   
   # View logs
   tail -f logs/app.log
   
   # Test database
   python -c "import sqlite3; print(sqlite3.version)"
   
   # Memory usage
   ps aux | grep python  # macOS/Linux
   tasklist | findstr python  # Windows

For more help, see:

* :doc:`faq` for common questions
* :doc:`examples` for working code
* :doc:`framework` for architecture details
