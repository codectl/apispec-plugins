import functools
import re
import typing
import urllib.parse
from collections.abc import Sequence
from dataclasses import MISSING, asdict, fields

from apispec import yaml_utils

from apispec_plugins.base import types

__all__ = (
    "spec_from",
    "load_method_specs",
    "load_specs_from_docstring",
    "path_parser",
    "dataclass_schema_resolver",
    "base_template",
)


def spec_from(specs):
    def decorator(func):

        docstring_specs = load_specs_from_docstring(func.__doc__)

        # merge specs prioritizing decorator specs
        docstring_specs.update(specs)

        func.specs = docstring_specs

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


def load_method_specs(method):
    if hasattr(method, "specs"):
        return method.specs
    else:
        return load_specs_from_docstring(method.__doc__)


def load_specs_from_docstring(docstring):
    """Get dict APISpec from any given docstring."""

    # character sequence used by APISpec to separate
    # yaml specs from the rest of the method docstring
    yaml_sep = "---"

    if not docstring:
        return {}

    specs = yaml_utils.load_yaml_from_docstring(docstring)

    # extract summary out of docstring and make it part of specs
    summary = docstring.split(yaml_sep)[0] if yaml_sep in docstring else docstring
    if (
        summary
        and not any(key in yaml_utils.PATH_KEYS for key in specs.keys())
        and "summary" not in specs
    ):
        specs["summary"] = summary.strip()  # sanitize

    return specs


def path_parser(path, **kwargs):
    """Make rule path OpenAPI specs compliant."""
    reg = r"<([^<>]*:)?([^<>]*)>"
    parsed = re.sub(reg, r"{\2}", path)

    base_path = kwargs.get("base_path", "")
    parsed = parsed[len(base_path) :] if parsed.startswith(base_path) else parsed
    parsed = urllib.parse.urljoin("/", parsed)

    return parsed


def dataclass_schema_resolver(schema):
    """A schema resolver for dataclasses."""

    def _resolve_field_type(f):
        if f.type == str:
            return "string"
        if f.type == int:
            return "integer"
        if f.type == float:
            return "number"
        if f.type == bool:
            return "boolean"
        elif isinstance(field.type, Sequence):
            return "array"
        return "object"

    definition = {"type": "object", "properties": {}, "required": []}
    for field in fields(schema):
        name = field.name
        definition["properties"][name] = {"type": _resolve_field_type(field)}
        if field.default == MISSING and field.default_factory == MISSING:
            definition["required"].append(name)
    return definition


def base_template(
    openapi_version: str,
    info: dict = None,
    servers: typing.List[types.Server] = (),
    auths: typing.List[types.AuthSchemes.BasicAuth] = (),
    tags: typing.List[types.Tag] = (),
):
    """Provide a base OpenAPI template."""

    return {
        "openapi": openapi_version,
        "info": info or {},
        "servers": servers,
        "tags": tags,
        "components": {
            "securitySchemes": {
                **{type(auth).__name__: asdict(auth) for auth in auths}
            },
        },
    }
