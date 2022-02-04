import pytest
from apispec import APISpec
from apispec_plugins.webframeworks.flask import FlaskPlugin
from flask import Flask

from .. import utils


@pytest.fixture()
def app():
    app = Flask(__name__)
    with app.test_request_context():
        yield app


@pytest.fixture(scope='module', params=('2.0.0', '3.0.0'))
def spec(request):
    return APISpec(
        title='Test Suite',
        version='1.0.0',
        openapi_version=request.param,
        plugins=(FlaskPlugin(),),
    )


class TestFlaskPlugin:

    def test_function_view(self, app, spec):
        @app.route('/foo')
        def foo():
            return 'bar'

        operations = {'get': {
            'parameters': [],
            'responses': {'200': {}}
        }}
        spec.path(view=foo, operations=operations)
        paths = utils.get_paths(spec)

        assert 'get' in paths['/foo']
        assert paths['/foo'] == operations
