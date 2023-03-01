import pytest
from apispec import APISpec
from apispec_plugins.base.registry import ModelMetaclass
from apispec_plugins.ext.pydantic import PydanticPlugin
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

    def test_resolve_response(self, spec):
        media = "application/json"
        spec.path(path="/users/{id}", operations={
            "get": {"responses": {200: {"content": {media: {"schema": "User"}}}}}
        })

        path = utils.get_paths(spec)["/users/{id}"]
        schema_ref = path["get"]["responses"]["200"]["content"][media]["schema"]
        assert schema_ref["$ref"] == "#/components/schemas/User"
        assert utils.get_components(spec)["schemas"]["User"] == User.schema()
