from __future__ import annotations

import contextlib
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

        return self.resolver.resolve_schema(model, use_ref=False)

    def parameter_helper(self, parameter: dict, **kwargs: Any) -> dict | None:
        self.resolver.resolve_parameters([parameter])
        return parameter

    def response_helper(self, response: dict, **kwargs: Any) -> dict | None:
        self.resolver.resolve_response(response)
        return response

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

    def resolve_schema_props(self, props: dict, use_ref: bool) -> None:
        if "schema" in props:
            props["schema"] = self.resolve_schema(props["schema"], use_ref=use_ref)
        elif props.get("type") == "array" and "items" in props:
            props["items"] = self.resolve_schema(props["items"], use_ref=use_ref)
        elif props.get("type") == "object" and "properties" in props:
            props["properties"] = {
                k: self.resolve_schema_props(v, use_ref=use_ref)
                for k, v in props["properties"].items()
            }
        for kw in ("oneOf", "anyOf", "allOf"):
            if kw in props:
                props[kw] = [self.resolve_schema(s, use_ref=use_ref) for s in props[kw]]

    def resolve_schema(
        self, schema: dict | str | BaseModel | type[BaseModel], use_ref=True
    ) -> str | dict:
        if isinstance(schema, dict):
            self.resolve_schema_props(schema, use_ref=use_ref)
            return schema
        elif isinstance(schema, (str, BaseModel, type(BaseModel))):
            model = self.resolve_schema_instance(schema)
            if model is None:
                raise APISpecError(
                    f"Schema resolver returned None for schema {schema!r}. Either the"
                    " schema was not registered or it is not a pydantic schema."
                )
            # register schema as a component or resolve it inline
            if use_ref:
                self.register_model(model)
                return self.resolve_schema_name(schema)
            else:
                return self.to_schema(model)

    def resolve_parameters(self, parameters: list[dict]) -> None:
        params = []
        for parameter in parameters:
            if "schema" in parameter and not isinstance(parameter["schema"], dict):
                self.resolve_schema(parameter, use_ref=False)
                for name, props in parameter["schema"]["properties"].items():
                    param = {"in": parameter["in"], "name": name, "schema": props}
                    params.append(param)
            elif "content" in parameter:
                for media_type in parameter["content"].values():
                    self.resolve_schema(media_type)
                params.append(parameter)
        parameters[:] = params[:]

    def resolve_response(self, response: dict) -> None:
        if self.spec.openapi_version.major < 3:
            if "schema" in response:
                self.resolve_schema(response)
        elif self.spec.openapi_version.major >= 3:
            if "headers" in response:
                for header in response["headers"].values():
                    self.resolve_schema(header, use_ref=False)
            if "content" in response:
                for media_type in response["content"].values():
                    self.resolve_schema(media_type)

    def resolve_header(self, header: dict) -> None:
        self.resolve_schema(header, use_ref=False)

    def resolve_operation(self, operation: dict) -> None:
        if "parameters" in operation:
            self.resolve_parameters(operation["parameters"])
        for response in operation.get("responses", {}).values():
            self.resolve_response(response)

        # props that are OAS 3 only
        if self.spec.openapi_version.major >= 3:
            for callback in operation.get("callbacks", {}).values():
                self.resolve_callback(callback)
            if "requestBody" in operation:
                self.resolve_response(operation["requestBody"])

    def resolve_callback(self, callback: dict) -> None:
        for event in callback.values():
            for operation in (event or {}).values():
                self.resolve_operation(operation)

    def register_model(self, model: BaseModel | type[BaseModel]) -> None:
        # suppress duplicate model registration
        with contextlib.suppress(DuplicateComponentNameError):
            self.spec.components.schema(component_id=model.__name__, model=model)

    @staticmethod
    def to_schema(model: BaseModel | type[BaseModel]) -> dict:
        """The pydantic model conversion to OAS is performed by pydentic itself."""
        return model.schema()

    @classmethod
    def resolve_schema_instance(
        cls, schema: str | BaseModel | type[BaseModel] | None
    ) -> type[BaseModel] | None:
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            return schema
        elif isinstance(schema, BaseModel):
            return schema.__class__
        elif isinstance(schema, str):
            return registry.RegistryMixin.get_cls(schema)
        return None

    @classmethod
    def resolve_schema_name(cls, schema: str | BaseModel | type[BaseModel]) -> str:
        if isinstance(schema, str):
            return schema
        elif isinstance(schema, BaseModel):
            return schema.__class__.__name__
        elif isinstance(schema, type(BaseModel)):
            return schema.__name__
