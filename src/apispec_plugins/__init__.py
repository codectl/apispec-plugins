from importlib import metadata

from .utils import spec_from
from .ext.pydantic import PydanticPlugin
from .webframeworks.flask import FlaskPlugin

__version__ = metadata.version("apispec-plugins")
__all__ = (FlaskPlugin, PydanticPlugin, spec_from)
