from importlib import metadata

from .utils import spec_from
from .ext.pydantic import BaseModel, PydanticPlugin
from .webframeworks.flask import FlaskPlugin
from .base.mixin import DataclassSchemaMixin, RegistryMixin

__version__ = metadata.version("apispec-plugins")
__all__ = (
    BaseModel,
    DataclassSchemaMixin,
    FlaskPlugin,
    PydanticPlugin,
    RegistryMixin,
    spec_from,
)
