from dataclasses import MISSING, dataclass, fields
from typing import Type, get_args

from apispec import APISpec
from apispec.ext.marshmallow.openapi import OpenAPIConverter, marshmallow as ma
from apispec_plugins.base.registry import Registry


class RegistryMixin(Registry):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.register(cls)


class DataclassSchemaMixin:
    @classmethod
    def schema(cls):

        # resolve pydantic schema
        model = getattr(cls, "__pydantic_model__")
        if model:
            Registry.register(model)
            return model.schema()

        # or fallback to marshmallow resolver
        return cls.dataclass_schema()

    @classmethod
    def dataclass_schema(cls, openapi_version="2.0"):
        openapi_converter = OpenAPIConverter(
            openapi_version=openapi_version,
            schema_name_resolver=lambda f: None,
            spec=APISpec("", "", openapi_version),
        )

        def schema_type(t):
            return ma.Schema.TYPE_MAPPING[next(iter(get_args(t)), t)]

        schema_dict = {
            f.name: schema_type(f.type)(data_key=f.name, required=f.default is MISSING)
            for f in fields(cls)
        }
        schema = ma.Schema.from_dict(schema_dict)
        return openapi_converter.schema2jsonschema(schema)
