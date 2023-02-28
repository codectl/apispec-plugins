class RegistryError(NameError):
    """Raised on every class registry error, for instance,
    when a class lookup does not find the class.
    """


class RegistryBase(type):

    _registry: dict[str, type] = {}

    def __new__(mcs, name, bases, attrs):
        # instantiate a new type corresponding to the type of class being defined
        # this is currently RegisterBase but in child classes will be the child class
        cls = type.__new__(mcs, name, bases, attrs)
        mcs._registry[cls.__name__] = cls
        return cls

    @classmethod
    def get_registry(mcs):
        return dict(mcs._registry)

    @classmethod
    def get_cls(mcs, classname: str) -> type:
        try:
            return mcs._registry[classname]
        except KeyError as error:
            raise RegistryError(
                f"Class with name {classname!r} was not found. You may need "
                "to import the class."
            ) from error
