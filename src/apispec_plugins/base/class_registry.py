_registry: dict[str, type] = {}


class RegistryError(NameError):
    """Raised on every class registry error, for instance,
    when a class lookup does not find the class.
    """


def register(classname: str, cls: type) -> None:
    if classname not in _registry:
        _registry[classname] = cls


def get_class(classname: str) -> type:
    try:
        return _registry[classname]
    except KeyError as error:
        raise RegistryError(
            f"Class with name {classname!r} was not found. You may need "
            "to import the class."
        ) from error
