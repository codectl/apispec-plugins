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
        def greeting():
            return 'hi'

        operations = {'get': {
            'parameters': [],
            'responses': {'200': {}}
        }}
        spec.path(view=greeting, operations=operations)
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

    def test_path_with_multiple_methods(self, app, spec):
        @app.route('/hello', methods=['GET', 'POST'])
        def greeting():
            return 'hi'

        spec.path(
            view=greeting,
            operations=dict(
                get={'description': 'get a greeting', 'responses': {'200': {}}},
                post={'description': 'post a greeting', 'responses': {'200': {}}},
            ),
        )
        paths = utils.get_paths(spec)
        get_op = paths['/hello']['get']
        post_op = paths['/hello']['post']

        assert get_op['description'] == 'get a greeting'
        assert post_op['description'] == 'post a greeting'

    def test_methods_from_rule(self, app, spec):
        class GreetingView(MethodView):
            """The greeting view.
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

            def delete(self):
                return {}

        method_view = GreetingView.as_view("hi")
        app.add_url_rule('/hi', view_func=method_view, methods=('GET', 'POST'))
        spec.path(view=method_view)
        paths = utils.get_paths(spec)

        assert 'get' in paths['/hi']
        assert 'post' in paths['/hi']
        assert 'delete' not in paths['/hi']
