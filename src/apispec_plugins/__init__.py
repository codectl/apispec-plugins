import pkg_resources
from .utils import spec_from
from .webframeworks.flask import FlaskPlugin

__version__ = pkg_resources.get_distribution("apispec-plugins").version
__all__ = (FlaskPlugin, spec_from)
