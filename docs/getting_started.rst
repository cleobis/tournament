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

    pip install -r requirements.txt

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

Configuring the tournament
--------------------------

User accounts
^^^^^^^^^^^^^

Create a super-user for administration by running :command:`./manage.py createsuperuser`.

Create additional users in the Django admin web page. Views are configured to require one of three permission levels. Grant the appropriate level to the account.

* For read only access, grant the account the :command:`=> Read only access` privileges.
* For edit access (most tournament staff), grant the account :command:`=> Read only access` privileges. Notably, this does not include deleting brackets if they are created accidentally.
* For unrestricted access, either create a super-user account or grant the account :command:`=> Edit all data` privileges.

Events and Divisions
^^^^^^^^^^^^^^^^^^^^

For people to register, :mod:`registration.models.Event` objects must be created first. In the Django admin web page, create the appropriate events. The current implementation is sensitive to the exact names. A typical configuration is

.. list-table:: Typical event configuration
   :header-rows: 1
   
   * - Name
     - Format
     - Is Team
   * - Kata
     - kata
     - False
   * - Team kata
     - kata
     - True
   * - Kumite
     - elim1
     - False

:class:`registration.models.Division` objects are the groupings of people who will compete against each other. They do not need to be created immediately. People will be assigned to the correct division as the divisions are created or their criteria changed. To create a default set of divisions that may be later modified, use the utility function :func:`registration.models.create_divisions`::

   ./manage.py shell_plus
   >>> from registration.models import create_divisions
   >>> create_divisions()

Registration
^^^^^^^^^^^^

Registration is most conveniently done with a Google form. Export the form data as a csv. Import the form data by running::

   ./manage.py import_registrations path/to/file.csv

The application remembers the date stamp on the last imported record to prevent re-importing records multiple times. To reset the date, edit the Config record in the Django admin web page.

Registration may also be done with the sign-up page included with the application. It is assumed that this option will only be used the day of the tournament so it is protected with a login prompt.

Deploying for production
------------------------

The documentation is very clear that the built-in web server is suitable for development use only. In production, full
web, dynamic content, and database servers should be used.

.. todo::
   Discuss securing the server for production. (`ref <https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/>`_)

Web server
^^^^^^^^^^

One possible web server is `nginx <https://www.nginx.com>`_ (pronounced *Engine X*). An example :file:`nginx.conf` file is provided. Create a symlink from `/etc/nginx/sites-available`
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

   ./manage.py dumpdata --exclude auth.permission --exclude contenttypes --exclude accounts > db.json

changing database configuration and then loading into the new database::

   ./manage.py loaddata db.json

