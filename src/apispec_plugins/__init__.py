try:
    from importlib import metadata
except ImportError:
    import importlib_metadata as metadata  # python<=3.7

from .utils import spec_from
from .webframeworks.flask import FlaskPlugin

__version__ = metadata.version("apispec-plugins")
__all__ = (FlaskPlugin, spec_from)
