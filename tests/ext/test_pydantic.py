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

    def test_resolve_response_single_object(self, spec):
        mime = "application/json"
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
        schema_ref = path["get"]["responses"]["200"]["content"][mime]["schema"]
        assert schema_ref["$ref"] == "#/components/schemas/User"
        assert utils.get_components(spec)["schemas"]["User"] == self.User.schema()

    def test_resolve_response_multi_object(self, spec):
        mime = "application/json"
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
        schema_ref = path["get"]["responses"]["200"]["content"][mime]["schema"]["items"]
        assert schema_ref["$ref"] == "#/components/schemas/User"
        assert utils.get_components(spec)["schemas"]["User"] == self.User.schema()
