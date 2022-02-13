import importlib.metadata
from .utils import spec_from
from .webframeworks.flask import FlaskPlugin

__version__ = importlib.metadata.version("apispec-plugins")
__all__ = (FlaskPlugin, spec_from)
