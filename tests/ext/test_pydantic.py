from typing import Optional

import pytest
from apispec import APISpec
from apispec_plugins.base.registry import RegistryMixin
from apispec_plugins.ext.pydantic import PydanticPlugin
from apispec_plugins.utils import load_specs_from_docstring
from pydantic import BaseModel

from .. import utils


@pytest.fixture(params=("2.0", "3.1.0"))
def spec(request):
    return APISpec(
        title="Swagger Petstore",
        version="1.0.0",
        openapi_version=request.param,
        plugins=(PydanticPlugin(),),
        info={
            "description": "This is a sample Pet Store Server based on the OpenAPI "
            "specifications which can be found at https://petstore3.swagger.io."
        },
    )


class TestPydanticPlugin:
    class Pet(BaseModel, RegistryMixin):
        id: Optional[int]
        name: str

    def test_resolve_parameter(self, spec):
        spec.path(
            path="/pet/{petId}",
            operations=load_specs_from_docstring(
                """
        ---
        get:
            parameters:
                - in: path
                  schema: Pet
        """
            ),
        )

        path = utils.get_paths(spec)["/pet/{petId}"]
        props = self.Pet.schema()["properties"]
        assert path["get"]["parameters"] == [
            {"in": "path", "name": "id", "schema": props["id"], "required": True},
            {"in": "path", "name": "name", "schema": props["name"], "required": True},
        ]

    @pytest.mark.parametrize("spec", ("3.1.0",), indirect=True)
    @pytest.mark.skip(reason="waiting PR#831 on apispec to be merged")
    def test_resolve_parameter_v3(self, spec):
        spec.path(
            path="/pet/{petId}",
            operations=load_specs_from_docstring(
                """
        ---
        get:
            parameters:
                - in: query
                  name: pet
                  content:
                    application/json:
                        schema: Pet
        """
            ),
        )

        path = utils.get_paths(spec)["/pet/{petId}"]
        assert path["get"]["parameters"] == [
            {
                "in": "query",
                "name": "pet",
                "content": {"application/json": {"schema": self.Pet.schema()}},
            },
        ]
        assert utils.get_schemas(spec)["Pet"] == self.Pet.schema()

    @pytest.mark.parametrize("spec", ("3.1.0",), indirect=True)
    def test_resolve_request_body(self, spec):
        spec.path(
            path="/pet",
            operations=load_specs_from_docstring(
                """
        ---
        post:
            requestBody:
                content:
                    application/json:
                        schema: Pet
        """
            ),
        )

        path = utils.get_paths(spec)["/pet"]
        schema_ref = utils.get_schema(spec, base=path["post"]["requestBody"])
        assert schema_ref == utils.build_ref(spec, "schema", "Pet")
        assert utils.get_schemas(spec)["Pet"] == self.Pet.schema()

    @pytest.mark.parametrize("spec", ("3.1.0",), indirect=True)
    def test_resolve_callback(self, spec):
        spec.path(
            path="/pet",
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
                                        schema: Pet
        """
            ),
        )

        path = utils.get_paths(spec)["/pet"]
        callback = path["post"]["callbacks"]["onEvent"]["/callback"]
        schema_ref = utils.get_schema(spec, base=callback["post"]["requestBody"])
        assert schema_ref == utils.build_ref(spec, "schema", "Pet")
        assert utils.get_schemas(spec)["Pet"] == self.Pet.schema()

    def test_resolve_single_object_response(self, spec):
        response = {"schema": "Pet"}
        if spec.openapi_version.major >= 3:
            response = {"content": {"application/json": response}}
        operations = {"get": {"responses": {200: response}}}
        spec.path(path="/pet/{petId}", operations=operations)

        path = utils.get_paths(spec)["/pet/{petId}"]
        schema_ref = utils.get_schema(spec, base=path["get"]["responses"]["200"])
        assert schema_ref == utils.build_ref(spec, "schema", "Pet")
        assert utils.get_schemas(spec)["Pet"] == self.Pet.schema()

    def test_resolve_multi_object_response(self, spec):
        response = {"schema": {"type": "array", "items": "Pet"}}
        if spec.openapi_version.major >= 3:
            response = {"content": {"application/json": response}}
        spec.path(path="/pet", operations={"get": {"responses": {200: response}}})

        path = utils.get_paths(spec)["/pet"]
        schema_ref = utils.get_schema(spec, base=path["get"]["responses"]["200"])
        assert schema_ref["items"] == utils.build_ref(spec, "schema", "Pet")
        assert utils.get_schemas(spec)["Pet"] == self.Pet.schema()

    @pytest.mark.parametrize("spec", ("3.1.0",), indirect=True)
    def test_resolve_one_of_object_response(self, spec):
        spec.path(
            path="/pet/{petId}",
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
                                    - Pet
                                    - type: array
                                      items: Pet
        """
            ),
        )

        path = utils.get_paths(spec)["/pet/{petId}"]
        schema_ref = utils.get_schema(spec, base=path["get"]["responses"]["200"])
        model_ref = utils.build_ref(spec, "schema", "Pet")
        assert schema_ref["oneOf"] == [model_ref, {"type": "array", "items": model_ref}]
        assert utils.get_schemas(spec)["Pet"] == self.Pet.schema()

    @pytest.mark.parametrize("spec", ("3.1.0",), indirect=True)
    def test_resolve_response_header(self, spec):
        spec.path(
            path="/pet/{petId}",
            operations=load_specs_from_docstring(
                """
        ---
        get:
            responses:
                200:
                    headers:
                        X-Pet:
                            schema: Pet
        """
            ),
        )

        path = utils.get_paths(spec)["/pet/{petId}"]
        assert (
            path["get"]["responses"]["200"]["headers"]["X-Pet"]["schema"]
            == self.Pet.schema()
        )

    def test_component_schema(self, spec):
        spec.components.schema("Pet", model=self.Pet)
        assert utils.get_schemas(spec)["Pet"] == self.Pet.schema()

    def test_component_schema_parameter(self, spec):
        parameter = {"schema": self.Pet}
        spec.components.parameter("Pet", location="path", component=parameter)

        schema = utils.get_schema(spec, utils.get_parameters(spec)["Pet"])
        assert schema == self.Pet.schema()

    @pytest.mark.parametrize("spec", ("3.1.0",), indirect=True)
    @pytest.mark.skip(reason="waiting PR#831 on apispec to be merged")
    def test_component_parameter_v3(self, spec):
        schema = {"schema": self.Pet}
        parameter = {"content": {"application/json": schema}}
        spec.components.parameter("Pet", location="path", component=parameter)

        schema_ref = utils.build_ref(spec, "schema", "Pet")
        assert utils.get_parameters(spec)["Pet"] == schema_ref

    def test_component_response(self, spec):
        response = {"schema": self.Pet}
        if spec.openapi_version.major >= 3:
            response = {"content": {"application/json": response}}
        spec.components.response("Pet", component=response)

        schema_ref = utils.build_ref(spec, "schema", "Pet")
        assert utils.get_schema(spec, utils.get_responses(spec)["Pet"]) == schema_ref

    @pytest.mark.parametrize("spec", ("3.1.0",), indirect=True)
    def test_component_header(self, spec):
        header = {"schema": self.Pet}
        spec.components.header("Pet", component=header)

        header = utils.get_headers(spec)["Pet"]
        assert utils.get_schema(spec, header) == self.Pet.schema()
