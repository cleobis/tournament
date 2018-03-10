Getting Started
===============

Configure environment
---------------------

Python
^^^^^^

The application has been tested with Python 3.6. If necessary, install a recent version of python.

It is easier to manage dependencies on a per-project basis by creating a
`virtual environment <https://docs.python.org/3/library/venv.html>`_. In the root project directory, run::

    python -m venv venv

Once the environment is created, activate it by running either, on Posix::

    source venv/bin/activate

or Windows::

    venv\Scripts\activate.bat

Install the project dependencies by running::

    pip install -e requirements.txt

manage.py
^^^^^^^^^

The application includes a :file:`manage.py` script for running administrative operations. On Posix, the file is
executed by calling :command:`./manage.py` from the folder containing it. Depending on your configuration, you may need
to update the first line of the file to point to the python installation location. Alternatively, or on Windows, run
:command:`python manage.py`.

JavaScript Dependencies
^^^^^^^^^^^^^^^^^^^^^^^

JavaScript libraries are managed with `Yarn <https://yarnpkg.com/>`_. Install it. Then install the packages by running::

    yarn install

Files will be installed into the :file:`node_modules` folder.

Running locally
---------------

Testing the server locally is easy using the built-in web server and `SQLite <https://www.sqlite.org/index.html>`_
database. First configure the database by running from the command line::

   ./manage.py migrate

Then launch the demo server by running::

   ./manage.py runserver

Deploying for production
------------------------

The documentation is very clear that the built-in web server is suitable for development use only. In production, full
web, dynamic content, and database servers should be used.

.. todo::
   Discuss securing the server for production. (`ref <django deploy>`_)

Web server
^^^^^^^^^^

One possible web server is `nginx <https://www.nginx.com>`_. An example :file:`nginx.conf` file is provided. Create a symlink from `/etc/nginx/sites-available`
to your `nginx.conf`.  Useful commands:

- :command:`nginx` - Start the server
- :command:`nginx -s stop` - Stop the server
- :command:`nginx -s reload` - Restart the server.

Nginx serves the static assets. They must be collected into a single location by running::

   ./manage.py collectstatic

The static storage location in :mod:`tournament.settings` must match the location in :file:`nginx.conf`.

Dynamic content server
^^^^^^^^^^^^^^^^^^^^^^

Nginx forwards request for dynamic pages to the Gunicorn server. Install Gunicorn with :command:`pip install gunicorn`. A
sample configuration file :file:`gunicorn.conf.py` is provided. Start the server with::

    gunicorn --bind 0.0.0.0:8000 tournament.wsgi

The port in this line must match the port that nginx forwards requests to.

Database server
^^^^^^^^^^^^^^^

For production deployments, I have used the PostgreSql server. Install it and create a database, username, and password.
Configure :mod:`tournament.settings`. Initialize the database by running :command:`manage.py migrate`.

Migrating from local to production
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can migrate from the old database by exporting its content (`ref <https://coderwall.com/p/mvsoyg/django-dumpdata-and-loaddata>`_)::

   ./manage.py dumpdata --exclude auth.permission --exclude contenttypes > db.json

changing database configuration and then loading into the new database::

   ./manage.py loaddata db.json

