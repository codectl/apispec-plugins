import pytest
from apispec import APISpec
from apispec_plugins.base.registry import ModelMetaclass
from apispec_plugins.ext.pydantic import PydanticPlugin
from apispec_plugins.utils import load_specs_from_docstring
from pydantic import BaseModel

from .. import utils


@pytest.fixture(scope="function", params=("2.0", "3.0.0"))
def spec(request):
    return APISpec(
        title="Test Suite",
        version="1.0.0",
        openapi_version=request.param,
        plugins=(PydanticPlugin(),),
    )


@pytest.mark.parametrize("spec", ("3.1.0",), indirect=True)
class TestPydanticPlugin:
    class User(BaseModel, metaclass=ModelMetaclass):
        id: int
        name = "John Doe"

    def test_resolve_parameter(self, spec):
        spec.path(
            path="/users/{id}",
            operations=load_specs_from_docstring(
                """
        ---
        get:
            parameters:
                - in: path
                  schema: User
                - in: query
                  name: user
                  content:
                    application/json:
                        schema: User
        """
            ),
        )

        path = utils.get_paths(spec)["/users/{id}"]
        props = self.User.schema()["properties"]
        assert path["get"]["parameters"] == [
            {
                "in": "query",
                "name": "user",
                "content": {"application/json": {"schema": self.User.schema()}},
            },
            {"in": "path", "name": "id", "schema": props["id"], "required": True},
            {"in": "path", "name": "name", "schema": props["name"], "required": True},
        ]

    def test_resolve_request_body(self, spec):
        spec.path(
            path="/users",
            operations=load_specs_from_docstring(
                """
        ---
        post:
            requestBody:
                content:
                    application/json:
                        schema: User
        """
            ),
        )

        path = utils.get_paths(spec)["/users"]
        media_type = path["post"]["requestBody"]["content"]["application/json"]
        assert media_type["schema"]["$ref"] == "#/components/schemas/User"
        assert utils.get_components(spec)["schemas"]["User"] == self.User.schema()

    def test_resolve_callback(self, spec):
        spec.path(
            path="/users",
            operations=load_specs_from_docstring(
                """
        ---
        post:
            callbacks:
                onEvent:
                    /callback:
                        post:
                            requestBody:
                                content:
                                    application/json:
                                        schema: User
        """
            ),
        )

        path = utils.get_paths(spec)["/users"]
        callback = path["post"]["callbacks"]["onEvent"]["/callback"]
        media_type = callback["post"]["requestBody"]["content"]["application/json"]
        assert media_type["schema"]["$ref"] == "#/components/schemas/User"
        assert utils.get_components(spec)["schemas"]["User"] == self.User.schema()

    def test_resolve_single_object_response(self, spec):
        spec.path(
            path="/users/{id}",
            operations=load_specs_from_docstring(
                """
        ---
        get:
            responses:
                200:
                    content:
                        application/json:
                            schema: User
        """
            ),
        )

        path = utils.get_paths(spec)["/users/{id}"]
        media_type = path["get"]["responses"]["200"]["content"]["application/json"]
        assert media_type["schema"]["$ref"] == "#/components/schemas/User"
        assert utils.get_components(spec)["schemas"]["User"] == self.User.schema()

    def test_resolve_multi_object_response(self, spec):
        spec.path(
            path="/users",
            operations=load_specs_from_docstring(
                """
        ---
        get:
            responses:
                200:
                    content:
                        application/json:
                            schema:
                                type: array
                                items: User
        """
            ),
        )

        path = utils.get_paths(spec)["/users"]
        media_type = path["get"]["responses"]["200"]["content"]["application/json"]
        assert media_type["schema"]["items"]["$ref"] == "#/components/schemas/User"
        assert utils.get_components(spec)["schemas"]["User"] == self.User.schema()

    def test_resolve_one_of_object_response(self, spec):
        spec.path(
            path="/users/{id}",
            operations=load_specs_from_docstring(
                """
        ---
        get:
            responses:
                200:
                    content:
                        application/json:
                            schema:
                                oneOf:
                                    - User
                                    - type: array
                                      items: User
        """
            ),
        )

        path = utils.get_paths(spec)["/users/{id}"]
        media_type = path["get"]["responses"]["200"]["content"]["application/json"]
        assert media_type["schema"]["oneOf"] == [
            {"$ref": "#/components/schemas/User"},
            {"type": "array", "items": {"$ref": "#/components/schemas/User"}},
        ]
        assert utils.get_components(spec)["schemas"]["User"] == self.User.schema()

    def test_resolve_response_helper(self, spec):
        spec.path(
            path="/users/{id}",
            operations=load_specs_from_docstring(
                """
        ---
        get:
            responses:
                200:
                    headers:
                        X-User:
                            schema: User
        """
            ),
        )

        path = utils.get_paths(spec)["/users/{id}"]
        schema_ref = path["get"]["responses"]["200"]["headers"]["X-User"]["schema"]
        assert schema_ref["$ref"] == "#/components/schemas/User"
        assert utils.get_components(spec)["schemas"]["User"] == self.User.schema()
