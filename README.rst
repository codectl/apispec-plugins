***************
apispec-plugins
***************

.. image:: https://img.shields.io/pypi/v/apispec-plugins
    :target: https://pypi.org/project/apispec-plugins
    :alt: PyPI version
.. image:: https://github.com/rena2damas/apispec-plugins/actions/workflows/ci.yaml/badge.svg
    :target: https://github.com/rena2damas/apispec-plugins/actions/workflows/ci.yaml
    :alt: CI
.. image:: https://codecov.io/gh/rena2damas/apispec-plugins/branch/master/graph/badge.svg
    :target: https://app.codecov.io/gh/rena2damas/apispec-plugins/branch/master
    :alt: codecov
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: code style: black
.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
    :target: https://opensource.org/licenses/MIT
    :alt: license: MIT

`apispec_plugins <https://github.com/marshmallow-code/apispec>`_ plugins for easy
integration with different components (web frameworks, packages, etc).

Features
========

* Supports the OpenAPI Specification (versions 2 and 3)
* Currently supported frameworks/plugins include:

  * ``apispec_plugins.webframeworks.flask``

Installation
============

Install the package directly from ``PyPI`` (recommended):

.. code-block:: bash

   $ pip install apispec-plugins

Plugin dependencies like ``Flask`` are not installed with the package by default. To
have ``Flask`` installed, do like so:

.. code-block:: bash

   $ pip install apispec-plugins[flask]

Example Usage
=============

.. code-block:: python

   from apispec import APISpec
   from apispec_plugins.webframeworks.flask import FlaskPlugin
   from flask import Flask

   spec = APISpec(
       title="Pet Store",
       version="1.0.0",
       openapi_version="2.0",
       info=dict(description="A minimal pet store API"),
       plugins=(FlaskPlugin(),),
   )

   app = Flask(__name__)


   @app.route("/pet/<petId>")
   def pet(petId):
       """Find pet by ID.
       ---
       get:
           parameters:
               - in: path
                 name: petId
           responses:
               200:
                   description: display pet data
       """
       return f"Display pet with ID {petId}"


   # Since `path` inspects the view and its route,
   # we need to be in a Flask request context
   with app.test_request_context():
       spec.path(view=pet)

Alternatively, a ``Flask`` ``MethodView`` can be used:

.. code-block:: python

   from flask.views import MethodView


   class PetAPI(MethodView):
       def get(self, petId):
           # get pet by ID
           pass


   app.add_url_rule("/pet/<petId>", view_func=PetAPI.as_view("pet_view"))

There is also easy integration with other packages like
``Flask-RESTful``:

.. code-block:: python

   from flask_restful import Api, Resource


   class PetAPI(Resource):
       def get(self, petId):
           # get pet by ID
           pass


   api = Api(app)
   api.add_resource(PetAPI, "/pet/<petId>", endpoint="pet")

Dynamic specs
-------------

As seen so far, specs are specified in the docstring of the view or
class. However, with the ``spec_from`` decorator, one can dynamically
set specs:

.. code-block:: python

   from apispec_plugins import spec_from


   @spec_from(
       {
           "parameters": {"in": "path", "name": "petId"},
           "responses": {200: {"description": "display pet data"}},
       }
   )
   def pet(petID):
       """Find pet by ID."""
       pass

Why not ``apispec-webframeworks``?
==================================

The conceiving of this project was based
on `apispec-webframeworks <https://github
.com/marshmallow-code/apispec-webframeworks>`_. While that project is focused on
integrating web frameworks with ``APISpec``, this repository goes a step further in providing the best integration
possible with the ``APISpec`` standards. Some limitations on that project were also addressed, like:

* a path cannot register no more than 1 single rule per endpoint;
* support for additional libraries like ``Flask-RESTful``;
* limited docstring spec processing;

Tests & linting
===============

Run tests with ``tox``:

.. code-block:: bash

    # ensure tox is installed
    $ tox

Run linter only:

.. code-block:: bash

    $ tox -e lint

Optionally, run coverage as well with:

.. code-block:: bash

    $ tox -e coverage

License
=======

MIT licensed. See `LICENSE <LICENSE>`_.
