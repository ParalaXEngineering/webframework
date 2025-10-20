Frequently Asked Questions
==========================

Common questions about the ParalaX Web Framework.

General Questions
-----------------

What is ParalaX Web Framework?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

ParalaX Framework is a Flask-based web framework designed to simplify the creation of tool management and monitoring applications. It provides built-in support for authentication, real-time updates, background task management, and dynamic UI generation.

Who should use this framework?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

ParalaX is ideal for:

* Developers building internal tools and dashboards
* Engineers creating monitoring and control interfaces
* Teams needing rapid prototyping with professional UI
* Projects requiring background task management
* Applications needing role-based access control

Do I need to know Flask?
^^^^^^^^^^^^^^^^^^^^^^^^^

Basic Flask knowledge is helpful but not required. The framework abstracts most Flask complexity, allowing you to focus on your application logic. You should understand:

* Python basics (classes, functions, imports)
* HTTP concepts (requests, responses, sessions)
* Basic HTML/CSS (helpful but not essential with the Displayer system)

Can I use this in production?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yes! The framework has been successfully deployed in production environments. However, ensure you:

* Change default secret keys
* Use a production WSGI server (Gunicorn, uWSGI)
* Enable HTTPS
* Configure proper logging
* Set up database backups (if using)

Installation Questions
----------------------

What Python versions are supported?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Python 3.8 or higher is required. The framework is tested on:

* Python 3.8
* Python 3.9
* Python 3.10
* Python 3.11
* Python 3.12

Which operating systems are supported?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The framework runs on:

* macOS (Intel and Apple Silicon)
* Linux (Ubuntu, Debian, RHEL, CentOS)
* Windows 10/11

Can I use this with Docker?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yes! Create a Dockerfile:

.. code-block:: dockerfile

   FROM python:3.11-slim
   
   WORKDIR /app
   COPY . .
   
   RUN pip install --no-cache-dir -r requirements.txt
   
   EXPOSE 5001
   CMD ["python", "app.py"]

How do I update the framework?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If using as a git submodule:

.. code-block:: bash

   cd submodules/framework
   git pull origin main
   cd ../..
   pip install -r submodules/framework/requirements.txt

If installed directly:

.. code-block:: bash

   cd webframework
   git pull origin main
   pip install -e .

Development Questions
---------------------

How do I debug my application?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Enable Flask debug mode:

.. code-block:: python

   if __name__ == "__main__":
       app.run(debug=True, port=5001)

Check logs at ``logs/`` directory (created automatically).

Use the Python debugger:

.. code-block:: python

   import pdb; pdb.set_trace()

How do I add custom CSS/JavaScript?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Place files in ``webengine/assets/``:

* CSS: ``webengine/assets/css/custom.css``
* JavaScript: ``webengine/assets/js/custom.js``

Reference in templates or use the resource registry:

.. code-block:: python

   from src.modules.displayer.core import ResourceRegistry
   
   ResourceRegistry.register_css("/assets/css/custom.css")
   ResourceRegistry.register_js("/assets/js/custom.js")

How do I create custom display items?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Extend the ``DisplayerItem`` base class:

.. code-block:: python

   from src.modules.displayer.items.base_item import DisplayerItem
   
   class DisplayerItemCustom(DisplayerItem):
       def __init__(self, label, custom_param, **kwargs):
           super().__init__(label, "custom_widget", **kwargs)
           self.custom_param = custom_param
       
       def to_dict(self):
           data = super().to_dict()
           data['custom_param'] = self.custom_param
           return data

Then create a corresponding template in ``templates/displayer_items/``.

How do I access the database?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The framework doesn't include a database by default. You can use:

* **SQLAlchemy**: Full ORM

  .. code-block:: python

     from flask_sqlalchemy import SQLAlchemy
     app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
     db = SQLAlchemy(app)

* **SQLite**: Lightweight option

  .. code-block:: python

     import sqlite3
     conn = sqlite3.connect('database.db')

* **PostgreSQL/MySQL**: Enterprise databases

Can I use this with React/Vue?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yes! You can:

1. Use the framework as an API backend (JSON responses)
2. Serve your React/Vue app from ``webengine/assets/``
3. Use Flask routes for API endpoints

Example API endpoint:

.. code-block:: python

   from flask import jsonify
   
   @app.route("/api/data")
   def api_data():
       return jsonify({"data": [1, 2, 3]})

Authentication Questions
------------------------

How do I change default passwords?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Modify auth initialization in your app:

.. code-block:: python

   from src.modules.auth.auth_manager import auth_manager
   
   # Change admin password
   auth_manager.update_password("admin", "new_secure_password")

Where are user credentials stored?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, in JSON files at ``auth/users.json``. You can customize the location:

.. code-block:: python

   from src.modules.auth.auth_manager import AuthManager
   
   auth_manager_instance = AuthManager(auth_dir="custom/auth/path")

