from typing import TypeVar

from pydantic import BaseModel

__all__ = (
    "RegistryMixin",
    "ModelMetaclass",
    "RegistryError",
)

T = TypeVar("T")


class RegistryMixin(type):

    _registry: dict[str, T] = {}

    def __new__(mcs, name, bases, attrs):
        cls = type.__new__(mcs, name, bases, attrs)
        mcs._registry[cls.__name__] = cls
        return cls

    @classmethod
    def get_registry(mcs):
        return mcs._registry

    @classmethod
    def get_cls(mcs, classname: str) -> T:
        try:
            return mcs._registry[classname]
        except KeyError as error:
            raise RegistryError(
                f"Class with name {classname!r} was not found. You may need "
                "to import the class."
            ) from error


class ModelMetaclass(type(BaseModel), RegistryMixin):
    """Harness registry metaclass for pydantic"""


class RegistryError(NameError):
    """Raised on every class registry error, for instance,
    when a class lookup does not find the class.
    """
