from functools import wraps

from apispec import yaml_utils


def spec_from(specs):

    def decorator(func):

        method_specs = load_specs_from_docstring(func.__doc__)

        # merge specs prioritizing decorator specs
        method_specs.update(specs)

        func.__doc__ = yaml_utils.dict_to_yaml(method_specs)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    return decorator


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
