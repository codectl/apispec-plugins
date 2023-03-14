***************
apispec-plugins
***************

.. image:: https://img.shields.io/pypi/v/apispec-plugins
    :target: https://pypi.org/project/apispec-plugins
    :alt: PyPI version
.. image:: https://github.com/codectl/apispec-plugins/actions/workflows/ci.yaml/badge.svg
    :target: https://github.com/codectl/apispec-plugins/actions/workflows/ci.yaml
    :alt: CI
.. image:: https://codecov.io/gh/codectl/apispec-plugins/branch/master/graph/badge.svg
    :target: https://app.codecov.io/gh/codectl/apispec-plugins/branch/master
    :alt: codecov
.. image:: https://img.shields.io/badge/code_style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: code style: black
.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
    :target: https://opensource.org/licenses/MIT
    :alt: license: MIT
.. image:: https://img.shields.io/badge/OAS-2_|_3-14ACBB.svg
    :target: https://github.com/OAI/OpenAPI-Specification
    :alt: OpenAPI Specification 2/3 compatible
.. image:: https://img.shields.io/pypi/pyversions/apispec-plugins
   :alt: Python compatibility

`APISpec <https://github.com/marshmallow-code/apispec>`__ plugins for easy
integration with different components (web frameworks, packages, etc).

Features
========
* Support for the OpenAPI Specification (versions 2 and 3)
* Support for frameworks/plugins which include:

  * ``apispec_plugins.webframeworks.flask``
  * ``apispec_plugins.ext.pydantic``

Installation
============
Install the package directly from ``PyPI`` (recommended):

.. code-block:: bash

   $ pip install apispec-plugins

Plugin dependencies like ``flask`` and ``pydantic`` are not installed with the package by default. To
have ``flask`` and ``pydantic`` installed, run:

.. code-block:: bash

   $ pip install apispec-plugins[flask,pydantic]

Example Usage
=============
.. code-block:: python

    from typing import Optional

    from apispec import APISpec
    from apispec_plugins.base.registry import RegistryMixin
    from apispec_plugins.ext.pydantic import PydanticPlugin
    from apispec_plugins.webframeworks.flask import FlaskPlugin
    from flask import Flask
    from pydantic import BaseModel


    # set APISpec plugins
    spec = APISpec(
        title="Pet Store",
        version="1.0.0",
        openapi_version="3.1.0",
        info=dict(description="A minimal pet store API"),
        plugins=(FlaskPlugin(), PydanticPlugin()),
    )


    # optional Flask support
    app = Flask(__name__)


    # optional pydantic support
    class Pet(BaseModel, RegistryMixin):
        id: Optional[int]
        name: str


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
                     content:
                         application/json:
                             schema: Pet
        """
        return f"Display pet with ID {petId}"

        # register `path` for the Flask route
        with app.test_request_context():
            spec.path(view=pet)

Alternatively, to ``Flask`` routes, ``MethodView`` can be used:

.. code-block:: python

   from flask.views import MethodView


   class PetAPI(MethodView):
       def get(self, petId):
           # get pet by ID
           pass


   app.add_url_rule("/pet/<petId>", view_func=PetAPI.as_view("pet_view"))

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
The conceiving of this project was based on `apispec-webframeworks <https://github.com/marshmallow-code/
apispec-webframeworks>`__. While that project is focused on integrating web frameworks with ``APISpec``, this
project goes a step further in providing the best integration possible with the ``APISpec`` standards. Some
limitations on that project were also addressed, like:

* a path cannot register no more than 1 single rule per endpoint;
* limited docstring spec processing;

Tests & linting 🚥
==================
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
MIT licensed. See `LICENSE <LICENSE>`__.
