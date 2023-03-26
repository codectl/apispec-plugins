import pytest
from apispec import APISpec
from apispec_plugins import FlaskPlugin, PydanticPlugin, spec_from
from flask import Flask
from flask.views import MethodView

from ..utils import (
    build_ref,
    get_paths,
    get_responses,
    get_schema,
    get_schemas,
)


@pytest.fixture()
def app():
    app = Flask(__name__)
    with app.test_request_context():
        yield app


@pytest.fixture(scope="function", params=("2.0", "3.0.3"))
def spec(request):
    return APISpec(
        title="Swagger Petstore",
        version="1.0.0",
        openapi_version=request.param,
        plugins=(FlaskPlugin(),),
    )


class TestFlaskPlugin:
    def test_function_view(self, app, spec):
        @app.route("/pet")
        def pet():
            return "Max"

        spec.path(
            view=pet,
            operations={
                "get": {
                    "responses": {200: {"description": "get a pet"}},
                }
            },
        )
        paths = get_paths(spec)
        assert "get" in paths["/pet"]
        assert paths["/pet"]["get"]["responses"]["200"] == {"description": "get a pet"}

    def test_method_view(self, app, spec):
        class PetView(MethodView):
            """The greeting view.
            ---
            x-extension: global metadata
            """

            def get(self):
                """Get a pet's name.
                ---
                description: get a pet's name
                responses:
                    200:
                        description: the pet's name
                """
                return "Max"

            def post(self):
                return {}

        method_view = PetView.as_view("pet")
        app.add_url_rule("/pet", view_func=method_view, methods=("GET", "POST"))
        spec.path(view=method_view)
        paths = get_paths(spec)
        assert paths["/pet"]["get"] == {
            "summary": "Get a pet's name.",
            "description": "get a pet's name",
            "responses": {"200": {"description": "the pet's name"}},
        }
        assert paths["/pet"]["post"] == {}
        assert paths["/pet"]["x-extension"] == "global metadata"

    def test_path_with_multiple_methods(self, app, spec):
        @app.route("/pet", methods=["GET", "POST"])
        def pet():
            return "Max"

        spec.path(
            view=pet,
            operations={
                "get": {"description": "get a pet's name", "responses": {200: {}}},
                "post": {"description": "register a pet", "responses": {200: {}}},
            },
        )
        paths = get_paths(spec)
        get_op = paths["/pet"]["get"]
        post_op = paths["/pet"]["post"]
        assert get_op["description"] == "get a pet's name"
        assert post_op["description"] == "register a pet"

    def test_methods_from_rule(self, app, spec):
        class PetView(MethodView):
            """A view for pets."""

            def get(self):
                """Get a pet's name.
                ---
                description: get a pet's name
                responses:
                    200:
                        description: the pet's name
                """
                return "Max"

            def post(self):
                return {}

            def delete(self):
                return {}

        method_view = PetView.as_view("pet")
        app.add_url_rule("/pet", view_func=method_view, methods=("GET", "POST"))
        spec.path(view=method_view)
        paths = get_paths(spec)
        assert "get" in paths["/pet"]
        assert "post" in paths["/pet"]
        assert "delete" not in paths["/pet"]

    def test_docstring_introspection(self, app, spec):
        @app.route("/pet")
        def pet():
            """Get a pet's name.
            ---
            x-extension: value
            get:
                description: get a pet's name
                responses:
                    200:
                        description: the pet's name
            post:
                description: register a pet
                responses:
                    200:
                        description: the registered pet's name
            foo:
                description: not a valid operation
            """
            return "Max"

        spec.path(view=pet)
        paths = get_paths(spec)
        assert paths["/pet"]["x-extension"] == "value"
        assert paths["/pet"]["get"] == {
            "description": "get a pet's name",
            "responses": {"200": {"description": "the pet's name"}},
        }
        assert paths["/pet"]["post"] == {
            "description": "register a pet",
            "responses": {"200": {"description": "the registered pet's name"}},
        }
        assert "foo" not in paths["/pet"]

    def test_specs_from_decorator(self, app, spec):
        class PetView(MethodView):
            @spec_from(
                {
                    "description": "get a pet's name",
                    "responses": {200: {"description": "the pet's name"}},
                }
            )
            def get(self):
                """Get a pet's name."""
                return "Max"

        method_view = PetView.as_view("pet")
        app.add_url_rule("/pet", view_func=method_view)
        spec.path(view=method_view)
        paths = get_paths(spec)
        assert paths["/pet"]["get"] == {
            "summary": "Get a pet's name.",
            "description": "get a pet's name",
            "responses": {"200": {"description": "the pet's name"}},
        }

    def test_path_is_translated_to_swagger_template(self, app, spec):
        @app.route("/pet/<name>")
        def pet(name):
            return name

        spec.path(view=pet)
        assert "/pet/{name}" in get_paths(spec)

    def test_explicit_app_kwarg(self, spec):
        app = Flask(__name__)

        @app.route("/pet")
        def pet():
            return "Max"

        spec.path(view=pet, app=app)
        assert "/pet" in get_paths(spec)

    def test_auto_responses(self, app, spec):
        class PetView(MethodView):
            """A view for pets."""

            def get(self):
                """Get a pet's name.
                ---
                description: get a pet's name
                responses:
                    200:
                        description: the pet's name
                    400:
                    404:
                        description: pet not found
                    default:
                        description: unexpected error
                """
                return "Max"

        method_view = PetView.as_view("pet")
        app.add_url_rule("/pet", view_func=method_view)
        spec.path(view=method_view)
        paths = get_paths(spec)

        assert paths["/pet"]["get"] == {
            "summary": "Get a pet's name.",
            "description": "get a pet's name",
            "responses": {
                "200": {"description": "the pet's name"},
                "400": build_ref(spec, "response", "BadRequest"),
                "404": {"description": "pet not found"},
                "default": {"description": "unexpected error"},
            },
        }

        ref = build_ref(spec, "schema", "HTTPResponse")
        assert get_schema(spec, get_responses(spec)["BadRequest"]) == ref

    def test_default_dataclass_resolver(self, app, spec, mocker):
        model = "apispec_plugins.base.types.HTTPResponse"
        mocker.patch(f"{model}.__pydantic_model__", None)

        @app.route("/pet")
        def pet():
            return "Max"

        spec.path(view=pet, operations={"get": {"responses": {400: None}}})

        paths = get_paths(spec)
        ref = build_ref(spec, "schema", "HTTPResponse")
        assert "get" in paths["/pet"]
        assert get_schema(spec, get_responses(spec)["BadRequest"]) == ref
        assert "HTTPResponse" in get_schemas(spec)

    @pytest.mark.parametrize("version", ("2.0", "3.1.0"))
    def test_pydantic_plugin(self, app, version):
        spec = APISpec(
            title="Swagger Petstore",
            version="1.0.0",
            openapi_version=version,
            plugins=(FlaskPlugin(), PydanticPlugin()),
        )

        @app.route("/pet")
        def pet():
            return "Max"

        response = {"schema": "Pet"}
        if spec.openapi_version.major >= 3:
            response = {"content": {"application/json": response}}

        spec.path(
            view=pet, operations={"get": {"responses": {200: response, 400: None}}}
        )

        responses = get_paths(spec)["/pet"]["get"]["responses"]
        pet_ref = build_ref(spec, "schema", "Pet")
        response_ref = build_ref(spec, "schema", "HTTPResponse")
        assert get_schema(spec, responses["200"]) == pet_ref
        assert responses["400"] == build_ref(spec, "response", "BadRequest")
        assert get_schema(spec, get_responses(spec)["BadRequest"]) == response_ref
        assert "Pet" in get_schemas(spec)
        assert "HTTPResponse" in get_schemas(spec)