Can I integrate with LDAP/Active Directory?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Not built-in, but you can extend the AuthManager:

.. code-block:: python

   from src.modules.auth.auth_manager import AuthManager
   import ldap
   
   class LDAPAuthManager(AuthManager):
       def authenticate(self, username, password):
           # Your LDAP authentication logic
           pass

Can I use OAuth/SSO?
^^^^^^^^^^^^^^^^^^^^

You can integrate third-party authentication using Flask extensions:

* Flask-Login for session management
* Flask-Dance for OAuth (Google, GitHub, etc.)
* Flask-OIDC for OpenID Connect

Background Tasks Questions
---------------------------

How many concurrent tasks can I run?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There's no hard limit, but consider:

* System resources (CPU, memory)
* Python's GIL (Global Interpreter Lock)
* For CPU-intensive tasks, use multiprocessing instead of threading

How do I stop a running task?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Call the ``stop()`` method:

.. code-block:: python

   task.stop()  # Signals the task to stop
   task.wait_completion()  # Wait for it to finish

Or from the threads monitoring page (``/threads``).

Can tasks persist across restarts?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

No, tasks are in-memory. For persistent jobs, consider:

* Celery (distributed task queue)
* APScheduler (persistent scheduling)
* Database-backed job queues

How do I schedule recurring tasks?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use the long-term scheduler:

.. code-block:: python

   from src.modules.scheduler.scheduler import Scheduler_LongTerm
   
   lt_scheduler = Scheduler_LongTerm()
   lt_scheduler.register_function(my_function, period=60)  # Every 60 min
   lt_scheduler.start()

UI/Display Questions
--------------------

How do I customize the theme?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Modify CSS in ``webengine/assets/css/`` or override Bootstrap variables.

The framework uses Bootstrap 5 for styling.

Can I use custom templates?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yes! Create Jinja2 templates in ``templates/`` and render them:

.. code-block:: python

   from flask import render_template
   
   @app.route("/custom")
   def custom():
       return render_template("my_template.html", data="value")

How do I add icons?
^^^^^^^^^^^^^^^^^^^

The framework uses Bootstrap Icons. Reference by name:

.. code-block:: python

   DisplayerItemButton("Save", icon="save")

Or use custom icons by placing SVG/PNG in ``webengine/assets/images/``.

Performance Questions
---------------------

How do I improve page load times?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Minimize display items per page
* Use pagination for large data sets
* Cache expensive computations
* Enable Flask response compression
* Use a CDN for static assets

Can the framework handle high traffic?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For production with high traffic:

* Use a production WSGI server (Gunicorn with multiple workers)
* Put behind a reverse proxy (Nginx, Apache)
* Use Redis for session storage instead of filesystem
* Scale horizontally with load balancer

Should I use WebSockets in production?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yes, but consider:

* Use Redis as message broker for multi-worker setups
* Configure proper WebSocket timeout values
* Monitor open connections

Deployment Questions
--------------------

How do I deploy to production?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use a production WSGI server:

.. code-block:: bash

   # Install Gunicorn
   pip install gunicorn
   
   # Run with 4 workers
   gunicorn -w 4 -b 0.0.0.0:5001 "app:app"

For WebSocket support:

.. code-block:: bash

   gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 -b 0.0.0.0:5001 "app:app"

How do I configure Nginx?
^^^^^^^^^^^^^^^^^^^^^^^^^^

Example Nginx configuration:

.. code-block:: nginx

   server {
       listen 80;
       server_name example.com;
       
       location / {
           proxy_pass http://127.0.0.1:5001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       location /socket.io {
           proxy_pass http://127.0.0.1:5001/socket.io;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }

How do I handle logs in production?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Configure log rotation:

.. code-block:: python

   from logging.handlers import RotatingFileHandler
   
   handler = RotatingFileHandler(
       'logs/app.log',
       maxBytes=10485760,  # 10MB
       backupCount=10
   )
   app.logger.addHandler(handler)

Or use external logging services (Papertrail, Loggly, etc.).

Testing Questions
-----------------

How do I write tests for my app?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use pytest with Flask's test client:

.. code-block:: python

   def test_home_page(client):
       response = client.get('/')
       assert response.status_code == 200

See ``tests/`` directory for examples.

How do I test authenticated routes?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use test fixtures:

.. code-block:: python

   @pytest.fixture
   def authenticated_client(client):
       with client.session_transaction() as sess:
           sess['username'] = 'testuser'
       return client
   
   def test_protected_route(authenticated_client):
       response = authenticated_client.get('/admin')
       assert response.status_code == 200

Can I use the demo app in tests?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yes! The demo app (``tests/manual_test_webapp.py``) can serve as a testing playground and reference implementation.

Still Have Questions?
---------------------

* Check the :doc:`troubleshooting` guide
* Review :doc:`examples` for code patterns
* Explore the :doc:`framework_classes` API reference
* Examine the demo application source code

You can also review the source code - it's designed to be readable and well-documented!
