import pytest
from apispec import APISpec
from apispec_plugins import FlaskPlugin, spec_from
from flask import Flask
from flask.views import MethodView
from flask_restful import Api, Resource

from .. import utils


@pytest.fixture()
def app():
    app = Flask(__name__)
    with app.test_request_context():
        yield app


@pytest.fixture(scope="function", params=("2.0", "3.0.0"))
def spec(request):
    return APISpec(
        title="Test Suite",
        version="1.0.0",
        openapi_version=request.param,
        plugins=(FlaskPlugin(),),
    )


class TestFlaskPlugin:
    def test_function_view(self, app, spec):
        @app.route("/hello")
        def greeting():
            return "hello"

        operations = {
            "get": {
                "parameters": [],
                "responses": {"200": {"description": "get a greeting"}},
            }
        }
        spec.path(view=greeting, operations=operations)
        paths = utils.get_paths(spec)
        assert "get" in paths["/hello"]
        assert paths["/hello"] == operations

    def test_method_view(self, app, spec):
        class GreetingView(MethodView):
            """The greeting view.
            ---
            x-extension: global metadata
            """

            def get(self):
                """A greeting endpoint.
                ---
                description: get a greeting
                responses:
                    200:
                        description: received greeting
                """
                return "hello"

            def post(self):
                return {}

        method_view = GreetingView.as_view("hello")
        app.add_url_rule("/hello", view_func=method_view, methods=("GET", "POST"))
        spec.path(view=method_view)
        paths = utils.get_paths(spec)
        assert paths["/hello"]["get"] == {
            "summary": "A greeting endpoint.",
            "description": "get a greeting",
            "responses": {"200": {"description": "received greeting"}},
        }
        assert paths["/hello"]["post"] == {}
        assert paths["/hello"]["x-extension"] == "global metadata"

    def test_resource_view(self, app, spec):
        api = Api(app)

        @api.resource("/hello", endpoint="hello")
        class GreetingView(Resource):
            def get(self):
                """A greeting endpoint.
                ---
                description: get a greeting
                responses:
                    200:
                        description: received greeting
                """
                return "hello"

        class FarewellView(Resource):
            def get(self):
                """A farewell endpoint.
                ---
                description: get a farewell
                responses:
                    200:
                        description: received farewell
                """
                return "bye"

        api.add_resource(FarewellView, "/bye", endpoint="bye")

        greeting_view = app.view_functions["hello"]
        farewell_view = app.view_functions["bye"]
        spec.path(view=greeting_view)
        spec.path(view=farewell_view)
        paths = utils.get_paths(spec)
        assert paths["/hello"]["get"] == {
            "summary": "A greeting endpoint.",
            "description": "get a greeting",
            "responses": {"200": {"description": "received greeting"}},
        }
        assert paths["/bye"]["get"] == {
            "summary": "A farewell endpoint.",
            "description": "get a farewell",
            "responses": {"200": {"description": "received farewell"}},
        }

    def test_path_with_multiple_methods(self, app, spec):
        @app.route("/hello", methods=["GET", "POST"])
        def greeting():
            return "hello"

        spec.path(
            view=greeting,
            operations={
                "get": {"description": "get a greeting", "responses": {"200": {}}},
                "post": {"description": "post a greeting", "responses": {"200": {}}},
            },
        )
        paths = utils.get_paths(spec)
        get_op = paths["/hello"]["get"]
        post_op = paths["/hello"]["post"]
        assert get_op["description"] == "get a greeting"
        assert post_op["description"] == "post a greeting"

    def test_methods_from_rule(self, app, spec):
        class GreetingView(MethodView):
            """The greeting view."""

            def get(self):
                """A greeting endpoint.
                ---
                description: get a greeting
                responses:
                    200:
                        description: received greeting
                """
                return "hello"

            def post(self):
                return {}

            def delete(self):
                return {}

        method_view = GreetingView.as_view("hello")
        app.add_url_rule("/hello", view_func=method_view, methods=("GET", "POST"))
        spec.path(view=method_view)
        paths = utils.get_paths(spec)
        assert "get" in paths["/hello"]
        assert "post" in paths["/hello"]
        assert "delete" not in paths["/hello"]

    def test_docstring_introspection(self, app, spec):
        @app.route("/hello")
        def greeting():
            """A greeting endpoint.
            ---
            x-extension: value
            get:
                description: get a greeting
                responses:
                    200:
                        description: received greeting
            post:
                description: post a greeting
                responses:
                    200:
                        description: delivered greeting
            foo:
                description: not a valid operation
            """
            return "hello"

        spec.path(view=greeting)
        paths = utils.get_paths(spec)
        assert paths["/hello"]["x-extension"] == "value"
        assert paths["/hello"]["get"] == {
            "description": "get a greeting",
            "responses": {"200": {"description": "received greeting"}},
        }
        assert paths["/hello"]["post"] == {
            "description": "post a greeting",
            "responses": {"200": {"description": "delivered greeting"}},
        }
        assert "foo" not in paths["/hello"]

    def test_specs_from_decorator(self, app, spec):
        class GreetingView(MethodView):
            @spec_from(
                {
                    "description": "get a greeting",
                    "responses": {200: {"description": "received greeting"}},
                }
            )
            def get(self):
                """A greeting endpoint."""
                return "hello"

        method_view = GreetingView.as_view("hello")
        app.add_url_rule("/hello", view_func=method_view)
        spec.path(view=method_view)
        paths = utils.get_paths(spec)
        assert paths["/hello"]["get"] == {
            "summary": "A greeting endpoint.",
            "description": "get a greeting",
            "responses": {"200": {"description": "received greeting"}},
        }

    def test_path_is_translated_to_swagger_template(self, app, spec):
        @app.route("/hello/<user_id>")
        def hello_user(user_id):
            return f"greeting sent to user {user_id}"

        spec.path(view=hello_user)
        assert "/hello/{user_id}" in utils.get_paths(spec)

    def test_explicit_app_kwarg(self, spec):
        app = Flask(__name__)

        @app.route("/bye")
        def bye():
            return "bye"

        spec.path(view=bye, app=app)
        assert "/bye" in utils.get_paths(spec)

    def test_auto_responses(self, app, spec):
        class ResponsesView(MethodView):
            """The greeting view."""

            def get(self):
                """A greeting endpoint.
                ---
                description: get a greeting
                responses:
                    200:
                        description: received greeting
                    400:
                    404:
                        description: greeting not found
                    default:
                        description: unexpected error
                """
                return "hello"

        method_view = ResponsesView.as_view("responses")
        app.add_url_rule("/hello", view_func=method_view)
        spec.path(view=method_view)
        paths = utils.get_paths(spec)

        assert paths["/hello"]["get"] == {
            "summary": "A greeting endpoint.",
            "description": "get a greeting",
            "responses": {
                "200": {"description": "received greeting"},
                "400": {
                    "$ref": "#/responses/BadRequest"
                    if spec.openapi_version.major < 3
                    else "#/components/responses/BadRequest"
                },
                "404": {"description": "greeting not found"},
                "default": {"description": "unexpected error"},
            },
        }

        if spec.openapi_version.major < 3:
            assert spec.to_dict()["responses"] == {
                "BadRequest": {"schema": {"$ref": "#/definitions/HTTPResponse"}}
            }
        else:
            assert utils.get_components(spec)["responses"] == {
                "BadRequest": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/HTTPResponse"}
                        }
                    }
                },
            }
