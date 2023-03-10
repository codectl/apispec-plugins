import pytest
from apispec import APISpec
from apispec_plugins.base.registry import RegistryMixin
from apispec_plugins.ext.pydantic import PydanticPlugin
from apispec_plugins.utils import load_specs_from_docstring
from pydantic import BaseModel

from .. import utils


@pytest.fixture(scope="function", params=("2.0", "3.1.0"))
def spec(request):
    return APISpec(
        title="Test Suite",
        version="1.0.0",
        openapi_version=request.param,
        plugins=(PydanticPlugin(),),
    )


class TestPydanticPlugin:
    class User(BaseModel, RegistryMixin):
        id: int
        name: str = "John Doe"

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
        """
            ),
        )

        path = utils.get_paths(spec)["/users/{id}"]
        props = self.User.schema()["properties"]
        assert path["get"]["parameters"] == [
            {"in": "path", "name": "id", "schema": props["id"], "required": True},
            {"in": "path", "name": "name", "schema": props["name"], "required": True},
        ]

    @pytest.mark.parametrize("spec", ("3.1.0",), indirect=True)
    @pytest.mark.skip(reason="waiting PR#831 on apispec to be merged")
    def test_resolve_parameter_v3(self, spec):
        spec.path(
            path="/users/{id}",
            operations=load_specs_from_docstring(
                """
        ---
        get:
            parameters:
                - in: query
                  name: user
                  content:
                    application/json:
                        schema: User
        """
            ),
        )

        path = utils.get_paths(spec)["/users/{id}"]
        assert path["get"]["parameters"] == [
            {
                "in": "query",
                "name": "user",
                "content": {"application/json": {"schema": self.User.schema()}},
            },
        ]
        assert utils.get_schemas(spec)["User"] == self.User.schema()

    @pytest.mark.parametrize("spec", ("3.1.0",), indirect=True)
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
        schema_ref = utils.get_schema(spec, base=path["post"]["requestBody"])
        assert schema_ref == utils.build_ref(spec, "schema", "User")
        assert utils.get_schemas(spec)["User"] == self.User.schema()

    @pytest.mark.parametrize("spec", ("3.1.0",), indirect=True)
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
        schema_ref = utils.get_schema(spec, base=callback["post"]["requestBody"])
        assert schema_ref == utils.build_ref(spec, "schema", "User")
        assert utils.get_schemas(spec)["User"] == self.User.schema()

    def test_resolve_single_object_response(self, spec):
        response = {"schema": "User"}
        if spec.openapi_version.major >= 3:
            response = {"content": {"application/json": response}}
        operations = {"get": {"responses": {200: response}}}
        spec.path(path="/users/{id}", operations=operations)

        path = utils.get_paths(spec)["/users/{id}"]
        schema_ref = utils.get_schema(spec, base=path["get"]["responses"]["200"])
        assert schema_ref == utils.build_ref(spec, "schema", "User")
        assert utils.get_schemas(spec)["User"] == self.User.schema()

    def test_resolve_multi_object_response(self, spec):
        response = {"schema": {"type": "array", "items": "User"}}
        if spec.openapi_version.major >= 3:
            response = {"content": {"application/json": response}}
        spec.path(path="/users", operations={"get": {"responses": {200: response}}})

        path = utils.get_paths(spec)["/users"]
        schema_ref = utils.get_schema(spec, base=path["get"]["responses"]["200"])
        assert schema_ref["items"] == utils.build_ref(spec, "schema", "User")
        assert utils.get_schemas(spec)["User"] == self.User.schema()

    @pytest.mark.parametrize("spec", ("3.1.0",), indirect=True)
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
        schema_ref = utils.get_schema(spec, base=path["get"]["responses"]["200"])
        model_ref = utils.build_ref(spec, "schema", "User")
        assert schema_ref["oneOf"] == [model_ref, {"type": "array", "items": model_ref}]
        assert utils.get_schemas(spec)["User"] == self.User.schema()

    @pytest.mark.parametrize("spec", ("3.1.0",), indirect=True)
    def test_resolve_response_header(self, spec):
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
        assert (
            path["get"]["responses"]["200"]["headers"]["X-User"]["schema"]
            == self.User.schema()
        )

    def test_component_schema(self, spec):
        spec.components.schema("User", model=self.User)
        assert utils.get_schemas(spec)["User"] == self.User.schema()

    def test_component_schema_parameter(self, spec):
        parameter = {"schema": self.User}
        spec.components.parameter("User", location="path", component=parameter)

        schema = utils.get_schema(spec, utils.get_parameters(spec)["User"])
        assert schema == self.User.schema()

    @pytest.mark.parametrize("spec", ("3.1.0",), indirect=True)
    @pytest.mark.skip(reason="waiting PR#831 on apispec to be merged")
    def test_component_parameter_v3(self, spec):
        schema = {"schema": self.User}
        parameter = {"content": {"application/json": schema}}
        spec.components.parameter("User", location="path", component=parameter)

        schema_ref = utils.build_ref(spec, "schema", "User")
        assert utils.get_parameters(spec)["User"] == schema_ref

    def test_component_response(self, spec):
        response = {"schema": self.User}
        if spec.openapi_version.major >= 3:
            response = {"content": {"application/json": response}}
        spec.components.response("User", component=response)

        schema_ref = utils.build_ref(spec, "schema", "User")
        assert utils.get_schema(spec, utils.get_responses(spec)["User"]) == schema_ref

    @pytest.mark.parametrize("spec", ("3.1.0",), indirect=True)
    def test_component_header(self, spec):
        header = {"schema": self.User}
        spec.components.header("User", component=header)

        header = utils.get_headers(spec)["User"]
        assert utils.get_schema(spec, header) == self.User.schema()
