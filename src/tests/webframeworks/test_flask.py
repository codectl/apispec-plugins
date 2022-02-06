import pytest
from apispec import APISpec
from apispec_plugins.webframeworks.flask import FlaskPlugin
from flask import Flask
from flask.views import MethodView

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
        @app.route('/hi')
        def hi():
            return 'hi'

        operations = {'get': {
            'parameters': [],
            'responses': {'200': {}}
        }}
        spec.path(view=hi, operations=operations)
        paths = utils.get_paths(spec)

        assert 'get' in paths['/hi']
        assert paths['/hi'] == operations

    def test_method_view(self, app, spec):
        class GreetingView(MethodView):
            """The greeting view.
            ---
            x-extension: global metadata
            """

            def get(self):
                """Get a greeting.
                ---
                description: request a new greeting
                responses:
                    200:
                        description: the requested greeting
                """
                return 'hi'

            def post(self):
                return {}

        method_view = GreetingView.as_view('hi')
        app.add_url_rule('/hi', view_func=method_view, methods=('GET', 'POST'))
        spec.path(view=method_view)
        paths = utils.get_paths(spec)

        assert paths['/hi']['get'] == {
            'summary': 'Get a greeting.',
            'description': 'request a new greeting',
            'responses': {'200': {'description': 'the requested greeting'}},
        }
        assert paths['/hi']['post'] == {}
        assert paths['/hi']['x-extension'] == 'global metadata'
