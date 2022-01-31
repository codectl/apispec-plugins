from functools import wraps

from apispec import yaml_utils


def spec_from(specs):

    # character sequence used by APISpec to separate
    # yaml specs from the rest of the method docstring
    yaml_sep = '---'

    def decorator(func):

        docstring = func.__doc__
        summary = docstring.split(yaml_sep)[0] if docstring else None
        if 'summary' not in specs and summary:
            specs['summary'] = summary.strip()

        yaml_specs = yaml_utils.dict_to_yaml(specs)
        yaml_specs = f"{yaml_sep}\n{yaml_specs}"
        func.__doc__ = yaml_specs

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    return decorator
