from apispec import APISpec
from apispec_plugins.base.registry import Registry


class RegistryMixin(Registry):

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.register(cls)


class DataclassSchemaMixin:

    @classmethod
    def schema(cls):
        try:
            from pydantic.dataclasses import dataclass
            from apispec_plugins.base.registry import Registry
            model = dataclass(cls).__pydantic_model__
            Registry.register(model)
            print(model)
            return model.schema()
        except ImportError:
            from apispec.ext.marshmallow import OpenAPIConverter
            openapi_converter = OpenAPIConverter(
                openapi_version='2.0',
                schema_name_resolver=lambda schema: None,
                spec=APISpec(),
            )
