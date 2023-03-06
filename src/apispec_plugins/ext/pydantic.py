from __future__ import annotations

from typing import Any

from apispec import BasePlugin, APISpec
from apispec.exceptions import APISpecError, DuplicateComponentNameError
from apispec_plugins.base import registry
from pydantic import BaseModel


class PydanticPlugin(BasePlugin):
    def __init__(self):
        self.spec = None
        self.resolver = None

    def init_spec(self, spec: APISpec):
        super().init_spec(spec)
        self.spec = spec
        self.resolver = OASResolver(spec=spec)

    def schema_helper(self, name: str, definition: dict, **kwargs: Any) -> dict | None:
        model: BaseModel | None = kwargs.pop("model", None)
        if not model:
            return None

        return self.resolver.oas_convert(model)

    def response_helper(self, response: dict, **kwargs: Any) -> dict | None:
        self.resolver.resolve_response(response)
        return response

    def parameter_helper(self, parameter: dict, **kwargs: Any) -> dict | None:
        self.resolver.resolve_parameter(parameter)
        return parameter

    def header_helper(self, header: dict, **kwargs: Any) -> dict | None:
        self.resolver.resolve_header(header)
        return header

    def operation_helper(
        self,
        path: str | None = None,
        operations: dict | None = None,
        **kwargs: Any,
    ) -> None:
        for operation in (operations or {}).values():
            self.resolver.resolve_operation(operation)


class OASResolver:
    def __init__(self, spec: APISpec):
        self.spec = spec

    def resolve_operation(self, operation: dict):
        # if "parameters" in operation:
        #     operation["parameters"] = self.resolve_parameters(
        #         operation["parameters"]
        #     )
        for response in operation.get("responses", {}).values():
            self.resolve_response(response)

        # props that are OAS 3 only
        if self.spec.openapi_version.major >= 3:
            for callback in operation.get("callbacks", {}).values():
                self.resolve_callback(callback)
            if "requestBody" in operation:
                self.resolve_response(operation["requestBody"])

    def resolve_callback(self, callback: dict):
        for event in callback.values():
            for operation in (event or {}).values():
                self.resolve_operation(operation)

    def resolve_parameters(self, parameters: list[dict]):
        for parameter in parameters:
            if "schema" in parameter and not isinstance(parameter["schema"], dict):
                schema = self.resolve_schema_instance(parameter["schema"])

    def resolve_response(self, response: dict):
        if self.spec.openapi_version.major < 2:
            if "schema" in response:
                self.resolve_schema(response["schema"])
        if self.spec.openapi_version.major >= 3:
            if "content" in response:
                for media_type in response["content"].values():
                    self.resolve_schema(media_type["schema"])

    def resolve_schema(self, schema: dict | str, use_ref=True) -> str | dict:
        if isinstance(schema, dict):
            if schema.get("type") == "array" and "items" in schema:
                schema["items"] = self.resolve_schema(schema["items"], use_ref=use_ref)
            elif schema.get("type") == "object" and "properties" in schema:
                schema["properties"] = {
                    k: self.resolve_schema(v, use_ref=use_ref)
                    for k, v in schema["properties"].items()
                }
            for keyword in ("oneOf", "anyOf", "allOf"):
                if keyword in schema:
                    schema[keyword] = [self.resolve_schema(s) for s in schema[keyword]]
            return schema
        elif isinstance(schema, str):
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
                return self.oas_convert(model)

    def register_model(self, model: BaseModel | type[BaseModel]) -> None:
        try:
            self.spec.components.schema(component_id=model.__name__, model=model)
        except DuplicateComponentNameError:
            # suppress duplicate model registration
            pass

    @staticmethod
    def oas_convert(model: BaseModel | type[BaseModel]) -> dict:
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
