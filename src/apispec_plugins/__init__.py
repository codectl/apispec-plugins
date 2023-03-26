from importlib import metadata

from .utils import spec_from
from .ext.pydantic import PydanticPlugin
from .webframeworks.flask import FlaskPlugin
from .base.mixin import DataclassSchemaMixin, RegistryMixin

__version__ = metadata.version("apispec-plugins")
__all__ = (
    DataclassSchemaMixin,
    FlaskPlugin,
    PydanticPlugin,
    RegistryMixin,
    spec_from,
)
