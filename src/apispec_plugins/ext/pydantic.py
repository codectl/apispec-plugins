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

    # def schema_helper(self, name: str, definition: dict, **kwargs: Any) -> None | dict:
    #     model: None | BaseModel = kwargs.pop("model", None)
    #     if not model:
    #         return None
    #
    #     schema = model.schema(ref_template="#/components/schemas/{model}")
    #
    #     if "definitions" in schema:
    #         for k, v in schema["definitions"].items():
    #             try:
    #                 self.spec.components.schema(k, v)
    #             except DuplicateComponentNameError:
    #                 pass
    #
    #     if "definitions" in schema:
    #         del schema["definitions"]
    #
    #     return schema

    def operation_helper(
        self, path: str | None = None, operations: dict | None = None, **kwargs: Any
    ):
        from pprint import pprint

        # pprint(operations)

        for operation in (operations or {}).values():
            if not isinstance(operation, dict):
                continue

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

    def resolve_schema(self, data: str | dict) -> None:
        if self.spec.openapi_version.major >= 3 and "content" in data:
            for media_type in data["content"].values():
                self.resolve_schema(media_type)
        if "schema" in data:
            schema_data = data["schema"]
            schema_instance = self.resolve_schema_instance(schema_data)
            # register schema
            if schema_instance:
                self.spec.components.schema(
                    component_id=data["schema"],
                    component=schema_instance.schema()
                )

    @classmethod
    def resolve_schema_instance(
        cls, schema: str | BaseModel | type[BaseModel]
    ) -> type[BaseModel] | None:
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            return schema
        if isinstance(schema, BaseModel):
            return schema.__class__
        if isinstance(schema, str):
            return registry.PydanticRegistry.get_cls(schema)
        return None
