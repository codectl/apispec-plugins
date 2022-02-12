import re
from functools import wraps

from apispec import yaml_utils


def spec_from(specs):
    def decorator(func):

        docstring_specs = load_specs_from_docstring(func.__doc__)

        # merge specs prioritizing decorator specs
        docstring_specs.update(specs)

        func.specs = docstring_specs

        @wraps(func)
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

    return parsed
