from __future__ import annotations

from typing import Any

from apispec import BasePlugin, APISpec
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

        return model.schema()

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
        return self.resolve_schema(response)

    def resolve_schema(self, data: str | dict, use_ref=True) -> None:
        if self.spec.openapi_version.major >= 3 and "content" in data:
            for media_type in data["content"].values():
                self.resolve_schema(media_type)
        if "schema" in data:
            schema_data = data["schema"]
            schema_instance = self.resolve_schema_instance(schema_data)
            if schema_instance is not None:
                # register schema as a component or resolve it inline
                if use_ref:
                    self.register_schema(schema=schema_instance)
                else:
                    data["schema"] = schema_instance.schema()

    def register_schema(self, schema: type[BaseModel]):
        self.spec.components.schema(component_id=schema.__name__, model=schema)

    @classmethod
    def resolve_schema_instance(
        cls, schema: str | BaseModel | type[BaseModel]
    ) -> type[BaseModel] | None:
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            return schema
        if isinstance(schema, BaseModel):
            return schema.__class__
        if isinstance(schema, str):
            return registry.ModelMetaclass.get_cls(schema)
        return None
