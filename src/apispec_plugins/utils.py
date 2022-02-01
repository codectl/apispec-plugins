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
    if hasattr(method, 'specs'):
        return method.specs
    else:
        return load_specs_from_docstring(method.__doc__)


def load_specs_from_docstring(docstring):

    # character sequence used by APISpec to separate
    # yaml specs from the rest of the method docstring
    yaml_sep = '---'

    if not docstring:
        return {}

    specs = yaml_utils.load_yaml_from_docstring(docstring)
    summary = docstring.split(yaml_sep)[0] if yaml_sep in docstring else docstring
    if 'summary' not in specs and summary:
        specs['summary'] = summary.strip()

    return specs
