import pytest
from apispec import APISpec
from apispec.exceptions import DuplicateComponentNameError
from apispec_plugins.ext.pydantic import PydanticPlugin

from ..conftest import Pet
from ..utils import (
    build_ref,
    get_headers,
    get_parameters,
    get_paths,
    get_responses,
    get_schema,
    get_schemas,
)


@pytest.fixture(params=("2.0", "3.0.3"))
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
            operations={
                "get": {
                    "parameters": [
                        {"in": "path", "name": "petId", "schema": {"type": "string"}},
                        {"in": "path", "schema": schema},
                    ]
                }
            },
        )

        path = get_paths(spec)["/pet/{petId}"]
        props = Pet.schema()["properties"]
        required = {"required": True}
        assert path["get"]["parameters"] == [
            {"in": "path", "name": "petId", "schema": {"type": "string"}, **required},
            {"in": "path", "name": "id", "schema": props["id"], **required},
            {"in": "path", "name": "name", "schema": props["name"], **required},
        ]

    @pytest.mark.parametrize("spec", ("3.0.3",), indirect=True)
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

        path = get_paths(spec)["/pet/{petId}"]
        assert path["get"]["parameters"] == [
            {
                "in": "query",
                "name": "pet",
                "content": {
                    "application/json": {"schema": build_ref(spec, "schema", "Pet")}
                },
            },
        ]
        assert "Pet" in get_schemas(spec)

    @pytest.mark.parametrize("spec", ("3.0.3",), indirect=True)
    def test_resolve_request_body(self, spec, schema):
        content = {"content": {"application/json": {"schema": schema}}}
        spec.path(
            path="/pet",
            operations={"post": {"requestBody": content}},
        )

        path = get_paths(spec)["/pet"]
        pet_ref = build_ref(spec, "schema", "Pet")
        assert get_schema(spec, base=path["post"]["requestBody"]) == pet_ref
        assert "Pet" in get_schemas(spec)

    @pytest.mark.parametrize("spec", ("3.0.3",), indirect=True)
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

        path = get_paths(spec)["/pet"]
        callback = path["post"]["callbacks"]["onEvent"]["/callback"]
        pet_ref = build_ref(spec, "schema", "Pet")
        assert get_schema(spec, callback["post"]["requestBody"]) == pet_ref
        assert "Pet" in get_schemas(spec)

    def test_resolve_single_object_response(self, spec, schema):
        response = {"schema": schema}
        if spec.openapi_version.major >= 3:
            response = {"content": {"application/json": response}}
        operations = {"get": {"responses": {"200": response}}}
        spec.path(path="/pet/{petId}", operations=operations)

        path = get_paths(spec)["/pet/{petId}"]
        pet_ref = build_ref(spec, "schema", "Pet")
        assert get_schema(spec, path["get"]["responses"]["200"]) == pet_ref
        assert "Pet" in get_schemas(spec)

    def test_resolve_multi_object_response(self, spec, schema):
        response = {"schema": {"type": "array", "items": schema}}
        if spec.openapi_version.major >= 3:
            response = {"content": {"application/json": response}}
        spec.path(path="/pet", operations={"get": {"responses": {"200": response}}})

        path = get_paths(spec)["/pet"]
        response_ref = get_schema(spec, path["get"]["responses"]["200"])["items"]
        assert response_ref == build_ref(spec, "schema", "Pet")
        assert "Pet" in get_schemas(spec)

    @pytest.mark.parametrize("spec", ("3.0.3",), indirect=True)
    def test_resolve_one_of_object_response(self, spec, schema):
        one_of = [schema, {"type": "array", "items": schema}]
        content = {"content": {"application/json": {"schema": {"oneOf": one_of}}}}
        spec.path(
            path="/pet/{petId}", operations={"get": {"responses": {"200": content}}}
        )

        path = get_paths(spec)["/pet/{petId}"]
        response_ref = get_schema(spec, base=path["get"]["responses"]["200"])
        pet_ref = build_ref(spec, "schema", "Pet")
        assert response_ref["oneOf"] == [pet_ref, {"type": "array", "items": pet_ref}]
        assert "Pet" in get_schemas(spec)

    @pytest.mark.parametrize("spec", ("3.0.3",), indirect=True)
    def test_resolve_response_header(self, spec, schema):
        spec.path(
            path="/pet/{petId}",
            operations={
                "get": {
                    "responses": {"200": {"headers": {"X-Pet": {"schema": schema}}}}
                }
            },
        )

        path = get_paths(spec)["/pet/{petId}"]
        definition = path["get"]["responses"]["200"]["headers"]["X-Pet"]["schema"]
        assert isinstance(definition, dict)
        assert "properties" in definition

    def test_component_schema(self, spec, schema):
        spec.components.schema("Pet", model=schema)
        assert "Pet" in get_schemas(spec)

    def test_component_duplicate_schema_raises_error(self, spec, schema):
        spec.components.schema("Pet", model=schema)
        with pytest.raises(DuplicateComponentNameError):
            spec.components.schema("Pet", model=schema)

    def test_component_parameter(self, spec, schema):
        parameter = {"schema": schema}
        spec.components.parameter("Pet", location="path", component=parameter)
        assert "Pet" in get_parameters(spec)

    def test_component_response(self, spec, schema):
        response = {"schema": schema}
        if spec.openapi_version.major >= 3:
            response = {"content": {"application/json": response}}
        spec.components.response("Pet", component=response)

        pet_ref = build_ref(spec, "schema", "Pet")
        assert get_schema(spec, get_responses(spec)["Pet"]) == pet_ref

    @pytest.mark.parametrize("spec", ("3.0.3",), indirect=True)
    def test_component_header(self, spec, schema):
        header = {"schema": schema}
        spec.components.header("Pet", component=header)
        assert "Pet" in get_headers(spec)
