# apispec-plugins

[apispec](https://github.com/marshmallow-code/apispec) plugins for integrating with different components (web
frameworks, packages, etc).

Currently supported plugins:

* ```apispec_plugins.webframeworks.flask```

## Installation
 
Install the package directly from ```PyPI``` (recommended):

```bash
pip install apispec-plugins
```

Plugin dependencies like ```Flask``` are not installed with the package by default.
To have ```Flask``` installed, do like so:

```bash
pip install apispec-plugins[flask]
```

### Migration from ```apispec<1.0.0```

The location from where plugins, like ```FlaskPlugin``` imports, are imported is different.
Therefore, the imports need to be performed this way:

```python
# apispec<1.0.0
from apispec.ext.flask import FlaskPlugin

# apispec>=1.0.0
from apispec_plugins.webframeworks.flask import FlaskPlugin
```

## Example Usage

```python
from apispec import APISpec
from apispec_plugins.webframeworks.flask import FlaskPlugin
from flask import Flask

spec = APISpec(
    title='Pet Store',
    version='1.0.0',
    openapi_version='2.0',
    info=dict(description='A minimal pet store API'),
    plugins=(FlaskPlugin(),)
)

app = Flask(__name__)


@app.route('/pet/<petId>')
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
```

Alternatively, a ```Flask``` ```MethodView``` can be used:

```python
from flask.views import MethodView

class PetAPI(MethodView):

    def get(self, petId):
        # get pet by ID
        pass


app.add_url_rule('/pet/<petId>', view_func=PetAPI.as_view('pet_view'))
```

There is also easy integration with other packages like ```Flask-RESTful```:

```python
from flask_restful import Api, Resource


class PetAPI(Resource):

    def get(self, petId):
        # get pet by ID
        pass

api = Api(app)
api.add_resource(PetAPI, '/pet/<petId>', endpoint='pet')
```

### Dynamic specs

As seen so far, specs are specified in the docstring of the view or class. However, with the ```spec_from``` decorator,
one can dynamically set specs:

```python
from apispec_plugins import spec_from

@spec_from({
    'parameters': {'in': 'path', 'name': 'petId'},
    'responses': {200: {'description': 'display pet data'}}
})
def pet(petID):
    """Find pet by ID."""
    pass
```
