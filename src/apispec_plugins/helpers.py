from functools import wraps

from apispec import yaml_utils


def spec_from(specs):
    def decorator(func):

        func.__doc__ = yaml_utils.dict_to_yaml(specs)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    return decorator
