from typing import Optional

import pytest
from apispec import APISpec
from apispec_plugins.base.registry import RegistryMixin
from apispec_plugins.ext.pydantic import PydanticPlugin
from pydantic import BaseModel

from .. import utils


class Pet(BaseModel, RegistryMixin):
    id: Optional[int]
    name: str


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


@pytest.fixture(params=(Pet, Pet(name="Max"), "Pet"))
def schema(request):
    return request.param


class TestPydanticPlugin:
    def test_resolve_parameter(self, spec, schema):
        spec.path(
            path="/pet/{petId}",
            operations={"get": {"parameters": [{"in": "path", "schema": schema}]}},
        )

        path = utils.get_paths(spec)["/pet/{petId}"]
        props = Pet.schema()["properties"]
        assert path["get"]["parameters"] == [
            {"in": "path", "name": "id", "schema": props["id"], "required": True},
            {"in": "path", "name": "name", "schema": props["name"], "required": True},
        ]

    @pytest.mark.parametrize("spec", ("3.1.0",), indirect=True)
    def test_resolve_parameter_v3(self, spec, schema):
        spec.path(
            path="/pet/{petId}",
            operations={
                "get": {
                    "parameters": [
                        {
                            "in": "query",
                            "name": "pet",
                            "content": {"application/json": {"schema": schema}},
                        }
                    ]
                }
            },
        )

        path = utils.get_paths(spec)["/pet/{petId}"]
        assert path["get"]["parameters"] == [
            {
                "in": "query",
                "name": "pet",
                "content": {
                    "application/json": {
                        "schema": utils.build_ref(spec, "schema", "Pet")
                    }
                },
            },
        ]
        assert "Pet" in utils.get_schemas(spec)

    @pytest.mark.parametrize("spec", ("3.1.0",), indirect=True)
    def test_resolve_request_body(self, spec, schema):
        content = {"content": {"application/json": {"schema": schema}}}
        spec.path(
            path="/pet",
            operations={"post": {"requestBody": content}},
        )

        path = utils.get_paths(spec)["/pet"]
        pet_ref = utils.build_ref(spec, "schema", "Pet")
        assert utils.get_schema(spec, base=path["post"]["requestBody"]) == pet_ref
        assert "Pet" in utils.get_schemas(spec)

    @pytest.mark.parametrize("spec", ("3.1.0",), indirect=True)
    def test_resolve_callback(self, spec, schema):
        content = {"content": {"application/json": {"schema": schema}}}
        spec.path(
            path="/pet",
            operations={
                "post": {
                    "callbacks": {
                        "onEvent": {"/callback": {"post": {"requestBody": content}}}
                    }
                }
            },
        )

        path = utils.get_paths(spec)["/pet"]
        callback = path["post"]["callbacks"]["onEvent"]["/callback"]
        pet_ref = utils.build_ref(spec, "schema", "Pet")
        assert utils.get_schema(spec, callback["post"]["requestBody"]) == pet_ref
        assert "Pet" in utils.get_schemas(spec)

    def test_resolve_single_object_response(self, spec, schema):
        response = {"schema": schema}
        if spec.openapi_version.major >= 3:
            response = {"content": {"application/json": response}}
        operations = {"get": {"responses": {"200": response}}}
        spec.path(path="/pet/{petId}", operations=operations)

        path = utils.get_paths(spec)["/pet/{petId}"]
        pet_ref = utils.build_ref(spec, "schema", "Pet")
        assert utils.get_schema(spec, path["get"]["responses"]["200"]) == pet_ref
        assert "Pet" in utils.get_schemas(spec)

    def test_resolve_multi_object_response(self, spec, schema):
        response = {"schema": {"type": "array", "items": schema}}
        if spec.openapi_version.major >= 3:
            response = {"content": {"application/json": response}}
        spec.path(path="/pet", operations={"get": {"responses": {"200": response}}})

        path = utils.get_paths(spec)["/pet"]
        response_ref = utils.get_schema(spec, path["get"]["responses"]["200"])["items"]
        assert response_ref == utils.build_ref(spec, "schema", "Pet")
        assert "Pet" in utils.get_schemas(spec)

    @pytest.mark.parametrize("spec", ("3.1.0",), indirect=True)
    def test_resolve_one_of_object_response(self, spec, schema):
        one_of = [schema, {"type": "array", "items": schema}]
        content = {"content": {"application/json": {"schema": {"oneOf": one_of}}}}
        spec.path(
            path="/pet/{petId}", operations={"get": {"responses": {"200": content}}}
        )

        path = utils.get_paths(spec)["/pet/{petId}"]
        response_ref = utils.get_schema(spec, base=path["get"]["responses"]["200"])
        pet_ref = utils.build_ref(spec, "schema", "Pet")
        assert response_ref["oneOf"] == [pet_ref, {"type": "array", "items": pet_ref}]
        assert "Pet" in utils.get_schemas(spec)

    @pytest.mark.parametrize("spec", ("3.1.0",), indirect=True)
    def test_resolve_response_header(self, spec, schema):
        spec.path(
            path="/pet/{petId}",
            operations={
                "get": {
                    "responses": {"200": {"headers": {"X-Pet": {"schema": schema}}}}
                }
            },
        )

        path = utils.get_paths(spec)["/pet/{petId}"]
        definition = path["get"]["responses"]["200"]["headers"]["X-Pet"]["schema"]
        assert definition == Pet.schema()

    def test_component_schema(self, spec):
        spec.components.schema("Pet", model=Pet)
        assert utils.get_schemas(spec)["Pet"] == Pet.schema()

    def test_component_parameter(self, spec):
        parameter = {"schema": Pet}
        spec.components.parameter("Pet", location="path", component=parameter)

        definition = utils.get_schema(spec, utils.get_parameters(spec)["Pet"])
        assert definition == Pet.schema()

    def test_component_response(self, spec):
        response = {"schema": Pet}
        if spec.openapi_version.major >= 3:
            response = {"content": {"application/json": response}}
        spec.components.response("Pet", component=response)

        pet_ref = utils.build_ref(spec, "schema", "Pet")
        assert utils.get_schema(spec, utils.get_responses(spec)["Pet"]) == pet_ref

    @pytest.mark.parametrize("spec", ("3.1.0",), indirect=True)
    def test_component_header(self, spec):
        header = {"schema": Pet}
        spec.components.header("Pet", component=header)

        definition = utils.get_headers(spec)["Pet"]
        assert utils.get_schema(spec, definition) == Pet.schema()
