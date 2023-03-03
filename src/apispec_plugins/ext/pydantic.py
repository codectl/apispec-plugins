from __future__ import annotations

from typing import Any

from apispec import BasePlugin, APISpec
from apispec.exceptions import APISpecError
from apispec_plugins.base import registry
from pydantic import BaseModel


class PydanticPlugin(BasePlugin):
    def __init__(self):
        self.spec = None
        self.resolver = None

    def init_spec(self, spec: APISpec):
        super().init_spec(spec)
        self.spec = spec
        self.resolver = OpenAPIResolver(spec=spec)

    def schema_helper(self, name: str, definition: dict, **kwargs: Any) -> None | dict:
        model: BaseModel | None = kwargs.pop("model", None)
        if not model:
            return None

        return self.resolver.model_spec_conversion(model)

    def operation_helper(
        self, path: str | None = None, operations: dict | None = None, **kwargs: Any
    ):
        for operation in (operations or {}).values():
            if "parameters" in operation:
                operation["parameters"] = self.resolver.resolve_parameters(
                    operation["parameters"]
                )
            # if self.openapi_version.major >= 3:
            #     self.resolve_callback(operation.get("callbacks", {}))
            #     if "requestBody" in operation:
            #         self.resolve_schema(operation["requestBody"])
            for response in operation.get("responses", {}).values():
                self.resolver.resolve_response(response)


class OpenAPIResolver:
    def __init__(self, spec: APISpec):
        self.spec = spec

    def resolve_parameters(self, parameters: list[dict]):
        for parameter in parameters:
            if "schema" in parameter and not isinstance(parameter["schema"], dict):
                schema = self.resolve_schema_instance(parameter["schema"])

    def resolve_response(self, response: dict):
        return self.resolve_nested_schemas(response)

    def resolve_schema(self, schema: dict | str, use_ref=True) -> str | dict:
        if isinstance(schema, str):
            model = self.resolve_schema_instance(schema)
            if model is None:
                raise APISpecError(
                    f"Schema resolver returned None for schema {schema!r}. Either the"
                    " schema was not registered or it is not a pydantic schema."
                )
            # register schema as a component or resolve it inline
            if use_ref:
                self.register_model(model)
                return schema
            else:
                return self.model_spec_conversion(model)
        return self.resolve_nested_schemas(schema, use_ref=use_ref)

    def resolve_nested_schemas(self, data: dict, use_ref=True) -> dict:

        # OAS 2 and OAS 3 common props
        if "schema" in data:
            data["schema"] = self.resolve_schema(data["schema"], use_ref=use_ref)
        elif data.get("type") == "array" and "items" in data:
            data["items"] = self.resolve_schema(data["items"], use_ref=use_ref)

        # OAS 3 content property
        if self.spec.openapi_version.major >= 3 and "content" in data:
            for media_type in data["content"].values():
                self.resolve_nested_schemas(media_type, use_ref=use_ref)
        return data

    def register_model(self, model: BaseModel | type[BaseModel]) -> None:
        self.spec.components.schema(component_id=model.__name__, model=model)

    @staticmethod
    def model_spec_conversion(model: BaseModel | type[BaseModel]) -> dict:
        """The pydantic model conversion to OAS is performed by pydentic itself."""
        return model.schema()

    @classmethod
    def resolve_schema_instance(
        cls, schema: str | BaseModel | type[BaseModel] | None
    ) -> type[BaseModel] | None:
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            return schema
        if isinstance(schema, BaseModel):
            return schema.__class__
        if isinstance(schema, str):
            return registry.ModelMetaclass.get_cls(schema)
        return None
